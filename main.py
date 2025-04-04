from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from PIL import Image
import pytesseract
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configura la ruta de Tesseract si estás en Windows
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_PATH")

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    form = await request.form()

    media_url = form.get("MediaUrl0")
    num_media = int(form.get("NumMedia", 0))
    from_number = form.get("From")

    response = MessagingResponse()

    if num_media > 0 and media_url:
        # Descargar la imagen
        image_response = requests.get(media_url)
        with open("temp.jpg", "wb") as f:
            f.write(image_response.content)

        # OCR para extraer texto
        image = Image.open("temp.jpg")
        extracted_text = pytesseract.image_to_string(image)

        reply = extracted_text.strip() or "No pude detectar texto en la imagen 😕"
        response.message(reply)

    else:
        response.message("Por favor, envíame una imagen con texto para extraerlo ✨")

    return PlainTextResponse(str(response))
