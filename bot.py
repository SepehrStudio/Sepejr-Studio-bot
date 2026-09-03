import os
import time
import requests

# =========================================================
# CONFIG
# =========================================================

TOKEN = os.getenv("RUBIKA_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("RUBIKA_BOT_TOKEN is not configured.")

API = f"https://botapi.rubika.ir/v3/{TOKEN}"

# Chat ID فعلی
ADMIN_CHAT_ID = "b0IGuhX0BBcQ085f392a2b3fce01be44"

session = requests.Session()

# جلوگیری از پردازش دوباره یک پیام
processed_messages = set()

# وضعیت ثبت سفارش کاربران
user_states = {}


# =========================================================
# API
# =========================================================

def api(method, data=None):
    try:
        response = session.post(
            f"{API}/{method}",
            json=data or {},
            timeout=30
        )

        try:
            result = response.json()
        except Exception:
            result = {
                "status": "INVALID_RESPONSE",
                "text": response.text
            }

        print(
            f"[API] {method}: HTTP {response.status_code} -> {result}",
            flush=True
        )

        return result

    except requests.RequestException as e:
        print(f"[API ERROR] {method}: {e}", flush=True)
        return {}

    except Exception as e:
        print(f"[API ERROR] {method}: {e}", flush=True)
        return {}


# =========================================================
# BUTTON
# =========================================================

def button(button_id, text):
    return {
        "id": str(button_id),
        "type": "Simple",
        "button_text": text
    }


# =========================================================
# MAIN KEYBOARD
# =========================================================

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
        ],
        "resize_keyboard": True,
        "on_time_keyboard": False
    }


# =========================================================
# SERVICES KEYBOARD
# =========================================================

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
                    button("order", "📋 ثبت سفارش")
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


# =========================================================
# SEND MESSAGE
# =========================================================

def send(chat_id, text, keyboard=None):

    payload = {
        "chat_id": str(chat_id),
        "text": str(text)
    }

    # کیبورد معمولی روبیکا
    if keyboard is not None:
        payload["chat_keypad"] = keyboard
        payload["chat_keypad_type"] = "New"

    return api("sendMessage", payload)


# =========================================================
# SEND TO ADMIN
# =========================================================

def send_to_admin(text):

    return send(
        ADMIN_CHAT_ID,
        text
    )


# =========================================================
# ORDER STATE
# =========================================================

def start_order(chat_id):

    user_states[str(chat_id)] = {
        "step": "details",
        "data": {}
    }

    send(
        chat_id,
        "📋 ثبت سفارش جدید\n\n"
        "لطفاً توضیحات پروژه‌ات را ارسال کن.\n\n"
        "مثلاً:\n"
        "🌐 طراحی سایت فروشگاهی\n"
        "📱 ساخت اپلیکیشن\n"
        "🤖 پروژه هوش مصنوعی\n\n"
        "هرچه توضیحات کامل‌تر باشد، بررسی سفارش دقیق‌تر انجام می‌شود.",
        main_keyboard()
    )


# =========================================================
# HANDLE ORDER MESSAGE
# =========================================================

def handle_order_message(chat_id, text):

    chat_id = str(chat_id)

    state = user_states.get(chat_id)

    if not state:
        return False

    if state.get("step") != "details":
        return False

    if not text:
        return True

    # ذخیره سفارش
    state["data"]["details"] = text
    state["step"] = "completed"

    # ارسال سفارش به ادمین
    admin_message = (
        "🔔 سفارش جدید Sepehr Studio\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 Chat ID مشتری:\n{chat_id}\n\n"
        "📋 توضیحات سفارش:\n"
        f"{text}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📌 وضعیت: در انتظار بررسی"
    )

    result = send_to_admin(admin_message)

    # پاسخ به مشتری
    if result.get("status") == "OK":

        send(
            chat_id,
            "✅ سفارش شما با موفقیت ثبت شد!\n\n"
            "📨 اطلاعات سفارش برای Sepehr Studio ارسال شد.\n"
            "پس از بررسی، ادامه مراحل اعلام می‌شود.",
            main_keyboard()
        )

    else:

        send(
            chat_id,
            "⚠️ سفارش دریافت شد، اما ارسال اعلان به بخش مدیریت با مشکل مواجه شد.\n"
            "لطفاً دوباره کمی بعد تلاش کنید.",
            main_keyboard()
        )

    # پاک کردن وضعیت
    user_states.pop(chat_id, None)

    return True


# =========================================================
# UPDATE HANDLER
# =========================================================

