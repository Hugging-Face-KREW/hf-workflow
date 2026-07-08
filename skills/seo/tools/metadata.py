"""Metadata writer — Module 2.

Runs only after the eval gate passes (design §2). Metadata generation is
policy-aware: title/description can be proposed from content evidence, but
canonical/hreflang are emitted only when the workflow provides explicit
translation URL policy.

Write-back targets (design §4):
  1. post ``.md`` frontmatter (yaml round-trip) — title / description / categories / image
  2. ``manifest.yaml`` ``handoff.seo`` — generated meta + eval result + rubric scores
  3. Schema.org JSON-LD — prefer the target's ``jekyll-seo-tag`` frontmatter fields
     (it already emits BlogPosting); inline only the fields the plugin omits
Plus, for this translation workflow (design §8):
  - canonical: language self-canonical
  - hreflang: ko ↔ en source bidirectional
  - visible date ↔ datePublished / dateModified consistency
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

import yaml

from utils import parse_frontmatter

MetadataGenerator = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass
class MetadataPlan:
    """The metadata the writer intends to apply to a passing post."""

    title: str = ""
    description: str = ""
    categories: list[str] = field(default_factory=list)
    image: str = ""
    canonical: str = ""
    hreflang: dict[str, str] = field(default_factory=dict)  # {"ko": url, "en": url}
    json_ld: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "categories": self.categories,
            "image": self.image,
            "canonical": self.canonical,
            "hreflang": self.hreflang,
            "json_ld": self.json_ld,
        }


@dataclass
class MetadataBuildResult:
    """Policy-aware metadata generation result."""

    status: str
    candidate: MetadataPlan
    needs_policy_decision: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence_used: list[str] = field(default_factory=list)
    reason: str = ""

    def __getattr__(self, name: str) -> Any:
        """Delegate MetadataPlan fields for legacy plan-like access.

        ``build_plan`` used to be annotated as returning ``MetadataPlan`` while
        still raising ``NotImplementedError``. Delegating plan fields lets simple
        call chains such as ``apply(build_plan(...), post)`` keep working once
        build_plan starts returning the richer policy result.
        """
        return getattr(self.candidate, name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "candidate": self.candidate.to_dict(),
            "needs_policy_decision": self.needs_policy_decision,
            "warnings": self.warnings,
            "evidence_used": self.evidence_used,
            "reason": self.reason,
        }


REQUIRED_POLICY_FIELDS = (
    "target_url",
    "source_url",
    "canonical_policy",
    "translation_indexing",
    "target_locale",
    "source_locale",
)


def _metadata_policy(manifest: dict[str, Any]) -> dict[str, Any]:
    seo = ((manifest.get("handoff", {}) or {}).get("seo", {}) or {})
    return seo.get("metadata_policy", {}) or {}


def _first_heading(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            text = stripped.lstrip("#").strip()
            if text:
                return text
    return ""


def _first_paragraph(body: str) -> str:
    for part in body.split("\n\n"):
        text = part.strip()
        if not text or text.startswith("#") or text.startswith("<!--"):
            continue
        return " ".join(text.split())
    return ""


def _clip_sentence(text: str, limit: int = 170) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    clipped = text[:limit].rstrip()
    for sep in (". ", "。", "! ", "? ", "."):
        idx = clipped.rfind(sep)
        if idx >= 70:
            return clipped[:idx + len(sep)].strip()
    return clipped.rstrip(" ,.;") + "..."


def _base_candidate(body: str, frontmatter: dict[str, Any]) -> MetadataPlan:
    title = str(frontmatter.get("title") or "").strip() or _first_heading(body)
    description = str(frontmatter.get("description") or "").strip()
    if not description:
        description = _clip_sentence(_first_paragraph(body))
    categories = frontmatter.get("categories") or []
    if isinstance(categories, str):
        categories = [categories]
    return MetadataPlan(
        title=title,
        description=description,
        categories=list(categories),
        image=str(frontmatter.get("image") or ""),
    )


def _apply_url_policy(plan: MetadataPlan, policy: dict[str, Any]) -> list[str]:
    missing = [field for field in REQUIRED_POLICY_FIELDS if not policy.get(field)]
    if missing:
        return missing

    canonical_policy = str(policy.get("canonical_policy"))
    target_url = str(policy["target_url"])
    source_url = str(policy["source_url"])
    if canonical_policy == "self":
        plan.canonical = target_url
    elif canonical_policy == "source":
        plan.canonical = source_url
    else:
        missing.append("canonical_policy")

    plan.hreflang = {
        str(policy["target_locale"]): target_url,
        str(policy["source_locale"]): source_url,
    }
    return missing


def build_plan(
    body: str,
    frontmatter: dict[str, Any],
    manifest: dict[str, Any],
    *,
    source_url: str = "",
    primary_keyword: str = "",
    generator: MetadataGenerator | None = None,
) -> MetadataBuildResult:
    """Derive a policy-aware metadata candidate.

    ``generator`` is the seam for a schema-bound LLM metadata writer. Without
    it, the function returns a conservative candidate from existing frontmatter
    and the first meaningful paragraph. URL policy is never guessed.
    """
    evidence = {
        "frontmatter": {
            "title": frontmatter.get("title") or "",
            "description": frontmatter.get("description") or "",
            "image": frontmatter.get("image") or "",
            "categories": frontmatter.get("categories") or [],
        },
        "content": {
            "first_heading": _first_heading(body),
            "first_paragraph": _first_paragraph(body),
            "primary_keyword": primary_keyword,
            "source_url": source_url,
        },
    }

    if generator is None:
        plan = _base_candidate(body, frontmatter)
        warnings = [] if plan.title and plan.description else [
            "title_or_description_candidate_is_incomplete"
        ]
    else:
        raw = generator(evidence)
        candidate = raw.get("candidate", raw) if isinstance(raw, dict) else {}
        base = _base_candidate(body, frontmatter)
        plan = MetadataPlan(
            title=str(candidate.get("title") or "").strip(),
            description=str(candidate.get("description") or "").strip(),
            categories=list(candidate.get("categories") or base.categories),
            image=str(candidate.get("image") or base.image),
        )
        warnings = [str(w) for w in raw.get("warnings", [])] if isinstance(raw, dict) else []

    missing = _apply_url_policy(plan, _metadata_policy(manifest))
    status = "READY" if not missing and plan.title and plan.description else "PARTIAL"
    reason = (
        "metadata candidate is ready for approved write-back"
        if status == "READY" else
        "metadata candidate needs policy decisions or missing title/description"
    )
    return MetadataBuildResult(
        status=status,
        candidate=plan,
        needs_policy_decision=missing,
        warnings=warnings,
        evidence_used=["frontmatter", "content", "metadata_policy"],
        reason=reason,
    )


def hreflang_entries(plan: MetadataPlan) -> list[dict[str, str]]:
    """Structured-output friendly representation of hreflang values."""
    return [
        {"locale": locale, "url": url}
        for locale, url in sorted(plan.hreflang.items())
    ]


def apply(
    plan: MetadataPlan,
    post_path: Path,
    manifest_path: Optional[Path] = None,
) -> None:
    """Apply an already-approved metadata plan.

    This deliberately does not decide metadata policy. Candidate generation may
    use policy/LLM input, while write-back stays deterministic and testable so
    the SEO skill can verify the post after metadata has been applied.
    """
    content = post_path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)

    updates = {
        "title": plan.title,
        "description": plan.description,
        "categories": plan.categories,
        "image": plan.image,
        "canonical": plan.canonical,
    }
    for key, value in updates.items():
        if value:
            frontmatter[key] = value
    if plan.hreflang:
        frontmatter["hreflang"] = plan.hreflang
    if plan.json_ld:
        frontmatter["json_ld"] = plan.json_ld

    serialized = yaml.safe_dump(
        frontmatter,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).strip()
    post_path.write_text(f"---\n{serialized}\n---\n{body}", encoding="utf-8")

    if manifest_path is not None:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        if not isinstance(manifest, dict):
            manifest = {}
        handoff = manifest.setdefault("handoff", {})
        if not isinstance(handoff, dict):
            handoff = {}
            manifest["handoff"] = handoff
        seo = handoff.setdefault("seo", {})
        if not isinstance(seo, dict):
            seo = {}
            handoff["seo"] = seo
        seo["metadata_candidate"] = plan.to_dict()
        manifest_path.write_text(
            yaml.safe_dump(
                manifest,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
            ),
            encoding="utf-8",
        )
