import base64
from .pdf_utils import extract_pages_as_images

def extract_document_data(instructor_client, pdf_images, segments):
    # pdf_images: list of PIL Images
    # segments: list of (start,end) for each doc
    # We'll store per-doc metadata
    print(f"Starting metadata extraction for {len(segments)} document segments")
    docs_data = []
    for i, (start, end) in enumerate(segments):
        print(f"\nProcessing document {i+1}/{len(segments)} (pages {start}-{end})")
        doc_pages = pdf_images[start:end+1]
        print(f"Converting {len(doc_pages)} pages to base64")
        pages_b64 = []
        for j, p in enumerate(doc_pages):
            print(f"Converting page {j+1}/{len(doc_pages)}")
            # Convert each page to base64
            from io import BytesIO
            buf = BytesIO()
            p.save(buf, format='PNG')
            page_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            pages_b64.append(page_b64)
        print("Extracting metadata from pages...")
        metadata = instructor_client.extract_metadata(pages_b64)
        print(f"Successfully extracted metadata: {metadata.title}")
        docs_data.append(metadata)
    print(f"\nCompleted metadata extraction for all {len(segments)} documents")
    return docs_data
