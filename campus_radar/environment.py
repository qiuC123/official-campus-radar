from __future__ import annotations

import os
from pathlib import Path
from typing import MutableMapping

from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_project_exa_key(
    path: Path | None = None,
    *,
    environ: MutableMapping[str, str] | None = None,
) -> bool:
    """Load only EXA_API_KEY from the ignored project .env file."""

    values = dotenv_values(path or PROJECT_ROOT / ".env", interpolate=False)
    api_key = str(values.get("EXA_API_KEY") or "").strip()
    if not api_key:
        return False
    target = os.environ if environ is None else environ
    target["EXA_API_KEY"] = api_key
    return True
