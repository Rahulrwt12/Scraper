import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- CONFIGURATION ---
MAIN_FOLDER = "Advanced Energy"
START_URL = "https://www.advancedenergy.com/en-us/"
# --- END CONFIGURATION ---

def sanitize_name(name):
    """Removes invalid characters for folder or file names."""
    name = name.strip()
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def get_soup(url, session):
    """Fetches a URL and returns a BeautifulSoup object, handling errors."""
    print(f"  - Visiting: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        }
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching {url}: {e}")
        return None

def save_text_file(file_path, title, description):
    """Saves the title and description to a text file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"{title}\n\n")
            f.write(description)
        print(f"    📝 Saved description to: {os.path.basename(file_path)}")
    except IOError as e:
        print(f"    ❌ Error saving text file: {e}")

def download_pdf(pdf_url, file_path, session):
    """Downloads a PDF from a URL and saves it to a specific path."""
    if os.path.exists(file_path):
        print(f"    - Skipping already downloaded file: {os.path.basename(file_path)}")
        return
        
    print(f"    -> Downloading: {os.path.basename(file_path)}")
    try:
        response = session.get(pdf_url, stream=True, timeout=30)
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        print(f"    ✅ Saved datasheet successfully.")
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Error downloading {pdf_url}: {e}")

def main():
    """Main function to orchestrate the scraping process."""
    print(f"🚀 Starting the Advanced Energy scraper...")
    os.makedirs(MAIN_FOLDER, exist_ok=True)
    session = requests.Session()

    # Step 1 & 2: Open start URL and get the Products page URL
    print(f"\n[Step 1/2] Navigating to Products page...")
    homepage_soup = get_soup(START_URL, session)
    if not homepage_soup: return
    
    products_link_tag = homepage_soup.select_one('nav a[href="/en-us/products/"]')
    if not products_link_tag:
        print("❌ Critical error: Could not find the main 'Products' navigation link.")
        return
    products_url = urljoin(START_URL, products_link_tag['href'])
    
    # Step 3: Parse the main Products page to find all categories and their sub-categories
    print(f"\n[Step 3 & 4] Finding all categories and sub-categories from: {products_url}")
    products_page_soup = get_soup(products_url, session)
    if not products_page_soup: return

    # Find the container for "Explore Our Product Portfolio"
    portfolio_container = products_page_soup.select_one('div.stack.my-12')
    if not portfolio_container:
        print("❌ Critical error: Could not find the 'Explore Our Product Portfolio' container.")
        return

    # Find each main category block within the container
    category_blocks = portfolio_container.select('div.hover\\:shadow-highlight')
    print(f"✅ Found {len(category_blocks)} main category blocks.")

    for block in category_blocks:
        main_category_tag = block.find('h3', class_='title-highlight')
        if not main_category_tag: continue

        category_name = sanitize_name(main_category_tag.get_text(strip=True))
        category_path = os.path.join(MAIN_FOLDER, category_name)
        os.makedirs(category_path, exist_ok=True)
        print(f"\nProcessing Category: {category_name}")

        # Find all sub-category links within this same block
        sub_category_links = block.select('ul li a')
        print(f"  Found {len(sub_category_links)} sub-categories.")

        for sub_cat_link in sub_category_links:
            sub_category_name = sanitize_name(sub_cat_link.get_text(strip=True))
            sub_category_url = urljoin(products_url, sub_cat_link['href'])
            sub_category_path = os.path.join(category_path, sub_category_name)
            os.makedirs(sub_category_path, exist_ok=True)
            print(f"  -> Processing Sub-Category: {sub_category_name}")
            
            # Step 5 & 6: Visit the sub-category page to get its details
            sub_category_soup = get_soup(sub_category_url, session)
            if not sub_category_soup: continue

            # Step 5: Get the title and description and save to a .txt file
            print("[Step 5] Saving description text file...")
            title_tag = sub_category_soup.find('h1')
            title = title_tag.get_text(strip=True) if title_tag else sub_category_name
            description_div = sub_category_soup.select_one('div.header-content-description')
            description = description_div.get_text(strip=True) if description_div else "No description found."
            
            text_filename = f"{sub_category_name}_description.txt"
            text_filepath = os.path.join(sub_category_path, text_filename)
            save_text_file(text_filepath, title, description)

            # Step 6: Find the table below "Parametric Search" and download datasheets
            print("[Step 6] Searching for product datasheets in the table...")
            product_rows = sub_category_soup.select('div.table-responsive tbody tr')
            if not product_rows:
                print("    - No product table found on this page.")
                continue
            
            print(f"    Found {len(product_rows)} products in the table.")
            for row in product_rows:
                product_cell = row.find('td', {'data-title': 'Product'})
                datasheet_cell = row.find('td', {'data-title': 'Datasheet'})

                if product_cell and datasheet_cell:
                    product_name = sanitize_name(product_cell.get_text(strip=True))
                    datasheet_link_tag = datasheet_cell.find('a', href=True)

                    if product_name and datasheet_link_tag:
                        pdf_url = urljoin(sub_category_url, datasheet_link_tag['href'])
                        pdf_filename = f"{product_name}_datasheet.pdf"
                        file_path = os.path.join(sub_category_path, pdf_filename)
                        download_pdf(pdf_url, file_path, session)

    print("\n\n✅ All tasks completed. Scraping finished.")

if __name__ == "__main__":
    main()