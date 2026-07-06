import os
import logging
from flask import Flask, request, jsonify
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ============================================
# CONFIGURATION
# ============================================

# Get bot token from environment
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# IMPORTANT: Get Railway URL from environment or use fallback
# Railway provides RAILWAY_STATIC_URL automatically
RAILWAY_URL = os.environ.get('RAILWAY_STATIC_URL')

# If RAILWAY_STATIC_URL is not set, try the public domain
if not RAILWAY_URL:
    RAILWAY_URL = os.environ.get('RAILWAY_PUBLIC_DOMAIN')

# If still not set, use the hardcoded URL (REPLACE THIS WITH YOUR ACTUAL URL)
if not RAILWAY_URL:
    RAILWAY_URL = 'https://smartreply1bot.up.railway.app'  # <-- CHANGE THIS TO YOUR URL

# Ensure URL doesn't have trailing slash
RAILWAY_URL = RAILWAY_URL.rstrip('/')

WEBHOOK_URL = f"{RAILWAY_URL}/webhook"

logger.info(f"✅ Bot token loaded: {bool(BOT_TOKEN)}")
logger.info(f"🌐 Railway URL: {RAILWAY_URL}")
logger.info(f"🔗 Webhook URL: {WEBHOOK_URL}")

# ============================================
# SMART REPLY RULES
# ============================================

def get_reply(text):
    """Generate smart reply based on user message"""
    if not text:
        return "🤔 Please say something!"
    
    text_lower = text.lower().strip()
    
    # Greetings
    if any(word in text_lower for word in ['hi', 'hello', 'hey', 'howdy', 'good morning', 'good evening']):
        return "Hello! 👋 How can I help you today?"
    
    # How are you
    elif any(word in text_lower for word in ['how are you', "how're you", "how are you doing"]):
        return "I'm doing fantastic! 😊 Thanks for asking! How about you?"
    
    # Help
    elif any(word in text_lower for word in ['help', 'commands', 'what can you do', 'what do you do']):
        return (
            "🤖 <b>I can do a lot!</b>\n\n"
            "✅ Reply to your messages\n"
            "✅ Tell you the time\n"
            "✅ Crack jokes\n"
            "✅ Have simple conversations\n\n"
            "Try saying:\n"
            "• hi\n"
            "• how are you\n"
            "• time\n"
            "• joke\n"
            "• bye"
        )
    
    # Time
    elif any(word in text_lower for word in ['time', 'what time', 'current time', 'date', 'what date']):
        from datetime import datetime
        now = datetime.now()
        return f"🕐 Current time: <b>{now.strftime('%I:%M %p')}</b>\n📅 Date: <b>{now.strftime('%B %d, %Y')}</b>"
    
    # Jokes
    elif any(word in text_lower for word in ['joke', 'tell me a joke', 'funny', 'make me laugh']):
        jokes = [
            "Why do programmers prefer dark mode?\n🖥️ Because light attracts bugs! 🐛",
            "What do you call a fake noodle?\n🍜 An <b>impasta</b>! 🍝",
            "Why don't scientists trust atoms?\n⚛️ Because they make up everything!",
            "What do you call a bear with no teeth?\n🐻 A gummy bear!",
        ]
        import random
        return jokes[random.randint(0, len(jokes)-1)]
    
    # Thanks
    elif any(word in text_lower for word in ['thanks', 'thank you', 'thx', 'thank']):
        return "You're welcome! 😊 Happy to help!"
    
    # Goodbye
    elif any(word in text_lower for word in ['bye', 'goodbye', 'see you', 'see ya', 'ttyl']):
        return "Goodbye! 👋 Have a great day! ✨"
    
    # Love
    elif any(word in text_lower for word in ['love you', 'i love you', 'luv you']):
        return "Aww, that's so sweet! ❤️ I love you too! 😊"
    
    # Test
    elif 'test' in text_lower or 'ping' in text_lower:
        return "✅ Bot is working perfectly! 🎉"
    
    # Who are you
    elif any(word in text_lower for word in ['who are you', 'who created you', 'who made you']):
        return "I'm Smart Reply Bot 🤖 - your friendly auto-reply assistant! I was created by a talented developer using Python and Flask! 🚀"
    
    # Default reply
    else:
        default_replies = [
            "🤔 I'm not sure how to reply to that. Try saying 'hi' or 'help'!",
            "😅 I don't understand that yet. I'm still learning!",
            "🤷 I'm not programmed to respond to that. Try asking something else!",
            "💡 Try saying 'help' to see what I can do!"
        ]
        import random
        return default_replies[random.randint(0, len(default_replies)-1)]

