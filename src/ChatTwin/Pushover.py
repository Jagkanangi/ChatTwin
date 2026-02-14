import requests
from dotenv import load_dotenv
load_dotenv()
import os

class PushOver:
    def __init__(self):
        self.api_key = os.getenv("PUSHOVER_API_KEY")
        self.user_key = os.getenv("PUSHOVER_USER_KEY")
        self.url = "https://api.pushover.net/1/messages.json"
        if not self.api_key or not self.user_key:
            print(f"Pushover API Key or User Key not found in environment variables. api {self.api_key} user {self.user_key}")
            exit()
    def send_message(self, message):
        data = {
            "token": self.api_key,
            "user": self.user_key,
            "message": message
        }
        response = requests.post(self.url, data=data)
        if response.status_code == 200:
            print("Message sent successfully.")
        else:
            print("Failed to send message. Status code:", response.status_code)
            print("Response:", response.text)

