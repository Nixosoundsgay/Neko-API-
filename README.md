# Neko-API-
# NekoAPI

Python wrapper for the Cat Fact API (https://catfact.ninja)

Supports caching, retries, and basic error handling.

## How to use

```python
from nekoapi import NekoAPI

neko = NekoAPI()

print(neko.get_fact())
print(neko.get_facts(3))
print(neko.get_breeds(5))
