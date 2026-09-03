import os
import time
import requests
import json

TOKEN = os.environ["RUBIKA_BOT_TOKEN"]
BASE = f"https://botapi.rubika.ir/v3/{TOKEN}"

# =========================
# ADMIN
# =========================

ADMIN_CHAT_ID = "b0IGuhX0BBcQ085f392a2b3fce01be44"

# =========================
# DATABASE / MEMORY
# =========================

users = {}

# وضعیت‌های ممکن:
# waiting_order
# waiting_price
# waiting_receipt
# waiting_file

# =========================
# API
# =========================

def api(method, data=None):

    try:

        r = requests.post(
            f"{BASE}/{method}",
            json=data or {},
            timeout=30
        )

        print(f"API {method}: HTTP {r.status_code}")

        try:

            result = r.json()

            print("API RESPONSE:", result)

            return result

        except Exception:

            print("Invalid JSON response")

            return {}

    except Exception as e:

        print("API ERROR:", e)

        return {}


# =========================
# SEND MESSAGE
# =========================

def send_message(chat_id, text, keyboard=None):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    # فقط Chat Keypad
    if keyboard:

        data["chat_keypad_type"] = "New"
        data["chat_keypad"] = keyboard

    return api("sendMessage", data)


# =========================
# KEYBOARD
# =========================

def button(button_id, text):

    return {
        "id": button_id,
        "type": "Simple",
        "button_text": text
    }


def main_menu():

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
                    button("about", "ℹ️ درباره Sepehr Studio")
                ]
            }
        ],
        "resize_keyboard": True,
        "on_time_keyboard": False
    }


def services_menu():

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
                    button("ai", "🤖 پروژه هوش مصنوعی"),
                    button("coding", "💻 برنامه‌نویسی")
                ]
            },
            {
                "buttons": [
                    button("back", "🔙 بازگشت")
                ]
            }
        ],
        "resize_keyboard": True,
        "on_time_keyboard": False
    }


# =========================
# USER DATA
# =========================

def get_user(chat_id):

    if chat_id not in users:

        users[chat_id] = {
            "state": None,
            "order": None,
            "price": None,
            "receipt_message": None
        }

    return users[chat_id]


# =========================
# SEND ORDER TO ADMIN
# =========================

def send_order_to_admin(chat_id, order_text):

    user = get_user(chat_id)

    user["state"] = "waiting_price"
    user["order"] = order_text

    admin_text = (
        "📋 سفارش جدید Sepehr Studio\n\n"
        f"👤 Chat ID مشتری:\n{chat_id}\n\n"
        "📝 توضیحات سفارش:\n"
        f"{order_text}\n\n"
        "💰 برای تعیین قیمت، فقط مبلغ را ارسال کنید.\n"
        "مثال:\n"
        "850000"
    )

    send_message(
        ADMIN_CHAT_ID,
        admin_text
    )


# =========================
# ADMIN PRICE
# =========================

def set_price(price):

    price = price.replace(",", "").replace("٬", "").strip()

    try:

        return int(price)

    except:

        return None


def send_price_to_customer(price):

    # آخرین سفارشی که در انتظار قیمت است
    for chat_id, user in users.items():

        if user.get("state") == "waiting_price":

            user["price"] = price
            user["state"] = "waiting_receipt"

            send_message(
                chat_id,
                "💰 قیمت سفارش شما مشخص شد.\n\n"
                f"💵 مبلغ قابل پرداخت:\n"
                f"{price:,} تومان\n\n"
                "🧾 لطفاً فیش پرداخت را همینجا ارسال کنید.\n\n"
                "پس از بررسی فیش، پروژه برای شما ارسال خواهد شد.",
                main_menu()
            )

            send_message(
                ADMIN_CHAT_ID,
                "✅ قیمت برای مشتری ارسال شد.\n\n"
                f"👤 Chat ID:\n{chat_id}\n\n"
                f"💰 مبلغ:\n{price:,} تومان"
            )

            return True

    return False


# =========================
# FORWARD RECEIPT
# =========================

