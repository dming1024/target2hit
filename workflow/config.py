"""Pipeline configuration loader."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """Configuration loading error."""
    pass


def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """Load YAML config, merging with defaults.

    Raises:
        ConfigError: If the default or override config file cannot be read or parsed.
    """
    default_path = Path(__file__).parent.parent / "configs" / "default.yaml"
    try:
        with open(default_path) as f:
            config = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        raise ConfigError(f"Failed to load default config from {default_path}: {e}") from e

    if path:
        try:
            with open(path) as f:
                override = yaml.safe_load(f)
        except (OSError, yaml.YAMLError) as e:
            raise ConfigError(f"Failed to load override config from {path}: {e}") from e
        _deep_merge(config, override)

    return config


def _deep_merge(base: dict, override: dict) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
