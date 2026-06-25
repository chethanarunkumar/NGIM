import requests
import json

ACCESS_TOKEN =" "

# 🔥 ADD THIS LINE (YOUR PHONE NUMBER ID)
PHONE_NUMBER_ID = " "

def send_whatsapp_message(number, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "text",
        "text": {"body": message}
    }

    response = requests.post(url, headers=headers, json=payload)
    print(response.json())


num = "+91 "   # your verified test number
message = "Hello! This is a test from NGIM  from msruas🔔"
send_whatsapp_message(num, message)
