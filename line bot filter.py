from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import csv

app = Flask(__name__)

# 設置 Line Bot 的 Channel access token 和 Channel secret
line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_CHANNEL_SECRET')

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

if __name__ == "__main__":
    app.run()
