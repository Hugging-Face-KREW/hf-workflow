"""Shared pytest config for the SEO skill harness.

Puts the skill's ``tools/`` (and the skill root, for the legacy ``tools.*``
import style) on ``sys.path`` so tests can import the checkers and orchestrator
directly with no install step. The whole harness is offline and deterministic.
"""
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]   # skills/seo
TOOLS_DIR = SKILL_DIR / "tools"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _drop_foreign_tools_package() -> None:
    loaded = sys.modules.get("tools")
    loaded_file = Path(getattr(loaded, "__file__", "") or "")
    loaded_paths = [Path(path) for path in getattr(loaded, "__path__", [])]
    if loaded and TOOLS_DIR not in loaded_paths and SKILL_DIR not in loaded_file.parents:
        for name in list(sys.modules):
            if name == "tools" or name.startswith("tools."):
                del sys.modules[name]


_drop_foreign_tools_package()

for _p in (str(TOOLS_DIR), str(SKILL_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture(scope="session")
def generated_dir() -> Path:
    return FIXTURES / "generated"


@pytest.fixture(scope="session")
def real_dir() -> Path:
    return FIXTURES / "real"


@pytest.fixture(scope="session")
def sample_target_root() -> Path:
    return FIXTURES / "target-repo"


@pytest.fixture(scope="session")
def sample_manifest() -> Path:
    return FIXTURES / "manifests" / "sample.yaml"
