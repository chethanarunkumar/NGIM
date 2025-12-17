import requests
import json

ACCESS_TOKEN ="EAAJsOhd98kgBQCgLQVZCH9gorgJgZAvWxZCRRaQ97hQltGuTTzS4hY8Lt7qgPpsc14fZCJILfWYxzYd5s89btfYHW5YZCsDv7RXGne9FqYWKw3z7rCvRZA2gu9bZAMtWIAfSWKdsvmIVFw77FZAZAZCRdfN1vPTbIqEdMfecxBnVqTeUbruqVhyYaVgSUIcZBArXDn8ZCKZAwWe9J7AkBNLhxq0oW8AKl7v04KrZCp9h42AiMnJzmnbTBuDCk9VCCcX4y8Tp45FioGoebMZCmgbmo09eQV4itS0"

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