# ============================================
# TELEGRAM BOT FUNCTIONS
# ============================================

def send_message(chat_id, text, parse_mode='HTML'):
    """Send message via Telegram Bot API"""
    if not BOT_TOKEN:
        logger.error("❌ No bot token available")
        return None
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode,
        'disable_web_page_preview': True
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
    """Set webhook URL for the bot"""
    if not BOT_TOKEN:
        logger.error("❌ Cannot set webhook: No bot token")
        return False
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    payload = {
        'url': WEBHOOK_URL,
        'drop_pending_updates': True
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

def get_webhook_info():
    """Get current webhook information"""
    if not BOT_TOKEN:
        return None
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    try:
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"❌ Failed to get webhook info: {e}")
        return None

def get_bot_info():
    """Get bot information"""
    if not BOT_TOKEN:
        return None
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    try:
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"❌ Failed to get bot info: {e}")
        return None

# ============================================
# FLASK ROUTES
# ============================================

@app.route('/', methods=['GET'])
def home():
    """Home page"""
    return jsonify({
        'status': 'running',
        'bot_name': 'Smart Reply Bot 🤖',
        'version': '1.0.0',
        'token_loaded': bool(BOT_TOKEN),
        'railway_url': RAILWAY_URL,
        'webhook_url': WEBHOOK_URL
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Main webhook endpoint"""
    logger.info("📨 Webhook received")
    
    if not BOT_TOKEN:
        logger.error("❌ No bot token available")
        return jsonify({'error': 'Bot not configured'}), 500
    
    try:
        data = request.get_json()
        if not data:
            logger.warning("⚠️ No JSON data received")
            return jsonify({'error': 'No data'}), 400
        
        logger.info(f"📥 Data: {data}")
        
        # Process message
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            
            # Text message
            if 'text' in message:
                user_text = message['text']
                logger.info(f"💬 Message from {chat_id}: {user_text}")
                
                # Generate reply
                reply = get_reply(user_text)
                logger.info(f"💬 Reply: {reply}")
                
                # Send reply
                send_message(chat_id, reply)
            
            # New chat member
            elif 'new_chat_members' in message:
                welcome = "👋 Welcome! I'm Smart Reply Bot. Say 'hi' to get started!"
                send_message(chat_id, welcome)
            
            # Other message types
            else:
                send_message(chat_id, "🤖 I can only understand text messages right now.")
        
        return jsonify({'status': 'ok'}), 200
    
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/set_webhook', methods=['GET'])
def set_webhook_route():
    """Manually set webhook"""
    if set_webhook():
        return jsonify({
            'success': True,
            'webhook_url': WEBHOOK_URL,
            'message': 'Webhook set successfully!'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to set webhook'
        }), 500

@app.route('/webhook_info', methods=['GET'])
def webhook_info_route():
    """Get webhook info"""
    info = get_webhook_info()
    if info:
        return jsonify(info)
    else:
        return jsonify({'error': 'Failed to get webhook info'}), 500

@app.route('/bot_info', methods=['GET'])
def bot_info_route():
    """Get bot info"""
    info = get_bot_info()
    if info:
        return jsonify(info)
    else:
        return jsonify({'error': 'Failed to get bot info'}), 500

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Bot is running',
        'token_loaded': bool(BOT_TOKEN),
        'railway_url': RAILWAY_URL,
        'webhook_url': WEBHOOK_URL
    })

# ============================================
# STARTUP
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info("=" * 50)
    logger.info("🚀 Starting Smart Reply Bot")
    logger.info("=" * 50)
    logger.info(f"📡 Port: {port}")
    logger.info(f"🔑 Token loaded: {bool(BOT_TOKEN)}")
    logger.info(f"🌐 URL: {RAILWAY_URL}")
    logger.info(f"🔗 Webhook: {WEBHOOK_URL}")
    
    # Get bot info if token is available
    if BOT_TOKEN:
        bot_info = get_bot_info()
        if bot_info and bot_info.get('ok'):
            logger.info(f"🤖 Bot: @{bot_info['result']['username']}")
            logger.info(f"📛 Name: {bot_info['result']['first_name']}")
    
    # Set webhook on startup
    if BOT_TOKEN:
        logger.info("📡 Setting webhook...")
        set_webhook()
    else:
        logger.warning("⚠️ Bot token not set! Please set TELEGRAM_BOT_TOKEN environment variable.")
    
    logger.info("=" * 50)
    logger.info("✅ Bot is ready to receive messages!")
    logger.info("=" * 50)
    
    # Run the app
    app.run(host='0.0.0.0', port=port)
