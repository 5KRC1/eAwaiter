# eAwaiter
eAwaiter is a Python package that can change your eAsistent meals automatically.

## Description
eAwaiter was made out of pure laziness of mine. In eAsistent, meals can be changed a week in advance, but since I rarely use the app I forget to see if what I am subscribed to is enjoyable. Due to this I've created this package that (given the necessary information) changes the meals according to your preferances.

## Install & Run
If you are changing the code or using it locally, you can easily install and run it with the following commands:
- Clone the project
```bash
git clone https://github.com/5KRC1/eAwaiter && cd eAmenu
```
- Setup Python venv
```bash
python -m venv env && source env/bin/activate
```
- Install dependencies
```bash
pip install -r requirements.txt
```
- Run the example provided under "Usage"
```bash
python examples/example.py
```

## Usage
To use the package, you simply follow the following instructions:
- install with pip
```bash
pip install git+https://github.com/5KRC1/eAwaiter.git
```
- run in python "example.py"
```python
## example.py ##
from eAwaiter.waiter import Waiter

waiter = Waiter()

# Login
waiter.username = "__your_username__"   # use your eAsistent username
waiter.password = "__your_password__"   # use your eAsistent password
waiter.login()

# Provide info
waiter.default_menu = "1"    # str | any of numbers from 1-6 (eAsistent menus)
waiter.preferred_menu = "2"  # str | any of numbers from 1-6 (eAsistent menus)
waiter.favourite_foods = ["pica", "špageti"] # array of str | foods must be exatly spelled as in eAsistent
waiter.disliked_foods = ["Cheder", "hrenovko", "osličev", "oslič"]  # array of str | foods must be exatly spelled as in eAsistent

# Run service
waiter.service()
```

## Contribute
