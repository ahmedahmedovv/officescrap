import asyncio
import json
import os
from mistralai import Mistral
from dotenv import load_dotenv
import time
import random
from tenacity import retry, stop_after_attempt, wait_exponential
import hashlib
import yaml

async def load_articles():
    with open('data/scraped_content.json', 'r', encoding='utf-8') as file:
        return json.load(file)

async def load_cache():
    # Create cache directory if it doesn't exist
    os.makedirs('cache', exist_ok=True)
    
    cache_path = 'cache/analysis_cache.json'
    if os.path.exists(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

async def save_cache(cache):
    # Create cache directory if it doesn't exist
    os.makedirs('cache', exist_ok=True)
    
    cache_path = 'cache/analysis_cache.json'
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def get_article_hash(article):
    # Create a unique hash based on the article content
    content = article.get('content', '')
    return hashlib.md5(content.encode('utf-8')).hexdigest()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry_error_callback=lambda retry_state: retry_state.outcome.result()
)
async def analyze_article(client, article, cache):
    # Generate hash for the article
    article_hash = get_article_hash(article)
    
    # Check if article is in cache
    if article_hash in cache:
        print(f"\nUsing cached analysis for article...")
        cached_result = cache[article_hash]
        # Add source_url and scraped_date to cached result
        cached_result['source_url'] = article.get('source_url', '')
        cached_result['scraped_date'] = article.get('scraped_at', '')
        return cached_result
    
    # If not in cache, proceed with analysis
    print(f"\nAnalyzing new article...")
    
    # Add random delay between requests (1-3 seconds)
    await asyncio.sleep(random.uniform(1, 3))
    
    prompts = await load_prompts()
    prompt = prompts['article_analysis']['prompt'].format(content=article['content'])
    
    response = await client.chat.stream_async(
        model="mistral-tiny",
        messages=[{"role": "user", "content": prompt}],
    )
    
    full_response = ""
    print(f"\nAnalyzing article content...\n")
    
    async for chunk in response:
        if chunk.data.choices[0].delta.content is not None:
            content = chunk.data.choices[0].delta.content
            full_response += content
            print(content, end="")
    
    print("\n" + "-"*50)
    
    # Parse the response to extract title and summary
    try:
        lines = full_response.strip().split('\n')
        
        # Debug print
        print("\nDebug - Full response:", full_response)
        print("Debug - Lines:", lines)
        
        # More robust parsing
        title = ""
        summary = ""
        
        for line in lines:
            if line.lower().startswith('title:'):
                title = line.replace('Title:', '').replace('title:', '').strip()
            elif line.lower().startswith('summary:'):
                summary = line.replace('Summary:', '').replace('summary:', '').strip()
            elif summary and line.strip():  # Append additional summary lines
                summary += ' ' + line.strip()
        
        # If parsing failed, use some fallbacks
        if not title:
            title = "Untitled Article"
        if not summary:
            summary = full_response.strip()
        
        print("\nDebug - Extracted title:", title)
        print("Debug - Extracted summary:", summary)
        
        # Store result in cache before returning
        result = {
            "title": title,
            "analysis": summary,
            "source_url": article.get('source_url', ''),
            "scraped_date": article.get('scraped_at', '')
        }
        cache[article_hash] = result
        return result
    except Exception as e:
        print(f"Error parsing response: {e}")
        # Fallback to raw response
        return {
            "title": "Error parsing title",
            "analysis": full_response.strip()
        }

async def load_prompts():
    with open('prompts/prompts.yaml', 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

async def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Load API key from .env
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not found in environment variables")

    # Initialize Mistral client
    client = Mistral(api_key=api_key)
    
    # Load cache
    cache = await load_cache()
    
    # Load articles
    articles = await load_articles()
    
    # Analyze articles in smaller batches
    batch_size = 3
    results = []
    
    for i in range(0, len(articles), batch_size):
        batch = articles[i:i + batch_size]
        tasks = [analyze_article(client, article, cache) for article in batch]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)
        
        # Save cache after each batch
        await save_cache(cache)
        
        # Add delay between batches
        if i + batch_size < len(articles):
            await asyncio.sleep(5)
    
    # Save final results
    output_path = 'data/analysis_results.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
