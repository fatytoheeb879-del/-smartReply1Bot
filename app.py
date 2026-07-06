import os
import logging
from flask import Flask, request, jsonify
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Get bot token
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# Get Railway URL
RAILWAY_URL = os.environ.get('RAILWAY_STATIC_URL', 'https://your-app.up.railway.app')

logger.info(f"Bot token loaded: {bool(BOT_TOKEN)}")
logger.info(f"Railway URL: {RAILWAY_URL}")

# Simple reply function
def get_reply(text):
    text = text.lower()
    if 'hi' in text or 'hello' in text or 'hey' in text:
        return "Hello! 👋 How can I help you?"
    elif 'how are you' in text:
        return "I'm doing great! 😊 Thanks for asking!"
    elif 'help' in text:
        return "I can reply to your messages! Try saying 'hi' or 'how are you'"
    elif 'time' in text:
        return "It's bot time! ⏰"
    elif 'joke' in text:
        return "Why do programmers prefer dark mode? Because light attracts bugs! 😄"
    elif 'bye' in text or 'goodbye' in text:
        return "Goodbye! 👋 Have a great day!"
    elif 'test' in text:
        return "✅ Bot is working perfectly!"
    else:
        return "🤔 Try saying 'hi' or 'help'!"

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'running',
        'token_loaded': bool(BOT_TOKEN)
    })

@app.route('/health', methods=['GET'])
def health():
    return 'OK', 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        logger.info(f"Webhook received: {data}")
        
        if data and 'message' in data:
            msg = data['message']
            chat_id = msg['chat']['id']
            
            if 'text' in msg:
                user_text = msg['text']
                logger.info(f"Message from {chat_id}: {user_text}")
                
                reply = get_reply(user_text)
                
                if BOT_TOKEN:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    payload = {
                        'chat_id': chat_id,
                        'text': reply
                    }
                    requests.post(url, json=payload)
                    logger.info(f"Sent reply: {reply}")
        
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    if not BOT_TOKEN:
        return jsonify({'error': 'No token'}), 500
    
    webhook_url = f"{RAILWAY_URL}/webhook"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}"
    
    try:
        response = requests.get(url)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting bot on port {port}")
    app.run(host='0.0.0.0', port=port)
