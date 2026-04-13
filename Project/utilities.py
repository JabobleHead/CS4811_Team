import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0"
}


def check_url(url):
        try:
            response = requests.get(url, headers = headers)
            soup = BeautifulSoup(response.text, "html.parser")
            print(url, " is valid")
        except:
             print(url, " is not valid")


