import requests


def main():
    response = requests.get("https://pypi.org/pypi/requests/json")
    data = response.json()
    print(data["info"]["summary"])  # prints the package summary from PyPI
