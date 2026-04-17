# shawking

`shawking` is a Python client for the Shawking natural-language date/time parser service.

## Example

```python
from shawking import ShawkingClient

client = ShawkingClient(ip="127.0.0.1", port=8080)
client.config(time_zone="Asia/Kolkata", reference_time=1748736000000)

response = client.parse("Meet me next Friday at 6 PM")
```

Use `config()` for reusable defaults and pass keyword arguments to `parse()` when a single request needs different values.
