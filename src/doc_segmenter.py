import base64
from io import BytesIO

def pil_to_base64(img):
    print(f"Converting image to base64...")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    b64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    print(f"Successfully converted image to base64 string of length {len(b64_str)}")
    return b64_str

def segment_document(anthropic_client, pdf_images):
    print(f"\nStarting document segmentation for {len(pdf_images)} pages")
    # pdf_images: list of PIL images of each page
    # We'll assume page 0 is start of first doc
    segments = []
    doc_start_pages = [0]
    print("Analyzing pages for document boundaries...")
    for i in range(1, len(pdf_images)):
        print(f"\nProcessing page {i}/{len(pdf_images)-1}")
        prev_image_b64 = pil_to_base64(pdf_images[i-1])
        curr_image_b64 = pil_to_base64(pdf_images[i])
        print(f"Checking if page {i} starts a new document...")
        if anthropic_client.is_new_document(prev_image_b64, curr_image_b64):
            print(f"Found new document starting at page {i}")
            doc_start_pages.append(i)
    
    print(f"\nFound {len(doc_start_pages)} document start pages: {doc_start_pages}")
    # doc_start_pages now has start pages of each doc
    # Convert into (start,end) tuples
    doc_segments = []
    print("\nConverting start pages into document segments...")
    for idx, start in enumerate(doc_start_pages):
        end = doc_start_pages[idx+1]-1 if idx+1 < len(doc_start_pages) else len(pdf_images)-1
        doc_segments.append((start, end))
        print(f"Document {idx+1}: pages {start}-{end}")
    
    print(f"\nSegmentation complete. Found {len(doc_segments)} documents")
    return doc_segments
