# PDF Link Extractor & Processor

A comprehensive Python backend application that extracts links from PDF documents and downloads/processes PDFs from those links using FastAPI.

## 🚀 Features

### **Core PDF Processing**

- **Multiple PDF Processing Libraries**: Uses both PyPDF2 and pdfplumber for comprehensive link extraction
- **Various Link Types**: Extracts:
  - HTTP/HTTPS URLs from text
  - Email addresses
  - PDF annotations (clickable links)
  - Hyperlinks embedded in the PDF

### **Advanced PDF Download & Processing**

- **Automatic PDF Download**: Downloads PDFs from extracted URLs
- **Content Extraction**: Extracts full text content from downloaded PDFs
- **Content Analysis**: Analyzes extracted content for:
  - Word count and character count
  - Email addresses
  - Phone numbers
  - Dates
  - Numerical values
  - Content samples
- **Metadata Extraction**: Extracts PDF metadata (title, author, creation date, etc.)

### **Web Interface**

- **Modern UI**: Clean, responsive web interface with tabbed navigation
- **Multiple Modes**:
  - Extract links from uploaded PDF
  - Process PDF URLs directly
  - Extract links and automatically download/process found PDFs
- **Real-time Processing**: Progress indicators and detailed results display
- **Collapsible Results**: Organized, expandable content analysis

### **RESTful API**

- **FastAPI-based**: Modern REST API for programmatic access
- **Async Processing**: Concurrent processing of multiple URLs
- **Comprehensive Error Handling**: Detailed error messages and status codes

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd pdf-analyzer
```

2. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Starting the Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000`

### Web Interface

1. Open your browser and go to `http://localhost:8000`
2. Upload a PDF file using the drag-and-drop interface or file picker
3. View the extracted links with detailed information

### API Endpoints

#### POST `/extract-links`

Extract links from an uploaded PDF file.

**Parameters:**

- `file`: PDF file (multipart/form-data)

**Response:**

```json
{
  "status": "success",
  "filename": "document.pdf",
  "file_size": 1234567,
  "data": {
    "total_links": 15,
    "links": [...],
    "summary": {...}
  }
}
```

#### POST `/process-pdf-urls`

Download and process PDFs from a list of URLs.

**Parameters:**

- `urls`: Array of PDF URLs (JSON array)

**Response:**

```json
{
  "status": "completed",
  "summary": {
    "total_urls": 5,
    "successful": 3,
    "failed": 1,
    "skipped": 1
  },
  "results": [
    {
      "url": "http://example.com/document.pdf",
      "status": "success",
      "data": {
        "links": {...},
        "content": {
          "summary": {...},
          "content_analysis": {...},
          "metadata": {...}
        }
      }
    }
  ]
}
```

#### POST `/extract-and-process`

Extract links from uploaded PDF and automatically download/process found PDF URLs.

**Parameters:**

- `file`: PDF file (multipart/form-data)

**Response:**

```json
{
  "status": "completed",
  "original_file": "source.pdf",
  "pdf_urls_found": 5,
  "successful_downloads": 3,
  "results": [...]
}
```

#### GET `/health`

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "service": "pdf-link-extractor"
}
```

## Testing

### API Testing

Run the enhanced test script to verify all functionality:

```bash
python test_enhanced_api.py
```

This will test:

- URL processing with PDF download and content extraction
- Link extraction from uploaded files
- Content analysis and metadata extraction

### Example Usage

1. **Process URL directly**: Use the "Process URLs" tab to download and analyze PDFs from URLs like:

   ```
   http://www.qkb.gov.al/umbraco/Surface/SearchSurface/GenerateBulletinExtract?subjectDefCode=3AC4FF72-172E-4173-BC32-1D3E24F2AE41&isSimple=true
   ```

2. **Extract and Process**: Upload a PDF containing links, and the system will automatically find PDF URLs and download/analyze them.

3. **Manual Processing**: Use the API endpoints directly for programmatic access.

## Link Types Detected

1. **Text URLs**: HTTP/HTTPS URLs found in the PDF text content
2. **Email Addresses**: Email addresses found in the text (converted to mailto: links)
3. **PDF Annotations**: Clickable links embedded as PDF annotations
4. **Hyperlinks**: Links embedded in the PDF structure (when available)

## Dependencies

- **FastAPI**: Modern web framework for building APIs
- **PyPDF2**: PDF processing library for annotations and basic text extraction
- **pdfplumber**: Advanced PDF processing for better text extraction
- **uvicorn**: ASGI server for running the FastAPI application
- **aiofiles**: Async file operations
- **python-multipart**: For handling file uploads

## Error Handling

The application includes comprehensive error handling for:

- Invalid file types (non-PDF files)
- Corrupted PDF files
- Empty files
- Network connectivity issues
- Server errors

## Performance Considerations

- The application processes PDFs in memory for better performance
- Large PDF files may require more processing time
- Duplicate links are efficiently removed using set operations
- Both PDF libraries are used to ensure maximum link detection

## License

This project is open source and available under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository.
