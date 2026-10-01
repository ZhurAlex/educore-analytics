import pymupdf
from pathlib import Path


def chapter_page_ranges(chapter_pages, total_pages):
    """chapter_pages holds 1-indexed page numbers where each chapter starts.
    Returns 0-indexed (start_page, end_page) pairs, end_page exclusive — the
    last chapter's end is total_pages, not another entry in chapter_pages, so
    every entry is a real chapter and none is lost as a mere terminator."""
    ends = chapter_pages[1:] + [total_pages + 1]
    return [
        (start - 1, end - 1)
        for start, end in zip(chapter_pages, ends)
    ]


def save_chapter_pdf(source_path, start_page, end_page, output_path):
    doc = pymupdf.open(source_path)
    doc.select([*range(start_page, end_page)])
    doc.save(output_path, garbage=4, deflate=True)


def split_pdf_into_chapters(book_name, doc_path, chapter_pages):
    source_path = f"{doc_path}/{book_name}.pdf"
    output_dir = Path(f"{doc_path}/{book_name}_chapters")
    output_dir.mkdir(parents=True, exist_ok=True)

    total_pages = pymupdf.open(source_path).page_count
    for num, (start_page, end_page) in enumerate(chapter_page_ranges(chapter_pages, total_pages), start=1):
        output_path = output_dir / f"chapter_{num}_{start_page}.pdf"
        save_chapter_pdf(source_path, start_page, end_page, output_path)
        print(f"Chapter {num} saved as {output_path.name}")

def split_large_chapter(source_path, output_dir, name_prefix, pages_per_part=15):
    doc = pymupdf.open(source_path)
    for i, start in enumerate(range(0, doc.page_count, pages_per_part), start=1):
        end = min(start + pages_per_part, doc.page_count)
        output_path = Path(output_dir) / f"{name_prefix}_part{i}.pdf"
        save_chapter_pdf(source_path, start, end, output_path)

book_name = "grammatika_golitsynskiy"
doc_path = f"data/textbooks/english"
chapter_pages = [5, 71, 79, 95, 101, 111, 128, 234, 256, 292, 303, 323, 342, 348, 370, 378, 393, 445, 450, 451, 539, 567]

# split_pdf_into_chapters(book_name, doc_path, chapter_pages)

split_large_chapter("data/textbooks/english/grammatika_golitsynskiy_chapters/chapter_1_4.pdf",
                     "data/textbooks/english/grammatika_golitsynskiy_chapters", "chapter_1_4")
split_large_chapter("data/textbooks/english/grammatika_golitsynskiy_chapters/chapter_7_127.pdf",
                     "data/textbooks/english/grammatika_golitsynskiy_chapters", "chapter_7_127")