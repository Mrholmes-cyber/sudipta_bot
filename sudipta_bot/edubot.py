import os
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

TOKEN = "7288836137:AAHY1IAQ_D12Hh1eZZHeYbHSV_U3Sl9rsJU"
ADMIN_ID = 5747731787  # put your telegram ID here

DB = "data.db"

CAT, NAME, LINK, IMAGE = range(4)

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect(DB)
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
    conn.commit()
    conn.close()

def db(query, params=(), fetch=False):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    data = cur.fetchall() if fetch else None
    conn.close()
    return data

# ================= MENUS =================
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📚 COURSES", callback_data="courses")]]
    text = "✨ Main Menu"

    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def courses_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    cats = db("SELECT DISTINCT category FROM courses", fetch=True)

    keyboard = [[InlineKeyboardButton(c[0], callback_data=f"cat_{c[0]}")] for c in cats]
    keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="main")])

    await query.edit_message_text("📚 Courses", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_courses(update: Update, context: ContextTypes.DEFAULT_TYPE, category):
    query = update.callback_query
    data = db("SELECT name, link, image FROM courses WHERE category=?", (category,), True)

    for name, link, image in data:
        text = f"🎓 {name}\n{link}"
        await context.bot.send_photo(query.message.chat_id, photo=image, caption=text)

    await query.answer()

# ================= BUTTON ROUTER =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    await q.answer()

    if data == "main":
        await main_menu(update, context)

    elif data == "courses":
        await courses_menu(update, context)

    elif data.startswith("cat_"):
        await show_courses(update, context, data.replace("cat_", ""))

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await main_menu(update, context)

# ================= ADMIN PANEL =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    await update.message.reply_text("Send category:")
    return CAT

async def add_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cat"] = update.message.text
    await update.message.reply_text("Send course name:")
    return NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Send course link:")
    return LINK

async def add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["link"] = update.message.text
    await update.message.reply_text("Send image:")
    return IMAGE

async def add_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1].file_id

    db(
        "INSERT INTO courses(category,name,link,image) VALUES(?,?,?,?)",
        (context.user_data["cat"], context.user_data["name"], context.user_data["link"], photo)
    )

    await update.message.reply_text("✅ Course added!")
    return ConversationHandler.END

# ================= MAIN =================
init_db()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

conv = ConversationHandler(
    entry_points=[CommandHandler("admin", admin)],
    states={
        CAT: [MessageHandler(filters.TEXT, add_cat)],
        NAME: [MessageHandler(filters.TEXT, add_name)],
        LINK: [MessageHandler(filters.TEXT, add_link)],
        IMAGE: [MessageHandler(filters.PHOTO, add_image)],
    },
    fallbacks=[]
)

app.add_handler(conv)

app.run_polling()
