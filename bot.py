import os
import time
import requests

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("RUBIKA_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("RUBIKA_BOT_TOKEN is not configured.")

API = f"https://botapi.rubika.ir/v3/{TOKEN}"

# Chat ID ادمین
ADMIN_CHAT_ID = "b0IGuhX0BBcQ085f392a2b3fce01be44"

session = requests.Session()

users = {}
processed_updates = set()


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

        try:
            result = response.json()
        except Exception:
            print("[API ERROR] Invalid JSON", flush=True)
            return {}

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

def btn(button_id, text):
    return {
        "id": str(button_id),
        "type": "Simple",
        "button_text": str(text)
    }


def make_keyboard(rows):
    return {
        "rows": [
            {
                "buttons": row
            }
            for row in rows
        ]
    }


def main_keyboard():
    return make_keyboard([
        [
            btn("services", "💻 خدمات Sepehr Studio")
        ],
        [
            btn("order", "📋 ثبت سفارش"),
            btn("contact", "👨‍💻 ارتباط با ما")
        ],
        [
            btn("about", "ℹ️ درباره ما")
        ]
    ])


def services_keyboard():
    return make_keyboard([
        [
            btn("website", "🌐 طراحی سایت"),
            btn("app", "📱 ساخت اپ")
        ],
        [
            btn("ai", "🤖 هوش مصنوعی"),
            btn("coding", "💻 برنامه‌نویسی")
        ],
        [
            btn("back", "🔙 بازگشت")
        ]
    ])


# =========================
# SEND MESSAGE
# =========================

def send_message(chat_id, text, keypad=None):

    payload = {
        "chat_id": str(chat_id),
        "text": str(text)
    }

    if keypad is not None:
        payload["inline_keypad"] = keypad

    return call_api(
        "sendMessage",
        payload
    )


# =========================
# ADMIN ORDER
# =========================

def send_order_to_admin(order, customer_chat_id):

    admin_text = (
        "🔔 سفارش جدید Sepehr Studio\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 نام مشتری:\n{order['name']}\n\n"
        f"💻 نوع پروژه:\n{order['type']}\n\n"
        f"📝 توضیحات:\n{order['description']}\n\n"
        f"💰 بودجه:\n{order['budget']}\n\n"
        f"🆔 Chat ID مشتری:\n{customer_chat_id}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📌 وضعیت: سفارش جدید"
    )

    result = send_message(
        ADMIN_CHAT_ID,
        admin_text
    )

    print(
        f"[ADMIN] Order sent -> {result}",
        flush=True
    )


# =========================
# ORDER SYSTEM
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

    # مرحله ۱
    if state["step"] == "name":

        state["order"]["name"] = text
        state["step"] = "type"

        send_message(
            chat_id,
            "✅ نام دریافت شد.\n\n"
            "مرحله ۲ از ۴\n\n"
            "💻 نوع پروژه را ارسال کنید.\n\n"
            "مثلاً:\n"
            "طراحی سایت\n"
            "ساخت اپ\n"
            "هوش مصنوعی\n"
            "برنامه‌نویسی"
        )

        return True

    # مرحله ۲
    if state["step"] == "type":

        state["order"]["type"] = text
        state["step"] = "description"

        send_message(
            chat_id,
            "✅ نوع پروژه دریافت شد.\n\n"
            "مرحله ۳ از ۴\n\n"
            "📝 توضیحات کامل پروژه را ارسال کنید."
        )

        return True

    # مرحله ۳
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

    # مرحله ۴
    if state["step"] == "budget":

        state["order"]["budget"] = text

        order = state["order"].copy()

        del users[uid]

        # ارسال برای مشتری
        send_message(
            chat_id,
            "🎉 سفارش شما با موفقیت ثبت شد!\n\n"
            f"👤 نام: {order['name']}\n"
            f"💻 پروژه: {order['type']}\n"
            f"💰 بودجه: {order['budget']}\n\n"
            f"📝 توضیحات:\n{order['description']}\n\n"
            "🚀 سفارش برای Sepehr Studio ارسال شد.",
            main_keyboard()
        )

        # ارسال برای ادمین
        send_order_to_admin(
            order,
            chat_id
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

    if not isinstance(message, dict):
        message = update.get("message")

    if not isinstance(message, dict):
        message = {}

    if not chat_id:
        chat_id = message.get("chat_id")

    if not chat_id:
        return

    message_id = (
        message.get("message_id")
        or update.get("update_id")
    )

    if message_id:

        message_id = str(message_id)

        if message_id in processed_updates:
            return

        processed_updates.add(message_id)

        if len(processed_updates) > 2000:
            processed_updates.clear()

    text = str(
        message.get("text")
        or update.get("text")
        or ""
    ).strip()

    # =========================
    # BUTTON ID
    # =========================

    button_id = None

    aux_data = message.get("aux_data")

    if isinstance(aux_data, dict):

        button_id = (
            aux_data.get("button_id")
            or aux_data.get("buttonId")
            or aux_data.get("id")
        )

    if not button_id:

        aux_data = update.get("aux_data")

        if isinstance(aux_data, dict):

            button_id = (
                aux_data.get("button_id")
                or aux_data.get("buttonId")
                or aux_data.get("id")
            )

    if button_id:
        button_id = str(button_id)

    print(
        f"[MESSAGE] chat={chat_id} "
        f"text={text!r} "
        f"button={button_id!r}",
        flush=True
    )

    # =========================
    # ADMIN COMMAND
    # =========================

    if (
        text.lower() in
        ["/admin", "admin", "ادمین", "مدیریت"]
    ):

        if str(chat_id) == ADMIN_CHAT_ID:

            send_message(
                chat_id,
                "👑 پنل مدیریت Sepehr Studio\n\n"
                "🟢 وضعیت بات: فعال\n"
                "📋 سیستم سفارش: فعال\n"
                "📨 ارسال سفارش به ادمین: فعال\n\n"
                f"🆔 Admin Chat ID:\n{ADMIN_CHAT_ID}"
            )

        else:

            send_message(
                chat_id,
                "⛔ شما دسترسی ادمین ندارید."
            )

        return

    # =========================
    # ORDER
    # =========================

    if str(chat_id) in users:

        if process_order(chat_id, text):
            return

    # =========================
    # BUTTONS
    # =========================

    command = button_id or text

    if command == "services":

        send_message(
            chat_id,
            "💻 خدمات Sepehr Studio:",
            services_keyboard()
        )

        return

    if command == "order":

        start_order(chat_id)

        return

    if command == "contact":

        send_message(
            chat_id,
            "👨‍💻 ارتباط با Sepehr Studio\n\n"
            "پیام خود را ارسال کنید.",
            main_keyboard()
        )

        return

    if command == "about":

        send_message(
            chat_id,
            "🚀 Sepehr Studio\n\n"
            "طراحی سایت، برنامه‌نویسی، "
            "اپلیکیشن و هوش مصنوعی.",
            main_keyboard()
        )

        return

    if command == "website":

        send_message(
            chat_id,
            "🌐 طراحی سایت\n\n"
            "طراحی سایت‌های مدرن و واکنش‌گرا.",
            services_keyboard()
        )

        return

    if command == "app":

        send_message(
            chat_id,
            "📱 ساخت اپلیکیشن\n\n"
            "ساخت اپلیکیشن و رابط کاربری.",
            services_keyboard()
        )

        return

    if command == "ai":

        send_message(
            chat_id,
            "🤖 پروژه‌های هوش مصنوعی\n\n"
            "طراحی پروژه‌های مبتنی بر هوش مصنوعی.",
            services_keyboard()
        )

        return

    if command == "coding":

        send_message(
            chat_id,
            "💻 برنامه‌نویسی\n\n"
            "توسعه پروژه‌های وب و نرم‌افزاری.",
            services_keyboard()
        )

        return

    if command == "back":

        send_message(
            chat_id,
            "🏠 منوی اصلی:",
            main_keyboard()
        )

        return

    # =========================
    # START
    # =========================

    if text in [
        "/start",
        "start",
        "شروع"
    ]:

        send_message(
            chat_id,
            "🚀 به Sepehr Studio خوش آمدید!\n\n"
            "یکی از گزینه‌های زیر را انتخاب کنید:",
            main_keyboard()
        )

        return

    # =========================
    # TEST
    # =========================

    if text == "/test":

        send_message(
            chat_id,
            "✅ Sepehr Studio Bot فعال است!",
            main_keyboard()
        )

        return


# =========================
# RUN
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

            if not isinstance(updates, list):
                updates = []

            print(
                f"[UPDATES] {len(updates)} update(s)",
                flush=True
            )

            for update in updates:

                try:
                    process_update(update)

                except Exception as error:

                    print(
                        f"[UPDATE ERROR] {error}",
                        flush=True
                    )

            next_offset = data.get(
                "next_offset_id"
            )

            if next_offset:
                offset_id = str(next_offset)

        except Exception as error:

            print(
                f"[BOT ERROR] {error}",
                flush=True
            )

        time.sleep(2)


# =========================
# START
# =========================

if __name__ == "__main__":
    run()
