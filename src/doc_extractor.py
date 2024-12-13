import base64
from .pdf_utils import extract_pages_as_images, extract_pages_text
from io import BytesIO
import os
from pathlib import Path

def save_markdown_files(output_dir: str, doc_title: str, doc_date: str, full_markdown: str, page_markdowns: list[str]):
    """Save both full document markdown and individual page markdowns."""
    # Format filename like we do for PDFs: YYYY-MM-DD - Document Title
    date_str = doc_date if doc_date else "undated"
    safe_title = doc_title.replace('/', '-').replace('\\', '-').replace(':', '-')
    base_filename = f"{date_str} - {safe_title}"
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Save full document markdown
    full_doc_path = os.path.join(output_dir, f"{base_filename}.md")
    with open(full_doc_path, 'w', encoding='utf-8') as f:
        f.write(full_markdown)
    
    # Create a subdirectory for individual pages if there's more than one
    if len(page_markdowns) > 1:
        pages_dir = os.path.join(output_dir, f"{base_filename}_pages")
        Path(pages_dir).mkdir(parents=True, exist_ok=True)
        
        # Save individual page markdowns
        for i, page_markdown in enumerate(page_markdowns, 1):
            page_path = os.path.join(pages_dir, f"page_{i:03d}.md")
            with open(page_path, 'w', encoding='utf-8') as f:
                f.write(page_markdown)

def extract_document_data(instructor_client, transcriber, pdf_path, segments, output_dir: str):
    # Extract both images and text
    print(f"Starting metadata extraction for {len(segments)} document segments")
    pdf_images = extract_pages_as_images(pdf_path)
    pdf_texts = extract_pages_text(pdf_path)
    
    # Get the PDF filename without extension to use as subdirectory name
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    pdf_output_dir = output_dir
    
    docs_data = []
    for i, (start, end) in enumerate(segments):
        print(f"\nProcessing document {i+1}/{len(segments)} (pages {start}-{end})")
        doc_pages = pdf_images[start:end+1]
        doc_texts = pdf_texts[start:end+1]
        
        # Combine all text pages for this document
        full_text = "\n\n".join(doc_texts)
        
        print(f"Converting {len(doc_pages)} pages to base64")
        pages_data = []
        for j, (page_img, page_text) in enumerate(zip(doc_pages, doc_texts)):
            print(f"Converting page {j+1}/{len(doc_pages)}")
            # Convert image to base64
            buf = BytesIO()
            page_img.save(buf, format='PNG')
            page_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            # Store both image and text
            pages_data.append((page_b64, page_text))
            
        # First: Generate markdown transcription
        print("Generating markdown transcription...")
        full_markdown, page_markdowns = transcriber.transcribe_document(pages_data)
        
        # Then: Extract metadata using both original data and markdown
        print("Extracting metadata from pages...")
        metadata = instructor_client.extract_metadata(pages_data, page_markdowns)
        print(f"Successfully extracted metadata: {metadata.title}")
        
        # Save markdown files to output directory
        print("Saving markdown files...")
        save_markdown_files(pdf_output_dir, metadata.title, metadata.date, 
                          full_markdown, page_markdowns)
        
        docs_data.append((metadata, full_text, full_markdown, page_markdowns))
    
    print(f"\nCompleted metadata extraction for all {len(segments)} documents")
    return docs_data
