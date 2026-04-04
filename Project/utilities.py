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


for url in ["https://beautiful-soup-4.readthedocs.io/en/latest/", "https://fakeurl.com", "https://en.wikipedia.org/wiki/Appellate_Division_Courthouse_of_New_York_State"]:
    check_url(url)