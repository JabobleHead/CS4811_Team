import requests
import json

def url_scan(url):
    api_url = "https://www.virustotal.com/api/v3/urls"

    payload = { "url": url }
    headers = {
        "x-apikey": "d358dac7630de070c127bd58365e0af3aa74e9bea6acb21df1e55aa2035ac7a6",
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded"
    }

    response = requests.post(api_url, data=payload, headers=headers)

    id = json.loads(response.text)["data"]["id"]


    api_url = "https://www.virustotal.com/api/v3/analyses/" + id

    headers = {
        "accept": "application/json",
        "x-apikey": "d358dac7630de070c127bd58365e0af3aa74e9bea6acb21df1e55aa2035ac7a6"
    }

    response = requests.get(api_url, headers=headers)

    #print(len(json.loads(response.text)["data"]["attributes"]["results"]))
    stats = json.loads(response.text)["data"]["attributes"]["stats"]
    #print(id)

    message = ""
    flag = 0
    #print(stats)
    if "undetected" in stats:
        if stats["undetected"] > 0:
            message += "Source could not be detected by " + str(stats["undetected"]) + " of " + str(len(json.loads(response.text)["data"]["attributes"]["results"])) + " scans. \n"
    if "harmless" in stats and "undetected" in stats:
        if stats["harmless"] < stats["undetected"]:
            message += "Not well known source. \n"
            flag = 1
    if "confirmed_timeout" in stats:
        if stats["confirmed_timeout"] > 0:
            message += "Source does not exist. \n"
            flag = 1
    if "malicious" in stats:
        if stats["malicious"] > 0:
            message += "Source was considered malicious by " + str(stats["malicious"]) + " scans. \n"
            flag = 1
    if "suspicious" in stats:
        if stats["suspicious"] > 0:
            message += "Source was considered suspicious by " + str(stats["suspicious"]) + " scans. \n"
            flag = 1
    if not flag:
        message = "Source passed all quality checks."
    
    return message

print("A malicious website like paypa1-login-secure.com shows: \n" + url_scan("paypa1-login-secure.com"))
print("\n A trustworthy website like https://www.cnn.com/ shows: \n" + url_scan("https://www.cnn.com/"))
print(url_scan("https://en.wikipedia.org/wiki/List_of_municipal_capitals_of_the_Republic_of_Portugal"))