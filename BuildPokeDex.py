import requests
import json

# Pokédex range for Gen I–V (Bulbasaur #1 → Genesect #649)
START, END = 1, 649

pokedex = {}

for num in range(START, END + 1):
    url = f"https://pokeapi.co/api/v2/pokemon/{num}"
    response = requests.get(url)
    data = response.json()
    
    # Capitalize first letter (PokeAPI returns lowercase)
    pokedex[num] = data["name"].capitalize()

# Save to JSON file
with open("pokedex.json", "w", encoding="utf-8") as f:
    json.dump(pokedex, f, indent=2, ensure_ascii=False)

print("Pokédex saved to pokedex.json")
