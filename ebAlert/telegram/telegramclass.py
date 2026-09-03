import requests

from ebAlert.core.config import settings
from ebAlert.ebayscrapping.ebayclass import EbayItem
from urllib.parse import urlencode


class SendingClass:

    def send_message(self, message):
        message_encoded = urlencode({"text": message})
        sending_url = settings.TELEGRAM_API_URL + message_encoded
        try:
            response = requests.get(sending_url, timeout=15)
        except requests.RequestException as exc:
            print(f"<< telegram message failed to send: {exc}")
            return False

        if response.status_code == 200:
            return response.json().get("ok", False)
        print(f"<< telegram message failed to send (status {response.status_code})")
        return False

    def send_formated_message(self, item: EbayItem):
        message = f"{item.title}\n\n{item.price} ({item.city})\n\n"
        url = f'<a href="{item.link}">{item.link}</a>'
        self.send_message(message + url)


telegram = SendingClass()
