import pickle
from playwright.sync_api import sync_playwright
from .world import swiggy, log

def get_cookies_csrf():
  log("[SESSION] Starting Playwright")
  with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
        ],
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 1024},
        user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like"
            " Gecko) Chrome/154.0.0.0 Safari/537.36"
        ),
    )
    page = context.new_page()
    log("[SESSION] Went to swiggy.com")
    page.goto("https://www.swiggy.com/")
    log("[SESSION] Waiting for idle")
    page.wait_for_load_state("networkidle")
    log("[SESSION] getting csrf")
    csrf = page.evaluate("() => window._csrfToken || null")
    log("[SESSION] got csrf")
    cookies = context.cookies()
    log("[SESSION] getting cookies and closing browser")
    browser.close()
    log("[SESSION] closed browser")

    return csrf ,cookies


def refresh_cookies():
    log("[SESSION] refreshing cookies.....")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 1024},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36",
        )
        page = context.new_page()
        page.goto("https://www.swiggy.com/")
        page.wait_for_load_state("networkidle")
        cookies = context.cookies()
        browser.close()
    new = next((c for c in cookies if c["name"] == "aws-waf-token"), None)
    if new:
        for old in [c for c in swiggy.cookies if c.name == "aws-waf-token"]:
            swiggy.cookies.clear(old.domain, old.path, old.name)
        swiggy.cookies.set("aws-waf-token", new["value"],
                           domain=new.get("domain", "www.swiggy.com"), path="/")
        with open("cookies.pkl", "wb") as f:
            pickle.dump(swiggy.cookies, f)
        log("[SESSION] saved cookies.pkl")
    else:
        log("[SESSION] ERROR aws-waf-token found")
    return cookies
