import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
OPENROUTER_API_KEY = os.environ['OPENROUTER_API_KEY']

BOT_USERNAME = '@ToniaAnswerBot'

OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
DEEPSEEK_MODEL = 'deepseek/deepseek-r1-0528-qwen3-8b:free'

MAX_MESSAGE_HISTORY = 1000

message_history = []

def add_to_history(user: str, text: str):
    entry = f"{user}: {text}"
    if len(message_history) >= MAX_MESSAGE_HISTORY:
        message_history.pop(0)
    message_history.append(entry)

def build_prompt(user_question: str) -> list:
    context = "\n".join(message_history)
    prompt_text = (
        "You are an assistant that answers questions based on the chat log."
        "You`re also a friendly and helpful talkative bot.\n\n"
        "here is the chat history:\n"
        f"Chat history:\n{context}\n\n"
        f"User message:\n{user_question}\n\n"
        "Give an accurate answer.\n"
        "if you don't know the answer, say 'I don't know' but in language of question.\n"
        "If the question is not clear, ask for clarification.\n"
        "If the question is about the chat history, answer based on the information provided.\n"
        "If the question is not about chat history, answer anyway.\n"
        "Keep your answers in the same language as the question.\n"
        "Be friendly and helpful.\n"
        "If the question is not a question, keep the conversation going.\n"
        "Try to be cute, funny and interesting.\n"
    )
    return [{"role": "user", "content": prompt_text}]

def ask_deepseek(messages: list) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.3
    }

    response = requests.post(OPENROUTER_API_URL, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content'].strip()
    else:
        if response.status_code == 429:
            return "Rate limit exceeded. Please try again later."
        else:
            return f"Error from DeepSeek: {response.text}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    user = update.message.from_user.full_name or update.message.from_user.username
    add_to_history(user, text)

    if BOT_USERNAME.lower() in text.lower():
        messages = build_prompt(text)
        reply = ask_deepseek(messages)
        await update.message.reply_text(reply)

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
