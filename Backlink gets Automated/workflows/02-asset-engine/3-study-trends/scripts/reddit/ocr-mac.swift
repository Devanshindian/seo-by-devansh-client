// ocr-mac.swift — free, native macOS OCR (Apple Vision framework). No install needed.
// Usage: ./ocr-mac <image-path>   ->   prints recognized text (one block per line) to stdout.
// Compile once: swiftc -O ocr-mac.swift -o ocr-mac
import Foundation
import Vision
import AppKit

let args = CommandLine.arguments
guard args.count > 1 else { FileHandle.standardError.write("usage: ocr-mac <image>\n".data(using: .utf8)!); exit(1) }
guard let img = NSImage(contentsOfFile: args[1]),
      let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { print(""); exit(0) }

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
try? handler.perform([request])
var lines: [String] = []
for obs in (request.results ?? []) {
    if let top = obs.topCandidates(1).first { lines.append(top.string) }
}
print(lines.joined(separator: " "))