def handle_receipt(message):

    chat_id = message.get("chat_id")

    user = get_user(chat_id)

    if user.get("state") != "waiting_receipt":

        return False

    user["receipt_message"] = message
    user["state"] = "waiting_file"

    order = user.get("order", "نامشخص")
    price = user.get("price", "نامشخص")

    # اطلاع به مشتری
    send_message(
        chat_id,
        "🧾 فیش شما دریافت شد.\n\n"
        "✅ فیش برای بررسی ارسال شد.\n"
        "⏳ پس از تأیید پرداخت، فایل پروژه برای شما ارسال می‌شود.",
        main_menu()
    )

    # اطلاعات فیش برای ادمین
    send_message(
        ADMIN_CHAT_ID,
        "🧾 فیش پرداخت جدید\n\n"
        f"👤 Chat ID مشتری:\n{chat_id}\n\n"
        f"💰 مبلغ سفارش:\n{price:,} تومان\n\n"
        f"📋 سفارش:\n{order}\n\n"
        "⬆️ فیش مشتری در پیام بعدی قرار دارد.\n"
        "📦 فایل پروژه را پس از تأیید پرداخت برای این Chat ID ارسال کنید."
    )

    # تلاش برای ارسال/فوروارد خود پیام فیش
    message_id = message.get("message_id")

    if message_id:

        api(
            "forwardMessage",
            {
                "from_chat_id": chat_id,
                "message_id": message_id,
                "to_chat_id": ADMIN_CHAT_ID
            }
        )

    return True


# =========================
# ADMIN FILE DELIVERY
# =========================

def admin_file_instruction():

    send_message(
        ADMIN_CHAT_ID,
        "📦 سفارش آماده تحویل است.\n\n"
        "فایل پروژه را برای همین ربات ارسال کنید.\n\n"
        "ربات باید آن را برای مشتری سفارش مربوطه ارسال کند."
    )


# =========================
# MESSAGE HANDLER
# =========================

