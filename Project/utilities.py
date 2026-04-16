import requests
from bs4 import BeautifulSoup
import re

headers = {
    "User-Agent": "Mozilla/5.0"
}


def check_url(url):
        try:
            response = requests.get(url, headers = headers)
            soup = BeautifulSoup(response.text, "html.parser")
            print(url, " is a valid source")
            return True
        except:
            print(url, " is not a valid source")
            return False

for url in ["https://beautiful-soup-4.readthedocs.io/en/latest/", "https://fakeurl.com", "https://en.wikipedia.org/wiki/Appellate_Division_Courthouse_of_New_York_State"]:
    check_url(url)

def extract_all_urls(response_text):
    # First try labeled format: "URL: https://..."
    labeled = re.findall(r'URL:\s*(https://\S+)', response_text)
    if labeled:
        return labeled
    
    # Fallback: grab all raw https:// URLs
    raw = re.findall(r'https://\S+', response_text)
    
    # Clean trailing punctuation that may get captured
    cleaned = [url.rstrip('.,;)]\'"') for url in raw]
    
    return cleaned if cleaned else []
