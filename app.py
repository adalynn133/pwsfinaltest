from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import tempfile, os
import datetime
import googlemaps
import time
import traceback
import json
import os
import requests
import pandas as pd
from datetime import datetime

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
    user_input = event.message.text.strip()
    user_request = user_input.split(' ', 1)
    
    if len(user_request) < 2:
        reply_message = "請輸入有效的格式，例如：「1 實習」"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
        return
    
    category = user_request[1]
    
    # 讀取 CSV 檔案
    with open('your_data.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        # 篩選出符合使用者輸入的資料
        filtered_data = [row for row in reader if category in row['category']]
    
    if filtered_data:
        reply_message = "\n".join([f"{data['title']}: {data['description']}" for data in filtered_data])
    else:
        reply_message = f"抱歉，找不到符合「{category}」的資料。"
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
if __name__ == "__main__":
    app.run()
