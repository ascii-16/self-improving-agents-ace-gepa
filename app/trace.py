
import json
from pathlib import Path
from datetime import datetime, timezone

TRACE_PATH = Path("traces/executions.jsonl")

def record(event: dict):
    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)

    event["timestamp"] = datetime.now(
        timezone.utc
    ).isoformat()

    with TRACE_PATH.open("a") as file:
        file.write(json.dumps(event, default=str) + "\n")
