"""
🎓 LISA GK TUTOR BOT — Telegram Bot
Powered by Groq AI + Real-time News (NewsAPI)
Railway.app pe deploy
"""

import os
import logging
import requests
from datetime import datetime
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)

# API KEYS
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY")
NEWS_API_KEY   = os.environ.get("NEWS_API_KEY")   # newsapi.org se free mein milega

if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    raise ValueError("TELEGRAM_TOKEN aur GROQ_API_KEY environment variables set karo!")

# GROQ CLIENT
client = Groq(api_key=GROQ_API_KEY)

LISA_SYSTEM_PROMPT = """
Tu "Lisa" hai — ek friendly, smart aur energetic AI GK Tutor.
Hinglish mein baat kar (Hindi + English mix).
Har jawab simple, clear aur easy-to-understand ho.
Examples se samjhao, students ko encourage karo, emojis use karo (par zyada nahi).

Tere subjects: Indian History, Geography, Science & Technology,
Current Affairs, Indian Polity & Constitution, Economy, Sports & Awards.

Agar koi non-GK cheez pooche: "Yaar, main sirf GK ki expert hoon. Koi GK question pooch!"
Hamesha response ke end mein ek fun fact ya follow-up question add karo.

IMPORTANT: Agar real-time news context diya gaya ho to usi pe base karke jawab do.
Purani information mat do jab current affairs poochha jaye.
"""

user_histories = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ============================================================
# REAL-TIME NEWS FETCH
# ============================================================
def get_latest_news(query: str = "India") -> str:
    """NewsAPI se latest news fetch karo."""
    if not NEWS_API_KEY:
        return ""
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 5,
            "apiKey": NEWS_API_KEY,
        }
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        if data.get("status") != "ok":
            return ""
        articles = data.get("articles", [])
        if not articles:
            return ""
        news_text = f"Latest News ({datetime.now().strftime('%d %b %Y')}):\n"
        for i, a in enumerate(articles[:5], 1):
            title = a.get("title", "")
            source = a.get("source", {}).get("name", "")
            published = a.get("publishedAt", "")[:10]
            news_text += f"{i}. [{source} | {published}] {title}\n"
        return news_text
    except Exception as e:
        logger.error(f"News fetch error: {e}")
        return ""


def is_current_affairs_query(text: str) -> bool:
    """Check karo ki user current affairs pooch raha hai ya nahi."""
    keywords = [
        "current", "latest", "recent", "today", "news", "2024", "2025", "2026",
        "abhi", "aaj", "nayi", "naya", "kal", "haal", "abhi tak",
        "prime minister", "president", "election", "award", "winner",
        "championship", "match", "score", "appointed", "resigned", "died",
        "launched", "scheme", "budget", "policy"
    ]
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


# ============================================================
# MAIN AI FUNCTION
# ============================================================
def ask_lisa(user_id: int, user_text: str) -> str:
    """Groq se response lo — current affairs ke liye real news inject karo."""
    if user_id not in user_histories:
        user_histories[user_id] = []

    # Current affairs query hai to live news fetch karo
    news_context = ""
    if is_current_affairs_query(user_text):
        news_context = get_latest_news(user_text)
        logger.info(f"News fetched for query: {user_text[:50]}")

    # News context ko user message ke saath inject karo
    if news_context:
        enriched_text = (
            f"{news_context}\n\n"
            f"Upar diye gaye latest news ke basis pe is sawaal ka jawab do:\n{user_text}"
        )
    else:
        enriched_text = user_text

    user_histories[user_id].append({"role": "user", "content": enriched_text})

    messages = [{"role": "system", "content": LISA_SYSTEM_PROMPT}] + user_histories[user_id]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=1024,
        temperature=0.7,
    )

    reply = response.choices[0].message.content
    user_histories[user_id].append({"role": "assistant", "content": reply})

    # Last 20 messages hi rakh
    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]

    return reply


