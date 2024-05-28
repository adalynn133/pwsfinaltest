from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import csv

app = Flask(__name__)

# 設置 Line Bot 的 Channel access token 和 Channel secret
line_bot_api = LineBotApi('CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('CHANNEL_SECRET')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    keywords = ['實習', '說明會', '徵才', '活動', '工讀', '獎學金']
    
    if user_message not in keywords:
        reply_message = "請輸入以下任一關鍵字：實習/說明會/徵才/活動/工讀/獎學金"
    else:
        filtered_data = []
        with open('your_data.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            filtered_data = [row for row in reader if user_message in row['category']]

        if filtered_data:
            reply_message = "\n\n".join(
                [f"Title: {data['Title']}\nLink: {data['link']}" for data in filtered_data]
            )
        else:
            reply_message = f"抱歉，找不到符合「{user_message}」的資料。"
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

if __name__ == "__main__":
    app.run()
