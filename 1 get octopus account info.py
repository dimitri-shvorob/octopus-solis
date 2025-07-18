import json
from pathlib import Path

import requests

PATH = Path(r"C:\Users\dimit\Documents\GitHub\octopus")

with Path.open(PATH / "secrets.json") as f:
    secrets = json.load(f)

url = f"https://api.octopus.energy/v1/accounts/{secrets["account_number"]}"
response = requests.get(url=url, auth=(secrets["api_key"], ""))  # noqa: S113
d = response.json()["properties"][0]

with Path(PATH / "octopus_account_info.json").open("w") as f:
    json.dump(d, f)
