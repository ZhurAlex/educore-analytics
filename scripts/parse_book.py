import time
from pathlib import Path

import pymupdf
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

book_name = "grammatika_golitsynskiy"
pdf_path = f"data/textbooks/english/{book_name}.pdf"
batch_size = 10

with pymupdf.open(pdf_path) as doc:
    total_pages = doc.page_count

print(f"Loading Marker models ({total_pages} pages total, batches of {batch_size})...")
converter = PdfConverter(
    artifact_dict=create_model_dict(),
)

output_path = Path(f"data/parsed/english/{book_name}.md")
output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open("w") as f:
    for start in range(0, total_pages, batch_size):
        end = min(start + batch_size, total_pages)
        batch_started_at = time.monotonic()

        converter.config["page_range"] = list(range(start, end))
        rendered = converter(pdf_path)
        text, _, _ = text_from_rendered(rendered)

        f.write(text)
        f.write("\n\n")
        f.flush()

        elapsed = time.monotonic() - batch_started_at
        print(f"Pages {start}-{end - 1} done ({end}/{total_pages}), {elapsed:.0f}s for this batch", flush=True)

print(f"Done: {output_path}")
