from order import cart
from otp import get_otp, verify_otp
from restaurant import search_restaurants, sel_address, get_address ,get_restaurant_menu, parse_menu
import json

if __name__ == "__main__":
    a = input("enter ur number sir: ")
    get_otp(a)
    b = input("enter ur otp sir: ")
    verify_otp(b)
    addresses = get_address()

    for address in addresses:
        print(f"{address['id']}: {address['address']}")

    address_id = input("Enter address ID: ")
    address = sel_address(addresses, address_id)
    q = input("what do you want to eat: ")
    restaurants = search_restaurants(
        q=q,
        lat=float(address["lat"]),
        long=float(address["lng"])
    )
    restaurants = [
        r for r in restaurants
        if r.get("type") == "RESTAURANT"
    ]
    for index, restaurant in enumerate(restaurants):
        print(f"{index}: {restaurant.get('text', 'Unknown restaurant')}")

    choice = int(input("Select restaurant: "))
    restaurant = restaurants[choice]

    get_restaurant_menu(address, restaurant)
    parse_menu()
    with open("parsed.json", "r") as f:
        data = json.load(f)

        for item in data["items"]:
            print(f"{item['index']}. {item['name']} - ₹{item['price']}")

        indices = []
        while True:
            choice = input("\nEnter item index (or DONE): ").strip()
            if choice.upper() == "DONE":
                break
            indices.append(int(choice))

        if indices:
            cart(data, indices, address_id)
            print("BUILT CART")