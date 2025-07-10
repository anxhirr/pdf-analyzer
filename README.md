# PDF Analyzer - Albanian Business Registry Extractor

A powerful web application that extracts and processes Albanian business registry data from PDFs with links to government databases.

## 🚀 Features

### **Core PDF Processing**

- **Multiple PDF Processing Libraries**: Uses both PyPDF2 and pdfplumber for comprehensive link extraction
- **Various Link Types**: Extracts HTTP/HTTPS URLs, email addresses, PDF annotations, and hyperlinks
- **Advanced Download**: Smart PDF downloading with enhanced headers for Albanian government sites

### **Albanian Business Registry Integration**

- **Automatic Business Data Extraction**: Processes Albanian business registry PDFs
- **Structured Data Parsing**: Extracts:
  - NUIS (Business Registration Number)
  - Business Names (Albanian & English)
  - Addresses and Contact Information
  - Activity Fields and Business Types
  - Registration Dates and Status
- **Government Database Support**: Specialized handling for QKB (National Business Center) URLs

### **Professional Data Table**

- **Comprehensive Business Table**: Displays all extracted business data in a searchable, sortable table
- **Advanced Filtering**: Filter by business name, activity field, NUIS, and address
- **Pagination**: Handles large datasets with efficient pagination
- **Export Ready**: Structured data format for easy export and integration

### **Web Interface**

- **Modern UI**: Clean, responsive web interface with 5 tabbed sections
- **Multiple Processing Modes**:
  - Extract links from uploaded PDF
  - Process PDF URLs directly
  - Extract and process all HTTP links
  - Business registry table with full data extraction
- **Real-time Processing**: Progress indicators and detailed results display

### **RESTful API**

- **FastAPI-based**: Modern REST API with async processing
- **Production Ready**: Environment variable configuration for deployment
- **Comprehensive Error Handling**: Detailed error messages and status codes

## 🚀 Quick Deploy

### Railway (Recommended)

1. Fork this repository
2. Visit [Railway](https://railway.app)
3. Click "Start a New Project" → "Deploy from GitHub repo"
4. Select your forked repository
5. Railway will automatically detect and deploy your FastAPI app

### Render

1. Fork this repository
2. Visit [Render](https://render.com)
3. Create a new Web Service from your GitHub repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python main.py`

### Heroku

1. Fork this repository
2. Create a new Heroku app
3. Connect your GitHub repository
4. Deploy from the main branch

## 🔧 Local Development

1. Clone the repository:

```bash
git clone <repository-url>
cd pdf-analyzer
```

2. Create a virtual environment:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the application:

```bash
python main.py
```

Visit `http://localhost:8000` to access the web interface.

## 🌍 Environment Variables

- `PORT`: Server port (default: 8000)
- `HOST`: Server host (default: 0.0.0.0)

## 📖 Usage Guide

### Web Interface

1. **Extract Links Tab**: Upload PDF to extract all links
2. **Process URLs Tab**: Input URLs directly to download and process
3. **Extract & Process Tab**: Upload PDF and automatically process all HTTP links
4. **Business Table Tab**: Upload PDF with Albanian registry links for structured business data

### Albanian Business Registry

The application specializes in processing Albanian business registry documents:

- Automatically downloads PDFs from QKB (National Business Center) URLs
- Extracts structured business information using regex patterns
- Displays results in a professional data table with search and filtering

## 🔌 API Endpoints

### Core Endpoints

#### POST `/extract-links`

Extract links from an uploaded PDF file.

**Parameters:**

- `file`: PDF file (multipart/form-data)

**Response:**

```json
{
  "filename": "example.pdf",
  "links": ["http://example.com", "mailto:test@example.com"],
  "metadata": {...}
}
```

#### POST `/process-pdf-urls`

Process multiple PDF URLs and extract content.

**Parameters:**

- `urls`: List of PDF URLs (JSON array)

**Response:**

```json
{
  "results": [
    {
      "url": "http://example.com/file.pdf",
      "success": true,
      "content": "...",
      "analysis": {...}
    }
  ]
}
```

#### POST `/extract-and-process-table`

Extract and process Albanian business registry data.

**Parameters:**

- `file`: PDF file (multipart/form-data)

**Response:**

```json
{
  "status": "completed",
  "businesses": [
    {
      "business_name": "Example Business",
      "nuis": "K12345678A",
      "address": "Tirana, Albania",
      "activity_field": "Information Technology"
    }
  ]
}
```

### Health Check

#### GET `/health`

Health check endpoint for deployment monitoring.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Response:**

```json
{
## 🏗️ Technical Architecture

### Backend Components

- **FastAPI Framework**: Modern, async web framework
- **PDF Processing**: PyPDF2 + pdfplumber for comprehensive extraction
- **HTTP Client**: Enhanced requests with browser-like headers
- **Albanian Parser**: Specialized regex patterns for business registry data
- **Production Ready**: Environment variable configuration

### Frontend Components

- **Responsive Design**: Mobile-friendly interface
- **Tab Navigation**: Organized workflow with 5 distinct sections
- **Data Table**: Professional table with sorting, filtering, and pagination
- **Progress Indicators**: Real-time processing feedback

### Deployment Architecture

- **Railway**: Automatic deployment with health checks
- **Render**: Simple deployment with build commands
- **Heroku**: Git-based deployment with Procfile
- **Environment Variables**: Configurable host and port settings

## 🔒 Security Features

- **Input Validation**: Comprehensive file type and size validation
- **Error Handling**: Graceful error handling with detailed logging
- **Rate Limiting**: Built-in protection against abuse
- **SSL Support**: HTTPS-ready for production deployment

## 📊 Performance

- **Async Processing**: Concurrent PDF downloads and processing
- **Memory Efficient**: Streaming file processing for large PDFs
- **Caching**: Intelligent caching for repeated operations
- **Load Testing**: Optimized for production workloads

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API endpoints

## 🔮 Future Enhancements

- [ ] Multi-language support
- [ ] Advanced data export formats
- [ ] Integration with more government databases
- [ ] Machine learning for improved data extraction
- [ ] Real-time collaboration features

---

**Made with ❤️ for Albanian business data processing**
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
