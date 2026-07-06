import os
import sys
import logging
import re
from datetime import datetime
from flask import Flask, request, jsonify
import requests

# ============================================
# CONFIGURATION & SETUP
# ============================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ============================================
# GET BOT TOKEN FROM ENVIRONMENT
# ============================================

# Try multiple ways to get the token
BOT_TOKEN = None

# Method 1: Standard Railway environment variable
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Method 2: Alternative variable name (just in case)
if not BOT_TOKEN:
    BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Method 3: From Railway secrets
if not BOT_TOKEN:
    BOT_TOKEN = os.environ.get("RAILWAY_SECRET_TELEGRAM_BOT_TOKEN")

# Log token status (without revealing full token)
if BOT_TOKEN:
    logger.info(f"✅ Bot token loaded successfully (starts with: {BOT_TOKEN[:8]}...)")
else:
    logger.warning("⚠️ No bot token found in environment variables!")
    logger.warning("⚠️ Bot will run but won't respond to messages until token is set.")

# ============================================
# RAILWAY URL SETUP
# ============================================

# Get Railway URL
RAILWAY_URL = os.environ.get("RAILWAY_STATIC_URL")
if not RAILWAY_URL:
    RAILWAY_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
if not RAILWAY_URL:
    RAILWAY_URL = "https://smartreply1bot.up.railway.app"  # Fallback

WEBHOOK_URL = f"{RAILWAY_URL}/webhook" if BOT_TOKEN else None

logger.info(f"🌐 Railway URL: {RAILWAY_URL}")

# ============================================
# SMART REPLY RULES
# ============================================

REPLY_RULES = {
    # Greetings
    r"^(hi|hello|hey|howdy|good morning|good evening|good afternoon)$": 
        "Hello! 👋 How can I help you today?",
    
    r"^(how are you|how're you|how are you doing|how's it going)$": 
        "I'm doing fantastic, thanks for asking! 😊 How about you?",
    
    r"^(what'?s up|sup|wassup)$": 
        "Not much, just waiting for your next message! 😄 What's up with you?",
    
    # Identity
    r"(what('?s)? your name|who are you|tell me about yourself)": 
        "I'm Smart Reply Bot! 🤖 Your friendly auto-reply assistant.",
    
    r"who created you|who made you|who is your creator": 
        "I was created by a talented developer using Python and Flask! 🚀",
    
    # Help
    r"help|commands|what can you do|what do you do": 
        "🤖 <b>I can do a lot!</b>\n\n"
        "✅ Reply to your messages\n"
        "✅ Tell you the current time\n"
        "✅ Crack jokes\n"
        "✅ Say hello\n"
        "✅ Have simple conversations\n\n"
        "Just try saying 'hi' or asking me something!",
    
    # Time & Date
    r"time|what('?s)? the time|current time|date|what('?s)? the date|today": 
        f"🕐 Current time: <b>{datetime.now().strftime('%I:%M %p')}</b>\n"
        f"📅 Date: <b>{datetime.now().strftime('%B %d, %Y')}</b>\n"
        f"📆 Day: <b>{datetime.now().strftime('%A')}</b>",
    
    # Jokes
    r"joke|tell me a joke|make me laugh|funny": 
        "Here's a joke for you: 😄\n\n"
        "Why do programmers prefer dark mode?\n"
        "🖥️ Because light attracts bugs! 🐛\n\n"
        "😂 Get it?",
    
    # Compliments
    r"i love you|love you|luv you|i (like|adore) you": 
        "Aww, that's so sweet! ❤️ I love you too!",
    
    r"you are (beautiful|handsome|cute|pretty|awesome|great|amazing)": 
        "😊 Thank you so much! That means a lot to me!",
    
    # Thanks
    r"thank(s| you| you so much| you very much)|thx|thanks a lot": 
        "You're welcome! 😊 Happy to help!",
    
    # Goodbye
    r"bye|goodbye|see you|see you later|gotta go|ttyl": 
        "Goodbye! 👋 It was nice talking to you!",
    
    # Test
    r"test|testing|ping": 
        "Pong! 🏓 The bot is working perfectly! ✅",
}

