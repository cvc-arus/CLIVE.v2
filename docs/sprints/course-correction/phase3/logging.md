## Logging

The client emits structured JSON logs to stderr via Python's stdlib `logging` module.

### Configuration

```python
from simpro_client.logging import configure_logging

# Set log level (default: INFO)
configure_logging(level="DEBUG")
```

### Correlation IDs

Every request is tagged with a correlation ID. IDs are auto-generated
per operation, or you can set one explicitly:

```python
from simpro_client.logging import set_correlation_id

set_correlation_id("my-operation-001")
```

### Log Fields

Each JSON log line includes:

| Field | Description |
|-------|-------------|
| `timestamp` | ISO-format time of the log entry |
| `level` | Log level (INFO, DEBUG, ERROR) |
| `correlation_id` | Unique ID linking related requests |
| `method` | HTTP method (GET, POST, etc.) |
| `url` | Request path |
| `status_code` | HTTP response status |
| `duration_ms` | Request duration in milliseconds |