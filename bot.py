import os, time, requests, sqlite3, textwrap, subprocess
from openai import OpenAI

# ----- توکن‌ها (Hard-coded) -----
BOT_TOKEN = "7492207364:AAHsss6qyoGpcy3q-w9JcdH1oB4sFswpOq4"
OPENROUTER_API_KEY = "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"

URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# ----- تنظیم دیتابیس SQLite -----
db_path = os.path.join(os.path.dirname(__file__), "my_database.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS links (id INTEGER PRIMARY KEY, link TEXT, text TEXT)''')
conn.commit()

# ----- ساخت کلاینت OpenAI -----
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)

# ----- توابع کمکی -----
def get_updates(offset=None):
    try:
        r = requests.get(URL + "getUpdates", params={"timeout": 100, "offset": offset})
        return r.json()
    except Exception as e:
        print("خطا در دریافت آپدیت:", e)
        return {}

def send_message(chat_id, text):
    try:
        requests.post(URL + "sendMessage", data={"chat_id": chat_id, "text": text})
        time.sleep(0.35)
    except Exception as e:
        print("خطا در ارسال پیام:", e)

def split_text(text, max_length=4096):
    return textwrap.wrap(text, max_length)

def send_long_text(chat_id, text):
    for part in split_text(text):
        send_message(chat_id, part)

def get_record_by_id(code):
    cursor.execute("SELECT * FROM links WHERE id = ?", (code,))
    return cursor.fetchone()

def get_record_count():
    cursor.execute("SELECT COUNT(*) FROM links")
    return cursor.fetchone()[0]

# ----- مدل‌های هوش مصنوعی -----
AI_MODELS = [
    "meta-llama/llama-3-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "openai/gpt-oss-20b:free"
]

def analyze_with_ai(text):
    prompt = (
        "You are a helpful assistant. Analyze the following news text and summarize it in Persian:\n\n"
        f"{text}"
    )
    for model in AI_MODELS:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
            )
            ai_text = resp.choices[0].message.content.strip()
            if ai_text:
                print(f"✅ پاسخ از مدل {model} دریافت شد.")
                return ai_text
        except Exception as e:
            print(f"⚠️ خطا در مدل {model}: {e}")
    return "❌ همه مدل‌ها پاسخ ندادند."

# ----- تابع جدید برای اجرای scraper.py -----
def run_scraper_script():
    try:
        script_path = os.path.join(os.path.dirname(__file__), "get.py")
        result = subprocess.run(["python", script_path], capture_output=True, text=True, timeout=300)
        output = result.stdout.strip()
        return output if output else "✅ جمع‌آوری انجام شد."
    except Exception as e:
        return f"❌ خطا در اجرای اسکریپت جمع‌آوری: {e}"

# ----- حلقه اصلی -----
def main():
    update_id, waiting_for_code = None, {}
    while True:
        updates = get_updates(offset=update_id)
        if "result" not in updates:
            time.sleep(1)
            continue

        for item in updates["result"]:
            update_id = item["update_id"] + 1
            msg = item.get("message", {})
            chat_id = msg.get("chat", {}).get("id")
            text = msg.get("text", "")

            if not chat_id or not text:
                continue

            # --- دستور /start ---
            if text == "/start":
                count = get_record_count()
                send_message(chat_id, f"سلام 👋\nدر حال حاضر {count} خبر در دیتابیس موجود است.\n\nبرای جمع‌آوری جدید دستور /new_get را بفرست.")

            # --- دستور /new_get ---
            elif text == "/new_get":
                send_message(chat_id, "🔄 در حال جمع‌آوری خبرهای جدید...")
                result_text = run_scraper_script()
                new_count = get_record_count()
                send_message(chat_id, f"{result_text}\n📊 اکنون {new_count} خبر در دیتابیس موجود است.")

            # --- حالت وارد کردن ID خبر ---
            elif text.isdigit():
                rec = get_record_by_id(int(text))
                if rec:
                    link, news_text = rec[1], rec[2]
                    send_message(chat_id, f"📎 لینک: {link}\nدر حال تحلیل با هوش مصنوعی...")
                    ai_summary = analyze_with_ai(news_text)
                    send_long_text(chat_id, ai_summary)
                else:
                    send_message(chat_id, "❌ کدی با این شماره یافت نشد.")

            else:
                send_message(chat_id, "دستور ناشناخته است. از /start یا /new_get استفاده کن.")
        time.sleep(1)

if __name__ == "__main__":
    main()
