from world import *
from session import *

def _save_csrf(body):
    csrf = body.get("csrfToken") if isinstance(body, dict) else None
    if csrf:
        with open("csrf.txt", "w") as f:
            f.write(csrf)
    return csrf

def _refresh_csrf():
    log("[CART] refreshing csrf...")
    res = swiggy.get("https://www.swiggy.com/dapi/cart")
    if res.status_code == 202:
        log("[CART] got 202, refreshing cookies..")
        refresh_cookies()
        res = swiggy.get("https://www.swiggy.com/dapi/cart")
    csrf = _save_csrf(res.json()) #uses the cart api response instead of the csrf.txt as the csrf is refreshed at this stage
    if not csrf:
        log("[CART] FATAL: no csrfToken in cart response")
        raise RuntimeError("no csrfToken in cart response")
    return csrf

def _send_cart(payload, retry=True):
    payload["_csrf"] = load_csrf()
    log("[CART] sending cart request...")
    res = swiggy.post("https://www.swiggy.com/dapi/cart", json=payload)
    log(f"[CART] cart response: {res.status_code}")
    if res.status_code == 202:
        log("[CART] got 202, refreshing cookies..")
        refresh_cookies()
        res = swiggy.post("https://www.swiggy.com/dapi/cart", json=payload)
    body = res.json() if res.status_code == 200 else {}
    if res.status_code != 200 or body.get("statusCode") != 0:
        if retry:
            log("[CART] cart failed, refreshing csrf and retrying once")
            _refresh_csrf()
            return _send_cart(payload, False)
        log(f"[CART] FATAL: the cart request failed: {res.status_code}")
        raise RuntimeError(f"cart failed: {res.status_code} {body.get('statusMessage')}")
    _save_csrf(body)
    return body

def _same(a, b):
    return str(a).strip().lower() == str(b).strip().lower()

def _find_item(data, index):
    for i in data["items"]:
        if i["index"] == index:
            return i
    log("[CART] item index provided is wrong")
    raise ValueError(f"item index {index} not found")

def item_options(data, index):
    item = _find_item(data, index)
    groups = (item.get("variants") or {}).get("variantGroups") or []
    return {
        "name": item["name"],
        "price": item["price"],
        "variants": {g.get("name"): [v.get("name") for v in g.get("variations") or []] for g in groups},
        "addons": [c.get("name") for g in item.get("addons") or [] for c in g.get("choices") or []],
    }

def _build_varients(item, chosen):
    chosen = {str(k).strip().lower(): v for k, v in (chosen or {}).items()}
    varients = []
    variants_data = item.get("variants") or {}
    for group in variants_data.get("variantGroups") or []:
        group_id = str(group.get("groupId"))
        variations = group.get("variations") or []
        wanted = chosen.get(str(group.get("name")).strip().lower())
        selected_var = None
        if wanted is not None:
            for var in variations:
                if _same(var.get("name"), wanted):
                    selected_var = var
                    break
            if not selected_var:
                raise ValueError(f"option '{wanted}' not found in {group.get('name')}")
        else:
            for var in variations:
                if var.get("default") == 1:
                    selected_var = var
                    break

        if selected_var:
            var_id = str(selected_var.get("id"))
            varients.append({
                "variation_id": var_id,
                "variationId": var_id,
                "group_id": group_id,
                "groupId": group_id,
                "name": selected_var.get("name"),
            })
            log(f"[CART] added varient {selected_var.get('name')}")
    return varients

def _build_addons(item, wanted_addons):
    addons = []
    for wanted in wanted_addons or []:
        found = None
        for group in item.get("addons") or []:
            for choice in group.get("choices") or []:
                if _same(choice.get("name"), wanted) or str(choice.get("id")) == str(wanted):
                    found = (str(group.get("groupId")), choice)
                    break
            if found:
                break
        if not found:
            raise ValueError(f"addon '{wanted}' not found")
        group_id, choice = found
        choice_id = str(choice.get("id"))
        addons.append({
            "choice_id": choice_id,
            "choiceId": choice_id,
            "group_id": group_id,
            "groupId": group_id,
            "name": choice.get("name"),
            "price": str(choice.get("price", 0)).removesuffix(".0"),
        })
        log(f"[CART] added addon {choice.get('name')}")
    return addons

def cart(data, items, address):
    cart_items = []
    for spec in items:
        if isinstance(spec, int):
            spec = {"index": spec}
        item = _find_item(data, spec["index"])
        if item.get("inStock") == 0 or item.get("isEnabled") == 0:
            log(f"[CART] {item['name']} is out of stock")
            raise ValueError(f"{item['name']} is out of stock")

        cart_items.append({
            "addons": _build_addons(item, spec.get("addons")),
            "variants": _build_varients(item, spec.get("variants")),
            "menu_item_id": str(item["menu_item_id"]),
            "quantity": int(spec.get("quantity", 1)),
        })

    payload = {
        "flushFirst": True,
        "cart": {
            "restaurantId": int(data["restaurant_id"]),
            "address_id": address,
            "couponCode": "",
            "cartItems": cart_items,
            "mealItems": [],  # TODO
            "subscriptionItems": [],  # TODO
        },
    }
    return _send_cart(payload), payload