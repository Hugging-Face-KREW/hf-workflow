"""Shared pytest config for the quality skill harness."""

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
TOOLS_DIR = SKILL_DIR / "tools"


def _drop_foreign_tools_package() -> None:
    loaded = sys.modules.get("tools")
    loaded_file = Path(getattr(loaded, "__file__", "") or "")
    loaded_paths = [Path(path) for path in getattr(loaded, "__path__", [])]
    if loaded and TOOLS_DIR not in loaded_paths and SKILL_DIR not in loaded_file.parents:
        for name in list(sys.modules):
            if name == "tools" or name.startswith("tools."):
                del sys.modules[name]


_drop_foreign_tools_package()

if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))
