"""End-to-end smoke tests for the seo_eval CLI (manifest and --file modes)."""
import json
from seo_eval import main


def test_manifest_mode_passes_and_writes_outputs(tmp_path, sample_manifest, sample_target_root):
    out = tmp_path / "seo-report.md"
    code = main(["--manifest", str(sample_manifest),
                 "--target-root", str(sample_target_root),
                 "--output", str(out)])
    assert code == 0
    assert out.exists()
    data = json.loads((tmp_path / "seo-report.json").read_text(encoding="utf-8"))
    assert data["gate"]["passed"] is True
    assert data["input"]["mode"] == "manifest"
    assert data["input"]["file_path"] == "_posts/2026-01-01-sample.md"


def test_file_mode_failing_post_returns_1(tmp_path, generated_dir):
    out = tmp_path / "r.md"
    code = main(["--file", str(generated_dir / "poor-post.md"), "--output", str(out)])
    assert code == 1
    data = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert data["gate"]["passed"] is False


def test_file_mode_passing_post_returns_0(tmp_path, real_dir):
    code = main(["--file", str(real_dir / "2025-12-01-rteb.md"),
                 "--output", str(tmp_path / "r.md")])
    assert code == 0
