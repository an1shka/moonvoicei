import asyncio
import json
import os
from dotenv import load_dotenv

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
print("TOKEN:", repr(TOKEN))
ADMIN_ID = 6768745428

DATA_FILE = "data/applications.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def main_menu():
    return ReplyKeyboardMarkup(
        [
            ["🎙️ Кастинги", "🎬 Проекты"],
            ["📜 Правила", "💌 Отправить работу"],
            ["❓ FAQ", "🆘 Помощь"]
        ],
        resize_keyboard=True
    )


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    await update.message.reply_text(
        f"""🌙 Добро пожаловать, {user.first_name}!

Этот бот поможет вам:
🎙️ Узнать о кастингах
🎬 Посмотреть проекты
📜 Правила студии
💌 Отправить работу
❓ FAQ

✨ Приятного пользования!""",
        reply_markup=main_menu()
    )


# ---------------- HELP ----------------
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """🆘 Помощь:

🎙️ Кастинги
🎬 Проекты
📜 Правила
💌 Отправить работу
❓ FAQ""",
        reply_markup=main_menu()
    )


# ---------------- STATIC PAGES ----------------
async def casting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """🎙️ Актуальные кастинги:

🌸 Адский рай — Габимару
⚔️ Клинок — Тандзиро, Геня

✨ Обращайтесь к администрации""",
    )


async def projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """🎬 Проекты студии:

⚔️ Клинок, рассекающий демонов
🪼 Адский рай

🌙 Moon_Voice""",
    )


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """📜 Правила:

🌙 Уважение
🎙️ Сдача вовремя
💌 Сообщать проблемы
🪼 Без конфликтов
✨ Соблюдение правил Telegram""",
    )


async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """❓ FAQ:

🎙️ Опыт не нужен
🌸 Возраст не важен
🎬 Через кастинг
⏳ 20–60 мин в неделю""",
    )


# ---------------- SEND WORK FLOW ----------------
async def sendwork(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["step"] = "name"
    context.user_data["voices"] = []

    await update.message.reply_text("🌸 Введите ваш ник или имя:")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    step = context.user_data.get("step")

    # -------- NAME --------
    if step == "name":
        context.user_data["name"] = text
        context.user_data["step"] = "role"
        await update.message.reply_text("🎭 Укажите роль:")
        return

    # -------- ROLE --------
    if step == "role":
        context.user_data["role"] = text
        context.user_data["step"] = "voice"
        await update.message.reply_text("🎙️ Отправьте 1-ю озвучку:")
        return

    await update.message.reply_text("Используйте меню 👇", reply_markup=main_menu())


# ---------------- VOICE HANDLER ----------------
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")

    if step != "voice":
        return

    file_id = update.message.voice.file_id if update.message.voice else update.message.audio.file_id

    voices = context.user_data.get("voices", [])
    voices.append(file_id)
    context.user_data["voices"] = voices

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Добавить ещё", callback_data="add_voice"),
            InlineKeyboardButton("📩 Отправить", callback_data="send_admin")
        ],
        [
            InlineKeyboardButton("❌ Отменить", callback_data="cancel")
        ]
    ])

    await update.message.reply_text(
        f"🎙️ Озвучка {len(voices)} получена!\n\nЧто дальше?",
        reply_markup=keyboard
    )


# ---------------- CALLBACK BUTTONS ----------------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # ADD MORE VOICE
    if data == "add_voice":
        await query.message.reply_text("🎙️ Отправьте следующую озвучку:")
        return

    # SEND TO ADMIN
    if data == "send_admin":
        user = update.effective_user

        name = context.user_data.get("name")
        role = context.user_data.get("role")
        voices = context.user_data.get("voices", [])

        text = f"""🌙 НОВАЯ ЗАЯВКА

🌸 Ник: {name}
🎭 Роль: {role}
👤 @{user.username}
🆔 {user.id}

🎙️ Озвучки: {len(voices)}"""

        # send to admin
        await context.bot.send_message(ADMIN_ID, text)

        for v in voices:
            await context.bot.send_voice(ADMIN_ID, v)

        # save
        data = load_data()
        data.append({
            "name": name,
            "role": role,
            "user_id": user.id,
            "voices": voices
        })
        save_data(data)

        await query.message.reply_text("✨ Заявка отправлена!")
        context.user_data.clear()
        return

    # CANCEL
    if data == "cancel":
        context.user_data.clear()
        await query.message.reply_text("❌ Отменено")
        return


# ---------------- ROUTER ----------------
async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🎙️ Кастинги":
        await casting(update, context)
    elif text == "🎬 Проекты":
        await projects(update, context)
    elif text == "📜 Правила":
        await rules(update, context)
    elif text == "❓ FAQ":
        await faq(update, context)
    elif text == "💌 Отправить работу":
        await sendwork(update, context)
    elif text == "🆘 Помощь":
        await help_cmd(update, context)
    else:
        await handle_message(update, context)


# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_router))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))

    app.add_handler(CallbackQueryHandler(buttons))

    print("Bot started...")
    app.run_polling()


asyncio.set_event_loop(asyncio.new_event_loop())

if __name__ == "__main__":
    main()
