import requests
import json
API_TOKEN = "EAAJsOhd98kgBQYgnESFhQcQLSof8FH7V2w1WrlFPQzNaxfwsdNU6JWU3n2kGUsOM1rot6vhc48WeZCFJGweUKtXRjAr0wONZAtWCZAQcZCXZAtNnHJConQjGPlSjaftzsds8ZAljc8ZAkDJP7cJqdE7VPzKO4ddFmTW1lFzemgWAkUBZCL6bbAzNZCsXJ9o2nmA4sCbl82ElQXTMOrT4XiOW6Gab09ZBTfTZB2oUG70429b14wcosSPu8aS7jwsVKTA7lZBqFZA5lrGnVEECbrBGZBXvA6hrP6"
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
