import os
import time
import requests

TOKEN = os.getenv("RUBIKA_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("RUBIKA_BOT_TOKEN is not configured.")

API = f"https://botapi.rubika.ir/v3/{TOKEN}"


def call_api(method, payload=None):
    try:
        response = requests.post(
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
            print(f"[API ERROR] {result}", flush=True)

        return result

    except Exception as error:
        print(f"[NETWORK ERROR] {error}", flush=True)
        return {}


def send_text(chat_id, text):
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    print("[SEND] Sending message...", flush=True)

    return call_api("sendMessage", payload)


def process_update(update):
    if not isinstance(update, dict):
        return

    chat_id = update.get("chat_id")
    message = update.get("new_message")

    if not chat_id or not isinstance(message, dict):
        return

    text = message.get("text") or ""
    text = text.strip()

    print(
        f"[MESSAGE] chat={chat_id} text={text!r}",
        flush=True
    )

    if text in ("/start", "start", "شروع"):
        send_text(
            chat_id,
            "🚀 سلام!\n\n"
            "به Sepehr Studio خوش آمدید. 🤖\n\n"
            "بات با موفقیت آنلاین است."
        )

    elif text == "/test":
        send_text(
            chat_id,
            "✅ تست موفق بود!\n\n"
            "Sepehr Studio Bot فعال است."
        )

    elif text:
        send_text(
            chat_id,
            f"📩 پیام شما دریافت شد:\n\n{text}"
        )


def run():
    print("🚀 Sepehr Studio Bot started!", flush=True)

    offset_id = None

    while True:
        try:
            payload = {
                "limit": 10
            }

            if offset_id:
                payload["offset_id"] = offset_id

            result = call_api("getUpdates", payload)

            data = result.get("data", {})

            if not isinstance(data, dict):
                data = {}

            updates = data.get("updates", [])

            print(
                f"[UPDATES] {len(updates)} update(s)",
                flush=True
            )

            for update in updates:
                process_update(update)

            next_offset_id = data.get("next_offset_id")

            if next_offset_id:
                offset_id = str(next_offset_id)

        except Exception as error:
            print(f"[BOT ERROR] {error}", flush=True)

        time.sleep(2)


if __name__ == "__main__":
    run()
