from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import tempfile, os
import datetime
import time
import traceback
import json
import os
import requests
import pandas as pd
from datetime import datetime
import csv

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

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    
    # 定義可接受的關鍵字
    valid_keywords = ["實習", "說明會", "徵才", "活動", "工讀", "獎學金"]
    
    if user_message in valid_keywords:
        # 讀取 CSV 檔案
        with open('data.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # 篩選出符合使用者訊息的資料
            filtered_data = [row for row in reader if user_message in row['category']]
        
        if filtered_data:
            reply_message = "\n".join([f"Title: {data['title']}\nLink: {data['link']}" for data in filtered_data])
        else:
            reply_message = f"抱歉，找不到符合「{user_message}」的資料。"
    else:
        reply_message = "請輸入有效的關鍵字：實習、說明會、徵才、活動、工讀、獎學金。"
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
if __name__ == "__main__":
    app.run()
