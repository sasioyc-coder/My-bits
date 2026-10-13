from flask import Flask, send_from_directory, request, jsonify
import threading, time, requests, json, os
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# --- CONFIGURE THESE TWO ---
BOT_TOKEN = "8863907078:AAG8b5l4kzYMUphv1OEIIV2oTipud4TzGhI"
RENDER_URL = "https://YOUR-RENDER-NAME.onrender.com"
# ---------------------------

app = Flask(__name__)
DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

def get_user(user_id):
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {"coins": 0, "referrals": 0, "referred_by": None}
        save_db(db)
    return db[uid]

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/api/user')
def api_user():
    user_id = request.args.get('user_id', '0')
    user = get_user(user_id)
    return jsonify(user)

@app.route('/api/add_coins', methods=['POST'])
def api_add_coins():
    data = request.json
    user_id = str(data.get('user_id'))
    amount = int(data.get('amount', 0))
    db = load_db()
    if user_id not in db:
        db[user_id] = {"coins": 0, "referrals": 0, "referred_by": None}
    db[user_id]['coins'] += amount
    save_db(db)
    return jsonify(db[user_id])

# --- TELEGRAM BOT WITH REFERRAL LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    db = load_db()

    if user_id not in db:
        db[user_id] = {"coins": 0, "referrals": 0, "referred_by": None}
        # Check referral
        if args and args[0].startswith("ref_"):
            referrer_id = args[0].replace("ref_", "")
            if referrer_id!= user_id and referrer_id in db:
                db[user_id]["referred_by"] = referrer_id
                db[referrer_id]["coins"] += 100
                db[referrer_id]["referrals"] += 1
        save_db(db)

    keyboard = [
        [InlineKeyboardButton("Open App", web_app=WebAppInfo(url=f"{RENDER_URL}"))]
    ]
    text = (
        f"Welcome to Mini Earn Bot!\n\n"
        f"Your ID: {user_id}\n"
        f"Balance: {db[user_id]['coins']} Coins\n"
        f"Referrals: {db[user_id]['referrals']}\n\n"
        f"Watch Ads and Invite Friends to Earn.\n"
        f"Your Referral Link:\n"
        f"https://t.me/mini_uearn_bot?start=ref_{user_id}"
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

def keep_alive():
    while True:
        time.sleep(600)
        try:
            requests.get(RENDER_URL)
        except:
            pass

if __name__ == '__main__':
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)
