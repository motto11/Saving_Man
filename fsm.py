from transitions.extensions import GraphMachine

from utils import send_text_message

from item import item

from linebot.models import MessageTemplateAction

buffer_name = ""
buffer_value = 0
buffer_year = 0
buffer_month = 0
buffer_day = 0
update_id = 0
max_id = 0
item_list = [] 

mode = 0

class TocMachine(GraphMachine):
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(model=self, **machine_configs)

    def is_going_to_name(self, event):
        text = event.message.text
        global mode
        if text.lower() == "create" and mode == 0:
            return True
        elif mode == 1:
            global update_id
            update_id = int(text)
            for i in item_list:
                if i.id == update_id:
                    return True
            return False
        else:
            return False

    def is_going_to_read_finish(self, event):
        text = event.message.text
        return text.lower() == "read"

    def is_going_to_delete(self, event):
        text = event.message.text
        return text.lower() == "delete"

    def is_going_to_update(self, event):
        text = event.message.text
        return text.lower() == "update"

    def is_going_to_value(self, event):
        global buffer_name
        text = event.message.text
        buffer_name = text
        return text != ""

    def is_going_to_time(self, event):
        text = event.message.text
        try:
            global buffer_value
            buffer_value = int(text)
            return True
        except ValueError:
            return False

    def is_going_to_create_finish(self, event):
        text = event.message.text
        global mode
        if mode == 1:
            return False
        if len(text) != 10:
            return False
        try:
            words = text.split("-")
            global buffer_year
            global buffer_month
            global buffer_day
            buffer_year = int(words[0])
            buffer_month = int(words[1])
            buffer_day = int(words[2])
            if buffer_month > 12 or buffer_month < 1:
                return False
            if buffer_day > 31 or buffer_day < 1:
                return False
            if buffer_year < 0:
                return False
            return True
        except ValueError:
            return False
    
    def is_going_to_read_finish(self, event):
        text = event.message.text
        return text.lower() == "read"

        #if text == "本月":
        #    read_mode = 0
        #    return True
        #elif text == "今年":
        #    read_mode = 1
        #    return True
        #elif text == "全部":
        #    read_mode = 2
        #    return True
        #else:
        #    return False

    def is_going_to_delete_by_id(self, event):
        text = event.message.text
        return text.lower() == "delete"

    def is_going_to_delete_finish(self, event):
        text = event.message.text
        try:
            id = int(text)
            for i in item_list:
                if i.id == id:
                    item_list.remove(i)
                    return True
            return False
        except ValueError:
            return False

    def is_going_to_update_by_id(self, event):
        text = event.message.text
        return text.lower() == "update"

    def is_going_to_update_finish(self, event):
        text = event.message.text
        global mode
        if mode == 0:
            return False
        if len(text) != 10:
            return False
        try:
            words = text.split("-")
            global buffer_year
            global buffer_month
            global buffer_day
            buffer_year = int(words[0])
            buffer_month = int(words[1])
            buffer_day = int(words[2])
            if buffer_month > 12 or buffer_month < 1:
                return False
            if buffer_day > 31 or buffer_day < 1:
                return False
            if buffer_year < 0:
                return False
            return True
        except ValueError:
            return False

    def on_enter_name(self, event):
        print("I'm entering state name")

        reply_token = event.reply_token
        send_text_message(reply_token, "請輸入記帳項目名稱")

    def on_enter_value(self, event):
        print("I'm entering state value")

        reply_token = event.reply_token
        send_text_message(reply_token, "請輸入記帳項目金額")

    def on_enter_time(self, event):
        print("I'm entering state time")

        reply_token = event.reply_token
        send_text_message(reply_token, "請輸入記帳項目時間(YYYY-MM-DD)")

    def on_enter_create_finish(self, event):
        print("I'm entering state create_finish")
        global max_id
        item_list.append(item(max_id, buffer_name, buffer_value, buffer_year, buffer_month, buffer_day))

        reply_token = event.reply_token
        send_text_message(reply_token, "記帳成功，本次記帳編號為" + str(max_id))
        max_id += 1

    def on_enter_time_range(self, event):
        print("I'm entering state time_range")

        reply_token = event.reply_token
        send_text_message(reply_token, "請選擇時間範圍(本月、今年、全部)")

    def on_enter_read_finish(self, event):
        print("I'm entering state read_finish")

        reply_token = event.reply_token

        text = ""
        for i in item_list:
            text += str(i.id) + ". " + str(i.name) + "\n金額: " + str(i.value) + "元\n日期" + str(i.year) + "-" + str(i.month) + "-" + str(i.day) + "\n\n"
        if text == "":
            send_text_message(reply_token, "無記帳紀錄")
            return
        
        send_text_message(reply_token, text)
        
    def on_enter_delete_by_id(self, event):
        print("I'm entering state delete_by_id")

        reply_token = event.reply_token
        send_text_message(reply_token, "請輸入要刪除的記帳編號")

    def on_enter_delete_finish(self, event):
        print("I'm entering state delete_finish")

        reply_token = event.reply_token
        send_text_message(reply_token, "刪除成功")

    def on_enter_update_by_id(self, event):
        print("I'm entering state update_by_id")
        global mode
        mode = 1
        reply_token = event.reply_token
        send_text_message(reply_token, "請輸入要修改的記帳編號")

    def on_enter_update_finish(self, event):
        print("I'm entering state update_finish")
        global mode
        mode = 0
        global update_id
        reply_token = event.reply_token
        for i in item_list:
            if i.id == update_id:
                i.name = buffer_name
                i.value = buffer_value
                i.year = buffer_year
                i.month = buffer_month
                i.day = buffer_day
                break

        send_text_message(reply_token, "修改成功")

    def on_enter_user(self):
        global mode
        print("I'm entering state user")
        mode = 0
        