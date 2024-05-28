from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import csv
import os
import pandas as pd

import requests
from bs4 import BeautifulSoup
import re
import pandas as pd


# set the file name
filename = "data.csv"

def clean_empty_rows(data):
    """
    clean the empty row if it exists
    """
    return data.dropna(how='all')

# try to lead the data in, if not, create a new list (will occur at the very first try)
try:
    existing_data = pd.read_csv(filename)
    existing_data = clean_empty_rows(existing_data)
    existing_links = existing_data['Link'].tolist()
    links = existing_links.copy()
    titles = existing_data['Title'].tolist()
    categories = existing_data['Category'].tolist()
    dates = existing_data['Release Date'].tolist()
    date_related_infos = existing_data['Date-Related Info'].tolist()
    is_new = existing_data['is_new'].tolist()
except FileNotFoundError:
    links = []
    titles = []
    categories = []
    dates = []
    date_related_infos = []
    is_new = []

# make a request 
response = requests.get('https://career.ntu.edu.tw/board/index/tab/0')
soup = BeautifulSoup(response.text, "html.parser")

# find all target we want
announcement_items = soup.find_all('li', class_='announcement-item')

# try to define the date-related keywords (although it often doesn't work QQ)
date_keywords = ["期間", "日期", "時間", "截止", "面試", "錄取", "日"]
date_pattern = re.compile(
    r'\b(?:\d{4}/\d{1,2}/\d{1,2}|(?:\d{1,2}|[一二三四五六日])/(?:\d{1,2}|[一二三四五六日]))'
    r'\s*[-~至到➨]?\s*'
    r'(?:\d{4}/\d{1,2}/\d{1,2}|(?:\d{1,2}|[一二三四五六日])/(?:\d{1,2}|[一二三四五六日]))'
    r'\s*.*?(?:[，,.\n])' 
)

# iteration 
for item in announcement_items:
    # Find the <a> tag within the <h5> tag
    h5_tag = item.find('h5')
    link = h5_tag.find('a')['href'] if h5_tag else None
    if link:
        if link in links:
            # if the link already exists, just change the is_new to False and not scraping any othet thing
            idx = existing_links.index(link)
            is_new[idx] = False
        else:
            # append new data 
            links.append(link)
            
            # make a request to the detail page
            detail_response = requests.get(link)
            detail_soup = BeautifulSoup(detail_response.text, "html.parser")
            
            # get the title
            detail_title = detail_soup.title.string if detail_soup.title else 'No title found'
            detail_title = detail_title.split(' ')
            titles.append(' '.join(map(str, detail_title[4:])))
            
            # get the content 
            detail_content = detail_soup.get_text(separator="\n", strip=True)
            
            # try to find the  date-related information
            lines = detail_content.split('\n')
            date_info = ""
            for line in lines:
                if any(keyword in line for keyword in date_keywords) or date_pattern.search(line):
                    matches = date_pattern.findall(line)
                    for match in matches:
                        date_info += match.strip() + " "  
            date_related_infos.append(date_info)
        
            # get category
            tags_wrap = item.find('div', class_='tags-wrap')
            category_link = tags_wrap.find('a') if tags_wrap else None
            if category_link:
                category = category_link.get_text()
                categories.append(category)
            else:
                categories.append('')  #  no category found
        
            # get release date
            date_span = item.find('span', class_='date')
            if date_span:
                date = date_span.get_text(strip=True)
                dates.append(date)
            else:
                dates.append('')  #no date found
            
            # Mark this item as new
            is_new.append(True)

# Combine the data 
final_data = pd.DataFrame({
    'Link': links,
    'Title': titles,
    'Category': categories,
    'Release Date': dates,
    'Date-Related Info': date_related_infos,
    'is_new': is_new
})

# Write data to CSV file
final_data.to_csv(filename, index=False, encoding='utf-8-sig')

print("CSV file saved as:", filename)







app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text.strip()
    # 讀取 CSV 檔案並轉換成 pandas DataFrame
    df = pd.read_csv('data.csv')
    # 篩選出符合使用者輸入文字的列
    filtered_df = df[df['Category'].str.contains(user_input)]
    if not filtered_df.empty:
        # 將符合條件的列的 Title 和 link 欄位組合成文字訊息
        reply_message = "\n".join([f"{row['Title']}\n{row['Link']}\n" for _, row in filtered_df.iterrows()])
    else:
        reply_message = f"抱歉，找不到符合「{user_input}」的資料。"
    # 傳送回覆訊息到 Line
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

if __name__ == "__main__":
    app.run()
