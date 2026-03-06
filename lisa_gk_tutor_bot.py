"""
🎓 LISA GK TUTOR BOT — Telegram Bot
Railway.app pe deploy | New google-genai package
"""

import os
import logging
from google import genai
from google.genai import types
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)

# API KEYS
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("TELEGRAM_TOKEN aur GEMINI_API_KEY environment variables set karo!")

# GEMINI SETUP (new SDK)
client = genai.Client(api_key=GEMINI_API_KEY)

LISA_SYSTEM_PROMPT = """
Tu "Lisa" hai — ek friendly, smart aur energetic AI GK Tutor.
Hinglish mein baat kar (Hindi + English mix).
Har jawab simple, clear aur easy-to-understand ho.
Examples se samjhao, students ko encourage karo, emojis use karo (par zyada nahi).

Tere subjects: Indian History, Geography, Science & Technology,
Current Affairs, Indian Polity & Constitution, Economy, Sports & Awards.

Agar koi non-GK cheez pooche: "Yaar, main sirf GK ki expert hoon. Koi GK question pooch!"
Hamesha response ke end mein ek fun fact ya follow-up question add karo.
"""

# Per-user chat history (list of dicts)
user_histories = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def ask_lisa(user_id: int, user_text: str) -> str:
    """Gemini se response lo, history maintain karo."""
    if user_id not in user_histories:
        user_histories[user_id] = []

    # User message add karo history mein
    user_histories[user_id].append(
        types.Content(role="user", parts=[types.Part(text=user_text)])
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(system_instruction=LISA_SYSTEM_PROMPT),
        contents=user_histories[user_id],
    )

    reply = response.text

    # Assistant reply bhi history mein save karo
    user_histories[user_id].append(
        types.Content(role="model", parts=[types.Part(text=reply)])
    )

    # History zyada badi na ho — last 20 messages rakh
    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]

    return reply


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
        "✅ Topics clearly samjhana\n"
        "✅ Quiz & Practice\n"
        "✅ Exam preparation tips\n\n"
        "Koi bhi GK question pooch, ya niche se topic select kar! 👇"
    )
    await update.message.reply_text(welcome_msg, reply_markup=reply_markup)


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎯 Ek second... main ek question dhundh rahi hoon!")
    try:
        user_id = update.effective_user.id
        quiz_prompt = (
            "Ek GK quiz question banao:\n"
            "Question: [question]\n"
            "A) ...\nB) ...\nC) ...\nD) ...\n\n"
            "Sirf question aur options do, answer mat do."
        )
        reply = ask_lisa(user_id, quiz_prompt)
        await update.message.reply_text(reply)
        await update.message.reply_text("Jawab btao! A, B, C ya D? 🤔")
        context.user_data["quiz_mode"] = True
        context.user_data["last_quiz"] = reply
    except Exception as e:
        logger.error(f"Quiz error: {type(e).__name__}: {e}")
        await update.message.reply_text(f"Error: {type(e).__name__}: {str(e)[:300]}")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    topic_map = {
        "topic_history": "Indian History ke 5 interesting points batao aur ek question pooch",
        "topic_geo": "India/World Geography ke interesting facts batao aur ek question pooch",
        "topic_science": "Science & Technology ke cool facts batao — space, inventions, discoveries",
        "topic_current": "Recent current affairs 2024-2025 ke important points batao",
        "topic_polity": "Indian Constitution aur Polity ke important points samjhao",
        "topic_sports": "Recent sports achievements aur awards ke baare mein batao",
        "quiz_random": "Ek random GK quiz question do with 4 options (A, B, C, D)",
    }
    user_message = topic_map.get(query.data, "Namaste!")
    await query.message.reply_text("Sooch rahi hoon... ⏳")
    try:
        user_id = query.from_user.id
        reply = ask_lisa(user_id, user_message)
        await query.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Button error: {type(e).__name__}: {e}")
        await query.message.reply_text(f"Error: {type(e).__name__}: {str(e)[:300]}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        if context.user_data.get("quiz_mode") and user_text.upper() in ["A", "B", "C", "D"]:
            last_quiz = context.user_data.get("last_quiz", "")
            prompt = (
                f"Quiz question tha:\n{last_quiz}\n\n"
                f"User ka answer: {user_text.upper()}\n\n"
                "Sahi answer batao, explain karo, aur encourage karo."
            )
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
        logger.error(f"Message error: {type(e).__name__}: {e}")
        await update.message.reply_text(f"Error: {type(e).__name__}: {str(e)[:300]}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎓 Lisa GK Tutor — Help\n\n"
        "/start — Main menu\n"
        "/quiz — Random GK quiz\n"
        "/help — Ye message\n\n"
        "Topics: History | Geography | Science | Current Affairs | Polity | Sports\n\n"
        "Koi bhi GK doubt ho — seedha type karo! 😊"
    )


def main():
    print("🚀 Lisa GK Tutor Bot (new SDK) start ho raha hai...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Lisa ready hai!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
