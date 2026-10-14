from session import get_cookies_csrf
from world import *
import json
import pickle

log("[OTP] getting csrf tokens and cookies")
csrf, rcookies = get_cookies_csrf()
with open("csrf.txt", "w") as f:
    f.write(csrf)
    log("[OTP]written csrf to csrf.txt")
log("[OTP] got csrf and cookies")

for cookie in rcookies:
    swiggy.cookies.set(
        cookie["name"],
        cookie["value"],
        domain=cookie.get("domain", "www.swiggy.com"),
        path=cookie.get("path", "/")
    )

def get_otp(number: str):
    payload = {"mobile": number, "_csrf": csrf}
    log(f"[OTP] requesting otp for {number}")
    try:
        resp = swiggy.post("https://www.swiggy.com/dapi/auth/sms-otp", json=payload)
        resp.raise_for_status()
    except requests.HTTPError as http_err:
        log(f"[OTP] HTTP error occurred while trying to get OTP: {http_err}")
    except Exception as err:
        print(resp)
        log(f"[OTP] Other error occurred while trying to get OTP: {err}")
    else:
        log("[OTP] Success! requested the OTP")

def verify_otp(otp: str):
    log("[OTP] trying to verify otp")
    payload = {"otp": otp, "_csrf": csrf}
    log("[OTP] sending swiggy request")
    try:
        resp = swiggy.post("https://www.swiggy.com/dapi/auth/otp-verify", json=payload)
        resp.raise_for_status()
    except requests.HTTPError as http_err:
        log(f"[OTP] HTTP error occurred while trying to verify OTP: {http_err}")
    except Exception as err:
        print(resp)
        log(f"[OTP] Other error occurred while trying to verify OTP: {err}")
    else:
        log("[OTP] Verified OTP!")
        with open("data.json", "w") as f:
            json.dump(resp.json(), f, indent=4)
            log("[OTP] written data to data.json")
        with open("cookies.pkl", "wb") as f:
            pickle.dump(swiggy.cookies, f)

