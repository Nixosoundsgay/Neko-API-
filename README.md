# Neko-API-
# Wrap

Python wrapper for the Cat Fact API (https://catfact.ninja)

Supports caching, retries, and basic error handling.

## How to use

```python
from nekoapi import NekoAPI

neko = NekoAPI()

print(neko.get_fact())
print(neko.get_facts(3))
print(neko.get_breeds(5))
```
Options
When you create the client you can pass some settings:
```python
neko = NekoAPI(
    timeout=15,
    max_retries=5,
    user_agent="MyApp/1.0",
    enable_cache=True
)
```
Methods
```pyton
•  get_fact() — returns one random cat fact
•  get_facts(limit=5) — returns a list of facts
•  get_breeds(limit=10) — returns breed info
•  clear_cache() — clears cached responses
•  close() — closes the session
Notes
```
It retries failed requests a few times automatically.
There’s a small cache so it doesn’t spam the API for the same request.
If something goes wrong it raises custom errors like APIConnectionError or RateLimitError.
Requirements
•  Python 3.8+
•  requests


## Installation

```bash
pip install requests
