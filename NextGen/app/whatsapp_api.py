import requests
import json

API_TOKEN = "EAAJsOhd98kgBQCgLQVZCH9gorgJgZAvWxZCRRaQ97hQltGuTTzS4hY8Lt7qgPpsc14fZCJILfWYxzYd5s89btfYHW5YZCsDv7RXGne9FqYWKw3z7rCvRZA2gu9bZAMtWIAfSWKdsvmIVFw77FZAZAZCRdfN1vPTbIqEdMfecxBnVqTeUbruqVhyYaVgSUIcZBArXDn8ZCKZAwWe9J7AkBNLhxq0oW8AKl7v04KrZCp9h42AiMnJzmnbTBuDCk9VCCcX4y8Tp45FioGoebMZCmgbmo09eQV4itS0"
PHONE_NUMBER_ID = "886425391222264"

def send_whatsapp_message(to_number, message):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": message
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()
