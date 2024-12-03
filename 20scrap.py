import json
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import hashlib

def load_cache():
    cache_path = 'cache/scraping_cache.json'
    if os.path.exists(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    # Create cache directory if it doesn't exist
    os.makedirs('cache', exist_ok=True)
    
    cache_path = 'cache/scraping_cache.json'
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def get_url_hash(url):
    return hashlib.md5(url.encode('utf-8')).hexdigest()

def extract_content(soup):
    """Helper function to extract content using multiple fallback methods"""
    # Try different content containers
    content_selectors = [
        'article',
        'main',
        '.content',  # Common content class
        '#content',  # Common content ID
        '.post-content',
        '.article-content',
        '.story-content'
    ]
    
    for selector in content_selectors:
        content_element = soup.select_one(selector)
        if content_element:
            # Remove unwanted elements
            for unwanted in content_element.select('script, style, nav, header, footer'):
                unwanted.decompose()
            
            # Get text and clean it
            content = content_element.get_text(separator='\n', strip=True)
            if content:
                return content
    
    # If no content found through selectors, try getting all paragraph text
    paragraphs = soup.find_all('p')
    if paragraphs:
        content = '\n'.join(p.get_text(strip=True) for p in paragraphs)
        if content:
            return content
            
    return 'Content extraction failed'

def scrape_and_save():
    # Create data folder if it doesn't exist
    data_folder = 'data'
    os.makedirs(data_folder, exist_ok=True)
    
    output_file = os.path.join(data_folder, 'scraped_content.json')
    
    # Load cache
    cache = load_cache()
    
    # Read existing data or create empty list
    existing_data = []
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    
    # Read URLs from json file
    with open('url.json', 'r') as file:
        url_data = json.load(file)
    
    # Process each URL in the file
    for url_entry in url_data:
        url = url_entry['url']
        url_hash = get_url_hash(url)
        
        print(f"\nProcessing URL: {url}")
        
        # Check if URL is in cache and not too old (e.g., less than 24 hours)
        if url_hash in cache:
            print("Using cached content...")
            cached_article = cache[url_hash]
            
            # Check if content already exists in output
            content_exists = False
            for article in existing_data:
                if article['source_url'] == url:
                    content_exists = True
                    break
            
            if not content_exists:
                existing_data.append(cached_article)
                print("Added cached content to output")
            continue
        
        try:
            # Fetch and parse webpage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': '*'  # Accept any language
            }
            response = requests.get(url, headers=headers)
            response.encoding = response.apparent_encoding  # Handle character encoding
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract content
            title = soup.find('h1')
            title = title.text.strip() if title else 'Title not found'
            content = extract_content(soup)
            
            # Create article content
            article_content = {
                'title': title,
                'content': content,
                'scraped_at': datetime.now().isoformat(),
                'source_url': url
            }
            
            # Add to cache
            cache[url_hash] = article_content
            save_cache(cache)
            
            # Check if content already exists
            content_exists = False
            for article in existing_data:
                if article['source_url'] == url:
                    content_exists = True
                    break
            
            if not content_exists:
                existing_data.append(article_content)
                print(f"New content found and saved")
            
        except Exception as e:
            print(f"Error processing URL {url}: {str(e)}")
    
    # Save all content to JSON file in data folder
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nAll processing complete. Data saved to: {output_file}")

if __name__ == "__main__":
    scrape_and_save()