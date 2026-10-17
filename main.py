from swiggy_api import get_otp, verify_otp, get_address, sel_address, search_restaurants, get_restaurant_menu, parse_menu, cart, item_options, order


def pick(options, label):
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    return int(input(f"{label} #: ")) - 1


def main():
    get_otp(input("Mobile number: ").strip())
    verify_otp(input("OTP: ").strip())
    addresses = get_address()
    a = pick([f"{x.get('annotation', 'Other')}: {x.get('address')}" for x in addresses], "Address")
    address_id = str(addresses[a]["id"])
    address = sel_address(addresses, address_id)

    hits = search_restaurants(input("Search: ").strip(), address["lat"], address["lng"])
    hits = [h for h in hits if h.get("type") == "RESTAURANT"]
    if not hits:
        print("No restaurants found")
        return
    r = pick([h["text"] for h in hits], "Restaurant")

    get_restaurant_menu(address, hits[r])
    parsed = parse_menu()
    for item in parsed["items"]:
        print(f"  {item['index']}. {item['name']} (₹{item['price']})")

    items = []
    for i in input("Item #s (comma-separated): ").split(","):
        index = int(i.strip())
        opts = item_options(parsed, index)
        print(f"{opts['name']}: variants={opts['variants']} addons={opts['addons']}")
        qty = input("  quantity (Enter for 1): ").strip()
        items.append({"index": index, "quantity": int(qty) if qty.isdigit() else 1})

    res = cart(parsed, items, address_id)
    total = res[0]["data"]["cartMeta"]["order_total"]
    if input(f"Cash on delivery, total ₹{total}. Place order? [y/N]: ").strip().lower() != "y":
        print("Cancelled, nothing placed")
        return

    done = order(res, address_id, address, max_total=total)
    print(f"Order {done['order_id']} confirmed, ETA ~{done.get('sla_time')} min")


if __name__ == "__main__":
    main()