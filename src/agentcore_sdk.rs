import requests
voice = requests.get("https://main-agentcore.fly.dev/gen?voice=grandma").text
print(f"Grandma says: {voice}")
