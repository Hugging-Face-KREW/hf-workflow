"""Dataset manifest checks.

These tests validate that the evaluation dataset is documented as a dataset,
not just as implementation snapshots. They intentionally check coverage and
metadata, not whether the current checker's PASS/FAIL labels are "correct".
"""
from collections import Counter

import yaml


def _manifest(fixtures_dir):
    return yaml.safe_load((fixtures_dir / "evaluation_manifest.yml").read_text(encoding="utf-8"))


def test_dataset_manifest_references_existing_files(fixtures_dir):
    manifest = _manifest(fixtures_dir)
    ids = [case["id"] for case in manifest["cases"]]

    assert len(ids) == len(set(ids))
    assert len(manifest["cases"]) >= 30
    for case in manifest["cases"]:
        path = fixtures_dir / case["path"]
        assert path.exists(), case["path"]
        assert case["label"] in manifest["label_definitions"], case["id"]
        assert case["rationale"], case["id"]
        assert case["limitation"], case["id"]


def test_dataset_manifest_has_minimum_source_diversity(fixtures_dir):
    manifest = _manifest(fixtures_dir)
    counts = Counter(case["source_type"] for case in manifest["cases"])

    assert counts["synthetic"] >= 5
    assert counts["mutation"] >= 10
    assert counts["real_hfkrew"] >= 10
    assert counts["curated_internal"] >= 5


def test_dataset_manifest_covers_declared_targets(fixtures_dir):
    manifest = _manifest(fixtures_dir)
    covered = {p for case in manifest["cases"] for p in case["phenomena"]}

    for target in manifest["coverage_targets"]["status_shape"]:
        assert target in covered, target
    for target in manifest["coverage_targets"]["phenomena"]:
        assert target in covered, target


def test_dataset_manifest_includes_known_limitations(fixtures_dir):
    manifest = _manifest(fixtures_dir)
    limitations = " ".join(case["limitation"] for case in manifest["cases"])

    assert "렌더" in limitations or "렌더링" in limitations
    assert "semantic" in limitations or "의미" in limitations
    assert "정책" in limitations


def test_dataset_manifest_separates_semantic_labels_from_current_gate(fixtures_dir):
    manifest = _manifest(fixtures_dir)
    cases = {case["id"]: case for case in manifest["cases"]}

    semantic_negative = cases["curated_semantic_negative_description"]
    assert semantic_negative["label"] == "negative"
    assert "pass_like" in semantic_negative["phenomena"]
    assert "semantic_metadata_negative" in semantic_negative["phenomena"]
