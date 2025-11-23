import requests, os

PATCH = "14.1.1"  # update to latest Data Dragon version
URL = f"http://ddragon.leagueoflegends.com/cdn/{PATCH}/img/champion/"

os.makedirs("champions", exist_ok=True)

# Get champion list
champ_list = requests.get(
    f"http://ddragon.leagueoflegends.com/cdn/{PATCH}/data/en_US/champion.json"
).json()["data"]

for champ in champ_list.values():
    name = champ["id"]
    img_url = URL + name + ".png"

    img = requests.get(img_url).content
    with open(f"champions/{name}.png", "wb") as f:
        f.write(img)

print("Done.")
