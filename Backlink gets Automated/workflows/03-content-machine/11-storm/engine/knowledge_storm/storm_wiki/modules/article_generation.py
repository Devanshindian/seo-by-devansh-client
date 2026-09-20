import concurrent.futures
import copy
import logging
from concurrent.futures import as_completed
from typing import List, Union

import dspy

from .callback import BaseCallbackHandler
from .storm_dataclass import StormInformationTable, StormArticle
from ... import brief
from ...interface import ArticleGenerationModule, Information
from ...utils import ArticleTextProcessing


class StormArticleGenerationModule(ArticleGenerationModule):
    """
    The interface for article generation stage. Given topic, collected information from
    knowledge curation stage, generated outline from outline generation stage,
    """

    def __init__(
        self,
        article_gen_lm=Union[dspy.dsp.LM, dspy.dsp.HFModel],
        retrieve_top_k: int = 5,
        max_thread_num: int = 10,
    ):
        super().__init__()
        self.retrieve_top_k = retrieve_top_k
        self.article_gen_lm = article_gen_lm
        self.max_thread_num = max_thread_num
        self.section_gen = ConvToSection(engine=self.article_gen_lm)

    def generate_section(
        self, topic, section_name, information_table, section_outline, section_query
    ):
        collected_info: List[Information] = []
        if information_table is not None:
            collected_info = information_table.retrieve_information(
                queries=section_query, search_top_k=self.retrieve_top_k
            )
        output = self.section_gen(
            topic=topic,
            outline=section_outline,
            section=section_name,
            collected_info=collected_info,
        )
        return {
            "section_name": section_name,
            "section_content": output.section,
            "collected_info": collected_info,
        }

    def generate_article(
        self,
        topic: str,
        information_table: StormInformationTable,
        article_with_outline: StormArticle,
        callback_handler: BaseCallbackHandler = None,
    ) -> StormArticle:
        """
        Generate article for the topic based on the information table and article outline.

        Args:
            topic (str): The topic of the article.
            information_table (StormInformationTable): The information table containing the collected information.
            article_with_outline (StormArticle): The article with specified outline.
            callback_handler (BaseCallbackHandler): An optional callback handler that can be used to trigger
                custom callbacks at various stages of the article generation process. Defaults to None.
        """
        information_table.prepare_table_for_retrieval()

        if article_with_outline is None:
            article_with_outline = StormArticle(topic_name=topic)

        sections_to_write = article_with_outline.get_first_level_section_names()

        section_output_dict_collection = []
        if len(sections_to_write) == 0:
            logging.error(
                f"No outline for {topic}. Will directly search with the topic."
            )
            section_output_dict = self.generate_section(
                topic=topic,
                section_name=topic,
                information_table=information_table,
                section_outline="",
                section_query=[topic],
            )
            section_output_dict_collection = [section_output_dict]
        else:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_thread_num
            ) as executor:
                future_to_sec_title = {}
                for section_title in sections_to_write:
                    # We don't want to write a separate introduction section.
                    if section_title.lower().strip() == "introduction":
                        continue
                        # We don't want to write a separate conclusion section.
                    if section_title.lower().strip().startswith(
                        "conclusion"
                    ) or section_title.lower().strip().startswith("summary"):
                        continue
                    section_query = article_with_outline.get_outline_as_list(
                        root_section_name=section_title, add_hashtags=False
                    )
                    queries_with_hashtags = article_with_outline.get_outline_as_list(
                        root_section_name=section_title, add_hashtags=True
                    )
                    section_outline = "\n".join(queries_with_hashtags)
                    future_to_sec_title[
                        executor.submit(
                            self.generate_section,
                            topic,
                            section_title,
                            information_table,
                            section_outline,
                            section_query,
                        )
                    ] = section_title

                for future in as_completed(future_to_sec_title):
                    section_output_dict_collection.append(future.result())

        article = copy.deepcopy(article_with_outline)
        for section_output_dict in section_output_dict_collection:
            article.update_section(
                parent_section_name=topic,
                current_section_content=section_output_dict["section_content"],
                current_section_info_list=section_output_dict["collected_info"],
            )
        article.post_processing()
        return article


class ConvToSection(dspy.Module):
    """Use the information collected from the information-seeking conversation to write a section."""

    def __init__(self, engine: Union[dspy.dsp.LM, dspy.dsp.HFModel]):
        super().__init__()
        self.write_section = dspy.Predict(WriteSection)
        self.engine = engine

    def forward(
        self, topic: str, outline: str, section: str, collected_info: List[Information]
    ):
        info = ""
        for idx, storm_info in enumerate(collected_info):
            info += f"[{idx + 1}]\n" + "\n".join(storm_info.snippets)
            info += "\n\n"

        info = ArticleTextProcessing.limit_word_count_preserve_newline(info, 5000)

        # LOCAL PATCH (2026-08-03): the section writer sees the article brief. "N/A" on bare runs.
        article = brief.get_block("THE ARTICLE THIS SECTION FEEDS") or "N/A"

        with dspy.settings.context(lm=self.engine):
            section = ArticleTextProcessing.clean_up_section(
                self.write_section(topic=topic, article=article, info=info, section=section).output
            )

        return dspy.Prediction(section=section)


class WriteSection(dspy.Signature):
    """Write a comprehensive, evidence-dense research section from the collected information.

    This section feeds a downstream writing phase, so your job is to CAPTURE THE EVIDENCE, not to
    produce short polished prose. Pull the most important, most relevant, and most specific facts the
    collected information contains about this section, and lay them out clearly.

    Priorities:
        1. Favor concrete specifics: statistics, figures, dollar amounts, percentages, ranges, dates,
           named organizations and studies, formulas, definitions, methods, and caveats. A specific
           number with its citation is worth more than a sentence that summarizes it away. Do not
           generalize away detail and do not drop numbers.
        2. Be comprehensive: include every distinct, relevant fact the collected information offers for
           this section. Do NOT omit useful specifics just to be brief.
        3. There is NO length target. Write as much as the evidence genuinely supports and no more. Do
           not pad, do not repeat the same fact, and do not add filler to reach a length. If the
           collected information is thin, the section is short; if it is rich, the section is long.
        4. Every sentence must be supported by the collected information. Do not invent facts, numbers,
           or sources. If sources conflict, present both figures with their citations.
        5. If article context is given (not N/A): material that does not serve the asset title and the
           angle does not belong — leave it out even when the collected information contains it, and
           write nothing from the world the context says this is NOT about. Costs, failures, limits and
           who a method disadvantages ARE on-spine: write them up in full, and never quietly drop a
           finding because it works against the article.

    Here is the format of your writing:
        1. Use "#" Title" to indicate section title, "##" Title" to indicate subsection title, "###" Title" to indicate subsubsection title, and so on.
        2. Use [1], [2], ..., [n] in line (for example, "The capital of the United States is Washington, D.C.[1][3]."). You DO NOT need to include a References or Sources section to list the sources at the end.
    """

    info = dspy.InputField(prefix="The collected information:\n", format=str)
    topic = dspy.InputField(prefix="The topic of the page: ", format=str)
    article = dspy.InputField(prefix="The article this section feeds:\n", format=str)
    section = dspy.InputField(prefix="The section you need to write: ", format=str)
    output = dspy.OutputField(
        prefix="Write the section with proper inline citations (Start your writing with # section title. Don't include the page title or try to write other sections):\n",
        format=str,
    )
