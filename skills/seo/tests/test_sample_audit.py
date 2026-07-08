from sample_audit import audit_posts, render_markdown


def test_sample_audit_collects_metadata_and_statuses(generated_dir):
    report = audit_posts(generated_dir)

    assert report["summary"]["total"] >= 5
    assert report["summary"]["status_counts"]["PASS"] >= 2
    assert report["summary"]["status_counts"]["FAIL"] >= 1
    assert report["summary"]["status_counts"]["BLOCKED"] >= 1
    assert "description" in report["summary"]["metadata_missing"]
    assert all("metadata" in row and "shape" in row and "failures" in row for row in report["posts"])


def test_sample_audit_renders_markdown(generated_dir):
    report = audit_posts(generated_dir)
    markdown = render_markdown(report)

    assert "# Internal SEO Sample Audit" in markdown
    assert "| File | Status | Metadata gaps | Required failures | Shape |" in markdown
    assert "blocked-post.md" in markdown
