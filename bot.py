import os
import time
import requests

TOKEN = os.environ["RUBIKA_BOT_TOKEN"]
BASE = f"https://botapi.rubika.ir/v3/{TOKEN}"

session = requests.Session()


def api(method, data=None):
    try:
        r = session.post(
            f"{BASE}/{method}",
            json=data or {},
            timeout=30
        )

        print(f"API {method}: HTTP {r.status_code}")

        result = r.json()

        if result.get("status") != "OK":
            print("API RESPONSE:", result)

        # API ممکن است data داشته باشد
        if isinstance(result.get("data"), dict):
            return result["data"]

        return result

    except Exception as e:
        print("API ERROR:", e)
        return {}


def send_message(chat_id, text, keyboard=None):
    data = {
        "chat_id": str(chat_id),
        "text": text
    }

    if keyboard:
        data["inline_keypad"] = keyboard

    return api("sendMessage", data)


def main_menu():
    return {
        "rows": [
            {
                "buttons": [
                    {
                        "id": "services",
                        "text": "💻 خدمات Sepehr Studio"
                    }
                ]
            },
            {
                "buttons": [
                    {
                        "id": "order",
                        "text": "📋 ثبت سفارش"
                    },
                    {
                        "id": "contact",
                        "text": "👨‍💻 ارتباط با ما"
                    }
                ]
            },
            {
                "buttons": [
                    {
                        "id": "about",
                        "text": "ℹ️ درباره Sepehr Studio"
                    }
                ]
            }
        ]
    }


def services_menu():
    return {
        "rows": [
            {
                "buttons": [
                    {
                        "id": "website",
                        "text": "🌐 طراحی سایت"
                    },
                    {
                        "id": "app",
                        "text": "📱 ساخت اپ"
                    }
                ]
            },
            {
                "buttons": [
                    {
                        "id": "ai",
                        "text": "🤖 پروژه هوش مصنوعی"
                    },
                    {
                        "id": "coding",
                        "text": "💻 برنامه‌نویسی"
                    }
                ]
            },
            {
                "buttons": [
                    {
                        "id": "back",
                        "text": "🔙 بازگشت"
                    }
                ]
            }
        ]
    }


def handle_message(update):

    chat_id = update.get("chat_id")

    message = update.get("new_message") or {}

    if not chat_id or not isinstance(message, dict):
        return

    # متن پیام
    text = (message.get("text") or "").strip()

    # دکمه‌های Inline
    aux_data = message.get("aux_data") or {}
    button_id = aux_data.get("button_id")

    # اگر دکمه زده شده، ID دکمه را استفاده کن
    command = button_id or text

    print(
        f"📩 Message received | "
        f"chat={chat_id} | "
        f"text={text} | "
        f"button={button_id}"
    )

    if command in ["/start", "شروع", "start"]:

        send_message(
            chat_id,
            "🚀 به Sepehr Studio خوش آمدید!\n\n"
            "خدمات و امکانات موردنظر خود را انتخاب کنید:",
            main_menu()
        )

    elif command == "services":

        send_message(
            chat_id,
            "💻 خدمات Sepehr Studio:",
            services_menu()
        )

    elif command == "website":

        send_message(
            chat_id,
            "🌐 طراحی سایت\n\n"
            "طراحی سایت‌های مدرن و واکنش‌گرا با HTML/CSS/JS.",
            main_menu()
        )

    elif command == "app":

        send_message(
            chat_id,
            "📱 ساخت اپلیکیشن\n\n"
            "ساخت رابط کاربری و اپلیکیشن‌های مختلف.",
            main_menu()
        )

    elif command == "ai":

        send_message(
            chat_id,
            "🤖 پروژه‌های هوش مصنوعی\n\n"
            "طراحی رابط کاربری و پروژه‌های مبتنی بر هوش مصنوعی.",
            main_menu()
        )

    elif command == "coding":

        send_message(
            chat_id,
            "💻 برنامه‌نویسی\n\n"
            "توسعه پروژه‌های وب، ابزارها و سیستم‌های سفارشی.",
            main_menu()
        )

    elif command == "order":

        send_message(
            chat_id,
            "📋 برای ثبت سفارش، لطفاً این اطلاعات را ارسال کنید:\n\n"
            "1️⃣ نام\n"
            "2️⃣ نوع پروژه\n"
            "3️⃣ توضیح پروژه\n"
            "4️⃣ بودجه تقریبی\n\n"
            "پس از دریافت اطلاعات، سفارش بررسی می‌شود.",
            main_menu()
        )

    elif command == "contact":

        send_message(
            chat_id,
            "👨‍💻 ارتباط با Sepehr Studio\n\n"
            "برای ارتباط و پیگیری سفارش، پیام خود را ارسال کنید.",
            main_menu()
        )

    elif command == "about":

        send_message(
            chat_id,
            "🚀 Sepehr Studio\n\n"
            "استودیو پروژه‌های برنامه‌نویسی، طراحی سایت و هوش مصنوعی.",
            main_menu()
        )

    elif command == "back":

        send_message(
            chat_id,
            "🏠 منوی اصلی:",
            main_menu()
        )


def run():

    print("🚀 Sepehr Studio Bot started!")

    offset_id = None

    while True:

        try:

            data = {
                "limit": 10
            }

            if offset_id:
                data["offset_id"] = offset_id

            result = api("getUpdates", data)

            updates = result.get("updates", [])

            print(f"🔄 Updates received: {len(updates)}")

            for update in updates:

                if not isinstance(update, dict):
                    continue

                handle_message(update)

            # خیلی مهم:
            # offset باید next_offset_id باشد
            next_offset = result.get("next_offset_id")

            if next_offset:
                offset_id = str(next_offset)

        except Exception as e:

            print("❌ ERROR:", e)

        time.sleep(2)


if __name__ == "__main__":
    run()
