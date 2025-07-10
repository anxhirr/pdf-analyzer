import requests
import json

def test_enhanced_api():
    """Test the enhanced PDF Link Extractor API"""
    
    base_url = "http://localhost:8000"
    
    print("=== Testing Enhanced PDF Link Extractor API ===\n")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        return
    
    # Test URL processing with the example URL you provided
    test_urls = [
        "http://www.qkb.gov.al/umbraco/Surface/SearchSurface/GenerateBulletinExtract?subjectDefCode=3AC4FF72-172E-4173-BC32-1D3E24F2AE41&isSimple=true",
        # Add more test URLs if you have them
    ]
    
    print(f"\n=== Testing URL Processing ===")
    print(f"Processing {len(test_urls)} URLs...")
    
    try:
        response = requests.post(
            f"{base_url}/process-pdf-urls",
            json=test_urls,
            timeout=60  # Give it time to download and process
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ URL processing completed!")
            print(f"📊 Summary:")
            print(f"   - Total URLs: {result['summary']['total_urls']}")
            print(f"   - Successful: {result['summary']['successful']}")
            print(f"   - Failed: {result['summary']['failed']}")
            print(f"   - Skipped: {result['summary']['skipped']}")
            
            # Show details for each URL
            for i, url_result in enumerate(result['results'], 1):
                print(f"\n📄 URL {i}: {url_result['status'].upper()}")
                print(f"   URL: {url_result['url']}")
                
                if url_result['status'] == 'success' and 'data' in url_result:
                    data = url_result['data']
                    content = data.get('content', {})
                    links = data.get('links', {})
                    
                    print(f"   📊 Content Analysis:")
                    print(f"      - Pages: {content.get('summary', {}).get('total_pages', 0)}")
                    print(f"      - Characters: {content.get('summary', {}).get('total_characters', 0)}")
                    print(f"      - Words: {content.get('content_analysis', {}).get('word_count', 0)}")
                    print(f"      - Links found: {links.get('total_links', 0)}")
                    
                    emails = content.get('content_analysis', {}).get('emails_found', [])
                    if emails:
                        print(f"      - Emails found: {', '.join(emails[:3])}{'...' if len(emails) > 3 else ''}")
                    
                    sample_text = content.get('content_analysis', {}).get('sample_text', '')
                    if sample_text:
                        print(f"      - Content sample: {sample_text[:100]}...")
                        
                elif url_result['status'] != 'success':
                    print(f"   ❌ Reason: {url_result.get('reason', 'Unknown error')}")
            
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing URL processing: {e}")
    
    # Test file upload (if user provides a file)
    print(f"\n=== Testing File Upload ===")
    pdf_file_path = input("Enter path to a PDF file to test extraction (or press Enter to skip): ").strip()
    
    if pdf_file_path:
        try:
            with open(pdf_file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{base_url}/extract-links", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Link extraction successful!")
                    print(f"📊 Found {result['data']['total_links']} total links")
                    
                    # Show first few links
                    links = result['data']['links'][:3]
                    for i, link in enumerate(links, 1):
                        print(f"   {i}. {link['url']} (Page {link['page']}, Type: {link['type']})")
                        
                else:
                    print(f"❌ Error: {response.status_code} - {response.text}")
                    
        except FileNotFoundError:
            print("❌ PDF file not found!")
        except Exception as e:
            print(f"❌ Error testing file upload: {e}")

if __name__ == "__main__":
    print("🚀 Enhanced PDF Link Extractor API Test")
    print("Make sure the server is running on http://localhost:8000")
    print("This will test the new URL downloading and processing functionality.\n")
    test_enhanced_api()
