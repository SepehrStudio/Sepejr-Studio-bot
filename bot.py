import os
import time
import requests

TOKEN = os.getenv("RUBIKA_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("RUBIKA_BOT_TOKEN is not configured.")

API = f"https://botapi.rubika.ir/v3/{TOKEN}"

session = requests.Session()

# وضعیت ثبت سفارش کاربران
users = {}


# =========================
# API
# =========================

def call_api(method, payload=None):
    try:
        response = session.post(
            f"{API}/{method}",
            json=payload or {},
            timeout=30
        )

        print(
            f"[API] {method} -> HTTP {response.status_code}",
            flush=True
        )

        result = response.json()

        if result.get("status") != "OK":
            print(
                f"[API ERROR] {result}",
                flush=True
            )

        return result

    except Exception as error:
        print(
            f"[NETWORK ERROR] {error}",
            flush=True
        )
        return {}


# =========================
# KEYBOARD
# =========================

def button(button_id, text):
    return {
        "id": button_id,
        "type": "Simple",
        "button_text": text
    }


def main_keyboard():
    return {
        "rows": [
            {
                "buttons": [
                    button(
                        "services",
                        "💻 خدمات Sepehr Studio"
                    )
                ]
            },
            {
                "buttons": [
                    button(
                        "order",
                        "📋 ثبت سفارش"
                    ),
                    button(
                        "contact",
                        "👨‍💻 ارتباط با ما"
                    )
                ]
            },
            {
                "buttons": [
                    button(
                        "about",
                        "ℹ️ درباره ما"
                    )
                ]
            }
        ]
    }


def services_keyboard():
    return {
        "rows": [
            {
                "buttons": [
                    button("website", "🌐 طراحی سایت"),
                    button("app", "📱 ساخت اپ")
                ]
            },
            {
                "buttons": [
                    button("ai", "🤖 هوش مصنوعی"),
                    button("coding", "💻 برنامه‌نویسی")
                ]
            },
            {
                "buttons": [
                    button("back", "🔙 بازگشت")
                ]
            }
        ]
    }


# =========================
# SEND MESSAGE
# =========================

def send_message(chat_id, text, keypad=None):

    payload = {
        "chat_id": str(chat_id),
        "text": str(text)
    }

    if keypad:
        payload["inline_keypad"] = keypad

    return call_api(
        "sendMessage",
        payload
    )


# =========================
# ORDER
# =========================

def start_order(chat_id):

    users[str(chat_id)] = {
        "step": "name",
        "order": {}
    }

    send_message(
        chat_id,
        "📋 ثبت سفارش جدید\n\n"
        "مرحله ۱ از ۴\n\n"
        "👤 نام خود را ارسال کنید.\n\n"
        "برای لغو بنویسید: لغو"
    )


def process_order(chat_id, text):

    uid = str(chat_id)

    if uid not in users:
        return False

    if text == "لغو":

        del users[uid]

        send_message(
            chat_id,
            "❌ ثبت سفارش لغو شد.",
            main_keyboard()
        )

        return True

    state = users[uid]

    # نام
    if state["step"] == "name":

        state["order"]["name"] = text
        state["step"] = "type"

        send_message(
            chat_id,
            "✅ نام دریافت شد.\n\n"
            "مرحله ۲ از ۴\n\n"
            "💻 نوع پروژه را بنویسید.\n\n"
            "مثلاً:\n"
            "طراحی سایت\n"
            "ساخت اپ\n"
            "هوش مصنوعی\n"
            "برنامه‌نویسی"
        )

        return True

    # نوع پروژه
    if state["step"] == "type":

        state["order"]["type"] = text
        state["step"] = "description"

        send_message(
            chat_id,
            "✅ نوع پروژه دریافت شد.\n\n"
            "مرحله ۳ از ۴\n\n"
            "📝 توضیحات پروژه را ارسال کنید."
        )

        return True

    # توضیحات
    if state["step"] == "description":

        state["order"]["description"] = text
        state["step"] = "budget"

        send_message(
            chat_id,
            "✅ توضیحات دریافت شد.\n\n"
            "مرحله ۴ از ۴\n\n"
            "💰 بودجه تقریبی پروژه را ارسال کنید."
        )

        return True

    # بودجه
    if state["step"] == "budget":

        state["order"]["budget"] = text

        order = state["order"]

        del users[uid]

        send_message(
            chat_id,
            "🎉 سفارش شما ثبت شد!\n\n"
            f"👤 نام: {order['name']}\n"
            f"💻 نوع پروژه: {order['type']}\n"
            f"💰 بودجه: {order['budget']}\n\n"
            "📌 توضیحات:\n"
            f"{order['description']}\n\n"
            "به‌زودی سفارش شما بررسی می‌شود. 🚀",
            main_keyboard()
        )

        return True

    return False


# =========================
# UPDATE
# =========================

def process_update(update):

    if not isinstance(update, dict):
        return

    chat_id = update.get("chat_id")
    message = update.get("new_message")

    if not chat_id:
        return

    if not isinstance(message, dict):
        return

    text = message.get("text") or ""
    text = text.strip()

    aux_data = message.get("aux_data") or {}

    button_id = aux_data.get("button_id")

    command = button_id or text

    print(
        f"[MESSAGE] chat={chat_id} "
        f"text={text!r} "
        f"button={button_id!r}",
        flush=True
    )

    # در حال ثبت سفارش
    if str(chat_id) in users:

        if process_order(chat_id, text):
            return

    # شروع
    if command in (
        "/start",
        "start",
        "شروع"
    ):

        send_message(
            chat_id,
            "🚀 به Sepehr Studio خوش آمدید!\n\n"
            "یکی از گزینه‌های زیر را انتخاب کنید:",
            main_keyboard()
        )

    elif command == "services":

        send_message(
            chat_id,
            "💻 خدمات Sepehr Studio:",
            services_keyboard()
        )

    elif command == "order":

        start_order(chat_id)

    elif command == "website":

        send_message(
            chat_id,
            "🌐 طراحی سایت\n\n"
            "طراحی سایت‌های مدرن و واکنش‌گرا.",
            main_keyboard()
        )

    elif command == "app":

        send_message(
            chat_id,
            "📱 ساخت اپلیکیشن\n\n"
            "ساخت اپلیکیشن و رابط کاربری.",
            main_keyboard()
        )

    elif command == "ai":

        send_message(
            chat_id,
            "🤖 پروژه‌های هوش مصنوعی\n\n"
            "طراحی پروژه‌های مبتنی بر هوش مصنوعی.",
            main_keyboard()
        )

    elif command == "coding":

        send_message(
            chat_id,
            "💻 برنامه‌نویسی\n\n"
            "توسعه پروژه‌های وب و نرم‌افزاری.",
            main_keyboard()
        )

    elif command == "contact":

        send_message(
            chat_id,
            "👨‍💻 ارتباط با Sepehr Studio\n\n"
            "پیام خود را ارسال کنید.",
            main_keyboard()
        )

    elif command == "about":

        send_message(
            chat_id,
            "🚀 Sepehr Studio\n\n"
            "توسعه پروژه‌های برنامه‌نویسی، طراحی سایت و هوش مصنوعی.",
            main_keyboard()
        )

    elif command == "back":

        send_message(
            chat_id,
            "🏠 منوی اصلی:",
            main_keyboard()
        )

    elif command == "/test":

        send_message(
            chat_id,
            "✅ بات Sepehr Studio فعال است!",
            main_keyboard()
        )


# =========================
# MAIN LOOP
# =========================

def run():

    print(
        "🚀 Sepehr Studio Bot started!",
        flush=True
    )

    offset_id = None

    while True:

        try:

            payload = {
                "limit": 10
            }

            if offset_id:
                payload["offset_id"] = offset_id

            result = call_api(
                "getUpdates",
                payload
            )

            data = result.get(
                "data",
                {}
            )

            if not isinstance(data, dict):
                data = {}

            updates = data.get(
                "updates",
                []
            )

            print(
                f"[UPDATES] {len(updates)} update(s)",
                flush=True
            )

            for update in updates:
                process_update(update)

            next_offset_id = data.get(
                "next_offset_id"
            )

            if next_offset_id:
                offset_id = str(
                    next_offset_id
                )

        except Exception as error:

            print(
                f"[BOT ERROR] {error}",
                flush=True
            )

        time.sleep(2)


if __name__ == "__main__":
    run()
