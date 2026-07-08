"""SEO checkers package.

The body-only deterministic gate (content / keywords / images / frontmatter)
imports only ``utils`` (pyyaml), so it stays usable in a minimal environment.
The Lighthouse Tier-B sub-audits in ``seo_audits`` require beautifulsoup4 and are
imported directly by ``heuristic`` / ``benchmark``, so they are intentionally
NOT re-exported here.
"""
from .frontmatter import check_frontmatter
from .content import check_content_structure
from .images import check_images
from .keywords import check_keywords
from .blockers import check_blockers

__all__ = [
    'check_frontmatter',
    'check_content_structure',
    'check_images',
    'check_keywords',
    'check_blockers',
]
