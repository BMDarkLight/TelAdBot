from fastapi import FastAPI, Request
from dotenv import load_dotenv

import httpx
import os

load_dotenv("../.env")

TOKEN = os.environ.get("TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

app = FastAPI()
client = httpx.AsyncClient()

@app.post("/")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    if 'message' in data:
        chat_id = data['message']['chat']['id']
        text = data['message']['text']
        
        await client.get(f"{BASE_URL}/sendMessage?chat_id={chat_id}&text=You said: {text}")
    
    return {"status": "ok"}