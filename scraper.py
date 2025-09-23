import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# --- CONFIGURATION ---
# 1. The URL of the single page you want to scrape.
TARGET_URL = "https://www.advancedenergy.com/en-us/" 

# 2. The folders where the files will be saved.
TEXT_FOLDER = 'Text'
IMAGE_FOLDER = 'Images'
# --- END CONFIGURATION ---

def setup_folders():
    """Create the necessary folders if they don't exist."""
    os.makedirs(TEXT_FOLDER, exist_ok=True)
    os.makedirs(IMAGE_FOLDER, exist_ok=True)
    print(f"✅ Folders '{TEXT_FOLDER}' and '{IMAGE_FOLDER}' are ready.")

def scrape_single_page(url, session):
    """Scrapes systematically formatted text and all image URLs from a single page."""
    print(f" anFetching content from: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
        }
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching {url}: {e}")
        return None, []

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # --- 1. Scrape Text Systematically ---
    # Instead of getting all text, we target specific tags that usually hold content.
    # This provides a much cleaner and more organized output.
    systematic_text = []
    # Find all headings, paragraphs, and list items in the order they appear.
    content_tags = soup.find_all(['h1', 'h2', 'h3', 'p', 'li'])
    
    for tag in content_tags:
        # Get the text from each tag and strip extra whitespace.
        text = tag.get_text(strip=True)
        if text: # Only add the line if it's not empty.
            systematic_text.append(text)
    
    # Join the collected lines of text with a newline character.
    formatted_text = "\n".join(systematic_text)

    # --- 2. Find All Images on the Page ---
    image_urls = []
    for img_tag in soup.find_all('img'):
        src = img_tag.get('src')
        if src:
            # Convert relative image URLs (e.g., '/logo.png') to absolute URLs.
            full_url = urljoin(url, src)
            image_urls.append(full_url)

    return formatted_text, image_urls

def save_text(text_content):
    """Saves the scraped text to a file."""
    # Create a simple filename for the single page.
    filename = "scraped_content.txt"
    filepath = os.path.join(TEXT_FOLDER, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text_content)
        print(f"📄 Saved text to: {filepath}")
    except IOError as e:
        print(f"❌ Error saving text to {filepath}: {e}")

def save_image(url, session):
    """Downloads and saves a single image from a URL."""
    try:
        response = session.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        # Get a clean image name from the URL.
        image_name = os.path.basename(urlparse(url).path)
        if not image_name:
            return # Skip if we can't get a valid filename.
            
        filepath = os.path.join(IMAGE_FOLDER, image_name)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        print(f"🖼️ Saved image: {image_name}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading image {url}: {e}")
    except IOError as e:
        print(f"❌ Error saving image {image_name}: {e}")

def main():
    """Main function to run the single-page scraper."""
    setup_folders()
    
    # Use a session object for efficient requests.
    session = requests.Session()
    
    # --- Scrape, Save Text, and Save Images ---
    text, images = scrape_single_page(TARGET_URL, session)
    
    if text:
        save_text(text)
    
    if images:
        print(f"\nFound {len(images)} images. Downloading...")
        for image_url in images:
            save_image(image_url, session)
            
    print("\n✅ Scraping finished.")
    session.close()

if __name__ == "__main__":
    main()