from app.whatsapp_api import send_whatsapp_message

# Add your list of recipients (max 5 numbers in test mode)
recipients = [
    "+91",   # your number
    "+91", # another number
    
]

message = "Hello! This is a test message from NGIM🚀, from chethan and co"

for number in recipients:
    print(f"Sending to {number}...")
    result = send_whatsapp_message(number, message)
    print(result)

