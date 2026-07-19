"""Root pytest config for the multi-package workflow repository."""

from __future__ import annotations

import sys
import types
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
QUALITY_TOOLS = REPO_ROOT / "skills" / "quality" / "tools"
SEO_TOOLS = REPO_ROOT / "skills" / "seo" / "tools"
TRANSLATION_FLOW = REPO_ROOT / "translation-flow"

for path in (TRANSLATION_FLOW, SEO_TOOLS):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

tools_package = types.ModuleType("tools")
tools_package.__path__ = [str(QUALITY_TOOLS), str(SEO_TOOLS)]
sys.modules["tools"] = tools_package
