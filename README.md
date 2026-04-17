# shawking

`shawking` is a Python client for the [Shawking Spring Boot REST service](https://github.com/adi-amatdev/shawking.git), which parses natural-language date and time expressions into structured timestamps.

The client is class-based and keeps service connection details plus default parse options in one place. Constructor arguments configure the service IP and port, `config()` sets reusable defaults, and `parse()` can override those defaults for individual requests.

- Service repo/API target: Shawking `POST /parse`
- Python package: `shawking`
- Documentation: <https://adi-amatdev.github.io/shawking/>

## Install

```bash
uv sync
```

## Quick start

```python
from shawking import ShawkingClient

client = ShawkingClient(ip="127.0.0.1", port=8080)
client.config(
    time_zone="Asia/Kolkata",
    reference_time=1748736000000,
)

result = client.parse("Call me at 9 AM tomorrow")
print(result)
```

## Per-call overrides

```python
from datetime import datetime, timezone

from shawking import ShawkingClient

client = ShawkingClient(ip="192.168.1.20", port=8080)
client.config(time_zone="Asia/Kolkata", reference_time=1748736000000)

result = client.parse(
    "Book a flight on 15 Jan 2026",
    time_zone="UTC",
    reference_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
    maxParseDate=1,
)
```

## API

### `ShawkingClient`

```python
ShawkingClient(
    ip: str = "127.0.0.1",
    port: int = 8080,
    *,
    scheme: str = "http",
    timeout: float = 30.0,
)
```

Creates a client that points to a running Shawking service such as `http://127.0.0.1:8080`.

### `config()`

```python
client.config(
    *,
    time_zone: str | None = ...,
    reference_time: int | datetime | None = ...,
    **options,
)
```

Stores default request options for future `parse()` calls.

- `time_zone` maps to Shawking's `timeZone`
- `reference_time` maps to Shawking's `referenceTime`
- extra keyword arguments are forwarded directly to the REST API
- passing `None` removes a stored default

### `parse()`

```python
client.parse(
    text: str,
    *,
    time_zone: str | None = ...,
    reference_time: int | datetime | None = ...,
    **overrides,
)
```

Parses text by calling `POST /parse`. Any values passed here override defaults from `config()` for that one request.

## Development

Run tests with:

```bash
make test
```

Run only unit tests with:

```bash
make tests -- unit
```

Run only integration tests with:

```bash
SHAWKING_HOST=127.0.0.1 \
SHAWKING_PORT=8080 \
make tests -- integ
```

`SHAWKING_HOST`, `SHAWKING_PORT`, and `SHAWKING_SCHEME` are optional and default to `127.0.0.1`, `8080`, and `http`.

Useful development commands:

```bash
make install
```

Creates the `uv` environment and installs pre-commit hooks.

```bash
make check
```

Runs the configured quality checks: lockfile validation, pre-commit hooks, static typing, and dependency checks.

```bash
make docs-test
```

Builds the documentation locally to catch MkDocs issues.

```bash
make docs
```

Serves the documentation locally.

```bash
make help
```

Lists all available Make targets.

## Build the package

Build a distributable wheel with:

```bash
make build
```

This writes the package artifacts into `dist/`.

If you want to clean old build output first by hand, run:

```bash
make clean-build
```
