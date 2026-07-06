# 🤖 Smart Reply Bot

A Telegram bot that automatically replies to messages with smart, context-aware responses using Railway and GitHub.

## ✨ Features

- ✅ Smart keyword-based replies
- 🕐 Current time and date
- 😄 Joke generator  
- 💬 Friendly conversational responses
- 🎯 Easy to customize reply rules
- 🔒 Secure with environment variables
- 📊 Detailed logging for debugging
- 🚀 Deployed on Railway with auto-scaling

## 🚀 Quick Deploy

### Prerequisites
- GitHub account
- Railway account
- Telegram account

### Step 1: Create Bot on Telegram
1. Open Telegram and message **@BotFather**
2. Send `/newbot`
3. Name: `Smart Reply Bot`
4. Username: `smartReply1Bot`
5. Copy the **API Token**

### Step 2: Deploy to Railway
1. Fork this repository on GitHub
2. Go to **railway.com** → **New** → **Deploy from GitHub**
3. Select this repository
4. Add environment variable:
   - `TELEGRAM_BOT_TOKEN`: Your bot token from @BotFather
5. Railway will automatically deploy!

### Step 3: Test Your Bot
1. Open Telegram and search for `@smartReply1Bot`
2. Send "hi" or "help"
3. Your bot will reply instantly! 🎉

## 🛠️ Customization

### Adding New Reply Rules
Edit the `REPLY_RULES` dictionary in `app.py`:

```python
REPLY_RULES = {
    r"your keyword": "Your reply message",
    r"another|alternative": "Another reply",
}
