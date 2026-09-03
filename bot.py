import os
import time
import requests

TOKEN = os.getenv("RUBIKA_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("RUBIKA_BOT_TOKEN is not configured.")

API = f"https://botapi.rubika.ir/v3/{TOKEN}"

session = requests.Session()


# =========================
# API
# =========================

def api(method, data=None):
    try:
        r = session.post(
            f"{API}/{method}",
            json=data or {},
            timeout=30
        )

        result = r.json()

        print(
            f"[API] {method}: HTTP {r.status_code} -> {result}",
            flush=True
        )

        return result

    except Exception as e:
        print(f"[API ERROR] {e}", flush=True)
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
                    button("services", "💻 خدمات Sepehr Studio")
                ]
            },
            {
                "buttons": [
                    button("order", "📋 ثبت سفارش"),
                    button("contact", "👨‍💻 ارتباط با ما")
                ]
            },
            {
                "buttons": [
                    button("about", "ℹ️ درباره ما")
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
# SEND
# =========================

def send(chat_id, text, keyboard=None):

    payload = {
        "chat_id": str(chat_id),
        "text": text
    }

    if keyboard is not None:
        payload["inline_keypad"] = keyboard

    return api("sendMessage", payload)


# =========================
# UPDATE PARSER
# =========================

def handle_update(update):

    if not isinstance(update, dict):
        return

    print(
        "[RAW UPDATE]",
        update,
        flush=True
    )

    # ساختار اصلی getUpdates
    chat_id = update.get("chat_id")

    message = update.get("new_message")

    # بعضی ساختارها ممکن است message داشته باشند
    if not isinstance(message, dict):
        message = update.get("message")

    if not isinstance(message, dict):
        message = {}

    # اگر chat_id داخل message بود
    if not chat_id:
        chat_id = message.get("chat_id")

    if not chat_id:
        print("[WARNING] chat_id not found", flush=True)
        return

    text = str(
        message.get("text") or ""
    ).strip()

    # =========================
    # BUTTON
    # =========================

    aux = message.get("aux_data")

    button_id = None

    if isinstance(aux, dict):
        button_id = aux.get("button_id")

    if button_id:
        button_id = str(button_id)

    print(
        f"[EVENT] chat={chat_id} "
        f"text={text!r} "
        f"button_id={button_id!r}",
        flush=True
    )

    # دکمه یا متن
    command = button_id or text

    # =========================
    # START
    # =========================

    if command in ["/start", "start", "شروع"]:

        send(
            chat_id,
            "🚀 به Sepehr Studio خوش آمدید!\n\n"
            "یکی از گزینه‌های زیر را انتخاب کنید:",
            main_keyboard()
        )

        return

    # =========================
    # SERVICES
    # =========================

    if command == "services":

        send(
            chat_id,
            "💻 خدمات Sepehr Studio:",
            services_keyboard()
        )

        return

    # =========================
    # WEBSITE
    # =========================

    if command == "website":

        send(
            chat_id,
            "🌐 طراحی سایت\n\n"
            "طراحی سایت‌های مدرن و واکنش‌گرا.",
            services_keyboard()
        )

        return

    # =========================
    # APP
    # =========================

    if command == "app":

        send(
            chat_id,
            "📱 ساخت اپلیکیشن\n\n"
            "ساخت اپلیکیشن و رابط کاربری.",
            services_keyboard()
        )

        return

    # =========================
    # AI
    # =========================

    if command == "ai":

        send(
            chat_id,
            "🤖 پروژه‌های هوش مصنوعی\n\n"
            "طراحی پروژه‌های مبتنی بر هوش مصنوعی.",
            services_keyboard()
        )

        return

    # =========================
    # CODING
    # =========================

    if command == "coding":

        send(
            chat_id,
            "💻 برنامه‌نویسی\n\n"
            "توسعه پروژه‌های وب و نرم‌افزاری.",
            services_keyboard()
        )

        return

    # =========================
    # ORDER
    # =========================

    if command == "order":

        send(
            chat_id,
            "📋 ثبت سفارش\n\n"
            "برای ثبت سفارش، اطلاعات پروژه را برای من ارسال کنید.",
            main_keyboard()
        )

        return

    # =========================
    # CONTACT
    # =========================

    if command == "contact":

        send(
            chat_id,
            "👨‍💻 ارتباط با Sepehr Studio\n\n"
            "پیام خود را ارسال کنید.",
            main_keyboard()
        )

        return

    # =========================
    # ABOUT
    # =========================

    if command == "about":

        send(
            chat_id,
            "🚀 Sepehr Studio\n\n"
            "طراحی سایت، برنامه‌نویسی، اپلیکیشن و هوش مصنوعی.",
            main_keyboard()
        )

        return

    # =========================
    # BACK
    # =========================

    if command == "back":

        send(
            chat_id,
            "🏠 منوی اصلی:",
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

            data = {
                "limit": 10
            }

            if offset_id:
                data["offset_id"] = offset_id

            result = api(
                "getUpdates",
                data
            )

            updates_data = result.get(
                "data",
                {}
            )

            if not isinstance(updates_data, dict):
                updates_data = {}

            updates = updates_data.get(
                "updates",
                []
            )

            if not isinstance(updates, list):
                updates = []

            print(
                f"🔄 Updates received: {len(updates)}",
                flush=True
            )

            for update in updates:

                try:
                    handle_update(update)

                except Exception as e:

                    print(
                        f"[UPDATE ERROR] {e}",
                        flush=True
                    )

            # مهم: offset بعد از پردازش Updateها
            next_offset = updates_data.get(
                "next_offset_id"
            )

            if next_offset:
                offset_id = str(next_offset)

        except Exception as e:

            print(
                f"[LOOP ERROR] {e}",
                flush=True
            )

        time.sleep(2)


if __name__ == "__main__":
    run()
