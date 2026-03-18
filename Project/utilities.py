import requests
from bs4 import BeautifulSoup


def check_url(url):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")

            print(url, " is a valid url")

            return soup
        
        except:
            print(url, " is not a valid url")
            return None