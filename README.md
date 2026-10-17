# Swiggy Ordering
This is an reverse engineered attempt at replicating what the swiggy frontend calls to initiate login , restaurant search , getting restaurant menu , ordering an item with cash on said restaurant menu.

## How it works
Basically, It works by replicating a browser agent and making requests to the swiggy backend with credentials the browser agent returns, like csrf tokens and headers and user-id.
It bypasses the aws bot test by using playwright chromium and extracting the csrf token through that.
Please see DOCS.md to figure out what the functions take in and what they return.
## How to install
```bash
pip install -r requirements.txt
playwright install chromium
```
and done!

## How to use
The repository contains an example main.py file which calls the functions in the library to
1) get and verify otp
2) ask for an restaurant and get its menu
3) display said menu and ask user to enter an item with addons
4) checkout

## License
MIT [license.txt]

## warn
The swiggy backend can change at anytime so this project is not guarenteed to work in lets say a year from now but i hope to update it frequently in my free time

## TODO:
include an http web server so one can call functions through http requests