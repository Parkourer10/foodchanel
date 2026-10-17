from world import *
import json

def _payment_headers(cart_id, address_id, lat, lng):
    with open("data.json", "r") as f:
        d = json.load(f)
    ua = swiggy.headers["user-agent"]
    return {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://www.swiggy.com",
        "referer": "https://www.swiggy.com/",
        "user-agent": ua,
        "browser-user-agent": ua,
        "tid": d["tid"],
        "token": d["data"]["token"],
        "sid": d["sid"],
        "swuid": d["deviceId"],
        "deviceid": d["deviceId"],
        "cartid": str(cart_id),
        "cartaddressid": str(address_id),
        "lat": str(lat), "latitude": str(lat),
        "lng": str(lng), "longitude": str(lng),
        "platform": "dweb", "agent-type": "Swiggy-Dweb", "client-id": "dweb",
        "x-client-id": "web-payment", "x-origin-id": "dweb",
        "x-checkout-webview": "dweb", "x-web-checkout-flow": "payment",
        "m_id": "CHECKOUT", "analyticsplatform": "dweb",
        "marketplaceid": "1", "marketplacecategory": "food",
        "marketplacebusinessline": "regular", "version-code": "370",
        "accessibility-enabled": "false", "custom-success-screen": "false",
        "isfirstsessionpostdeployment": "false", "isfrombottombar": "false",
        "issuperuser": "false", "iswebcachingxpenabled": "false",
        "iswebviewassetscached": "false", "statusbarheight": "0",
    }

def _pay_post(url, headers, body=None):
    res = requests.post(url, headers=headers, json=body, timeout=30)
    log(f"[PAYMENT] {url.split('/api/v3')[-1]}: {res.status_code}")
    if res.status_code != 200:
        raise RuntimeError(f"{url} failed: {res.status_code} {res.text[:300]}")
    data = res.json()
    if data.get("statusCode") != 0:
        raise RuntimeError(f"{url} rejected: {data.get('statusMessage')}")
    return data

def _get_cod_option(headers):
    body = {
        "address_id": "", "card_details": True,
        "is_user_cred_eligible": False, "is_user_eligible_for_single_click": False,
        "without_split_pay": False, "split_pay_methods": "default",
        "is_gifting_flow": False, "is_inapp_upi_eligible": False,
        "bill_to_company_toggle": False,
    }
    data = _pay_post("https://payments.swiggy.com/api/v3/payment/get-payment-options", headers, body)["data"]
    if not data.get("codEnabled"):
        log("[ORDER] FATAL cash on delivery is not enabled for this cart")
        raise RuntimeError("cash on delivery is not enabled for this cart")
    for group in data.get("payment_group") or []:
        for m in group.get("payment_methods") or []:
            if m.get("payment_code") == "Cash" and m.get("enabled"):
                return m
    log("[ORDER] FATAL no enabled cash payment method")
    raise RuntimeError("no enabled cash payment method")

def _place_cod(headers, address_id, lat, lng, amount):
    amt = float(amount)
    body = {
        "force_validate_coupon": False,
        "transaction_amount": int(amt) if amt.is_integer() else amt,
        "selected_split_pay_amounts": {},
        "twid_rewards_meta": {},
        "place_order_source": "payment",
        "lat": str(lat), "lng": str(lng),
        "addressId": address_id, "address_id": address_id,
        "paymentMethod": "Cash", "payment_cod_method": "Cash",
        "useJuspayNative": False,
        "paymentReturnUrl": "https://www.swiggy.com/web-checkout/order-received",
        "orderComments": "", "order_comments": "",
        "paymentAmount": str(amount),
    }
    data = _pay_post("https://payments.swiggy.com/api/v3/order/place", headers, body)["data"]
    for key in ("payment_failure_response", "invalid_coupon_response", "inventory_messages"):
        if data.get(key):
            log(f"[PAYMENT] place returned {key}: {data[key]}")
    order = data.get("order_data") or {}
    if not order.get("order_id"):
        log(f"[ORDER]no order_id in place response: {data}" )
        raise RuntimeError(f"no order_id in place response: {data}")
    return order

def _confirm_order(headers, order_id):
    return _pay_post("https://payments.swiggy.com/api/v3/order/confirm?order_id={order_id}", headers)["data"]["order_data"]

def checkout(cart_output, address_id, address, ask=True):
    cart_res = cart_output[0] if isinstance(cart_output, tuple) else cart_output
    lat, lng = address["lat"], address["lng"]
    meta = cart_res["data"]["cartMeta"]
    headers = _payment_headers(meta["cartId"], address_id, lat, lng)
    cod = _get_cod_option(headers)
    amount = cod["payable_amount"]
    if float(amount) != float(meta["order_total"]):
        log(f"[ORDER] FATAL total changed: cart says {meta['order_total']}, payments says {amount}")
        raise RuntimeError(f"total changed: cart says {meta['order_total']}, payments says {amount}")

    print(f"\nCash on delivery, total ₹{amount}")
    if ask and input("Place this order? [y/N]: ").strip().lower() != "y":
        log("[PAYMENT] user declined, nothing placed")
        return None

    order = _place_cod(headers, address_id, lat, lng, amount)
    order_id = order["order_id"]
    log(f"[PAYMENT] placed order {order_id} status={order.get('order_status')}")

    done = _confirm_order(headers, order_id)
    log(f"[PAYMENT] confirmed order {order_id} txn={done.get('payment_txn_status')} eta={done.get('sla_time')}min")
    print(f"Order {order_id} confirmed, ETA ~{done.get('sla_time')} min. Pay cash on delivery.")
    return done