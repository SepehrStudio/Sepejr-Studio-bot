import os
import time
import requests

TOKEN = os.getenv("RUBIKA_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("RUBIKA_BOT_TOKEN is not configured.")

API = f"https://botapi.rubika.ir/v3/{TOKEN}"

session = requests.Session()

# وضعیت سفارش کاربران
users = {}

# جلوگیری از پردازش دوباره یک پیام
processed_messages = set()


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
            print("[API ERROR] Invalid JSON response", flush=True)
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
# INLINE KEYBOARD
# =========================

def button(button_id, text):
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
            button("services", "💻 خدمات Sepehr Studio")
        ],
        [
            button("order", "📋 ثبت سفارش"),
            button("contact", "👨‍💻 ارتباط با ما")
        ],
        [
            button("about", "ℹ️ درباره ما")
        ]
    ])


def services_keyboard():
    return make_keyboard([
        [
            button("website", "🌐 طراحی سایت"),
            button("app", "📱 ساخت اپ")
        ],
        [
            button("ai", "🤖 هوش مصنوعی"),
            button("coding", "💻 برنامه‌نویسی")
        ],
        [
            button("back", "🔙 بازگشت")
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
# ORDER
# =========================

def start_order(chat_id):

    uid = str(chat_id)

    users[uid] = {
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

    text = text.strip()

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
            "💻 نوع پروژه را بنویسید.\n\n"
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
            "📝 توضیحات پروژه را ارسال کنید."
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

    message_id = message.get("message_id")

    # جلوگیری از پردازش دوباره
    if message_id:

        message_id = str(message_id)

        if message_id in processed_messages:
            print(
                f"[SKIP] Duplicate message: {message_id}",
                flush=True
            )
            return

        processed_messages.add(message_id)

        # جلوگیری از رشد بی‌نهایت حافظه
        if len(processed_messages) > 1000:
            processed_messages.clear()
            processed_messages.add(message_id)

    text = str(message.get("text") or "").strip()

    aux_data = message.get("aux_data")

    if not isinstance(aux_data, dict):
        aux_data = {}

    # مهم:
    # کلیک دکمه‌های Inline از اینجا می‌آید
    button_id = aux_data.get("button_id")

    if button_id:
        button_id = str(button_id)

    print(
        f"[MESSAGE] "
        f"chat={chat_id} "
        f"text={text!r} "
        f"button={button_id!r}",
        flush=True
    )

    # ==================================
    # اول دکمه را بررسی می‌کنیم
    # ==================================

    if button_id:

        print(
            f"[BUTTON] clicked: {button_id}",
            flush=True
        )

        if button_id == "services":

            send_message(
                chat_id,
                "💻 خدمات Sepehr Studio:",
                services_keyboard()
            )

            return

        if button_id == "order":

            start_order(chat_id)

            return

        if button_id == "contact":

            send_message(
                chat_id,
                "👨‍💻 ارتباط با Sepehr Studio\n\n"
                "پیام خود را ارسال کنید.",
                main_keyboard()
            )

            return

        if button_id == "about":

            send_message(
                chat_id,
                "🚀 Sepehr Studio\n\n"
                "توسعه پروژه‌های برنامه‌نویسی، "
                "طراحی سایت و هوش مصنوعی.",
                main_keyboard()
            )

            return

        if button_id == "website":

            send_message(
                chat_id,
                "🌐 طراحی سایت\n\n"
                "طراحی سایت‌های مدرن و واکنش‌گرا.",
                services_keyboard()
            )

            return

        if button_id == "app":

            send_message(
                chat_id,
                "📱 ساخت اپلیکیشن\n\n"
                "ساخت اپلیکیشن و رابط کاربری.",
                services_keyboard()
            )

            return

        if button_id == "ai":

            send_message(
                chat_id,
                "🤖 پروژه‌های هوش مصنوعی\n\n"
                "طراحی پروژه‌های مبتنی بر هوش مصنوعی.",
                services_keyboard()
            )

            return

        if button_id == "coding":

            send_message(
                chat_id,
                "💻 برنامه‌نویسی\n\n"
                "توسعه پروژه‌های وب و نرم‌افزاری.",
                services_keyboard()
            )

            return

        if button_id == "back":

            send_message(
                chat_id,
                "🏠 منوی اصلی:",
                main_keyboard()
            )

            return

        print(
            f"[BUTTON] Unknown button: {button_id}",
            flush=True
        )

        return

    # ==================================
    # پیام معمولی / سفارش
    # ==================================

    if str(chat_id) in users:

        if process_order(chat_id, text):
            return

    # ==================================
    # دستورات
    # ==================================

    if text in (
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

        return

    if text == "/test":

        send_message(
            chat_id,
            "✅ بات Sepehr Studio فعال است!",
            main_keyboard()
        )

        return


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

            data = result.get("data", {})

            if not isinstance(data, dict):
                data = {}

            updates = data.get("updates", [])

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


# =========================
# START
# =========================

if __name__ == "__main__":
    run()