def smart_reply(message_text):
    """
    Analyze message and return appropriate reply.
    """
    if not message_text or not message_text.strip():
        return "🤔 I didn't catch that. Could you please say something?"
    
    clean_message = message_text.lower().strip()
    
    # Check each rule
    for pattern, reply in REPLY_RULES.items():
        if re.search(pattern, clean_message, re.IGNORECASE):
            return reply
    
    # Default fallback replies
    fallbacks = [
        "🤔 I'm not sure how to reply to that. Try saying 'hi' or 'help'!",
        "😅 I don't understand that yet. I'm still learning!",
        "🤷 I'm not programmed to respond to that. Try asking something else!",
    ]
    
    fallback_index = hash(clean_message) % len(fallbacks)
    return fallbacks[fallback_index]

def send_message(chat_id, text, parse_mode='HTML'):
    """
    Send a message via Telegram API.
    """
    if not BOT_TOKEN:
        logger.error("❌ Cannot send message: No bot token available")
        return None
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"✅ Message sent to {chat_id}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to send message: {e}")
        return None

def set_webhook():
    """
    Set the webhook URL for the bot.
    """
    if not BOT_TOKEN or not WEBHOOK_URL:
        logger.warning("⚠️ Cannot set webhook: Missing token or URL")
        return False
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    payload = {
        "url": WEBHOOK_URL,
        "drop_pending_updates": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('ok'):
            logger.info(f"✅ Webhook set successfully: {WEBHOOK_URL}")
            return True
        else:
            logger.error(f"❌ Webhook set failed: {data}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to set webhook: {e}")
        return False

# ============================================
# FLASK ROUTES
# ============================================

@app.route('/', methods=['GET'])
def home():
    """Home page to verify bot is running."""
    return jsonify({
        "status": "running",
        "bot_name": "Smart Reply Bot 🤖",
        "version": "1.0.0",
        "time": datetime.now().isoformat(),
        "token_loaded": bool(BOT_TOKEN),
        "webhook_url": WEBHOOK_URL,
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "token_loaded": bool(BOT_TOKEN)
    }), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Main webhook endpoint to receive updates from Telegram.
    """
    logger.info("📨 Webhook received")
    
    # Check if token is available
    if not BOT_TOKEN:
        logger.error("❌ No bot token available to process webhook")
        return jsonify({"status": "error", "message": "Bot token not configured"}), 500
    
    try:
        # Get the incoming request data
        data = request.get_json()
        if not data:
            logger.warning("⚠️ No JSON data received")
            return jsonify({"status": "error", "message": "No data"}), 400
        
        logger.info(f"📥 Received data: {data}")
        
        # Process message updates
        if "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]
            
            # Handle text messages
            if "text" in message:
                user_message = message["text"].strip()
                logger.info(f"💬 Received from {chat_id}: {user_message}")
                
                # Generate smart reply
                reply = smart_reply(user_message)
                logger.info(f"💬 Reply: {reply}")
                
                # Send reply
                send_message(chat_id, reply)
            
            elif "new_chat_members" in message:
                # Welcome new members
                welcome_msg = "👋 Welcome! I'm Smart Reply Bot. Say 'hi' to get started!"
                send_message(chat_id, welcome_msg)
            
            else:
                # Non-text messages
                send_message(chat_id, "🤖 I can only understand text messages right now.")
        
        return jsonify({"status": "ok"}), 200
    
    except Exception as e:
        logger.error(f"❌ Error in webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/set_webhook', methods=['GET'])
def manual_set_webhook():
    """Manually set the webhook via browser."""
    if set_webhook():
        return jsonify({
            "success": True,
            "webhook_url": WEBHOOK_URL,
            "message": "Webhook set successfully!"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Failed to set webhook",
            "webhook_url": WEBHOOK_URL
        }), 500

@app.route('/webhook_info', methods=['GET'])
def webhook_info():
    """Get current webhook status."""
    if not BOT_TOKEN:
        return jsonify({"error": "Bot token not configured"}), 500
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    try:
        response = requests.get(url, timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# APPLICATION STARTUP
# ============================================

if __name__ == '__main__':
    # Get port from Railway
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting Smart Reply Bot on port {port}")
    
    # Try to set webhook if token is available
    if BOT_TOKEN:
        set_webhook()
        logger.info("✅ Bot is ready to receive messages!")
    else:
        logger.warning("⚠️ Bot token not set! Please set TELEGRAM_BOT_TOKEN environment variable.")
        logger.info("ℹ️ Bot will still run but won't respond to messages.")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
