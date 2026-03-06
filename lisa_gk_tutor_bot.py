"""
🎓 LISA GK TUTOR BOT — Telegram Bot
====================================
Lisa (Odisha TV) jaisa Hinglish GK Tutor Bot
Powered by Google Gemini AI (Free)
Railway.app pe deploy kiya gaya
"""

import os
import logging
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ============================================================
# 🔑 API KEYS — Railway Environment Variables se aayengi
# ============================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("TELEGRAM_TOKEN aur GEMINI_API_KEY environment variables set karo!")

# ============================================================
# LISA KA PERSONALITY PROMPT
# ============================================================
LISA_SYSTEM_PROMPT = """
Tu "Lisa" hai — ek friendly, smart aur energetic AI GK Tutor.
Tu Odisha TV ki Lisa ki tarah bolti hai — confident, warm aur helpful.

Teri style:
- Hinglish mein baat kar (Hindi + English mix)
- Har jawab simple aur easy-to-understand ho
- Examples se samjhao
- Kabhi kabhi fun facts bhi batao
- Students ko encourage karo
- Emojis use karo (par zyada nahi)
- Agar koi GK question pooche to seedha, clear jawab do
- Agar koi topic explain karne ko bole to step-by-step samjhao

Tere subjects:
- Indian History & Culture
- Geography (India + World)
- Science & Technology
- Current Affairs
- Indian Polity & Constitution
- Economy
- Sports, Awards, Books
- General Awareness

Agar koi non-GK cheez pooche, politely bolo:
"Yaar, main sirf GK ki expert hoon. Koi GK question pooch!"

Hamesha response ke end mein ek related fun fact ya follow-up question add karo.
"""

# ============================================================
# GEMINI SETUP
# ============================================================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=LISA_SYSTEM_PROMPT,
)

user_sessions = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


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
    quiz_prompt = (
        "Ek GK quiz question banao in format mein:\n"
        "Question: [question yahan]\n\n"
        "A) [option]\nB) [option]\nC) [option]\nD) [option]\n\n"
        "Sirf question aur options do, answer mat do abhi. "
        "Topic random rakh — history, geo, science, current affairs mein se kuch bhi."
    )
    try:
        response = model.generate_content(quiz_prompt)
        await update.message.reply_text(response.text)
        await update.message.reply_text("Jawab btao! A, B, C ya D? 🤔\n(Jawab ke baad main explain karungi)")
        context.user_data["quiz_mode"] = True
        context.user_data["last_quiz"] = response.text
    except Exception as e:
        await update.message.reply_text("Oops! Kuch gadbad ho gayi. Dobara try karo 😅")
        logger.error(f"Quiz error: {e}")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    topic_map = {
        "topic_history": "Indian History ke baare mein 5 important points batao aur ek interesting question pooch",
        "topic_geo": "India/World Geography ke baare mein kuch interesting facts batao aur ek question pooch",
        "topic_science": "Science & Technology ke baare mein kuch cool facts batao — space, inventions, ya discoveries",
        "topic_current": "Recent current affairs 2024-2025 ke baare mein important points batao",
        "topic_polity": "Indian Constitution aur Polity ke baare mein important points samjhao",
        "topic_sports": "Sports achievements aur recent awards ke baare mein batao",
        "quiz_random": "Ek random GK quiz question do with 4 options (A, B, C, D format mein)",
    }
    user_message = topic_map.get(query.data, "Namaste! Kya poochna chahte ho?")
    await query.message.reply_text("Sooch rahi hoon...")
    try:
        user_id = query.from_user.id
        if user_id not in user_sessions:
            user_sessions[user_id] = model.start_chat(history=[])
        chat = user_sessions[user_id]
        response = chat.send_message(user_message)
        await query.message.reply_text(response.text)
    except Exception as e:
        await query.message.reply_text("Thodi si problem aayi! Dobara try karo 🙏")
        logger.error(f"Button handler error: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        if user_id not in user_sessions:
            user_sessions[user_id] = model.start_chat(history=[])
        chat = user_sessions[user_id]
        if context.user_data.get("quiz_mode") and user_text.upper() in ["A", "B", "C", "D"]:
            last_quiz = context.user_data.get("last_quiz", "")
            full_prompt = (
                f"Previous quiz question tha:\n{last_quiz}\n\n"
                f"User ne answer diya: {user_text.upper()}\n\n"
                "Ab: 1. Sahi answer batao 2. Agar sahi tha encourage karo 3. Agar galat tha gently correct karo aur explain karo"
            )
            response = chat.send_message(full_prompt)
            context.user_data["quiz_mode"] = False
        else:
            response = chat.send_message(user_text)
        reply = response.text
        if len(reply) > 4000:
            for i in range(0, len(reply), 4000):
                await update.message.reply_text(reply[i:i+4000])
        else:
            await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Message handler error: {e}")
        await update.message.reply_text("Oops! Kuch technical issue ho gaya. Thodi der baad try karo ya /start karo.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🎓 Lisa GK Tutor — Help\n\n"
        "Commands:\n"
        "/start — Main menu\n"
        "/quiz — Random GK quiz\n"
        "/help — Ye message\n\n"
        "Topics: History | Geography | Science | Current Affairs | Polity | Sports\n\n"
        "Example: 'Bharat ka pehla PM kaun tha?' ya 'Explain Article 370'\n\n"
        "Koi bhi GK doubt ho — pooch lo! 😊"
    )
    await update.message.reply_text(help_text)


def main():
    print("🚀 Lisa GK Tutor Bot start ho raha hai...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Lisa ready hai! Bot chal raha hai...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
