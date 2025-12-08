import sys
import json
import os
import html
from docling.document_converter import DocumentConverter
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

if len(sys.argv) < 2:
    sys.exit("Usage: python 1_process_document.py <path_to_file.pdf>")

file_path = sys.argv[1]
output_path = os.path.splitext(file_path)[0] + ".jsonl"

print(f"Processing {file_path}...")

# 1. Convert PDF to Markdown
md_content = DocumentConverter().convert(file_path).document.export_to_markdown()

# 2. Split by Headers
headers = [("##", "Section"), ("###", "Subsection")]
header_splits = MarkdownHeaderTextSplitter(headers_to_split_on=headers).split_text(md_content)

# 3. Recursive Split
chunks = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
).split_documents(header_splits)

# 4. Write to JSONL
with open(output_path, "w", encoding="utf-8") as f:
    for i, chunk in enumerate(chunks):
        page_content = chunk.page_content or ""

        # remove literal "\n" and real newlines
        page_content = page_content.replace("\\n", " ")
        page_content = page_content.replace("\n", " ")

        # unescape HTML entities (&amp; -> &, etc.)
        page_content = html.unescape(page_content)

        # avoid double quotes inside the text
        page_content = page_content.replace('"', "'")

        # normalize whitespace
        page_content = " ".join(page_content.split())

        record = {
            "id": i,
            "page_content": page_content,
            "metadata": chunk.metadata,
        }
        f.write(json.dumps(record) + "\n")

print(f"Saved {len(chunks)} chunks to {output_path}")
