import os
import sys
import logging
import re
import time
from datetime import datetime
from flask import Flask, request, jsonify
import requests

# ============================================
# CONFIGURATION & SETUP
# ============================================

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Get environment variables from Railway
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN not set in environment variables!")
    sys.exit(1)

# Railway provides this automatically
RAILWAY_URL = os.environ.get("RAILWAY_STATIC_URL")
if not RAILWAY_URL:
    logger.warning("⚠️ RAILWAY_STATIC_URL not set, using fallback")
    RAILWAY_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "https://your-app.up.railway.app")

WEBHOOK_URL = f"{RAILWAY_URL}/webhook"
logger.info(f"✅ Webhook URL: {WEBHOOK_URL}")

# ============================================
# SMART REPLY RULES - CUSTOMIZE HERE!
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
        "I'm Smart Reply Bot! 🤖 Your friendly auto-reply assistant. I was created to make conversations easier!",
    
    r"who created you|who made you|who is your creator": 
        "I was created by a talented developer using Python and Flask! 🚀",
    
    # Help & Commands
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
    
    r"another joke|more jokes": 
        "What do you call a fake noodle? 🍜\n"
        "An <b>impasta</b>! 🍝\n\n"
        "😂 Okay, that was cheesy!",
    
    # Compliments & Love
    r"i love you|love you|luv you|i (like|adore) you": 
        "Aww, that's so sweet! ❤️ I love you too! You're amazing! 😊",
    
    r"you are (beautiful|handsome|cute|pretty|awesome|great|amazing)": 
        "😊 Thank you so much! That means a lot to me! You're pretty awesome yourself! 🌟",
    
    # Thanks
    r"thank(s| you| you so much| you very much)|thx|thanks a lot": 
        "You're welcome! 😊 Happy to help! Have a great day! 🌟",
    
    # Goodbye
    r"bye|goodbye|see you|see you later|gotta go|ttyl": 
        "Goodbye! 👋 It was nice talking to you! Have a wonderful day! ✨",
    
    # Miscellaneous
    r"weather|forecast|rain|sunny": 
        "🌤️ I don't have weather data yet, but I'm learning! Try checking a weather app for now!",
    
    r"who are you|what is this bot": 
        "I'm Smart Reply Bot 🤖 - your go-to bot for quick, friendly, and smart automatic replies!",
    
    r"test|testing|ping": 
        "Pong! 🏓 The bot is working perfectly! ✅",
}

# ============================================
# BOT FUNCTIONS
# ============================================

def smart_reply(message_text):
    """
    Analyze message and return the most appropriate reply using pattern matching.
    """
    if not message_text or not message_text.strip():
        return "🤔 I didn't catch that. Could you please say something?"
    
    # Clean the message
    clean_message = message_text.lower().strip()
    
    # Check each rule
    for pattern, reply in REPLY_RULES.items():
        if re.search(pattern, clean_message, re.IGNORECASE):
            logger.info(f"✅ Pattern matched: {pattern}")
            return reply
    
    # Default fallback replies
    fallbacks = [
        "🤔 I'm not sure how to reply to that. Try saying 'hi' or 'help' to get started!",
        "😅 I don't understand that yet. I'm still learning! Try asking me something else.",
        "🤷 I'm not programmed to respond to that. But I'm getting smarter every day!",
    ]
    
    # Rotate through fallbacks for variety
    fallback_index = hash(clean_message) % len(fallbacks)
    return fallbacks[fallback_index]

def send_message(chat_id, text, parse_mode='HTML'):
    """
    Send a message via the Telegram Bot API.
    """
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
        logger.error(f"❌ Failed to send message to {chat_id}: {e}")
        return None

def set_webhook():
    """
    Set the webhook URL for the bot.
    """
    if not BOT_TOKEN:
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
        logger.info(f"✅ Webhook set successfully: {data}")
        return data.get('ok', False)
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to set webhook: {e}")
        return False

def get_webhook_info():
    """
    Get current webhook information for debugging.
    """
    if not BOT_TOKEN:
        return None
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info(f"📊 Webhook info: {data}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to get webhook info: {e}")
        return None

def get_bot_info():
    """
    Get bot information.
    """
    if not BOT_TOKEN:
        return None
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('ok'):
            logger.info(f"🤖 Bot info: {data['result']}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to get bot info: {e}")
        return None

# ============================================
# FLASK ROUTES
# ============================================

@app.route('/', methods=['GET'])
def home():
    """
    Home page to verify bot is running on Railway.
    """
    return jsonify({
        "status": "running",
        "bot_name": "Smart Reply Bot 🤖",
        "version": "1.0.0",
        "time": datetime.now().isoformat(),
        "webhook_url": WEBHOOK_URL,
        "environment": os.environ.get("RAILWAY_ENVIRONMENT", "production"),
    })

@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint for Railway.
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Main webhook endpoint to receive updates from Telegram.
    """
    logger.info("📨 Webhook received")
    
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
            
            # Handle different message types
            if "text" in message:
                user_message = message["text"].strip()
                logger.info(f"💬 Received from {chat_id}: {user_message}")
                
                # Generate smart reply
                reply = smart_reply(user_message)
                logger.info(f"💬 Generated reply: {reply}")
                
                # Send reply
                send_message(chat_id, reply)
            
            elif "new_chat_members" in message:
                # Welcome new members
                for member in message["new_chat_members"]:
                    welcome_msg = f"👋 Welcome to the chat, {member.get('first_name', 'friend')}! I'm Smart Reply Bot. Say 'hi' to get started!"
                    send_message(chat_id, welcome_msg)
            
            else:
                # Non-text messages
                response = "🤖 I can only understand text messages right now. Try sending a message!"
                send_message(chat_id, response)
        
        return jsonify({"status": "ok"}), 200
    
    except Exception as e:
        logger.error(f"❌ Error in webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/set_webhook', methods=['GET'])
def manual_set_webhook():
    """
    Manually set the webhook via browser.
    """
    result = set_webhook()
    return jsonify({
        "success": result,
        "webhook_url": WEBHOOK_URL
    })

@app.route('/webhook_info', methods=['GET'])
def webhook_info():
    """
    Get current webhook status.
    """
    info = get_webhook_info()
    return jsonify(info)

# ============================================
# APPLICATION STARTUP
# ============================================

@app.before_first_request
def setup():
    """
    Run setup tasks before the first request.
    """
    logger.info("🚀 Starting up Smart Reply Bot...")
    
    # Get bot info
    bot_info = get_bot_info()
    if bot_info and bot_info.get('ok'):
        logger.info(f"✅ Bot authenticated: @{bot_info['result']['username']}")
    
    # Set webhook
    if set_webhook():
        logger.info(f"✅ Webhook configured: {WEBHOOK_URL}")
    else:
        logger.warning("⚠️ Failed to set webhook automatically")
        logger.warning(f"⚠️ Please visit: {RAILWAY_URL}/set_webhook")

# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == '__main__':
    # Get port from Railway environment
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting Flask server on port {port}")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
