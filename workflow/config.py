"""Pipeline configuration loader."""
from pathlib import Path
from typing import Any
import yaml


def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """Load YAML config, merging with defaults."""
    default_path = Path(__file__).parent.parent / "configs" / "default.yaml"
    with open(default_path) as f:
        config = yaml.safe_load(f)

    if path:
        with open(path) as f:
            override = yaml.safe_load(f)
            _deep_merge(config, override)

    return config


def _deep_merge(base: dict, override: dict) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
