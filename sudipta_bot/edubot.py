import os
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler

TOKEN ="7288836137:AAHY1IAQ_D12Hh1eZZHeYbHSV_U3Sl9rsJU"
ADMIN_ID = 5747731787  # put your telegram IDf

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
def main_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("📚 COURSES", callback_data="courses")]
    ]
    update.message.reply_text(
        "✨ Main Menu",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def courses_menu(update, context):
    query = update.callback_query
    cats = db("SELECT DISTINCT category FROM courses", fetch=True)

    keyboard = [[InlineKeyboardButton(c[0], callback_data=f"cat_{c[0]}")] for c in cats]
    keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="main")])

    query.edit_message_text(
        "📚 Courses",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_courses(update, context, category):
    query = update.callback_query
    data = db("SELECT name, link, image FROM courses WHERE category=?", (category,), True)

    for name, link, image in data:
        text = f"🎓 {name}\n{link}"
        context.bot.send_photo(query.message.chat_id, photo=image, caption=text)

    query.answer()

# ================= BUTTON ROUTER =================
def button_handler(update, context):
    query = update.callback_query
    data = query.data

    if data == "main":
        query.message.delete()
        main_menu(update, context)

    elif data == "courses":
        courses_menu(update, context)

    elif data.startswith("cat_"):
        show_courses(update, context, data.replace("cat_", ""))

# ================= START =================
def start(update, context):
    main_menu(update, context)

# ================= ADMIN PANEL =================
def admin(update, context):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    update.message.reply_text("Send category:")
    return CAT

def add_cat(update, context):
    context.user_data["cat"] = update.message.text
    update.message.reply_text("Send course name:")
    return NAME

def add_name(update, context):
    context.user_data["name"] = update.message.text
    update.message.reply_text("Send course link:")
    return LINK

def add_link(update, context):
    context.user_data["link"] = update.message.text
    update.message.reply_text("Send image:")
    return IMAGE

def add_image(update, context):
    photo = update.message.photo[-1].file_id

    db(
        "INSERT INTO courses(category,name,link,image) VALUES(?,?,?,?)",
        (context.user_data["cat"], context.user_data["name"], context.user_data["link"], photo)
    )

    update.message.reply_text("✅ Course added!")
    return ConversationHandler.END

# ================= MAIN =================
init_db()

updater = Updater(TOKEN)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CallbackQueryHandler(button_handler))

conv = ConversationHandler(
    entry_points=[CommandHandler("admin", admin)],
    states={
        CAT: [MessageHandler(Filters.text, add_cat)],
        NAME: [MessageHandler(Filters.text, add_name)],
        LINK: [MessageHandler(Filters.text, add_link)],
        IMAGE: [MessageHandler(Filters.photo, add_image)],
    },
    fallbacks=[]
)

dp.add_handler(conv)

updater.start_polling()
updater.idle()
