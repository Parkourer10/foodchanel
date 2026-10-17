# swiggy_api
this is the docs
## get_otp(number)
Takes your mobile number as a string. Sends you an OTP by SMS. Returns nothing.

## verify_otp(otp)
Takes the OTP you got as a string. Logs you in and saves the login to files. Returns nothing.

## get_address()
Takes nothing. Returns your saved addresses as a list. Each address has an `id`, `address`, `annotation`, `lat` and `lng`.

## sel_address(addresses, address_id)
Takes the list from `get_address()` and the `id` of the address you want. Returns that address as a dict with `address`, `lat` and `lng`.

## search_restaurants(q, lat, long)
Takes what to search for and your latitude and longitude. Returns a list of matches. Each one has a `text` (name) and a `type`, which is `"RESTAURANT"` or `"DISH"`. Only restaurants can be opened with the next function.

## get_restaurant_menu(address, restaurant)
Takes the dict from `sel_address()` and one restaurant from `search_restaurants()`. Saves that restaurant's menu to a file. Returns nothing.

## parse_menu()
Takes nothing. Reads the saved menu and returns it as a dict with the restaurant id, delivery time and a list of `items`. Each item has an `index`, `name` and `price`.

## item_options(data, index)
Takes the menu from `parse_menu()` and an item's `index`. Returns that item's name, price, the variant choices (like sizes) and the addon names.

## cart(data, items, address)
Takes the menu from `parse_menu()`, a list of items to order, and the address `id`.

Each item in the list is either an item `index` or a dict with `index`, `quantity`, `variants` (like `{"Size": "Large"}`) and `addons` (like `["Extra Cheese"]`).

Replaces your Swiggy cart with these items. Returns the cart response and what was sent, as a pair. Pass the whole thing to `order()`.

## order(cart_output, address_id, address, max_total=None)
Takes what `cart()` returned, the address `id`, the dict from `sel_address()`, and optionally the most you are willing to pay.

Places a cash on delivery order straight away. Returns the confirmed order as a dict, including `order_id` and `sla_time` (estimated minutes).