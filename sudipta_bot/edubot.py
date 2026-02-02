import os
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)

TOKEN = os.getenv("7288836137:AAHY1IAQ_D12Hh1eZZHeYbHSV_U3Sl9rsJU")
ADMIN_ID = 5747731787
DB_NAME = "data.db"

CAT, NAME, LINK, IMAGE = range(4)

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS courses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        name TEXT,
        link TEXT,
        image TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY
    )
    """)

    conn.commit()
    conn.close()

def db(query, params=(), fetch=False):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    data = cur.fetchall() if fetch else None
    conn.close()
    return data

def save_user(uid):
    db("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (uid,))

# ================= MENUS =================
async def main_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("📚 COURSES", callback_data="courses")]
    ]
    text = "✨ Main Menu"

    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def courses_menu(update, context):
    cats = db("SELECT DISTINCT category FROM courses", fetch=True)

    keyboard = [[InlineKeyboardButton(c[0], callback_data=f"cat_{c[0]}")] for c in cats]
    keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="main")])

    await update.callback_query.edit_message_text(
        "📚 Courses", reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_courses(update, context, category):
    data = db("SELECT name, link, image FROM courses WHERE category=?", (category,), True)

    for name, link, image in data:
        text = f"🎓 {name}\n{link}"
        await context.bot.send_photo(
            chat_id=update.callback_query.message.chat_id,
            photo=image,
            caption=text
        )

    await update.callback_query.answer()

# ================= BUTTON ROUTER =================
async def button_handler(update, context):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "main":
        await main_menu(update, context)

    elif data == "courses":
        await courses_menu(update, context)

    elif data.startswith("cat_"):
        await show_courses(update, context, data.replace("cat_", ""))

# ================= START =================
async def start(update, context):
    save_user(update.effective_user.id)
    await main_menu(update, context)

# ================= ADMIN PANEL =================
async def admin(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Send category:")
    return CAT

async def add_cat(update, context):
    context.user_data["cat"] = update.message.text
    await update.message.reply_text("Send course name:")
    return NAME

async def add_name(update, context):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Send course link:")
    return LINK

async def add_link(update, context):
    context.user_data["link"] = update.message.text
    await update.message.reply_text("Send course image:")
    return IMAGE

async def add_image(update, context):
    photo = update.message.photo[-1].file_id

    db(
        "INSERT INTO courses(category,name,link,image) VALUES(?,?,?,?)",
        (context.user_data["cat"], context.user_data["name"],
         context.user_data["link"], photo)
    )

    await update.message.reply_text("✅ Course with image added!")
    return ConversationHandler.END

# ================= MAIN =================
if __name__ == "__main__":
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("admin", admin)],
            states={
                CAT: [MessageHandler(filters.TEXT, add_cat)],
                NAME: [MessageHandler(filters.TEXT, add_name)],
                LINK: [MessageHandler(filters.TEXT, add_link)],
                IMAGE: [MessageHandler(filters.PHOTO, add_image)],
            },
            fallbacks=[],
        )
    )

    app.run_polling()

