import os
from pathlib import Path

from src.anthropic_client import AnthropicClient
from src.instructor_client import InstructorClient, DocumentMetadata
from src.doc_segmenter import segment_document
from src.pdf_utils import extract_pages_as_images, add_bookmarks, split_documents
from src.db import init_db, insert_document
from anthropic import Anthropic
from src.doc_extractor import extract_document_data
from src.transcriber import DocumentTranscriber
from openai import OpenAI
from src.openai_client import OpenAIClient

def process_single_pdf(pdf_path: str, output_dir: str, db_path: str, api_client, instructor_client, model_client, model_provider):
    # Get the PDF filename without extension to use as subdirectory name
    pdf_name = Path(pdf_path).stem
    pdf_output_dir = os.path.join(output_dir, pdf_name)
    Path(pdf_output_dir).mkdir(exist_ok=True)
    
    output_pdf = os.path.join(pdf_output_dir, f"{pdf_name}_bookmarked.pdf")
    print(f"\nProcessing {pdf_path}")
    print(f"Output will be saved to {pdf_output_dir}")

    # Extract pages as images
    print("Extracting pages from PDF...")
    pdf_images = extract_pages_as_images(pdf_path)
    print(f"Extracted {len(pdf_images)} pages")

    # Segment the PDF into documents
    print("Segmenting PDF into separate documents...")
    segments = segment_document(api_client, pdf_images) 
    print(f"Found {len(segments)} distinct documents")

    # Initialize transcriber
    transcriber = DocumentTranscriber(model_client, model_provider)
    
    # Extract metadata and transcribe
    print("Extracting metadata from documents...")
    docs_data = extract_document_data(instructor_client, transcriber, pdf_path, segments, pdf_output_dir)
    print(f"Extracted metadata for {len(docs_data)} documents")

    # Create bookmarks in the original PDF
    print("Adding bookmarks to PDF...")
    doc_titles = [d[0].title for d in docs_data]
    doc_dates = [d[0].date for d in docs_data]
    doc_start_pages = [s[0] for s in segments]
    add_bookmarks(pdf_path, doc_start_pages, doc_titles, output_pdf, doc_dates)
    print("Bookmarks added successfully")

    # Split documents into separate PDFs
    print("Splitting into separate PDFs...")
    doc_pdfs = list(split_documents(pdf_path, segments, pdf_output_dir, doc_titles, doc_dates))
    print(f"Created {len(doc_pdfs)} separate PDF files")

    # Insert metadata into DB
    print("Inserting document metadata into database...")
    for doc_path, (doc_meta, full_text, full_markdown, page_markdowns) in zip(doc_pdfs, docs_data):
        insert_document(
            db_path, 
            doc_meta.title, 
            doc_meta.date, 
            doc_meta.summary, 
            os.path.basename(doc_path), 
            doc_meta.tags,
            full_text,
            full_markdown,
            page_markdowns
        )
        print(f"Inserted metadata for document: {doc_meta.title}")

    return len(segments)

def main():
    # Configuration
    input_dir = "input_dir"
    output_dir = "output_dir"
    db_path = "documents.db"
    
    # Get model choice from environment or user input
    model_provider = os.environ.get("MODEL_PROVIDER", "").lower()
    while model_provider not in ["anthropic", "openai"]:
        model_provider = input("Choose model provider (anthropic/openai): ").lower()

    # Create directories if they don't exist
    Path(input_dir).mkdir(exist_ok=True)
    Path(output_dir).mkdir(exist_ok=True)
    
    # Initialize database
    init_db(db_path)
    print("Database initialized")

    # Initialize API clients based on chosen provider
    print("Initializing API clients...")
    if model_provider == "anthropic":
        api_client = AnthropicClient()
        model_client = Anthropic()
    else:
        api_client = OpenAIClient()
        model_client = OpenAI()
    
    instructor_client = InstructorClient(model_client, model_provider)
    print(f"Initialized {model_provider.title()} clients")

    # Get all PDF files from input directory
    pdf_files = list(Path(input_dir).glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return

    print(f"Found {len(pdf_files)} PDF files to process")
    total_documents = 0

    # Process each PDF
    for pdf_file in pdf_files:
        try:
            num_docs = process_single_pdf(
                str(pdf_file),
                output_dir,
                db_path,
                api_client,
                instructor_client,
                model_client,
                model_provider
            )
            total_documents += num_docs
        except Exception as e:
            print(f"Error processing {pdf_file}: {str(e)}")
            continue

    print("\nProcess complete.")
    print(f"Processed {len(pdf_files)} PDF files")
    print(f"Found total of {total_documents} documents")
    print("Output directory:", output_dir)
    print("Metadata in DB:", db_path)

if __name__ == "__main__":
    main()
