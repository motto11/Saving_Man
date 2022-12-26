import os
import sys

from flask import Flask, jsonify, request, abort, send_file
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from fsm import TocMachine
from utils import send_text_message, send_image_message

load_dotenv()


machine = TocMachine(
    states=
    [
        "name",
        "value",
        "time",
        "delete_by_id",
        "update_by_id",
        "create_finish",
        "read_finish",
        "delete_finish",
        "update_finish",
    ],
    transitions=[
        {"trigger": "advance","source": "user","dest": "name","conditions": "is_going_to_name",},
        {"trigger": "advance","source": "user","dest": "read_finish","conditions": "is_going_to_read_finish",},
        {"trigger": "advance","source": "user","dest": "delete_by_id","conditions": "is_going_to_delete_by_id",},
        {"trigger": "advance","source": "user","dest": "update_by_id","conditions": "is_going_to_update_by_id",},
        {"trigger": "advance","source": "name","dest": "value","conditions": "is_going_to_value",},
        {"trigger": "advance","source": "value","dest": "time","conditions": "is_going_to_time",},
        {"trigger": "advance","source": "update_by_id","dest": "name","conditions": "is_going_to_name",},
        {"trigger": "advance","source": "time","dest": "create_finish","conditions": "is_going_to_create_finish",},
        {"trigger": "advance","source": "delete_by_id","dest": "delete_finish","conditions": "is_going_to_delete_finish",},
        {"trigger": "advance","source": "time","dest": "update_finish","conditions": "is_going_to_update_finish",},
        {
            "trigger": "go_back",
            "source": [
                "name",
                "value",
                "time",
                "delete_by_id",
                "update_by_id",
                "create_finish",
                "read_finish",
                "delete_finish",
                "update_finish",
            ],
            "dest": "user"
        },
    ],
    initial="user",
    auto_transitions=False,
    show_conditions=True,
)

app = Flask(__name__, static_url_path="")


# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.message.text)
        )

    return "OK"


@app.route("/webhook", methods=["POST"])
def webhook_handler():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue
        if not isinstance(event.message.text, str):
            continue
        print(f"\nFSM STATE: {machine.state}")
        print(f"REQUEST BODY: \n{body}")
        if(event.message.text.lower() == "!restart"):
            machine.go_back()
            send_text_message(event.reply_token, "請輸入以下指令開始操作\ncreate: 記錄一個新的記帳項目\nread: 印出所有記帳項目\ndelete: 刪除一個記帳項目\nupdate: 更改一個記帳項目的內容\n!restart: 重新開始\nfsm: 顯示fsm圖")
            continue
        if event.message.text.lower() == 'fsm':
            send_image_message(event.reply_token, 'https://dbf2-140-116-113-102.jp.ngrok.io/show-fsm')
            continue
        response = machine.advance(event)
        if response == False:
            if machine.state == "user":
                send_text_message(event.reply_token, "請輸入以下指令開始操作\ncreate: 記錄一個新的記帳項目\nread: 印出所有記帳項目\ndelete: 刪除一個記帳項目\nupdate: 更改一個記帳項目的內容\n!restart: 重新開始\nfsm: 顯示fsm圖")
            elif machine.state == "name":
                send_text_message(event.reply_token, "名稱格式錯誤，請重新輸入")
            elif machine.state == "value":
                send_text_message(event.reply_token, "金額格式錯誤，請重新輸入")
            elif machine.state == "time":
                send_text_message(event.reply_token, "日期格式錯誤，請重新輸入")
            elif machine.state == "delete_by_id":
                send_text_message(event.reply_token, "輸入的ID不存在，請重新輸入")
            elif machine.state == "update_by_id":
                send_text_message(event.reply_token, "輸入的ID不存在，請重新輸入")
            else:
                send_text_message(event.reply_token, "Not Entering any State")
        elif machine.state == "create_finish" or machine.state == "read_finish" or machine.state == "delete_finish" or machine.state == "update_finish":
            machine.go_back()

    return "OK"


@app.route("/show-fsm", methods=["GET"])
def show_fsm():
    machine.get_graph().draw("fsm.png", prog="dot", format="png")
    return send_file("fsm.png", mimetype="image/png")


if __name__ == "__main__":
    port = os.environ.get("PORT", 8000)
    app.run(host="0.0.0.0", port=port, debug=True)
