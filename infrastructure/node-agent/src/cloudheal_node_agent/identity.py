from pathlib import Path
from uuid import uuid4


IDENTITY_FILE = Path.home() / ".cloudheal" / "node_id"


def get_node_id() -> str:
    if IDENTITY_FILE.exists():
        return IDENTITY_FILE.read_text().strip()

    node_id = str(uuid4())

    IDENTITY_FILE.parent.mkdir(parents=True, exist_ok=True)
    IDENTITY_FILE.write_text(node_id)

    return node_id