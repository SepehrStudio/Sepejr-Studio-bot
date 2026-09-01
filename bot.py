import os
import time
import requests

TOKEN = os.environ["RUBIKA_BOT_TOKEN"]
BASE = f"https://botapi.rubika.ir/v3/{TOKEN}"

def api(method, data=None):
    try:
        r = requests.post(f"{BASE}/{method}", json=data or {}, timeout=30)
        return r.json()
    except Exception as e:
        print("API ERROR:", e)
        return {}

def send_message(chat_id, text, keyboard=None):
    data = {"chat_id": chat_id, "text": text}
    if keyboard:
        data["inline_keypad"] = keyboard
    return api("sendMessage", data)

def main_menu():
    return {"rows": [
        {"buttons": [{"id": "services", "text": "💻 خدمات Sepehr Studio"}]},
        {"buttons": [
            {"id": "order", "text": "📋 ثبت سفارش"},
            {"id": "contact", "text": "👨‍💻 ارتباط با ما"}
        ]},
        {"buttons": [{"id": "about", "text": "ℹ️ درباره Sepehr Studio"}]}
    ]}

def services_menu():
    return {"rows": [
        {"buttons": [
            {"id": "website", "text": "🌐 طراحی سایت"},
            {"id": "app", "text": "📱 ساخت اپ"}
        ]},
        {"buttons": [
            {"id": "ai", "text": "🤖 پروژه هوش مصنوعی"},
            {"id": "coding", "text": "💻 برنامه‌نویسی"}
        ]},
        {"buttons": [{"id": "back", "text": "🔙 بازگشت"}]}
    ]}

def handle_message(message):
    chat_id = message.get("chat_id")
    text = message.get("text", "").strip()
    if not chat_id:
        return

    if text in ["/start", "شروع", "start"]:
        send_message(chat_id, "🚀 به Sepehr Studio خوش آمدید!\n\nخدمات و امکانات موردنظر خود را انتخاب کنید:", main_menu())
    elif text == "services":
        send_message(chat_id, "💻 خدمات Sepehr Studio:", services_menu())
    elif text == "website":
        send_message(chat_id, "🌐 طراحی سایت\n\nطراحی سایت‌های مدرن و واکنش‌گرا با HTML/CSS/JS.", main_menu())
    elif text == "app":
        send_message(chat_id, "📱 ساخت اپلیکیشن\n\nساخت رابط کاربری و اپلیکیشن‌های مختلف.", main_menu())
    elif text == "ai":
        send_message(chat_id, "🤖 پروژه‌های هوش مصنوعی\n\nطراحی رابط کاربری و پروژه‌های مبتنی بر هوش مصنوعی.", main_menu())
    elif text == "coding":
        send_message(chat_id, "💻 برنامه‌نویسی\n\nتوسعه پروژه‌های وب، ابزارها و سیستم‌های سفارشی.", main_menu())
    elif text == "order":
        send_message(chat_id, "📋 برای ثبت سفارش، لطفاً این اطلاعات را ارسال کنید:\n\n1️⃣ نام\n2️⃣ نوع پروژه\n3️⃣ توضیح پروژه\n4️⃣ بودجه تقریبی\n\nپس از دریافت اطلاعات، سفارش بررسی می‌شود.", main_menu())
    elif text == "contact":
        send_message(chat_id, "👨‍💻 ارتباط با Sepehr Studio\n\nبرای ارتباط و پیگیری سفارش، پیام خود را ارسال کنید.", main_menu())
    elif text == "about":
        send_message(chat_id, "🚀 Sepehr Studio\n\nاستودیو پروژه‌های برنامه‌نویسی، طراحی سایت و هوش مصنوعی.", main_menu())
    elif text == "back":
        send_message(chat_id, "🏠 منوی اصلی:", main_menu())

def run():
    print("🚀 Sepehr Studio Bot started!")
    offset = None
    while True:
        try:
            data = {}
            if offset is not None:
                data["offset_id"] = offset
            result = api("getUpdates", data)
            updates = result.get("data", {}).get("updates", [])
            for update in updates:
                offset = update.get("update_id")
                message = update.get("message")
                if message:
                    handle_message(message)
        except Exception as e:
            print("ERROR:", e)
        time.sleep(2)

if __name__ == "__main__":
    run()
