from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import csv
import os
import pandas as pd

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
    filtered_df = df[df['category'].str.contains(user_input)]
    if not filtered_df.empty:
        # 將符合條件的列的 Title 和 link 欄位組合成文字訊息
        reply_message = "\n".join([f"Title: {row['Title']}\nLink: {row['link']}" for _, row in filtered_df.iterrows()])
    else:
        reply_message = f"抱歉，找不到符合「{user_input}」的資料。"
    # 傳送回覆訊息到 Line
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

if __name__ == "__main__":
    app.run()
