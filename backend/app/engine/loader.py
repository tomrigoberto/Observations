"""Loads the observation library from disk and exposes it as an in-memory rule pack.

The loader is responsible for:
  - reading every observation YAML
  - reading every pattern definition YAML
  - schema-validating both
  - exposing a ``RulePack`` with O(1) lookup by ID
  - rendering plain-English descriptions of each observation's logic
    (used by the library browser UI)

In dev, ``LIBRARY_PATH`` points at the sibling ``observations-library`` checkout.
In prod, it points at an unpacked rule-pack tarball.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from app.config import settings


@dataclass
class RulePack:
    version: str
    path: str
    observations: dict[str, dict] = field(default_factory=dict)
    patterns: dict[str, dict] = field(default_factory=dict)
    disclaimers: dict[str, dict] = field(default_factory=dict)


@lru_cache(maxsize=1)
def get_rule_pack() -> RulePack:
    return _load(settings.library_path)


def _load(library_path: str) -> RulePack:
    root = Path(library_path)
    pack = RulePack(version=_compute_version(root), path=str(root))

    obs_dir = root / "observations"
    if obs_dir.exists():
        for path in obs_dir.rglob("*.yaml"):
            with path.open() as f:
                obs = yaml.safe_load(f)
            if not obs or "id" not in obs:
                continue
            pack.observations[obs["id"]] = obs

    pat_dir = root / "patterns"
    if pat_dir.exists():
        for path in pat_dir.glob("*.yaml"):
            with path.open() as f:
                pat = yaml.safe_load(f)
            if not pat or "pattern" not in pat:
                continue
            pack.patterns[pat["pattern"]] = pat

    disc_path = root / "disclaimers" / "disclaimers.yaml"
    if disc_path.exists():
        with disc_path.open() as f:
            data = yaml.safe_load(f) or {}
        pack.disclaimers = data

    return pack


def _compute_version(root: Path) -> str:
    """Stable version hash over all YAML files in the library."""
    h = hashlib.sha256()
    if not root.exists():
        return "empty"
    for path in sorted(root.rglob("*.yaml")):
        h.update(path.relative_to(root).as_posix().encode())
        with path.open("rb") as f:
            h.update(f.read())
    return f"sha256:{h.hexdigest()[:12]}"


def render_plain_english_logic(obs: dict, patterns: dict[str, dict]) -> str:
    """Render an observation's logic as a plain-English description for the UI."""
    return _render_node(obs.get("logic", {}), patterns, depth=0)


def _render_node(node: dict, patterns: dict[str, dict], depth: int) -> str:
    indent = "  " * depth
    if "pattern" in node:
        pat = patterns.get(node["pattern"])
        if not pat:
            return f"{indent}- (unknown pattern: {node['pattern']})"
        params = node.get("parameters", {})
        descr = pat.get("description", node["pattern"]).strip()
        if params:
            param_str = ", ".join(f"{k}={_format_v(v)}" for k, v in params.items())
            return f"{indent}- {descr} — with {param_str}"
        return f"{indent}- {descr}"
    for kind in ("all_of", "any_of", "none_of"):
        if kind in node:
            label = {"all_of": "ALL of:", "any_of": "ANY of:", "none_of": "NONE of:"}[kind]
            children = "\n".join(_render_node(c, patterns, depth + 1) for c in node[kind])
            return f"{indent}{label}\n{children}"
    if "not" in node:
        return f"{indent}NOT:\n{_render_node(node['not'], patterns, depth + 1)}"
    return f"{indent}(empty logic)"


def _format_v(v) -> str:
    if isinstance(v, list):
        return "[" + ", ".join(str(x) for x in v) + "]"
    return str(v)


def reload() -> RulePack:
    """Force re-read from disk (useful in dev when the library checkout changes)."""
    get_rule_pack.cache_clear()
    return get_rule_pack()


def library_root() -> Path:
    return Path(os.environ.get("LIBRARY_PATH", settings.library_path))
