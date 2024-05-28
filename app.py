from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import csv
import os

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
    # 打開 CSV 檔案並進行資料篩選
    with open('data.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        # 篩選出包含使用者輸入文字的列
        filtered_rows = [row for row in reader if user_input in row['category']]
    if filtered_rows:
        # 將篩選出的資料以文字訊息的形式組合
        reply_message = "\n".join([f"{row['category']}: {row['title']}" for row in filtered_rows])
    else:
        reply_message = f"抱歉，找不到符合「{user_input}」的資料。"
    # 傳送回覆訊息到 Line
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

if __name__ == "__main__":
    app.run()
