from .world import *
import json
import os
from .session import refresh_cookies
from urllib.parse import quote

def get_address():
    log("[RESTAURANT] trying to read data.json")
    file="data.json"
    if os.path.isfile(file):
        with open("data.json", "r") as f:
            data = json.load(f)
            log("[RESTAURANT] loaded data into memory from data.json")
    else:
        log("[RESTAURANT] Could not find data.json in the current directory!")
        exit()
    cus_id= data["data"]["customer_id"]
    swiggy.headers.update({"user-id": str(cus_id)})
    log(f"[RESTAURANT] changed user-id to {cus_id}")
    addresses = data["data"]["addresses"]
    for i in addresses:
        log(f"[RESTAURANT] Found address: {i.get('annotation', 'Other')}")
    return addresses

def sel_address(addresses: list, address_id: str):
    for i in addresses:
        if str(i.get("id")) == address_id:
            log(f"[RESTAURANT] selected address {address_id}")
            return {
                "address": i.get("address", ""),
                "lat": i.get("lat"),
                "lng": i.get("lng"),
            }

    log(f"[RESTAURANT] address id not found or invalid: {address_id}")
    raise ValueError("Address ID not found or invalid")


def search_restaurants(q: str, lat: float, long: float):
    query = (f"lat={lat}&lng={long}&str={quote(q, safe='')}"
             "&trackingId=undefined&includeIMItem=true")
    resp = swiggy.get(f"https://www.swiggy.com/dapi/restaurants/search/suggest?{query}")
    log(f"[RESTAURANT] searched: {resp.status_code} {resp.url}")
    if resp.status_code == 202:
        log("[RESTAURANT] got 202, refreshing cookies..")
        refresh_cookies()
        resp = swiggy.get(f"https://www.swiggy.com/dapi/restaurants/search/suggest?{query}")
    data = resp.json()
    return data.get("data", {}).get("suggestions", [])

def get_restaurant_menu(address: dict, restaurant: dict) -> dict:
    metadata = json.loads(restaurant["metadata"])
    restaurant_id = metadata["data"]["primaryRestaurantId"]
    params = {
        "page-type": "REGULAR_MENU",
        "complete-menu": "true",
        "lat": address["lat"],
        "lng": address["lng"],
        "restaurantId": restaurant_id,
        "catalog_qa": "undefined",
        "metaData": restaurant["metadata"],
        "submitAction": "SUGGESTION",
    }
    resp = swiggy.get("https://www.swiggy.com/dapi/menu/pl",params=params)
    if resp.status_code == 202:
        log("[RESTAURANT] got 202, refreshing cookies..")
        refresh_cookies()
        resp = swiggy.get("https://www.swiggy.com/dapi/menu/pl",params=params)
    if resp.status_code != 200:
        log(f"[RESTAURANT] FATAL: the menu fetch failed: {resp.status_code}")
    with open("menu.json", "w") as f:
        json.dump(resp.json(), f, indent=4)


