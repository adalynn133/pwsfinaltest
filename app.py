from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import csv
import os
import pandas as pd
import json

import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

import requests
from bs4 import BeautifulSoup
import pandas as pd

#引路人計畫
# Set the file name
filename = "data2.csv"

def clean_empty_rows(data):
    """
    Clean the empty row if it exists
    """
    return data.dropna(how='all')

# Try to load the existing data, if not, create new lists
try:
    existing_data = pd.read_csv(filename)
    existing_data = clean_empty_rows(existing_data)
    existing_links = existing_data['Link'].tolist()
    links = existing_links.copy()
    titles = existing_data['Title'].tolist()
    categories = existing_data['Category'].tolist()
    dates = existing_data['Release Date'].tolist()
    is_new = [False] * len(titles)
except FileNotFoundError:
    links = []
    titles = []
    categories = []
    dates = []
    is_new = []

# Function to scrape a category
def scrape_category(url, category_name):
    global links, titles, categories, dates, is_new

    while True:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        announcement_items = soup.find_all("li", class_="list-item")

        # Get the information of each announcement
        for item in announcement_items:
            # Get title, use title to see if it already exists
            title = item.find("div", class_="list-title").text.strip()
            if title in titles:
                continue
            else:
                is_new.append(True)
                titles.append(title)

                # Get date
                date = item.find("span", class_="start").text.strip()
                month = item.find("span", class_="month").text.strip()
                # Convert month to number
                month_dict = {
                    "January": '01', "February": '02', "March": '03', "April": '04',
                    "May": '05', "June": '06', "July": '07', "August": '08', 
                    "September": '09', "October": '10', "November": '11', "December": '12'
                }
                month = month_dict.get(month, '00')
                year = item.find("span", class_="year").text.strip()
                dates.append(f"{year}-{month}-{date}")

                # Get category
                categories.append(category_name)

                # Get link
                a_tag = item.find('a', class_='announcement-link')
                if a_tag and 'href' in a_tag.attrs:
                    link = a_tag['href']
                    links.append(f'https://ntucace.ntu.edu.tw{link}')

        # Locate the span element that contains '»'
        next_page_element = soup.find('span', {'aria-hidden': 'true'}, text='»')
        if next_page_element:
            parent_anchor = next_page_element.find_parent('a')
            next_page_link = parent_anchor['href']
            if next_page_link == 'javascript:;'or next_page_link == '/bulletin/index/category_key/7/page/0'or next_page_link == '/bulletin/index/category_key/11/page/0'or next_page_link == '/bulletin/index/category_key/13/page/0'or next_page_link == '/bulletin/index/category_key/14/page/0':
                break  # End of pagination
            url = f'https://ntucace.ntu.edu.tw{next_page_link}'
        else:
            break  # No more pages

# Scrape each category
categories_urls = {
    '實習': 'https://ntucace.ntu.edu.tw/bulletin/index/category_key/7',
    '活動': [
        'https://ntucace.ntu.edu.tw/bulletin/index/category_key/13',
        'https://ntucace.ntu.edu.tw/bulletin/index/category_key/11'
    ],
    '說明會': 'https://ntucace.ntu.edu.tw/bulletin/index/category_key/14'
}

# Scrape all categories
for category, urls in categories_urls.items():
    if isinstance(urls, list):
        for url in urls:
            scrape_category(url, category)
    else:
        scrape_category(urls, category)

# Combine the data
final_data = pd.DataFrame({
    'Link': links,
    'Title': titles,
    'Category': categories,
    'Release Date': dates,
    'is_new': is_new
})

# Write data to CSV file
final_data.to_csv(filename, index=False, encoding='utf-8-sig')


#學生職涯中心
# Set the file name
filename = "data.csv"

def clean_empty_rows(data): # Clean the empty row if it exists
    return data.dropna(how='all')

# Try to load the data in
#if not, create a new list (will occur at the very first try)
try:
    existing_data = pd.read_csv(filename)
    existing_data = clean_empty_rows(existing_data)
    existing_links = existing_data['Link'].tolist()
    links = existing_links.copy()
    titles = existing_data['Title'].tolist()
    categories = existing_data['Category'].tolist()
    dates = existing_data['Release Date'].tolist()
    is_new = [False] * len(links)
except FileNotFoundError:
    links = []
    titles = []
    categories = []
    dates = []
    is_new = []

base_url = 'https://career.ntu.edu.tw/board/index/tab/0'
page_wanted = 5

# Loop through each page
for i in range(page_wanted):
    try:
        # Make a request
        url = f'{base_url}/page/{i+1}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all target items we want
        announcement_items = soup.find_all('li', class_='announcement-item')
        
        if not announcement_items:
            break  # Stop the loop if no more items are found
    
        # Iterate over each announcement item
        for item in announcement_items:
            # Find the <a> tag within the <h5> tag
            h5_tag = item.find('h5')
            link = h5_tag.find('a')['href'] if h5_tag else None
            if link:
                if link in links:
                    # If the link already exists, just continue
                    continue
                else:
                    # Append new data 
                    links.append(link)
                
                    # Make a request to the detail page
                    detail_response = requests.get(link)
                    detail_soup = BeautifulSoup(detail_response.text, "html.parser")
                 
                    # Get the title
                    detail_title = detail_soup.title.string if detail_soup.title else 'No title found'
                    detail_title = detail_title.split(' ')
                    titles.append(' '.join(map(str, detail_title[4:])))
                
                    # Get the content 
                    detail_content = detail_soup.get_text(separator="\n", strip=True)
                
                    # Get category
                    tags_wrap = item.find('div', class_='tags-wrap')
                    category_link = tags_wrap.find('a') if tags_wrap else None
                    if category_link:
                        category = category_link.get_text()
                        categories.append(category)
                    else:
                        categories.append('')  # No category found
            
                    # Get release date
                    date_span = item.find('span', class_='date')
                    if date_span:
                        date = date_span.get_text(strip=True)
                        dates.append(date)
                    else:
                        dates.append('')  # No date found
                
                    # Mark this item as new
                    is_new.append(True)


    except Exception as e:
        print(f"An error occurred: {e}")
        break

# Combine the data
final_data = pd.DataFrame({
    'Link': links,
    'Title': titles,
    'Category': categories,
    'Release Date': dates,
    'is_new': is_new
})

# Write data to CSV file
final_data.to_csv(filename, index=False, encoding='utf-8-sig')

print("CSV file saved as:", filename)


#轉換到line聊天室
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
    # 讀取兩個 CSV 檔案並轉換成 pandas DataFrame
    df1 = pd.read_csv('data.csv')
    df2 = pd.read_csv('data2.csv')
    # 合併兩個 DataFrame
    combined_df = pd.concat([df1, df2])
    # 篩選出符合使用者輸入文字的列
    filtered_df = combined_df[combined_df['Category'].str.contains(user_input, na=False)]
    if not filtered_df.empty:
        # 將符合條件的列的 Title 和 link 欄位組合成文字訊息，並加上數字編號
        reply_message = "\n".join([f"{idx+1}. {row.Title}\n {row.Link}\n" for idx, row in enumerate(filtered_df.itertuples())])
    else:
        reply_message = f"抱歉，找不到符合「{user_input}」的資料。"
    # 傳送回覆訊息到 Line
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))


if __name__ == "__main__":
    app.run()
