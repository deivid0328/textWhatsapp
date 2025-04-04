from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from PIL import Image
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

AZURE_OCR_KEY = os.getenv("AZURE_OCR_KEY")
AZURE_OCR_ENDPOINT = os.getenv("AZURE_OCR_ENDPOINT")  # Debe terminar en '/'

def extract_text_from_image_azure(image_path: str) -> str:
    ocr_url = AZURE_OCR_ENDPOINT + "vision/v3.2/read/analyze"

    with open(image_path, "rb") as f:
        image_data = f.read()

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_OCR_KEY,
        "Content-Type": "application/octet-stream"
    }

    # Paso 1: Enviar imagen
    response = requests.post(ocr_url, headers=headers, data=image_data)

    if response.status_code != 202:
        print("Error en la solicitud OCR:", response.text)
        return "Hubo un problema procesando la imagen 😓"

    operation_url = response.headers["Operation-Location"]

    # Paso 2: Esperar resultado
    time.sleep(3)
    result = requests.get(operation_url, headers={"Ocp-Apim-Subscription-Key": AZURE_OCR_KEY}).json()

    while result["status"] == "running":
        time.sleep(1)
        result = requests.get(operation_url, headers={"Ocp-Apim-Subscription-Key": AZURE_OCR_KEY}).json()

    # Paso 3: Extraer texto
    if result["status"] == "succeeded":
        lines = []
        for read_result in result["analyzeResult"]["readResults"]:
            for line in read_result["lines"]:
                lines.append(line["text"])
        return "\n".join(lines)

    return "No se pudo extraer texto de la imagen 😕"

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    try:
        form = await request.form()

        media_url = form.get("MediaUrl0")
        num_media = int(form.get("NumMedia", 0))
        from_number = form.get("From")

        response = MessagingResponse()

        if num_media > 0 and media_url:
            # Descargar imagen
            image_response = requests.get(media_url)
            with open("temp.jpg", "wb") as f:
                f.write(image_response.content)

            # Extraer texto usando Azure OCR
            extracted_text = extract_text_from_image_azure("temp.jpg")
            os.remove("temp.jpg")

            reply = extracted_text.strip() or "No detecté texto en la imagen 😕"
            response.message(reply)
        else:
            response.message("Por favor, envíame una imagen con texto para extraerlo ✨")

        return PlainTextResponse(str(response))

    except Exception as e:
        print("Error:", str(e))
        return PlainTextResponse("Ocurrió un error procesando tu mensaje 😓", status_code=500)
