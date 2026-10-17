from world import *
from session import *
import json

def save_csrf(body):
    csrf = body.get("csrfToken") if isinstance(body, dict) else None
    if csrf:
        with open("csrf.txt", "w") as f:
            f.write(csrf)
    return csrf

def refresh_csrf():
    log("[CART] refreshing csrf...")
    res = swiggy.get("https://www.swiggy.com/dapi/cart")
    if res.status_code == 202:
        log("[CART] got 202, refreshing cookies..")
        refresh_cookies()
        res = swiggy.get("https://www.swiggy.com/dapi/cart")
    csrf = save_csrf(res.json())
    if not csrf:
        log("[CART] FATAL: no csrfToken in cart response")
        exit()
    return csrf

def send_cart(payload, retry=True):
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
            refresh_csrf()
            return send_cart(payload, False)
        log(f"[CART] FATAL: the cart request failed: {res.status_code}")
        raise RuntimeError(f"cart failed: {res.status_code} {body.get('statusMessage')}")
    save_csrf(body)
    return body

def cart(data, indices, address):
    cart_items = []
    for index in indices:
        item = None
        for i in data["items"]:
            if i["index"] == index:
                item = i
                break
        if not item:
            log("[CART] item index provided is wrong")
            exit()
        if item.get("inStock") == 0 or item.get("isEnabled") == 0:
            log(f"[CART] {item['name']} is out of stock")
            exit()

        print(f"\n--- {item['name']} (₹{item['price']}) ---")
        qty_in = input("Quantity (Enter for 1): ").strip()
        quantity = int(qty_in) if qty_in.isdigit() else 1

        log("[CART] building varient index...")
        varients = []
        variants_data = item.get("variants") or {}
        for group in variants_data.get("variantGroups") or []:
            group_id = str(group.get("groupId"))
            variations = group.get("variations") or []

            print(f"\n[{group.get('name')}]")
            for v_i, var in enumerate(variations, 1):
                print(f"  {v_i}. {var.get('name')} (+₹{var.get('price', 0)})")

            pick = input("Select option # (Enter for default): ").strip()
            selected_var = None
            if pick.isdigit() and 1 <= int(pick) <= len(variations):
                selected_var = variations[int(pick) - 1]
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

        log("[CART] building addon index")
        addons = []
        addon_groups = item.get("addons") or []
        if addon_groups:
            flat_addons = []
            print("\n[Addons]")
            for group in addon_groups:
                group_id = str(group.get("groupId"))
                for choice in group.get("choices") or []:
                    flat_addons.append((group_id, choice))
                    print(f"  {len(flat_addons)}. {choice.get('name')} (+₹{choice.get('price', 0)})")

            picks = input("Select addon #s comma-separated (Enter to skip): ").strip()
            if picks:
                for p in picks.split(","):
                    if p.strip().isdigit() and 1 <= int(p.strip()) <= len(flat_addons):
                        group_id, choice = flat_addons[int(p.strip()) - 1]
                        choice_id = str(choice.get("id"))
                        price_val = choice.get("price", 0)
                        addons.append({
                            "choice_id": choice_id,
                            "choiceId": choice_id,
                            "group_id": group_id,
                            "groupId": group_id,
                            "name": choice.get("name"),
                            "price": str(price_val).removesuffix(".0"),
                        })
                        log(f"[CART] added addon {choice.get('name')}")

        cart_items.append({
            "addons": addons,
            "variants": varients,
            "menu_item_id": str(item["menu_item_id"]),
            "quantity": quantity,
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
    return send_cart(payload), payload