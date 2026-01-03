import requests
import json

ACCESS_TOKEN ="EAAJsOhd98kgBQYgnESFhQcQLSof8FH7V2w1WrlFPQzNaxfwsdNU6JWU3n2kGUsOM1rot6vhc48WeZCFJGweUKtXRjAr0wONZAtWCZAQcZCXZAtNnHJConQjGPlSjaftzsds8ZAljc8ZAkDJP7cJqdE7VPzKO4ddFmTW1lFzemgWAkUBZCL6bbAzNZCsXJ9o2nmA4sCbl82ElQXTMOrT4XiOW6Gab09ZBTfTZB2oUG70429b14wcosSPu8aS7jwsVKTA7lZBqFZA5lrGnVEECbrBGZBXvA6hrP6"

# 🔥 ADD THIS LINE (YOUR PHONE NUMBER ID)
PHONE_NUMBER_ID = "886425391222264"

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


num = "+919606641407"   # your verified test number
message = "Hello! This is a test from NGIM  from msruas🔔"
send_whatsapp_message(num, message)
