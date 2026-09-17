# from pathlib import Path

# from marker.converters.pdf import PdfConverter
# from marker.models import create_model_dict
# from marker.output import text_from_rendered

# converter = PdfConverter(
#     artifact_dict=create_model_dict(),
# )
# book_name = "grammatika_golitsynskiy"

# rendered = converter(f"data/textbooks/english/{book_name}.pdf")
# text, _, images = text_from_rendered(rendered)

# output_path = Path(f"data/parsed/english/{book_name}.md")
# output_path.parent.mkdir(parents=True, exist_ok=True)
# output_path.write_text(text)

from pathlib import Path

import pymupdf4llm

book_name = "grammatika_golitsynskiy"

md = pymupdf4llm.to_markdown(
    f"data/textbooks/english/{book_name}.pdf",
    ocr_language="eng+rus",
    show_progress=True,
)

output_path = Path(f"data/parsed/english/{book_name}.md")
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(md)
