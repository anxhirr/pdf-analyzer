from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any, Optional
import PyPDF2
import pdfplumber
import re
import io
import logging
from urllib.parse import urlparse, urljoin
import aiofiles
import os
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Albanian Business Registry Extractor", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class PDFLinkExtractor:
    def __init__(self):
        # Regex pattern to match various URL formats
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        # Pattern for email addresses
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
    
    def extract_links_with_pypdf2(self, pdf_content: bytes) -> List[Dict[str, Any]]:
        """Extract links using PyPDF2 - focuses on PDF annotations and links"""
        links = []
        
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                # Extract annotations (clickable links in PDF)
                if "/Annots" in page:
                    annotations = page["/Annots"]
                    try:
                        # Convert to list if it's a PdfObject
                        if hasattr(annotations, 'get_object'):
                            annotations = annotations.get_object()
                        if isinstance(annotations, (list, tuple)):
                            for annotation in annotations:
                                annotation_obj = annotation.get_object()
                                if "/A" in annotation_obj:
                                    action = annotation_obj["/A"]
                                    if "/URI" in action:
                                        uri = action["/URI"]
                                        links.append({
                                            "type": "annotation",
                                            "url": uri,
                                            "page": page_num,
                                            "source": "pypdf2"
                                        })
                    except (TypeError, AttributeError, IndexError):
                        # Skip if annotations cannot be processed
                        pass
                
                # Extract text and search for URLs
                try:
                    text = page.extract_text()
                    if text:
                        # Find HTTP/HTTPS URLs
                        url_matches = self.url_pattern.findall(text)
                        for url in url_matches:
                            links.append({
                                "type": "text_url",
                                "url": url,
                                "page": page_num,
                                "source": "pypdf2"
                            })
                        
                        # Find email addresses
                        email_matches = self.email_pattern.findall(text)
                        for email in email_matches:
                            links.append({
                                "type": "email",
                                "url": f"mailto:{email}",
                                "page": page_num,
                                "source": "pypdf2"
                            })
                            
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error with PyPDF2 extraction: {str(e)}")
            
        return links
    
    def extract_links_with_pdfplumber(self, pdf_content: bytes) -> List[Dict[str, Any]]:
        """Extract links using pdfplumber - better text extraction"""
        links = []
        
        try:
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text
                    text = page.extract_text()
                    if text:
                        # Find HTTP/HTTPS URLs
                        url_matches = self.url_pattern.findall(text)
                        for url in url_matches:
                            links.append({
                                "type": "text_url",
                                "url": url,
                                "page": page_num,
                                "source": "pdfplumber"
                            })
                        
                        # Find email addresses
                        email_matches = self.email_pattern.findall(text)
                        for email in email_matches:
                            links.append({
                                "type": "email",
                                "url": f"mailto:{email}",
                                "page": page_num,
                                "source": "pdfplumber"
                            })
                    
                    # Extract hyperlinks (if available)
                    try:
                        hyperlinks = page.hyperlinks
                        if hyperlinks:
                            for link in hyperlinks:
                                links.append({
                                    "type": "hyperlink",
                                    "url": link.get("uri", ""),
                                    "page": page_num,
                                    "source": "pdfplumber"
                                })
                    except Exception as e:
                        logger.warning(f"Error extracting hyperlinks from page {page_num}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error with pdfplumber extraction: {str(e)}")
            
        return links
    
    def validate_url(self, url: str) -> bool:
        """Validate if a URL is properly formatted"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def extract_all_links(self, pdf_content: bytes) -> Dict[str, Any]:
        """Extract links using both methods and combine results"""
        all_links = []
        
        # Extract using PyPDF2
        pypdf2_links = self.extract_links_with_pypdf2(pdf_content)
        all_links.extend(pypdf2_links)
        
        # Extract using pdfplumber
        pdfplumber_links = self.extract_links_with_pdfplumber(pdf_content)
        all_links.extend(pdfplumber_links)
        
        # Remove duplicates while preserving order
        unique_links = []
        seen = set()
        
        for link in all_links:
            url = link.get("url", "")
            # Create a unique key based on URL and page
            key = (url, link.get("page", 0))
            if key not in seen and url:
                # Additional validation for HTTP/HTTPS URLs
                if link["type"] in ["text_url", "hyperlink", "annotation"]:
                    if self.validate_url(url):
                        unique_links.append(link)
                        seen.add(key)
                else:  # Email addresses
                    unique_links.append(link)
                    seen.add(key)
        
        # Group links by type
        links_by_type = {}
        for link in unique_links:
            link_type = link["type"]
            if link_type not in links_by_type:
                links_by_type[link_type] = []
            links_by_type[link_type].append(link)
        
        return {
            "total_links": len(unique_links),
            "links": unique_links,
            "links_by_type": links_by_type,
            "summary": {
                "annotations": len(links_by_type.get("annotation", [])),
                "hyperlinks": len(links_by_type.get("hyperlink", [])),
                "text_urls": len(links_by_type.get("text_url", [])),
                "emails": len(links_by_type.get("email", []))
            }
        }

# Initialize the extractor
extractor = PDFLinkExtractor()

class PDFDownloaderAndExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.executor = ThreadPoolExecutor(max_workers=5)
        
    def is_pdf_url(self, url: str) -> bool:
        """Check if URL likely points to a PDF"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        query = parsed.query.lower()
        url_lower = url.lower()
        
        # Check file extension
        if path.endswith('.pdf'):
            return True
            
        # Check query parameters that suggest PDF download
        pdf_keywords = [
            'pdf', 'download', 'bulletin', 'extract', 'document', 'report', 
            'generate', 'attachment', 'file', 'export', 'print', 'doc'
        ]
        if any(keyword in query for keyword in pdf_keywords):
            return True
        
        # Check for common PDF generation patterns in URLs
        pdf_patterns = [
            'generatebulletin', 'bulletinextract', 'generatedocument',
            'downloadreport', 'exportpdf', 'printreport', 'getdocument'
        ]
        if any(pattern in url_lower for pattern in pdf_patterns):
            return True
            
        # Check for government/official document patterns
        gov_patterns = [
            '.gov.', '.org.', 'official', 'ministry', 'department',
            'qkb.gov.al', 'umbraco/surface'  # Specific to your example
        ]
        if any(pattern in url_lower for pattern in gov_patterns):
            # If it's a government site, be more liberal with PDF detection
            if any(keyword in query for keyword in ['code', 'id', 'simple', 'subject']):
                return True
        
        return False
        
    def is_potential_pdf_url(self, url: str) -> bool:
        """More liberal check for URLs that might download PDFs"""
        if not url.startswith(('http://', 'https://')):
            return False
            
        # Skip common non-PDF domains
        skip_domains = [
            'facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com',
            'youtube.com', 'google.com', 'wikipedia.org', 'amazon.com'
        ]
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        if any(skip_domain in domain for skip_domain in skip_domains):
            return False
        
        # More liberal criteria for potential PDF URLs
        url_lower = url.lower()
        query = parsed.query.lower()
        path = parsed.path.lower()
        
        # Obvious PDF indicators
        if any(indicator in url_lower for indicator in [
            '.pdf', 'pdf', 'download', 'document', 'report', 'bulletin',
            'extract', 'generate', 'export', 'attachment', 'file'
        ]):
            return True
            
        # Government or official sites are more likely to have documents
        if any(pattern in domain for pattern in ['.gov', '.org', 'official', 'ministry']):
            return True
            
        # URLs with query parameters that suggest dynamic content generation
        if query and any(param in query for param in ['id=', 'code=', 'subject=', 'type=']):
            return True
            
        return False
    
    def download_pdf(self, url: str, timeout: int = 30) -> Optional[bytes]:
        """Download PDF from URL"""
        try:
            # Enhanced headers to mimic a real browser more closely
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            # Make request with follow redirects
            response = self.session.get(
                url, 
                timeout=timeout, 
                stream=True, 
                headers=headers,
                allow_redirects=True,
                verify=False  # Ignore SSL certificate issues for testing
            )
            response.raise_for_status()
            
            # Log response details for debugging
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
            logger.info(f"Content-Length: {response.headers.get('content-length', 'Unknown')}")
            
            # Get full content
            content = response.content
            logger.info(f"Downloaded {len(content)} bytes from {url}")
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            
            # Check if content looks like PDF (starts with %PDF)
            if len(content) > 4 and content[:4] == b'%PDF':
                logger.info(f"Valid PDF detected from {url}")
                return content
            
            # Also accept if content-type says it's a PDF
            if 'application/pdf' in content_type:
                logger.info(f"PDF content-type detected from {url}")
                return content
            
            # For government sites, be more lenient
            if any(pattern in url.lower() for pattern in ['.gov.', 'qkb.gov.al']):
                # Check if it's a form response or redirect that might contain PDF
                if len(content) > 1000:  # Reasonable size for a document
                    logger.info(f"Large content from government site, assuming PDF: {url}")
                    return content
            
            # Log first few bytes for debugging
            logger.warning(f"Content does not appear to be PDF. First 50 bytes: {content[:50]}")
            logger.warning(f"Content-Type was: {content_type}")
            
            return None
            
        except requests.exceptions.SSLError as e:
            logging.error(f"SSL Error downloading from {url}: {str(e)}")
            # Try again without SSL verification
            try:
                response = self.session.get(
                    url, 
                    timeout=timeout, 
                    stream=True, 
                    headers=headers,
                    allow_redirects=True,
                    verify=False
                )
                response.raise_for_status()
                content = response.content
                if len(content) > 4 and content[:4] == b'%PDF':
                    return content
            except Exception as retry_e:
                logging.error(f"Retry without SSL also failed: {str(retry_e)}")
            return None
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error downloading PDF from {url}: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"General error downloading PDF from {url}: {str(e)}")
            return None
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """Extract text content from PDF"""
        text_data = {
            'pages': [],
            'total_pages': 0,
            'total_text_length': 0,
            'metadata': {}
        }
        
        try:
            # Try with PyPDF2 first
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text_data['total_pages'] = len(pdf_reader.pages)
            
            # Extract metadata
            if pdf_reader.metadata:
                text_data['metadata'] = {
                    'title': pdf_reader.metadata.get('/Title', ''),
                    'author': pdf_reader.metadata.get('/Author', ''),
                    'subject': pdf_reader.metadata.get('/Subject', ''),
                    'creator': pdf_reader.metadata.get('/Creator', ''),
                    'producer': pdf_reader.metadata.get('/Producer', ''),
                    'creation_date': str(pdf_reader.metadata.get('/CreationDate', '')),
                    'modification_date': str(pdf_reader.metadata.get('/ModDate', ''))
                }
            
            # Extract text from each page
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    text_data['pages'].append({
                        'page_number': page_num,
                        'text': page_text,
                        'text_length': len(page_text) if page_text else 0
                    })
                    text_data['total_text_length'] += len(page_text) if page_text else 0
                except Exception as e:
                    logging.warning(f"Error extracting text from page {page_num}: {str(e)}")
                    text_data['pages'].append({
                        'page_number': page_num,
                        'text': '',
                        'text_length': 0,
                        'error': str(e)
                    })
            
        except Exception as e:
            logging.error(f"Error with PyPDF2 text extraction: {str(e)}")
            
            # Fallback to pdfplumber
            try:
                with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                    text_data['total_pages'] = len(pdf.pages)
                    
                    for page_num, page in enumerate(pdf.pages, 1):
                        try:
                            page_text = page.extract_text() or ''
                            text_data['pages'].append({
                                'page_number': page_num,
                                'text': page_text,
                                'text_length': len(page_text)
                            })
                            text_data['total_text_length'] += len(page_text)
                        except Exception as e:
                            logging.warning(f"Error extracting text from page {page_num} with pdfplumber: {str(e)}")
                            text_data['pages'].append({
                                'page_number': page_num,
                                'text': '',
                                'text_length': 0,
                                'error': str(e)
                            })
                            
            except Exception as e:
                logging.error(f"Error with pdfplumber text extraction: {str(e)}")
                text_data['error'] = str(e)
        
        return text_data
    
    def clean_phone_number(self, phone: str) -> str:
        """Clean and validate Albanian phone numbers"""
        if not phone:
            return ""
        
        # Remove all non-digit characters except + and spaces
        cleaned = re.sub(r'[^\d\+\s]', '', phone)
        
        # Remove extra spaces
        cleaned = re.sub(r'\s+', '', cleaned)
        
        # Handle Albanian phone number formats
        # Remove country code if present and add it back properly
        if cleaned.startswith('355'):
            cleaned = '+' + cleaned
        elif cleaned.startswith('+355'):
            pass  # Already correct
        elif cleaned.startswith('0'):
            # Remove leading 0 and add +355
            cleaned = '+355' + cleaned[1:]
        else:
            # Assume it's a local number, add +355
            cleaned = '+355' + cleaned
        
        # Ensure it's exactly 12 digits (355 + 9 digits)
        if len(cleaned) == 13 and cleaned.startswith('+355'):
            return cleaned
        elif len(cleaned) == 12 and cleaned.startswith('355'):
            return '+' + cleaned
        else:
            # If it doesn't match expected format, return original but cleaned
            return cleaned
    
    def parse_albanian_business_registry(self, text: str) -> Dict[str, Any]:
        """Parse Albanian business registry details from PDF text"""
        registry_data = {
            'is_albanian_registry': False,
            'business_details': {}
        }
        
        # Check if this is an Albanian business registry document
        registry_indicators = [
            'EKSTRAKT I REGJISTRIT TREGTAR',
            'SUBJEKTIT "PERSON FIZIK"',
            'GJENDJA E REGJISTRIMIT',
            'Numri unik i identifikimit të subjektit',
            'NUIS',
            'Emri i subjektit',
            'Forma ligjore',
            'Data e regjistrimit',
            'Fusha e veprimtarisë',
            'Vendi i ushtrimit të aktivitetit',
            'Statusi'
        ]
        
        # If we find any Albanian business registry indicators, mark as Albanian registry
        found_indicators = sum(1 for indicator in registry_indicators if indicator in text)
        if found_indicators >= 3:  # Need at least 3 indicators to be confident
            registry_data['is_albanian_registry'] = True
            
            # Extract business details with improved patterns
            patterns = {
                'nuis': [
                    r'Numri unik i identifikimit të subjektit\s*\(NUIS\)\s*([A-Z0-9]+)',
                    r'NUIS[:\s]*([A-Z0-9]+)',
                    r'\(NUIS\)\s*([A-Z0-9]+)'
                ],
                'business_name': [
                    r'Emri i subjektit\s+([A-ZËÇÄÖÜ\s]+?)(?:\s*\d|\s*Person|\s*Forma)',
                    r'subjektit\s+"([^"]+)"',
                    r'Emri i subjektit\s+(.+?)(?=\s*\d|\s*Person|\s*Forma|\n)'
                ],
                'legal_form': [
                    r'Forma ligjore\s+([A-Za-zë\s]+?)(?=\s*\d|\n)',
                    r'Forma ligjore[:\s]*([A-Za-zë\s]+)'
                ],
                'registration_date': [
                    r'Data e regjistrimit\s+(\d{2}/\d{2}/\d{4})',
                    r'regjistrimit[:\s]*(\d{2}/\d{2}/\d{4})'
                ],
                'activity_field': [
                    r'Fusha e veprimtarisë\s+([^\.]+\.?)',
                    r'veprimtarisë[:\s]*([^\.]+\.?)'
                ],
                'business_address': [
                    r'Vendi i ushtrimit të aktivitetit\s+([^0-9]*\d[^0-9]*\d+[^\n]*)',
                    r'aktivitetit[:\s]*([^0-9]*\d[^0-9]*\d+[^\n]*)'
                ],
                'email': [
                    r'E-Mail:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                    r'email[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
                ],
                'phone': [
                    r'Telefon:\s*(\+?355\s*[0-9]{8,9})(?:\s|$|[^\d])',
                    r'telefon[:\s]*(\+?355\s*[0-9]{8,9})(?:\s|$|[^\d])',
                    r'Tel[:\s]*(\+?355\s*[0-9]{8,9})(?:\s|$|[^\d])',
                    r'Telefon:\s*(0[0-9]{8,9})(?:\s|$|[^\d])',
                    r'telefon[:\s]*(0[0-9]{8,9})(?:\s|$|[^\d])',
                    r'Tel[:\s]*(0[0-9]{8,9})(?:\s|$|[^\d])',
                    r'Telefon:\s*(\+355[0-9]{8,9})(?:\s|$|[^\d])',
                    r'telefon[:\s]*(\+355[0-9]{8,9})(?:\s|$|[^\d])',
                    r'Tel[:\s]*(\+355[0-9]{8,9})(?:\s|$|[^\d])'
                ],
                'status': [
                    r'Statusi\s+([A-Za-zë]+)',
                    r'Status[:\s]*([A-Zazanë]+)'
                ],
                'date_generated': [
                    r'Datë:\s*(\d{2}/\d{2}/\d{4})',
                    r'Data[:\s]*(\d{2}/\d{2}/\d{4})'
                ]
            }
            
            # Extract each field using multiple patterns
            for field, field_patterns in patterns.items():
                for pattern in field_patterns:
                    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                    if match:
                        value = match.group(1).strip()
                        # Clean up the extracted value
                        value = re.sub(r'\s+', ' ', value)  # Remove extra whitespace
                        value = value.strip('.,;')  # Remove trailing punctuation
                        
                        # Special cleaning for phone numbers
                        if field == 'phone':
                            value = self.clean_phone_number(value)
                        
                        if value:  # Only store non-empty values
                            registry_data['business_details'][field] = value
                            break  # Use first successful match
            
            # Special handling for business name - clean it up
            if 'business_name' in registry_data['business_details']:
                name = registry_data['business_details']['business_name']
                # Remove common suffixes that might be captured
                name = re.sub(r'\s+(Person|Forma|Data|Fusha)', '', name, flags=re.IGNORECASE)
                name = name.strip()
                if name:
                    registry_data['business_details']['business_name'] = name
            
            # Add field labels in both Albanian and English
            registry_data['field_labels'] = {
                'nuis': {'sq': 'NUIS', 'en': 'Unique Business Identification Number'},
                'business_name': {'sq': 'Emri i subjektit', 'en': 'Business Name'},
                'legal_form': {'sq': 'Forma ligjore', 'en': 'Legal Form'},
                'registration_date': {'sq': 'Data e regjistrimit', 'en': 'Registration Date'},
                'activity_field': {'sq': 'Fusha e veprimtarisë', 'en': 'Field of Activity'},
                'business_address': {'sq': 'Vendi i ushtrimit të aktivitetit', 'en': 'Business Address'},
                'email': {'sq': 'E-Mail', 'en': 'Email'},
                'phone': {'sq': 'Telefon', 'en': 'Phone'},
                'status': {'sq': 'Statusi', 'en': 'Status'},
                'date_generated': {'sq': 'Datë', 'en': 'Document Date'}
            }
        
        return registry_data

    def analyze_pdf_content(self, text_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze extracted text content"""
        analysis = {
            'summary': {
                'total_pages': text_data.get('total_pages', 0),
                'total_characters': text_data.get('total_text_length', 0),
                'has_text': text_data.get('total_text_length', 0) > 0
            },
            'metadata': text_data.get('metadata', {}),
            'content_analysis': {}
        }
        
        # Combine all text for analysis
        all_text = ' '.join([page.get('text', '') for page in text_data.get('pages', [])])
        
        if all_text:
            # Word count
            words = all_text.split()
            analysis['content_analysis']['word_count'] = len(words)
            
            # Find emails
            email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            emails = email_pattern.findall(all_text)
            analysis['content_analysis']['emails_found'] = list(set(emails))
            
            # Find phone numbers (basic pattern)
            phone_pattern = re.compile(r'(\+?[\d\s\-\(\)]{10,})')
            phones = [phone.strip() for phone in phone_pattern.findall(all_text) if len(phone.strip()) >= 10]
            analysis['content_analysis']['phone_numbers'] = list(set(phones))
            
            # Find dates (basic pattern)
            date_pattern = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b')
            dates = date_pattern.findall(all_text)
            analysis['content_analysis']['dates_found'] = list(set(dates))
            
            # Find numbers/amounts (basic financial data)
            amount_pattern = re.compile(r'\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b')
            amounts = amount_pattern.findall(all_text)
            analysis['content_analysis']['numerical_values'] = list(set(amounts))[:20]  # Limit to first 20
            
            # Parse Albanian Business Registry if detected
            albanian_registry = self.parse_albanian_business_registry(all_text)
            if albanian_registry['is_albanian_registry']:
                analysis['content_analysis']['albanian_business_registry'] = albanian_registry
            
            # Basic language detection (very simple)
            if all_text:
                analysis['content_analysis']['sample_text'] = all_text[:500] + '...' if len(all_text) > 500 else all_text
        
        return analysis
    
    async def process_url_liberal(self, url: str) -> Dict[str, Any]:
        """Download and process a URL with liberal PDF detection - for processing all links"""
        result = {
            'url': url,
            'status': 'failed',
            'timestamp': datetime.now().isoformat(),
            'data': {}
        }
        
        try:
            # Always try to download, regardless of URL pattern
            logger.info(f"Attempting to download from: {url}")
            
            # Download content
            pdf_content = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.download_pdf, url
            )
            
            if not pdf_content:
                result['status'] = 'skipped'
                result['reason'] = 'No content downloaded or content is not a PDF'
                return result
            
            result['data']['file_size'] = len(pdf_content)
            logger.info(f"Downloaded {len(pdf_content)} bytes from {url}")
            
            # Extract links from downloaded PDF
            links_data = extractor.extract_all_links(pdf_content)
            result['data']['links'] = links_data
            
            # Extract text content
            text_data = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.extract_text_from_pdf, pdf_content
            )
            
            # Analyze content
            analysis = self.analyze_pdf_content(text_data)
            result['data']['content'] = analysis
            result['data']['raw_text'] = text_data  # Include raw text data
            
            result['status'] = 'success'
            logger.info(f"Successfully processed PDF from: {url}")
            
        except Exception as e:
            result['status'] = 'error'
            result['reason'] = str(e)
            logging.error(f"Error processing URL {url}: {str(e)}")
        
        return result

# Initialize the downloader
pdf_downloader = PDFDownloaderAndExtractor()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return {"message": "Albanian Business Registry Extractor", "version": "1.0.0", "note": "Web interface not found"}

@app.post("/extract-and-process-table")
async def extract_and_process_table(file: UploadFile = File(...)):
    """Extract links from uploaded PDF and process all Albanian business registries into a table format"""
    
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        pdf_content = await file.read()
        links_result = extractor.extract_all_links(pdf_content)
        
        # Get all HTTP/HTTPS URLs
        all_urls = []
        for link in links_result.get('links', []):
            url = link.get('url', '')
            if url and url.startswith(('http://', 'https://')):
                all_urls.append(url)
        
        if not all_urls:
            return JSONResponse(content={
                "status": "no_http_links",
                "message": "No HTTP/HTTPS links found in the uploaded file",
                "businesses": []
            })
        
        # Limit to first 50 URLs to prevent server overload
        urls_to_process = all_urls[:50]
        
        # Process all URLs with liberal detection
        tasks = [pdf_downloader.process_url_liberal(url) for url in urls_to_process]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and extract business data
        businesses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                continue
            
            if isinstance(result, dict) and result.get('status') == 'success' and result.get('data', {}).get('content', {}).get('content_analysis', {}).get('albanian_business_registry'):
                registry = result['data']['content']['content_analysis']['albanian_business_registry']
                if registry.get('is_albanian_registry') and registry.get('business_details'):
                    business = {
                        'source_url': result['url'],
                        'nuis': registry['business_details'].get('nuis', ''),
                        'business_name': registry['business_details'].get('business_name', ''),
                        'legal_form': registry['business_details'].get('legal_form', ''),
                        'registration_date': registry['business_details'].get('registration_date', ''),
                        'activity_field': registry['business_details'].get('activity_field', ''),
                        'business_address': registry['business_details'].get('business_address', ''),
                        'email': registry['business_details'].get('email', ''),
                        'phone': registry['business_details'].get('phone', ''),
                        'status': registry['business_details'].get('status', ''),
                        'date_generated': registry['business_details'].get('date_generated', ''),
                        'file_size': result['data'].get('file_size', 0),
                        'pages': result['data']['content']['summary'].get('total_pages', 0),
                        'processed_at': result.get('timestamp', '')
                    }
                    businesses.append(business)
        
        return JSONResponse(content={
            "status": "completed",
            "original_file": file.filename,
            "total_links_found": len(all_urls),
            "total_processed": len(urls_to_process),
            "businesses_found": len(businesses),
            "businesses": businesses,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in extract and process table: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "albanian-business-registry-extractor"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
