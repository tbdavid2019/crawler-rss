import os
import time
import uuid
import random
import requests
from datetime import datetime, timedelta
import gradio as gr
from bs4 import BeautifulSoup

# 預設 RSS 來源清單
DEFAULT_SOURCES = {
    "BBC Business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "BBC Technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "Bloomberg Markets": "https://feeds.bloomberg.com/markets/news.rss",
    "Bloomberg Technology": "https://feeds.bloomberg.com/technology/news.rss",
    "Nasdaq Stocks": "https://www.nasdaq.com/feed/rssoutbound?category=Stocks",
    "Nasdaq ETFs": "https://www.nasdaq.com/feed/rssoutbound?category=ETFs",
    "Nasdaq Technology": "https://www.nasdaq.com/feed/rssoutbound?category=Technology",
    "Nasdaq Insight": "https://www.nasdaq.com/feed/rssoutbound?category=Nasdaq",
    "Nasdaq Innovation": "https://www.nasdaq.com/feed/rssoutbound?category=Innovation",
    "Nasdaq Financial Advisors": "https://www.nasdaq.com/feed/rssoutbound?category=Financial+Advisors"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

OUTPUT_DIR = "./outputs"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def cleanup_old_files():
    """刪除超過一小時的舊檔案"""
    now = time.time()
    one_hour_ago = now - 3600
    for fname in os.listdir(OUTPUT_DIR):
        if fname.endswith(".txt"):
            fpath = os.path.join(OUTPUT_DIR, fname)
            if os.path.getmtime(fpath) < one_hour_ago:
                os.remove(fpath)

def scrape_articles(article_urls):
    """給定文章 URL 清單，抓取文章內容"""
    logs = []
    articles = []
    for index, full_url in enumerate(article_urls, 1):
        logs.append(f"Processing article {index}/{len(article_urls)}: {full_url}")
        try:
            article_response = requests.get(full_url, headers=HEADERS, timeout=30)
            if article_response.status_code != 200:
                logs.append(f"Failed to fetch {full_url}. HTTP Status Code: {article_response.status_code}")
                continue
            
            article_soup = BeautifulSoup(article_response.text, "html.parser")
            paragraphs = article_soup.select("p")
            content = "\n".join([p.get_text(strip=True) for p in paragraphs])
            if len(content.strip()) < 50:
                logs.append(f"Content too short for article: {full_url}")
                continue
            articles.append({"URL": full_url, "Content": content})
            logs.append(f"Successfully scraped article: {full_url}")

            delay = random.uniform(0.5, 1.5)
            time.sleep(delay)
        except Exception as e:
            logs.append(f"Error processing {full_url}: {e}")

    return articles, "\n".join(logs)

def scrape_rss_feed(rss_url):
    """給定RSS URL，取得所有新聞連結"""
    article_urls = []
    try:
        resp = requests.get(rss_url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            return article_urls, f"Failed to fetch RSS: {rss_url} HTTP {resp.status_code}"
        
        soup = BeautifulSoup(resp.text, "xml")
        items = soup.find_all("item")
        for item in items:
            link_tag = item.find("link")
            if link_tag and link_tag.text.strip():
                article_urls.append(link_tag.text.strip())
        return article_urls, f"Found {len(article_urls)} articles from {rss_url}"
    except Exception as e:
        return article_urls, f"Error fetching RSS: {rss_url}, {e}"

def scrape(selected_sources, custom_rss):
    # 先清理舊檔案
    cleanup_old_files()

    logs = []
    # 將所選源的 RSS URL 收集起來
    rss_list = []
    for src in selected_sources:
        rss_list.append(DEFAULT_SOURCES[src])
    if custom_rss.strip():
        rss_list.append(custom_rss.strip())

    all_articles = []
    # 依序處理 RSS
    for rss_url in rss_list:
        article_urls, rss_log = scrape_rss_feed(rss_url)
        logs.append(rss_log)
        if article_urls:
            articles, article_logs = scrape_articles(article_urls)
            all_articles.extend(articles)
            logs.append(article_logs)

    # 產生獨特檔名
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"allnews_{timestamp_str}_{unique_id}.txt"
    output_path = os.path.join(OUTPUT_DIR, filename)

    # 寫入檔案
    if all_articles:
        with open(output_path, "w", encoding="utf-8") as f:
            for article in all_articles:
                f.write(f"URL: {article['URL']}\n")
                f.write(f"Content: {article['Content']}\n\n")
        logs.append(f"Scraping completed. Total articles: {len(all_articles)}. Output saved to {filename}")
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("No articles found.")
        logs.append("No articles found from the selected RSS sources.")

    return "\n".join(logs), output_path


# 建立 Gradio 介面
def run_interface(selected_feeds, custom_rss):
    logs, file_path = scrape(selected_feeds, custom_rss)
    return logs, file_path

with gr.Blocks() as demo:
    gr.Markdown("# News RSS Crawler (Hugging Face Spaces)")
    gr.Markdown("選擇你想抓取的 RSS 來源並可另外輸入自訂的 RSS URL，點擊「Scrape」後將產生文字檔以供下載。")
    
    with gr.Row():
        selected_sources = gr.CheckboxGroup(
            choices=list(DEFAULT_SOURCES.keys()),
            value=list(DEFAULT_SOURCES.keys()),
            label="Select RSS Feeds"
        )
        custom_rss = gr.Textbox(
            label="Custom RSS URL (optional)",
            placeholder="Paste your custom RSS feed URL here..."
        )

    scrape_button = gr.Button("Scrape")
    
    logs_output = gr.Textbox(label="Logs", interactive=False)
    download_file = gr.File(label="Download Result")
    
    scrape_button.click(fn=run_interface, inputs=[selected_sources, custom_rss], outputs=[logs_output, download_file])

demo.launch()