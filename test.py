import requests

url = (
    "https://world.openfoodfacts.net/api/v2/search?"
    "country=spain"
    "&page=1"
    "&page_size=1"  # we only need one result to get the total count
    "&sort_by=unique_scans_n"
    "&lc=en"
    "&tagtype_0=product_type"
    "&tag_contains_0=contains"
    "&tag_0=food"
)

response = requests.get(url)
data = response.json()

total_products = data.get("count", 0)
print(f"🔢 Total food products from Spain available: {total_products}")
