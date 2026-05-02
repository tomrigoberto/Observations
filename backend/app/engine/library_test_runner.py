"""Runs every observation's test_cases against its fixture.

Usage (inside the backend container):
  python -m app.engine.library_test_runner

Exit code 0 on full pass; non-zero on any failure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.engine import loader
from app.engine.runner import _eval_logic, _members_in_scope


def main() -> int:
    pack = loader.get_rule_pack()
    library_root = Path(pack.path)
    failures: list[str] = []
    passes = 0

    for obs in pack.observations.values():
        for case in obs.get("test_cases", []):
            fixture_path = library_root / case["fixture"]
            if not fixture_path.exists():
                failures.append(f"{obs['id']} :: fixture missing: {case['fixture']}")
                continue
            with fixture_path.open() as f:
                household = json.load(f)
            fired_for_any = False
            actual_caps = {}
            for member in _members_in_scope(obs, household):
                fired, caps = _eval_logic(obs["logic"], member, household)
                if fired:
                    fired_for_any = True
                    actual_caps = caps
                    break

            if fired_for_any != case["expected_fires"]:
                failures.append(
                    f"{obs['id']} :: '{case['name']}' expected_fires={case['expected_fires']} "
                    f"got={fired_for_any}"
                )
                continue
            if case["expected_fires"]:
                want = case.get("expected_capture", {})
                for k, v in want.items():
                    if actual_caps.get(k) != v:
                        failures.append(
                            f"{obs['id']} :: '{case['name']}' capture[{k}] expected={v} "
                            f"got={actual_caps.get(k)}"
                        )
                        break
                else:
                    passes += 1
                    continue
            else:
                passes += 1

    if failures:
        for f in failures:
            print("FAIL", f)
        print(f"\n{passes} passed, {len(failures)} failed.")
        return 1
    print(f"All {passes} library test cases passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
