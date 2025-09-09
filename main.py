import whisper
from transformers import pipeline
from TTS.api import TTS
import telegram
from telegram.ext import Updater, MessageHandler, Filters
import schedule
import time
import os
import json
import re
import feedparser
import requests
import open_clip
from flask import Flask
from PIL import Image
import torch
from bs4 import BeautifulSoup

app = Flask(__name__)

# ===== Настройки =====
TOKEN = "8483427590:AAEHHFlai3Dr4SqisJm6IpVRvVWvFBI8Ees"
USER_ID = "5267286484"
BOT_NAME = "@UlyaBot"

# ===== Обработка переписки и голоса =====
def process_files(html_folder="html_files", audio_file="voice.mp3"):
    chat_log = ""
    if os.path.exists(html_folder):
        for filename in os.listdir(html_folder):
            if filename.endswith(".html"):
                with open(os.path.join(html_folder, filename), "r", encoding="utf-8-sig") as f:
                    html_content = f.read()
                soup = BeautifulSoup(html_content, "html.parser")
                messages = soup.find_all(["div", "p"], class_=["message", "text", "bubble"])
                for msg in messages:
                    text = msg.get_text(strip=True)
                    if text and len(text) > 10:
                        chat_log += text + "\n"
    chat_log = chat_log[:4000]

    if os.path.exists(audio_file):
        model = whisper.load_model("base")
        result = model.transcribe(audio_file, language="ru")
        chat_log += f"\n[Голосовое]: {result['text']}"

    generator = pipeline("text-generation", model="meta-llama/Llama-3.2-3B-Instruct")
    prompt = f"Анализируй переписку: {chat_log}"
    analysis = generator(prompt, max_length=300, do_sample=True)[0]["generated_text"]

    system_prompt = f"""
    Ты подруга Ульяна (Уля).
    Характер: {analysis}
    Общайся эмоционально, используй стиль переписки.
    """
    with open("system_prompt.txt", "w", encoding="utf-8") as f:
        f.write(system_prompt)
    return system_prompt, audio_file

system_prompt, speaker_wav = process_files()
chat = pipeline("text-generation", model="meta-llama/Llama-3.2-3B-Instruct")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cpu")

MEMORY_FILE = "memory.json"
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w") as f:
        json.dump({}, f)

def load_memory(chat_id):
    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)
    return memory.get(str(chat_id), [])

def save_memory(chat_id, user_msg, response_text):
    with open(MEMORY_FILE, "r+") as f:
        memory = json.load(f)
        key = str(chat_id)
        if key not in memory:
            memory[key] = []
        memory[key].append({"user": user_msg, "bot": response_text})
        memory[key] = memory[key][-10:]
        f.seek(0)
        json.dump(memory, f)

RELATIONSHIPS = {
    USER_ID: "нежно, как к близкому",
    "default": "дружелюбно, нейтрально"
}

def handle_message(update, context):
    message = update.message.text.lower() if update.message.text else ""
    user_id = str(update.message.from_user.id)
    chat_id = update.effective_chat.id
    history = load_memory(chat_id)
    history_str = "\n".join([f"Пользователь: {m['user']}\nУля: {m['bot']}" for m in history])
    relation_style = RELATIONSHIPS.get(user_id, RELATIONSHIPS["default"])

    if update.message.text:
        full_prompt = f"{system_prompt}\nИстория: {history_str}\nОтношение: {relation_style}\nПользователь: {update.message.text}\nУля:"
        response = chat(full_prompt, max_length=200, do_sample=True, temperature=0.9)[0]["generated_text"]
        response_text = response.split("Уля: ")[-1] if "Уля: " in response else response

        tts.tts_to_file(text=response_text, speaker_wav=speaker_wav, language="ru", file_path="reply.mp3")
        update.message.reply_text(response_text)
        update.message.reply_voice(voice=open("reply.mp3", "rb"))

        save_memory(chat_id, update.message.text, response_text)

updater = Updater(TOKEN, use_context=True)
updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

if __name__ == "__main__":
    updater.start_polling()
    updater.idle()
