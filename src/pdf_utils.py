import tempfile
import os
from PyPDF2 import PdfReader, PdfWriter
import pdfplumber

def extract_pages_as_images(pdf_path: str, dpi=150):
    print(f"Converting PDF {pdf_path} to images at {dpi} DPI...")
    from pdf2image import convert_from_path
    pages = convert_from_path(pdf_path, dpi=dpi)
    print(f"Successfully converted {len(pages)} pages to images")
    return pages

def add_bookmarks(original_pdf_path: str, doc_start_pages: list[int], doc_titles: list[str], output_path: str, doc_dates: list[str]):
    # doc_start_pages, doc_titles, and doc_dates must have the same length
    print(f"Adding bookmarks to PDF {original_pdf_path}")
    print(f"Will add {len(doc_start_pages)} bookmarks")
    reader = PdfReader(open(original_pdf_path, 'rb'))
    writer = PdfWriter()
    print("Copying pages to new PDF...")
    for page_num, page in enumerate(reader.pages):
        writer.add_page(page)
    # Add bookmarks
    print("Adding bookmark entries...")
    for i, start_page in enumerate(doc_start_pages):
        # Format bookmark title: YYYY-MM-DD - Document Title
        date_str = doc_dates[i] if doc_dates[i] else "undated"
        bookmark_title = f"{date_str} - {doc_titles[i]}"
        # The add_outline_item method expects zero-based page indexing
        print(f"Adding bookmark '{bookmark_title}' at page {start_page}")
        writer.add_outline_item(bookmark_title, start_page)
    print(f"Writing bookmarked PDF to {output_path}")
    with open(output_path, "wb") as f:
        writer.write(f)
    print("Successfully added bookmarks")

def split_documents(original_pdf_path: str, segments: list[tuple[int,int]], output_dir: str, doc_titles: list[str], doc_dates: list[str]):
    # segments is list of (start_page, end_page) (0-based)
    # doc_titles & doc_dates correspond to those segments
    print(f"\nSplitting PDF {original_pdf_path} into {len(segments)} documents")
    reader = PdfReader(open(original_pdf_path, 'rb'))
    for (start, end), title, doc_date in zip(segments, doc_titles, doc_dates):
        print(f"\nProcessing document: {title}")
        print(f"Pages {start} to {end}")
        writer = PdfWriter()
        for p in range(start, end+1):
            writer.add_page(reader.pages[p])
        # Format filename: YYYY-MM-DD - Document Title.pdf
        # Fall back if date empty
        date_str = doc_date if doc_date else "undated"
        safe_title = title.replace('/', '-').replace('\\', '-').replace(':','-')
        out_filename = f"{date_str} - {safe_title}.pdf"
        out_path = os.path.join(output_dir, out_filename)
        print(f"Writing document to {out_path}")
        with open(out_path, 'wb') as f:
            writer.write(f)
        print(f"Successfully wrote document: {out_filename}")
        yield out_path

def extract_pages_text(pdf_path: str) -> list[str]:
    """Extract text from each page of the PDF."""
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""  # Use empty string if no text found
            pages_text.append(text)
    return pages_text
