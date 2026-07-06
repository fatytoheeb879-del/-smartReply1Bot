import os
import logging
import re
from datetime import datetime
from flask import Flask, request, jsonify
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Get bot token from environment
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

if BOT_TOKEN:
    logger.info(f"✅ Bot token loaded: {BOT_TOKEN[:10]}...")
else:
    logger.warning("⚠️ No TELEGRAM_BOT_TOKEN found in environment")

# Get Railway URL
RAILWAY_URL = os.environ.get('RAILWAY_STATIC_URL', 'https://your-app.up.railway.app')
WEBHOOK_URL = f"{RAILWAY_URL}/webhook" if BOT_TOKEN else None

# ============================================
# REPLY RULES
# ============================================

RULES = {
    r'hi|hello|hey': 'Hello! 👋 How can I help you?',
    r'how are you': 'I\'m doing great! 😊 Thanks for asking!',
    r'help': 'I can reply to your messages! Try saying "hi" or "how are you"',
    r'time': f'Current time: {datetime.now().strftime("%I:%M %p")} ⏰',
    r'date': f'Today is {datetime.now().strftime("%B %d, %Y")} 📅',
    r'joke': 'Why do programmers prefer dark mode? Because light attracts bugs! 😄',
    r'thanks|thank you': 'You\'re welcome! 😊',
    r'bye|goodbye': 'Goodbye! 👋 Have a great day!',
    r'test': '✅ Bot is working perfectly!',
}

def get_reply(message):
    """Get smart reply based on message"""
    if not message:
        return "🤔 Please say something!"
    
    msg_lower = message.lower()
    
    for pattern, reply in RULES.items():
        if re.search(pattern, msg_lower):
            return reply
    
    return "🤔 I'm not sure how to reply. Try saying 'hi' or 'help'!"

def send_message(chat_id, text):
    """Send message via Telegram API"""
    if not BOT_TOKEN:
        logger.error("No bot token available")
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        logger.info(f"✅ Message sent to {chat_id}")
        return response.json()
    except Exception as e:
        logger.error(f"❌ Error sending message: {e}")
        return None

# ============================================
# FLASK ROUTES
# ============================================

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'running',
        'bot': 'Smart Reply Bot',
        'token_loaded': bool(BOT_TOKEN),
        'time': datetime.now().isoformat()
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming messages"""
    logger.info("📨 Webhook received")
    
    if not BOT_TOKEN:
        logger.error("❌ No bot token")
        return jsonify({'error': 'Bot not configured'}), 500
    
    try:
        data = request.get_json()
        logger.info(f"📥 Data: {data}")
        
        if data and 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            
            if 'text' in message:
                user_text = message['text']
                logger.info(f"💬 From {chat_id}: {user_text}")
                
                reply = get_reply(user_text)
                send_message(chat_id, reply)
            else:
                send_message(chat_id, "🤖 I only understand text messages")
        
        return jsonify({'status': 'ok'}), 200
    
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Manually set webhook"""
    if not BOT_TOKEN or not WEBHOOK_URL:
        return jsonify({'error': 'Token or URL missing'}), 500
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    data = {'url': WEBHOOK_URL}
    
    try:
        response = requests.post(url, json=data, timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# START APP
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting bot on port {port}")
    
    if BOT_TOKEN:
        logger.info(f"✅ Bot is ready! Webhook URL: {WEBHOOK_URL}")
    else:
        logger.warning("⚠️ Bot token not set! Please add TELEGRAM_BOT_TOKEN variable")
    
    app.run(host='0.0.0.0', port=port)