def parse_menu():
    with open("menu.json", "r") as f:
        data = json.load(f)
    def to_rupees(value):
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                return value
        if isinstance(value, (int, float)) and value > 0:
            return round(value / 100, 2)
        return value
    def normalize_prices(node):
        if isinstance(node, dict):
            for key, value in list(node.items()):
                if key == "price" and isinstance(value, (int, float, str)):
                    node[key] = to_rupees(value)
                elif isinstance(value, (dict, list)):
                    normalize_prices(value)
        elif isinstance(node, list):
            for item in node:
                normalize_prices(item)
    def get_default_variant_price(info):
        if info.get("price") is not None:
            return info.get("price")
        if info.get("defaultPrice") is not None:
            return info.get("defaultPrice")

        variants_v2 = info.get("variantsV2") or {}
        pricing_models = variants_v2.get("pricingModels") or []
        if not pricing_models:
            return None
        default_variations = set()
        for group in variants_v2.get("variantGroups") or []:
            group_id = group.get("groupId")
            for variation in group.get("variations") or []:
                if variation.get("default") == 1:
                    default_variations.add((group_id, variation.get("id")))

        if default_variations:
            for model in pricing_models:
                model_variations = {
                    (item.get("groupId"), item.get("variationId"))
                    for item in (model.get("variations") or [])
                }
                if default_variations.issubset(model_variations):
                    return model.get("price")

        return pricing_models[0].get("price")
    def get_info(obj):
        if not isinstance(obj, dict):
            return None
        if isinstance(obj.get("info"), dict):
            return obj["info"]
        if isinstance(obj.get("card"), dict):
            card = obj["card"]
            if isinstance(card.get("info"), dict):
                return card["info"]
            if isinstance(card.get("card"), dict) and isinstance(card["card"].get("info"), dict):
                return card["card"]["info"]
        return None
    def find_delivery_time(node):
        if isinstance(node, dict):
            sla = node.get("sla")
            if isinstance(sla, dict) and isinstance(sla.get("deliveryTime"), int):
                return sla["deliveryTime"]
            if isinstance(node.get("deliveryTime"), int):
                return node["deliveryTime"]
            for value in node.values():
                result = find_delivery_time(value)
                if result is not None:
                    return result
        elif isinstance(node, list):
            for item in node:
                result = find_delivery_time(item)
                if result is not None:
                    return result
        return None

    def find_restaurant_id(node):
        def from_restaurant_card(n):
            if isinstance(n, dict):
                info = n.get("info")
                if isinstance(info, dict) and info.get("id") is not None:
                    if "restaurant" in str(n.get("@type", "")).lower():
                        return info["id"]
                for v in n.values():
                    r = from_restaurant_card(v)
                    if r is not None:
                        return r
            elif isinstance(n, list):
                for v in n:
                    r = from_restaurant_card(v)
                    if r is not None:
                        return r
            return None

        def from_key(n): #fallback TODO it sometimes errors out so fix that
            if isinstance(n, dict):
                if n.get("restaurantId") is not None:
                    return n["restaurantId"]
                for v in n.values():
                    r = from_key(v)
                    if r is not None:
                        return r
            elif isinstance(n, list):
                for v in n:
                    r = from_key(v)
                    if r is not None:
                        return r
            return None

        found = from_restaurant_card(node)
        if found is None:
            found = from_key(node)
        try:
            return int(found)
        except (TypeError, ValueError):
            return found

    items = []
    seen = set()

    def walk(node):
        if isinstance(node, list):
            for child in node:
                walk(child)
            return
        if not isinstance(node, dict):
            return

        info = get_info(node)
        if not isinstance(info, dict):
            for value in node.values():
                if isinstance(value, (dict, list)):
                    walk(value)
            return

        variants_v2 = info.get("variantsV2") or {}
        has_price = (
            info.get("price") is not None
            or info.get("defaultPrice") is not None
            or bool(variants_v2.get("pricingModels"))
        )
        if info.get("name") and has_price:
            item_id = info.get("id")
            key = (
                str(item_id)
                if item_id is not None
                else f"{info.get('name')}:{info.get('defaultPrice') or info.get('price')}"
            )
            if key in seen:
                return
            seen.add(key)

            base_price = get_default_variant_price(info)
            payload = {
                "index": len(items) + 1,
                "menu_item_id": item_id,
                "name": info.get("name"),
                "price": to_rupees(base_price),
            }
            if info.get("defaultPrice") is not None:
                payload["defaultPrice"] = to_rupees(info.get("defaultPrice"))
            for field in ("inStock", "isVeg", "isEnabled"):
                if info.get(field) is not None:
                    payload[field] = info[field]

            variants = info.get("variantsV2") or info.get("variants")
            if variants:
                normalize_prices(variants)
                payload["variants"] = variants
            addons = info.get("addons")
            if addons:
                normalize_prices(addons)
                payload["addons"] = addons
            items.append(payload)

        for value in node.values():
            if isinstance(value, (dict, list)):
                walk(value)

    walk(data)
    parsed = {
        "restaurant_id": find_restaurant_id(data),
        "delivery_time": find_delivery_time(data),
        "items": items,
    }

    with open("parsed.json", "w") as f:
        json.dump(parsed, f, indent=4, ensure_ascii=False)
    return parsed
