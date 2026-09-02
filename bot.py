import os
import time
import json
import uuid
import requests

TOKEN = os.getenv("RUBIKA_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("b0IGuhX0BBcQ085f392a2b3fce01be44")

if not TOKEN:
    raise RuntimeError("RUBIKA_BOT_TOKEN is not configured.")

if not ADMIN_CHAT_ID:
    raise RuntimeError("ADMIN_CHAT_ID is not configured.")

API = f"https://botapi.rubika.ir/v3/{TOKEN}"

session = requests.Session()

# وضعیت موقت کاربران
users = {}

# سفارش‌ها
orders = {}


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
# KEYBOARDS
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


def admin_keyboard(order_id):
    return {
        "rows": [
            {
                "buttons": [
                    button(
                        f"accept_{order_id}",
                        "✅ تأیید سفارش"
                    ),
                    button(
                        f"reject_{order_id}",
                        "❌ رد سفارش"
                    )
                ]
            },
            {
                "buttons": [
                    button(
                        f"working_{order_id}",
                        "🔨 در حال انجام"
                    ),
                    button(
                        f"done_{order_id}",
                        "🎉 تکمیل شد"
                    )
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
# ORDER SYSTEM
# =========================

def new_order_id():
    return "SS-" + uuid.uuid4().hex[:8].upper()


def start_order(chat_id):

    users[str(chat_id)] = {
        "step": "name",
        "order": {}
    }

    send_message(
        chat_id,
        "📋 ثبت سفارش جدید\n\n"
        "مرحله ۱ از ۴\n\n"
        "👤 لطفاً نام خود را ارسال کنید."
    )


def process_order(chat_id, text):

    uid = str(chat_id)

    if uid not in users:
        return False

    state = users[uid]

    if state.get("step") == "name":

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

    if state.get("step") == "type":

        state["order"]["type"] = text
        state["step"] = "description"

        send_message(
            chat_id,
            "✅ نوع پروژه دریافت شد.\n\n"
            "مرحله ۳ از ۴\n\n"
            "📝 توضیحات کامل پروژه را ارسال کنید."
        )

        return True

    if state.get("step") == "description":

        state["order"]["description"] = text
        state["step"] = "budget"

        send_message(
            chat_id,
            "✅ توضیحات دریافت شد.\n\n"
            "مرحله ۴ از ۴\n\n"
            "💰 بودجه تقریبی پروژه را بنویسید."
        )

        return True

    if state.get("step") == "budget":

        order_id = new_order_id()

        order = state["order"]

        order["budget"] = text
        order["order_id"] = order_id
        order["chat_id"] = chat_id
        order["status"] = "جدید"

        orders[order_id] = order.copy()

        del users[uid]

        # پیام مشتری
        send_message(
            chat_id,
            f"✅ سفارش شما ثبت شد!\n\n"
            f"🆔 کد سفارش: {order_id}\n"
            f"📌 وضعیت: جدید\n\n"
            "سفارش برای مدیریت ارسال شد. 👨‍💻"
        )

        # پیام ادمین
        admin_text = (
            "🔔 سفارش جدید Sepehr Studio\n\n"
            f"🆔 کد سفارش: {order_id}\n\n"
            f"👤 نام: {order['name']}\n"
            f"💻 نوع پروژه: {order['type']}\n\n"
            f"📝 توضیحات:\n"
            f"{order['description']}\n\n"
            f"💰 بودجه:\n"
            f"{order['budget']}\n\n"
            "📌 وضعیت: جدید"
        )

        send_message(
            ADMIN_CHAT_ID,
            admin_text,
            admin_keyboard(order_id)
        )

        return True

    return False


# =========================
# ADMIN ACTIONS
# =========================

def admin_action(chat_id, command):

    if str(chat_id) != str(ADMIN_CHAT_ID):
        return False

    parts = command.split("_", 1)

    if len(parts) != 2:
        return False

    action = parts[0]
    order_id = parts[1]

    if order_id not in orders:
        send_message(
            chat_id,
            "❌ سفارش پیدا نشد."
        )
        return True

    order = orders[order_id]

    status_map = {
        "accept": "تأیید شده",
        "reject": "رد شده",
        "working": "در حال انجام",
        "done": "تکمیل شده"
    }

    if action not in status_map:
        return False

    new_status = status_map[action]

    order["status"] = new_status

    # اطلاع به ادمین
    send_message(
        chat_id,
        f"✅ وضعیت سفارش {order_id} تغییر کرد.\n\n"
        f"📌 وضعیت جدید: {new_status}"
    )

    # اطلاع به مشتری
    send_message(
        order["chat_id"],
        f"📦 بروزرسانی سفارش شما\n\n"
        f"🆔 کد سفارش: {order_id}\n"
        f"📌 وضعیت: {new_status}"
    )

    return True


# =========================
# UPDATE HANDLER
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

    text = (message.get("text") or "").strip()

    aux_data = message.get("aux_data") or {}
    button_id = aux_data.get("button_id")

    command = button_id or text

    print(
        f"[MESSAGE] chat={chat_id} "
        f"text={text!r} "
        f"button={button_id!r}",
        flush=True
    )

    # ادمین
    if command.startswith(
        ("accept_", "reject_", "working_", "done_")
    ):

        admin_action(
            chat_id,
            command
        )

        return

    # اگر کاربر در حال ثبت سفارش است
    if str(chat_id) in users:

        if process_order(
            chat_id,
            text
        ):
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
            "طراحی و توسعه پروژه‌های مبتنی بر هوش مصنوعی.",
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
