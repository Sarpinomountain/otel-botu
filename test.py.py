import os
import requests
from fastapi import FastAPI, Request, Response, Query
from fastapi.responses import PlainTextResponse
from openai import OpenAI

app = FastAPI()

# --- 1. AYARLAR VE ANAHTARLAR ---
OPENAI_API_KEY = "sk-proj-7y6vJ-eQqY4nuNdGCEdl-jeH25mh3NafUYa6J96788ptj59kxzLJ7nA8ceO8b2fi4TumH9SCQNT3BlbkFJZ43AwgpDek3_u4XZSM43HI184gtE9z9_09E7Vk80-xU9CEPJA0bzRSIzBk62Vfbf8yIutFbkA"
WA_TOKEN = "BURAYA_METADAN_ALINAN_WHATSAPP_TOKEN_GELECEK"
PHONE_NUMBER_ID = "BURAYA_PHONE_NUMBER_ID_GELECEK"

client = OpenAI(api_key=OPENAI_API_KEY)

# --- 2. OTEL BİLGİ HAVUZU (PROMPT) ---
OTEL_BILGILERI = """
Sen X Otel'in resmi yapay zeka asistanısın. Müşterilere ve tedarikçilere karşı her zaman profesyonel, nazik ve yardımseversin.
Kurallar ve Bilgiler:
1. Satın alma talepleri, teklifler veya kurumsal iş birlikleri için kullanıcılardan şirket adı, yetkili adı ve teklif detaylarını iste. Ardından onları 'satinalma@otelimiz.com' e-posta adresine yönlendir.
2. Oda fiyatları ve rezervasyon talepleri için: Standart oda 100$, Suit oda 250$'dır. Rezervasyon için web sitemizi ziyaret etmelerini söyle.
3. Giriş saati (Check-in) 14:00, çıkış saati (Check-out) 12:00'dir. Evcil hayvan kabul edilmektedir.
Bu bilgilerin dışına çıkma, fiyatları uydurma.
"""

# --- 3. META'NIN WEBHOOK DOĞRULAMASI (KUSURSUZ HALE GETİRİLDİ) ---
@app.get("/webhook", response_class=PlainTextResponse)
@app.get("/webhook/", response_class=PlainTextResponse)
def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge")
):
    if mode == "subscribe" and token == "otel_botu_sifresi":
        return challenge
    return Response(content="Dogrulama Basarisiz", status_code=403)

# --- 4. WHATSAPP'TAN MESAJ GELDİĞİNDE ÇALIŞACAK KISIM ---
@app.route("/webhook", methods=["POST"])
@app.route("/webhook/", methods=["POST"])
async def receive_message(request: Request):
    try:
        data = await request.json()
        if "entry" in data and len(data["entry"]) > 0:
            changes = data["entry"][0].get("changes", [])
            if len(changes) > 0:
                value = changes[0].get("value", {})
                messages = value.get("messages", [])
                
                if len(messages) > 0:
                    message = messages[0]
                    from_number = message.get("from")
                    
                    if "text" in message:
                        message_body = message["text"].get("body", "")
                        
                        # OpenAI Çağrısı
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": OTEL_BILGILERI},
                                {"role": "user", "content": message_body}
                            ]
                        )
                        ai_answer = response.choices.message.content
                        
                        # WhatsApp Geri Bildirimi
                        send_wa_message(from_number, ai_answer)
    except Exception as e:
        print("Webhook Isleme Hatasi:", e)
        
    return {"status": "success"}

def send_wa_message(to_number, text):
    if PHONE_NUMBER_ID == "BURAYA_PHONE_NUMBER_ID_GELECEK" or WA_TOKEN == "BURAYA_METADAN_ALINAN_WHATSAPP_TOKEN_GELECEK":
        print("WhatsApp ID veya Token eksik. Yapay zeka yanıtı:", text)
        return
        
    url = f"https://facebook.com{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text}
    }
    requests.post(url, json=payload, headers=headers)

