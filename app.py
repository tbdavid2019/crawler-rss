import os
import time
import uuid
import random
import requests
from datetime import datetime
import gradio as gr
from bs4 import BeautifulSoup

# 預設 RSS 來源清單
DEFAULT_SOURCES = {
    "BBC Business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "Bloomberg Technology": "https://feeds.bloomberg.com/technology/news.rss",
    "WSJ World News": "https://feeds.content.dowjones.io/public/rss/RSSWorldNews",
    "WSJ US Business": "https://feeds.content.dowjones.io/public/rss/WSJcomUSBusiness",
    "WSJ Markets": "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain",
    "WSJ Technology": "https://feeds.content.dowjones.io/public/rss/RSSWSJD"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
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

def scrape_articles(article_urls, logs, max_retries=3, timeout=60):
    articles = []
    for index, full_url in enumerate(article_urls, 1):
        logs.append(f"[{datetime.now()}] Processing article {index}/{len(article_urls)}: {full_url}")
        success = False
        for attempt in range(1, max_retries+1):
            try:
                logs.append(f"[{datetime.now()}] Attempt {attempt} - GET {full_url}")
                article_response = requests.get(full_url, headers=HEADERS, timeout=timeout)
                if article_response.status_code != 200:
                    logs.append(f"[{datetime.now()}] Failed to fetch {full_url}. HTTP Status Code: {article_response.status_code}")
                else:
                    logs.append(f"[{datetime.now()}] Successfully fetched {full_url}, parsing content...")
                    article_soup = BeautifulSoup(article_response.text, "html.parser")
                    paragraphs = article_soup.select("p")
                    content = "\n".join([p.get_text(strip=True) for p in paragraphs])
                    if len(content.strip()) < 50:
                        logs.append(f"[{datetime.now()}] Content too short for article: {full_url}")
                    else:
                        articles.append({"URL": full_url, "Content": content})
                        logs.append(f"[{datetime.now()}] Successfully parsed article: {full_url}")
                        success = True
                        break
            except Exception as e:
                logs.append(f"[{datetime.now()}] Error processing {full_url}: {e}")

            if not success:
                wait_time = random.uniform(2, 5)
                logs.append(f"[{datetime.now()}] Waiting {wait_time:.2f}s before retry...")
                time.sleep(wait_time)

        if not success:
            logs.append(f"[{datetime.now()}] Giving up on article {full_url} after {max_retries} attempts.")

        delay = random.uniform(1, 2)
        logs.append(f"[{datetime.now()}] Waiting {delay:.2f} seconds before next article...")
        time.sleep(delay)

    return articles, logs

def scrape_rss_feed(rss_url, logs, max_retries=3, timeout=60):
    logs.append(f"[{datetime.now()}] Starting to fetch RSS: {rss_url}")
    article_urls = []
    success = False
    for attempt in range(1, max_retries+1):
        try:
            logs.append(f"[{datetime.now()}] Attempt {attempt} - GET {rss_url}")
            resp = requests.get(rss_url, headers=HEADERS, timeout=timeout)
            if resp.status_code != 200:
                logs.append(f"[{datetime.now()}] Failed to fetch RSS {rss_url}. HTTP Status: {resp.status_code}")
            else:
                logs.append(f"[{datetime.now()}] Successfully fetched RSS {rss_url}, parsing XML...")
                soup = BeautifulSoup(resp.text, "xml")
                items = soup.find_all("item")
                for item in items:
                    link_tag = item.find("link")
                    if link_tag and link_tag.text.strip():
                        article_urls.append(link_tag.text.strip())
                logs.append(f"[{datetime.now()}] Found {len(article_urls)} articles from {rss_url}")
                success = True
                break
        except Exception as e:
            logs.append(f"[{datetime.now()}] Error fetching RSS: {rss_url}, {e}")

        if not success:
            wait_time = random.uniform(3, 6)
            logs.append(f"[{datetime.now()}] Waiting {wait_time:.2f}s before retry...")
            time.sleep(wait_time)

    if not success:
        logs.append(f"[{datetime.now()}] Giving up on RSS {rss_url} after {max_retries} attempts.")

    return article_urls, logs

def scrape(selected_sources, custom_rss):
    # 清理舊檔
    cleanup_old_files()

    logs = []
    rss_list = []
    for src in selected_sources:
        rss_list.append(DEFAULT_SOURCES[src])
    if custom_rss.strip():
        rss_list.append(custom_rss.strip())

    all_articles = []
    for rss_url in rss_list:
        article_urls, logs = scrape_rss_feed(rss_url, logs)
        if article_urls:
            scraped_articles, logs = scrape_articles(article_urls, logs)
            all_articles.extend(scraped_articles)

    # 產生獨特檔名
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"allnews_{timestamp_str}_{unique_id}.txt"
    output_path = os.path.join(OUTPUT_DIR, filename)

    if all_articles:
        with open(output_path, "w", encoding="utf-8") as f:
            for article in all_articles:
                f.write(f"URL: {article['URL']}\n")
                f.write(f"Content: {article['Content']}\n\n")
        logs.append(f"[{datetime.now()}] Scraping completed. Total articles: {len(all_articles)}. Output saved to {filename}")
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("No articles found.")
        logs.append(f"[{datetime.now()}] No articles found from the selected RSS sources.")

    return "\n".join(logs), output_path

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