def handle_update(update):

    if not isinstance(update, dict):
        return

    print(
        "[RAW UPDATE]",
        update,
        flush=True
    )

    # فقط پیام‌های جدید
    update_type = update.get("type")

    if update_type != "NewMessage":
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
        print("[WARNING] chat_id not found", flush=True)
        return

    chat_id = str(chat_id)

    # =====================================================
    # MESSAGE ID
    # =====================================================

    message_id = message.get("message_id")

    if message_id:

        message_id = str(message_id)

        if message_id in processed_messages:
            print(
                f"[SKIP] Duplicate message: {message_id}",
                flush=True
            )
            return

        processed_messages.add(message_id)

        # حافظه را محدود نگه می‌داریم
        if len(processed_messages) > 5000:
            processed_messages.clear()

    # =====================================================
    # TEXT
    # =====================================================

    text = str(
        message.get("text") or ""
    ).strip()

    # =====================================================
    # BUTTON ID
    # =====================================================

    button_id = None

    aux_data = message.get("aux_data")

    if isinstance(aux_data, dict):

        button_id = aux_data.get("button_id")

        if button_id:
            button_id = str(button_id)

    print(
        f"[EVENT] chat={chat_id} "
        f"text={text!r} "
        f"button_id={button_id!r}",
        flush=True
    )

    # دکمه اولویت دارد
    command = button_id or text

    # =====================================================
    # ORDER MESSAGE
    # =====================================================

    if not button_id:

        if handle_order_message(chat_id, text):
            return

    # =====================================================
    # START
    # =====================================================

    if command in ["/start", "start", "شروع"]:

        # اگر سفارش قبلی نیمه‌کاره بوده
        user_states.pop(chat_id, None)

        send(
            chat_id,
            "🚀 به Sepehr Studio خوش آمدید!\n\n"
            "خدمات طراحی سایت، برنامه‌نویسی، اپلیکیشن و هوش مصنوعی.\n\n"
            "👇 یکی از گزینه‌های زیر را انتخاب کنید:",
            main_keyboard()
        )

        return

    # =====================================================
    # SERVICES
    # =====================================================

    if command in ["services", "💻 خدمات Sepehr Studio"]:

        send(
            chat_id,
            "💻 خدمات Sepehr Studio\n\n"
            "یکی از خدمات زیر را انتخاب کنید:",
            services_keyboard()
        )

        return

    # =====================================================
    # WEBSITE
    # =====================================================

    if command in ["website", "🌐 طراحی سایت"]:

        send(
            chat_id,
            "🌐 طراحی سایت\n\n"
            "طراحی سایت‌های مدرن، واکنش‌گرا و اختصاصی.\n\n"
            "برای ثبت درخواست طراحی سایت روی «📋 ثبت سفارش» بزن.",
            services_keyboard()
        )

        return

    # =====================================================
    # APP
    # =====================================================

    if command in ["app", "📱 ساخت اپ"]:

        send(
            chat_id,
            "📱 ساخت اپلیکیشن\n\n"
            "توسعه اپلیکیشن و رابط کاربری اختصاصی.",
            services_keyboard()
        )

        return

    # =====================================================
    # AI
    # =====================================================

    if command in ["ai", "🤖 هوش مصنوعی"]:

        send(
            chat_id,
            "🤖 هوش مصنوعی\n\n"
            "طراحی و توسعه پروژه‌های مبتنی بر هوش مصنوعی.",
            services_keyboard()
        )

        return

    # =====================================================
    # CODING
    # =====================================================

    if command in ["coding", "💻 برنامه‌نویسی"]:

        send(
            chat_id,
            "💻 برنامه‌نویسی\n\n"
            "توسعه پروژه‌های وب، نرم‌افزاری و ربات.",
            services_keyboard()
        )

        return

    # =====================================================
    # ORDER
    # =====================================================

    if command in ["order", "📋 ثبت سفارش"]:

        start_order(chat_id)

        return

    # =====================================================
    # CONTACT
    # =====================================================

    if command in ["contact", "👨‍💻 ارتباط با ما"]:

        send(
            chat_id,
            "👨‍💻 ارتباط با Sepehr Studio\n\n"
            "پیام یا درخواست خود را ارسال کنید.",
            main_keyboard()
        )

        return

    # =====================================================
    # ABOUT
    # =====================================================

    if command in ["about", "ℹ️ درباره ما"]:

        send(
            chat_id,
            "🚀 Sepehr Studio\n\n"
            "طراحی سایت\n"
            "برنامه‌نویسی\n"
            "ساخت اپلیکیشن\n"
            "هوش مصنوعی\n\n"
            "💙 ساخته شده برای پروژه‌های خلاقانه.",
            main_keyboard()
        )

        return

    # =====================================================
    # BACK
    # =====================================================

    if command in ["back", "🔙 بازگشت"]:

        user_states.pop(chat_id, None)

        send(
            chat_id,
            "🏠 منوی اصلی:",
            main_keyboard()
        )

        return

    # =====================================================
    # UNKNOWN
    # =====================================================

    if text:

        send(
            chat_id,
            "❓ این گزینه را متوجه نشدم.\n\n"
            "از کیبورد زیر استفاده کن:",
            main_keyboard()
        )


# =========================================================
# RUN
# =========================================================

def run():

    print(
        "🚀 Sepehr Studio Bot started!",
        flush=True
    )

    print(
        f"👤 Admin Chat ID: {ADMIN_CHAT_ID}",
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

            result = api(
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
                f"🔄 Updates received: {len(updates)}",
                flush=True
            )

            # پردازش آپدیت‌ها
            for update in updates:

                try:

                    handle_update(update)

                except Exception as e:

                    print(
                        f"[UPDATE ERROR] {e}",
                        flush=True
                    )

            # بسیار مهم:
            # بعد از پردازش، offset جدید را می‌گیریم
            next_offset = data.get(
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


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    run()