def handle_message(message):

    chat_id = message.get("chat_id")

    text = (message.get("text") or "").strip()

    if not chat_id:

        return

    print(
        f"📩 Message received | "
        f"chat={chat_id} | text={text}"
    )

    user = get_user(chat_id)

    # ==================================
    # ADMIN
    # ==================================

    if chat_id == ADMIN_CHAT_ID:

        # قیمت
        price = set_price(text)

        if price is not None:

            if send_price_to_customer(price):

                return

        # دستور مشاهده وضعیت
        if text == "/orders":

            found = False

            for uid, u in users.items():

                if u.get("order"):

                    found = True

                    send_message(
                        ADMIN_CHAT_ID,
                        "📋 سفارش\n\n"
                        f"👤 Chat ID:\n{uid}\n\n"
                        f"📝 سفارش:\n{u.get('order')}\n\n"
                        f"💰 قیمت:\n{u.get('price')}\n\n"
                        f"📌 وضعیت:\n{u.get('state')}"
                    )

            if not found:

                send_message(
                    ADMIN_CHAT_ID,
                    "📭 سفارشی ثبت نشده است."
                )

            return

    # ==================================
    # RECEIPT / FILE MESSAGE
    # ==================================

    # اگر پیام غیرمتنی/فایل/عکس باشد
    if not text:

        if chat_id != ADMIN_CHAT_ID:

            if handle_receipt(message):

                return

        else:

            # فایل ادمین
            send_message(
                ADMIN_CHAT_ID,
                "📦 فایل دریافت شد.\n"
                "برای ارسال فایل به مشتری، باید Chat ID سفارش مشخص باشد."
            )

            return

    # ==================================
    # START
    # ==================================

    if text in ["/start", "start", "شروع"]:

        user["state"] = None

        send_message(
            chat_id,
            "🚀 به Sepehr Studio خوش آمدید!\n\n"
            "از منوی زیر بخش موردنظر خود را انتخاب کنید:",
            main_menu()
        )

    # ==================================
    # SERVICES
    # ==================================

    elif text == "💻 خدمات Sepehr Studio":

        send_message(
            chat_id,
            "💻 خدمات Sepehr Studio\n\n"
            "یکی از خدمات زیر را انتخاب کنید:",
            services_menu()
        )

    # ==================================
    # ORDER
    # ==================================

    elif text == "📋 ثبت سفارش":

        user["state"] = "waiting_order"

        send_message(
            chat_id,
            "📋 ثبت سفارش جدید\n\n"
            "لطفاً توضیحات کامل پروژه خود را در یک پیام ارسال کنید.\n\n"
            "مثال:\n"
            "🌐 طراحی سایت فروشگاهی\n"
            "📱 ساخت اپلیکیشن\n"
            "🤖 پروژه هوش مصنوعی\n\n"
            "بعد از دریافت توضیحات، سفارش بررسی و قیمت‌گذاری می‌شود.",
            main_menu()
        )

    # ==================================
    # ORDER DESCRIPTION
    # ==================================

    elif user.get("state") == "waiting_order":

        send_order_to_admin(
            chat_id,
            text
        )

        send_message(
            chat_id,
            "✅ سفارش شما با موفقیت ثبت شد.\n\n"
            "📨 توضیحات برای مدیریت Sepehr Studio ارسال شد.\n"
            "⏳ لطفاً منتظر اعلام قیمت باشید.",
            main_menu()
        )

    # ==================================
    # CONTACT
    # ==================================

    elif text == "👨‍💻 ارتباط با ما":

        send_message(
            chat_id,
            "👨‍💻 ارتباط با Sepehr Studio\n\n"
            "پیام خود را همینجا ارسال کنید.",
            main_menu()
        )

    # ==================================
    # ABOUT
    # ==================================

    elif text == "ℹ️ درباره Sepehr Studio":

        send_message(
            chat_id,
            "🚀 Sepehr Studio\n\n"
            "طراحی سایت، برنامه‌نویسی، ساخت اپلیکیشن "
            "و پروژه‌های هوش مصنوعی.",
            main_menu()
        )

    # ==================================
    # WEBSITE
    # ==================================

    elif text == "🌐 طراحی سایت":

        send_message(
            chat_id,
            "🌐 طراحی سایت\n\n"
            "طراحی سایت‌های مدرن، واکنش‌گرا و اختصاصی.",
            main_menu()
        )

    # ==================================
    # APP
    # ==================================

    elif text == "📱 ساخت اپ":

        send_message(
            chat_id,
            "📱 ساخت اپلیکیشن\n\n"
            "طراحی و توسعه اپلیکیشن‌های مختلف.",
            main_menu()
        )

    # ==================================
    # AI
    # ==================================

    elif text == "🤖 پروژه هوش مصنوعی":

        send_message(
            chat_id,
            "🤖 پروژه هوش مصنوعی\n\n"
            "طراحی رابط کاربری و پروژه‌های مبتنی بر هوش مصنوعی.",
            main_menu()
        )

    # ==================================
    # CODING
    # ==================================

    elif text == "💻 برنامه‌نویسی":

        send_message(
            chat_id,
            "💻 برنامه‌نویسی\n\n"
            "توسعه پروژه‌های وب، ابزارها و سیستم‌های سفارشی.",
            main_menu()
        )

    # ==================================
    # BACK
    # ==================================

    elif text == "🔙 بازگشت":

        send_message(
            chat_id,
            "🏠 منوی اصلی:",
            main_menu()
        )

    # ==================================
    # NORMAL MESSAGE
    # ==================================

    elif text:

        send_message(
            chat_id,
            "📩 پیام شما دریافت شد.\n\n"
            "برای استفاده از امکانات، یکی از گزینه‌های منو را انتخاب کنید.",
            main_menu()
        )


# =========================
# RUN BOT
# =========================

def run():

    print("🚀 Sepehr Studio Bot started!")

    print(
        "👑 ADMIN CHAT ID:",
        ADMIN_CHAT_ID
    )

    offset = None

    while True:

        try:

            data = {}

            if offset is not None:

                data["offset_id"] = offset

            result = api(
                "getUpdates",
                data
            )

            updates = result.get(
                "data",
                {}
            ).get(
                "updates",
                []
            )

            print(
                f"🔄 Updates received: {len(updates)}"
            )

            for update in updates:

                update_id = update.get(
                    "update_id"
                )

                if update_id is not None:

                    offset = update_id

                message = update.get(
                    "message"
                )

                if message:

                    handle_message(
                        message
                    )

        except Exception as e:

            print(
                "❌ ERROR:",
                e
            )

        time.sleep(2)


# =========================
# START
# =========================

if __name__ == "__main__":

    run()
