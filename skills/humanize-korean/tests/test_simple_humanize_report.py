from __future__ import annotations

from pathlib import Path

from tools.simple_humanize_report import build_report


def test_build_report_flags_ai_tone_patterns(tmp_path: Path) -> None:
    source = tmp_path / "sample.md"
    source.write_text(
        """---
title: "샘플"
---

결론적으로, 이 기술은 시사하는 바가 크다.
AI 기술을 통해 효율을 높일 수 있을 것으로 보인다.
또한 이 접근 방식은 매우 주목할 만하다.
또한 모델 이름 `Qwen3`와 https://example.com 링크는 유지한다.
"""
    )

    report = build_report(source)

    assert "Humanize Korean Report" in report
    assert "결론적으로" in report
    assert "시사하는 바가 크다" in report
    assert "높일 수 있을 것으로 보인다" in report
    assert "https://example.com" not in report


def test_build_report_passes_plain_korean(tmp_path: Path) -> None:
    source = tmp_path / "plain.md"
    source.write_text("이 문서는 모델의 동작 방식을 설명한다. 필요한 값은 표에 정리했다.\n")

    report = build_report(source)

    assert "PASS: no deterministic AI-tone patterns found" in report
