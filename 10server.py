from flask import Flask, request, jsonify, render_template_string
import os
import json
from datetime import datetime
import webbrowser

app = Flask(__name__)

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>URL Analysis System</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        .entry {
            border: 1px solid #ddd;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .date {
            color: #666;
            font-size: 0.9em;
        }
        .url {
            color: #0066cc;
            text-decoration: none;
            word-break: break-all;
            display: block;
            margin: 10px 0;
        }
        .title {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .analysis {
            margin-top: 10px;
            color: #333;
        }
    </style>
</head>
<body>
    <h1></h1>
    {% for entry in entries %}
    <div class="entry">
        <div class="title">{{ entry.title }}</div>
        <div class="date">{{ entry.scraped_date.strftime('%d/%m/%Y') if entry.scraped_date else '' }}</div>
        <a class="url" href="{{ entry.source_url }}" target="_blank">{{ entry.source_url }}</a>
        <div class="analysis">{{ entry.analysis }}</div>
    </div>
    {% endfor %}
</body>
</html>
'''

def load_news():
    if os.path.exists('data/analysis_results.json'):
        with open('data/analysis_results.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

@app.route('/')
def show_urls():
    try:
        entries = load_news()
        latest_entry = entries[-1] if entries else None
        if latest_entry and 'scraped_date' in latest_entry:
            latest_entry['scraped_date'] = datetime.fromisoformat(latest_entry['scraped_date'].replace('Z', '+00:00'))
        return render_template_string(HTML_TEMPLATE, entries=[latest_entry] if latest_entry else [])
    except Exception as e:
        return f"Error loading news: {str(e)}", 500

@app.route('/save', methods=['POST'])
def save_url():
    try:
        data = request.json
        if not data or 'url' not in data:
            return jsonify({'status': 'error', 'message': 'Missing URL'}), 400

        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Load existing URLs from url.json (not data directory)
        articles = []
        if os.path.exists('url.json'):
            with open('url.json', 'r', encoding='utf-8') as f:
                articles = json.load(f)

        # Check if URL already exists
        if any(article['url'] == data['url'] for article in articles):
            return jsonify({'status': 'success', 'message': 'URL already saved'})

        # Create new article entry
        new_article = {
            'url': data['url'],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        articles.append(new_article)

        # Save updated articles
        with open('url.json', 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)

        return jsonify({'status': 'success', 'message': 'URL saved successfully'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

if __name__ == '__main__':
    # Open browser before starting the server
    webbrowser.open('http://127.0.0.1:5000')
    app.run(debug=True, port=5000)