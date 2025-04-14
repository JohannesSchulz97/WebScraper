import json

with open('merck-articles.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(f"Number of merck articles: {len(data)}")

with open('./data/dog-owners.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(f"Number of dog owner articles: {len(data)}")