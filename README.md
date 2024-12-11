---
title: Crawler Rss
emoji: 💻
colorFrom: gray
colorTo: gray
sdk: gradio
sdk_version: 5.8.0
app_file: app.py
pinned: false
short_description: 爬蟲  crawler 針對各大財經新聞網站
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference


---

# RSS 新聞爬蟲工具

這是一個基於 Python 開發的 RSS 新聞爬蟲工具，可以從多個新聞來源抓取文章內容。

## 功能特點

- 支援多個預設新聞來源（BBC、Bloomberg、WSJ 等）
- 可自訂添加 RSS 來源
- 自動清理超過一小時的暫存檔案
- 使用 Gradio 建立友善的使用者介面
- 輸出整理後的文字檔案

## 安裝需求

```bash
pip install gradio requests beautifulsoup4
```

## 使用方式

1. 執行程式後，選擇想要的新聞來源
2. 可選擇性地添加自訂 RSS URL
3. 點擊 "Scrape" 開始爬取
4. 等待程式執行完成後下載結果檔案

---

# RSS News Crawler

A Python-based RSS news crawler that fetches article content from multiple news sources.

## Features

- Support for multiple default news sources (BBC, Bloomberg, WSJ, etc.)
- Custom RSS feed URL input
- Automatic cleanup of temporary files older than one hour
- User-friendly interface built with Gradio
- Organized text file output

## Requirements

```bash
pip install gradio requests beautifulsoup4
```

## How to Use

1. Run the program and select desired news sources
2. Optionally add custom RSS URL
3. Click "Scrape" to start crawling
4. Download the result file after completion

## Default News Sources
- BBC Business
- Bloomberg Technology
- WSJ World News
- WSJ US Business
- WSJ Markets
- WSJ Technology

## Author
- tbdavid2019
- https://github.com/tbdavid2019/crawler-rss
