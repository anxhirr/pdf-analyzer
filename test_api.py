import requests
import json

def test_api():
    """Test the PDF Link Extractor API"""
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Error testing health endpoint: {e}")
        return
    
    # Test file upload (you'll need to provide a PDF file)
    pdf_file_path = input("Enter path to a PDF file to test (or press Enter to skip): ").strip()
    
    if pdf_file_path:
        try:
            with open(pdf_file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post("http://localhost:8000/extract-links", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"\nExtraction successful!")
                    print(f"Total links found: {result['data']['total_links']}")
                    print(f"Summary: {json.dumps(result['data']['summary'], indent=2)}")
                    
                    # Display first few links
                    links = result['data']['links'][:5]  # Show first 5 links
                    print("\nFirst few links:")
                    for i, link in enumerate(links, 1):
                        print(f"{i}. {link['url']} (Page {link['page']}, Type: {link['type']})")
                        
                else:
                    print(f"Error: {response.status_code} - {response.text}")
                    
        except FileNotFoundError:
            print("PDF file not found!")
        except Exception as e:
            print(f"Error testing file upload: {e}")

if __name__ == "__main__":
    print("PDF Link Extractor API Test")
    print("Make sure the server is running on http://localhost:8000")
    test_api()
