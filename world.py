import requests
import logging
import os
import pickle

header = {
    "__fetch_req__": "true",
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-IN,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "origin": "https://www.swiggy.com",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://www.swiggy.com/",
    "sec-ch-ua":'"Chromium";v="152", "Not?A_Brand";v="24", "Google Chrome";v="152"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
    "user-id": "0"
}

swiggy= requests.Session()
swiggy.headers.update(header)
logging.basicConfig(filename="main.log", level=logging.INFO)
log = logging.info
if os.path.exists("cookies.pkl"):
    with open("cookies.pkl", "rb") as f:
        swiggy.cookies.update(pickle.load(f))

def load_csrf():
    with open("csrf.txt","r") as f:
        csrf = f.read()
    return csrf