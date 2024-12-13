```markdown
# bookmarker

This repository provides a pipeline to process PDF files by segmenting them into separate documents, extracting metadata, inserting that metadata into a SQLite database, and generating individual PDF files and a bookmarked version of the original PDF.

**Key Features:**
- Automatically segment a PDF into multiple documents by analyzing page image similarities and layout changes using Anthropics' API.
- Extract metadata (title, date, summary, and tags) for each identified document using an LLM-based "instructor" model.
- Insert extracted metadata into a SQLite database.
- Generate separate PDF files for each segmented document and produce a bookmarked PDF of the original file.
- Easily configurable and extensible.

---

## Prerequisites

1. **Python 3.8+** recommended.
2. **Poetry or pip** for installing Python dependencies.
3. **Poppler**: Required by `pdf2image` for converting PDFs to images.  
   - On Ubuntu/Debian: `sudo apt-get install poppler-utils`
   - On macOS with Homebrew: `brew install poppler`
   - On Windows: [Download Poppler binaries](http://blog.alivate.com.au/poppler-windows/) and add to your PATH.

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/halfprice06/bookmarker.git
   cd bookmarker
   ```

2. **Set up a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

1. **API Keys:**  
   Copy `.env.example` to `.env` and add your Anthropic API key:
   ```bash
   cp .env.example .env
   ```
   
   Inside `.env`:
   ```env
   ANTHROPIC_API_KEY=your_api_key_here
   ```
   
   Make sure you have an API key from Anthropic. The `ANTHROPIC_API_KEY` environment variable is used by `AnthropicClient`.

2. **Input and Output Directories:**
   - **Input PDFs:** Place PDF files you want to process into `input_dir` (This directory is created automatically if missing).
   - **Output PDFs and documents:** Processed documents, bookmarked PDFs, and related output will appear in `output_docs`.

3. **Database:**
   - The pipeline uses a local SQLite database `documents.db` to store metadata about processed documents.
   - The `init_db` function in `db.py` automatically creates the necessary tables if they don't exist.

---

## Running the Pipeline

1. Ensure you have provided input PDF files in the `input_dir` directory.
2. Run the `main.py` script:
   ```bash
   python main.py
   ```

**What happens next?**  
- The script will:
  1. Initialize the database (`documents.db`).
  2. Detect PDF files in `input_dir`.
  3. For each PDF:
     - Convert all pages to images.
     - Use `AnthropicClient` to determine document boundaries.
     - Extract metadata for each segmented document via `InstructorClient`.
     - Insert the extracted metadata into `documents.db`.
     - Add bookmarks to the original PDF and write it to `output_docs/[PDFName]_bookmarked.pdf`.
     - Split the PDF into separate document PDFs in `output_docs/[PDFName]/`.
   - Finally, it will print the summary of how many documents were found and processed.

---

## Document Segmentation Logic

The logic for determining segmentation:
- Each page is converted to a base64-encoded PNG.
- Pages are compared in pairs (previous vs. current page) using the `AnthropicClient.is_new_document()` method.
- The Anthropics LLM is given images of two consecutive pages and asked whether the new page signifies the start of a new document.
- If "YES", a new segment is created starting from that page.

---

## Metadata Extraction

For each identified segment:
- All pages of that segment are converted to base64 images.
- These images are sent to the `InstructorClient` along with a system prompt asking for:
  1. A short, descriptive title.
  2. A creation or filing date (YYYY-MM-DD or Unknown).
  3. A summary.
  4. Tags that an attorney might assign.
  
The `InstructorClient` returns this metadata, which is then inserted into the database and used to name the output PDF files.

---

## Database Schema

The SQLite database `documents.db` has two tables:

- **`documents`**:  
  **Columns**:
  - `id`: Primary Key
  - `title`: Document title
  - `date`: Document date (YYYY-MM-DD or Unknown)
  - `summary`: Brief summary of the document
  - `original_filename`: The filename of the extracted/split PDF

- **`tags`**:  
  **Columns**:
  - `id`: Primary Key
  - `document_id`: Foreign key referencing `documents.id`
  - `tag`: A single tag associated with the document

This allows for easy retrieval, filtering, and categorization of processed documents.

---

## Customization

- **Adjusting Models & Prompts**:  
  You can modify system prompts or model parameters in `anthropic_client.py` and `instructor_client.py` to refine how documents are segmented or metadata is extracted.
  
- **Adding More Fields**:  
  For additional metadata fields, update the `DocumentMetadata` model in `instructor_client.py` and adjust the prompt accordingly.

- **Alternative Databases**:  
  By default, this uses SQLite for simplicity. You can integrate other databases by modifying `db.py`.

---

## Troubleshooting

1. **No PDFs processed**:  
   Ensure there are `.pdf` files in `input_dir` and that you have required system dependencies (Poppler) installed.

2. **Poppler not found**:  
   Ensure `pdf2image` can locate `pdftoppm`. On Windows, set the path in your environment variables; on Linux/macOS, install via package manager.

3. **Anthropic API errors**:  
   Check that your `ANTHROPIC_API_KEY` is valid and that you have enough quota.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

