from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rule:
    category: str
    severity: str
    pattern: str
    suggestion: str


RULES = [
    Rule("A. Translationese", "S2", r"\b[\w가-힣]+를 통해\b", "~로 / ~해"),
    Rule("A. Translationese", "S2", r"에 있어서", "에서 / 에"),
    Rule("A. Translationese", "S2", r"에 의해", "가 / 로"),
    Rule("D. Stock AI Expressions", "S1", r"결론적으로[, ]*", "삭제하거나 직접 결론으로 시작"),
    Rule("D. Stock AI Expressions", "S1", r"시사하는 바가 크다", "구체적 의미로 대체"),
    Rule("D. Stock AI Expressions", "S2", r"주목할 만하다", "무엇이 중요한지 직접 설명"),
    Rule("F. Inflated Modifiers", "S3", r"매우|정말|상당히", "필요할 때만 유지"),
    Rule("G. Hedging", "S2", r"[가-힣]+ 수 있을 것으로 보인다", "할 수 있다 / 한다"),
    Rule("H. Connector Overuse", "S3", r"또한|따라서|즉|나아가", "반복되면 삭제 또는 문장 연결"),
    Rule("I. Formal Noun Bloat", "S2", r"할 필요가 있다", "해야 한다"),
]


def strip_frontmatter(markdown: str) -> tuple[str, str]:
    if not markdown.startswith("---"):
        return "", markdown
    end = markdown.find("\n---", 3)
    if end == -1:
        return "", markdown
    return markdown[: end + 4], markdown[end + 4 :]


def mask_protected_spans(markdown: str) -> str:
    text = re.sub(r"```.*?```", "", markdown, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\[[^\]]+\]\([^)]+\)", "", text)
    text = re.sub(r">[^\n]+", "", text)
    return text


def korean_ratio(text: str) -> float:
    letters = re.findall(r"[A-Za-z가-힣]", text)
    if not letters:
        return 0.0
    korean = [ch for ch in letters if "가" <= ch <= "힣"]
    return len(korean) / len(letters)


def repeated_sentence_endings(text: str) -> dict[str, int]:
    endings = re.findall(r"(합니다|됩니다|있습니다|것입니다|수 있습니다)[.!?\n]", text)
    counts: dict[str, int] = {}
    for ending in endings:
        counts[ending] = counts.get(ending, 0) + 1
    return {ending: count for ending, count in counts.items() if count >= 3}


def build_report(input_path: Path) -> str:
    markdown = input_path.read_text()
    _, body = strip_frontmatter(markdown)
    prose = mask_protected_spans(body)
    findings: list[tuple[Rule, str]] = []

    for rule in RULES:
        for match in re.finditer(rule.pattern, prose):
            findings.append((rule, match.group(0)))

    repeated_endings = repeated_sentence_endings(prose)
    ratio = korean_ratio(prose)

    lines = [
        "# Humanize Korean Report",
        "",
        f"- Input: `{input_path}`",
        f"- Korean letter ratio: {ratio:.2%}",
        f"- Rule findings: {len(findings)}",
        "",
        "## Findings",
        "",
    ]
    if findings:
        for rule, span in findings[:30]:
            lines.append(
                f"- {rule.severity} {rule.category}: `{span}` -> {rule.suggestion}"
            )
    else:
        lines.append("- PASS: no deterministic AI-tone patterns found")

    lines += [
        "",
        "## Rhythm",
        "",
    ]
    if repeated_endings:
        for ending, count in sorted(repeated_endings.items()):
            lines.append(f"- WARN: `{ending}` repeated {count} times")
    else:
        lines.append("- PASS: no repeated sentence-ending warning")

    lines += [
        "",
        "## Guardrails",
        "",
        "- Preserve facts, numbers, names, URLs, code, links, and direct quotes.",
        "- Treat this report as review input, not an automatic edit plan.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a simple Korean AI-tone report.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_report(Path(args.input)))
    print(f"Wrote humanize report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
