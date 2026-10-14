from world import *
from session import *

def cart(data, indices, address):
    csrf = load_csrf()
    cart_items = []
    for index in indices:
        item = None
        for i in data["items"]:
            if i["index"] == index:
                item = i
                break
        if not item:
            log("[ORDER] item index provided is wrong")
            exit()

        print(f"\n--- {item['name']} (₹{item['price']}) ---")
        qty_in = input("Quantity (Enter for 1): ").strip()
        quantity = int(qty_in) if qty_in.isdigit() else 1

        log("[ORDER] building varient index...")
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
                log(f"[ORDER] added varient {selected_var.get('name')}")

        log("[ORDER] building addon index")
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
                            "price": str(int(price_val)) if isinstance(price_val, (int, float)) else str(price_val),
                        })
                        log(f"[ORDER] added addon {choice.get('name')}")

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
        "_csrf": csrf,
    }
    log("[ORDER] sending cart request...")
    res = swiggy.post("https://www.swiggy.com/dapi/cart", json=payload)
    log(f"[ORDER] cart response: {res.status_code}")
    if res.status_code == 202:
        log("[RESTAURANT] got 202, refreshing cookies..")
        refresh_cookies()
        res =swiggy.post("https://www.swiggy.com/dapi/cart", json=payload)
    if res.status_code != 200:
        log(f"[RESTAURANT] FATAL: the menu fetch failed: {res.status_code}")
    return res.json()