# ============================================================
# TELEGRAM HANDLERS
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "dost"
    keyboard = [
        [InlineKeyboardButton("📚 History", callback_data="topic_history"),
         InlineKeyboardButton("🌍 Geography", callback_data="topic_geo")],
        [InlineKeyboardButton("🔬 Science", callback_data="topic_science"),
         InlineKeyboardButton("📰 Current Affairs", callback_data="topic_current")],
        [InlineKeyboardButton("⚖️ Polity", callback_data="topic_polity"),
         InlineKeyboardButton("🏆 Sports & Awards", callback_data="topic_sports")],
        [InlineKeyboardButton("🎯 Random Quiz!", callback_data="quiz_random")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_msg = (
        f"🎓 Namaste {user_name}! Main hoon Lisa, teri GK Tutor!\n\n"
        "Main tujhe help karungi:\n"
        "✅ GK questions ke jawab\n"
        "✅ Real-time Current Affairs 📰\n"
        "✅ Topics clearly samjhana\n"
        "✅ Quiz & Practice\n\n"
        "Koi bhi GK question pooch, ya niche se topic select kar! 👇"
    )
    await update.message.reply_text(welcome_msg, reply_markup=reply_markup)


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎯 Ek second... main ek question dhundh rahi hoon!")
    try:
        user_id = update.effective_user.id
        reply = ask_lisa(user_id,
            "Ek GK quiz question banao:\nQuestion: [question]\nA) ...\nB) ...\nC) ...\nD) ...\nSirf question aur options do, answer mat do abhi."
        )
        await update.message.reply_text(reply)
        await update.message.reply_text("Jawab btao! A, B, C ya D? 🤔")
        context.user_data["quiz_mode"] = True
        context.user_data["last_quiz"] = reply
    except Exception as e:
        logger.error(f"Quiz error: {e}")
        await update.message.reply_text(f"Error: {str(e)[:200]}")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    topic_map = {
        "topic_history": "Indian History ke 5 interesting points batao aur ek question pooch",
        "topic_geo": "India/World Geography ke interesting facts batao aur ek question pooch",
        "topic_science": "Science & Technology ke cool facts batao",
        "topic_current": "Latest current affairs India 2025-2026 ke important points batao",
        "topic_polity": "Indian Constitution aur Polity ke important points samjhao",
        "topic_sports": "Recent sports achievements aur awards ke baare mein batao",
        "quiz_random": "Ek random GK quiz question do with 4 options (A, B, C, D)",
    }
    user_message = topic_map.get(query.data, "Namaste!")
    await query.message.reply_text("Sooch rahi hoon... ⏳")
    try:
        reply = ask_lisa(query.from_user.id, user_message)
        await query.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Button error: {e}")
        await query.message.reply_text(f"Error: {str(e)[:200]}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        if context.user_data.get("quiz_mode") and user_text.upper() in ["A", "B", "C", "D"]:
            last_quiz = context.user_data.get("last_quiz", "")
            prompt = f"Quiz question tha:\n{last_quiz}\n\nUser ka answer: {user_text.upper()}\n\nSahi answer batao, explain karo, encourage karo."
            context.user_data["quiz_mode"] = False
            reply = ask_lisa(user_id, prompt)
        else:
            reply = ask_lisa(user_id, user_text)

        if len(reply) > 4000:
            for i in range(0, len(reply), 4000):
                await update.message.reply_text(reply[i:i+4000])
        else:
            await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Message error: {e}")
        await update.message.reply_text(f"Error: {str(e)[:200]}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎓 Lisa GK Tutor — Help\n\n"
        "/start — Main menu\n"
        "/quiz — Random GK quiz\n"
        "/help — Ye message\n\n"
        "Topics: History | Geography | Science | Current Affairs | Polity | Sports\n\n"
        "Real-time news se updated current affairs milegi! 📰\n"
        "Koi bhi GK doubt ho — seedha type karo! 😊"
    )


def main():
    print("🚀 Lisa GK Tutor Bot (Groq + Live News) start ho raha hai...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Lisa ready hai — Live news enabled!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
