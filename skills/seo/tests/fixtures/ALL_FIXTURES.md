# SEO Fixture Corpus

이 파일은 내부 검토용으로 fixture 원문과 audit 요약을 한 곳에서 보기 위한 generated document입니다.

## evaluation_manifest.yml

```yaml
version: 1
purpose: >
  SEO skill 평가 데이터셋의 독립 라벨과 커버리지 근거를 문서화한다.
  이 manifest의 label은 current checker 결과를 그대로 답습하지 않고,
  사람이 보기에 해당 샘플이 어떤 현상을 검증하기 위한 자료인지 설명한다.

label_definitions:
  strong_positive: "본문/구조가 대체로 양호한 positive control"
  acceptable_positive: "실사용 가능하지만 일부 advisory가 있을 수 있는 positive sample"
  borderline: "한두 가지 명확한 개선점이 있는 경계 샘플"
  negative: "명확한 품질/구조 문제가 있는 샘플"
  blocker: "게시 또는 색인을 중단해야 하는 hard blocker 샘플"
  real_regression: "실제 HFKREW 글 형태를 보존한 회귀 샘플"

coverage_targets:
  status_shape:
    - pass_like
    - needs_changes_like
    - fail_like
    - blocked_like
  phenomena:
    - missing_description
    - missing_author
    - noindex
    - broken_internal_link
    - broken_image_path
    - missing_alt
    - empty_body
    - no_markdown_h1
    - multiple_h1
    - heading_level_skip
    - missing_citation
    - toc_before_opening
    - long_real_translation
    - image_heavy_real_post
    - hfkrew_layout_h1_ambiguity
    - description_body_mismatch
    - meaningless_alt
    - generic_link_text
    - source_canonical_policy_conflict
    - curated_gold_positive
    - semantic_metadata_negative
    - title_body_mismatch
    - hreflang_policy_review

cases:
  - id: generated_excellent
    path: generated/excellent-post.md
    source_type: synthetic
    label: strong_positive
    phenomena: [pass_like, synthetic_quality_gradient]
    rationale: "가짜 수치나 placeholder 링크 없이 제목, 도입부, 근거 링크, 이미지 alt를 갖춘 high-quality positive control."
    limitation: "여전히 synthetic 샘플이므로 실제 번역글의 길이와 원문 구조 보존 문제는 대표하지 않는다."

  - id: generated_good
    path: generated/good-post.md
    source_type: synthetic
    label: acceptable_positive
    phenomena: [pass_like, synthetic_quality_gradient]
    rationale: "필수 구조와 공식 근거 링크를 갖춘 단순 positive sample."
    limitation: "이미지와 긴 번역문 구조가 단순화되어 있어 실전 대표성은 제한적이다."

  - id: generated_medium
    path: generated/medium-post.md
    source_type: synthetic
    label: borderline
    phenomena: [needs_changes_like, missing_citation, synthetic_quality_gradient]
    rationale: "대체로 읽히지만 외부 근거가 부족한 경계 샘플."
    limitation: "citation 필요 여부는 글 유형에 따라 달라질 수 있어 hard-fail 근거로는 약하다."

  - id: generated_poor
    path: generated/poor-post.md
    source_type: synthetic
    label: negative
    phenomena: [fail_like, empty_or_thin_body, missing_alt, missing_metadata]
    rationale: "짧고 구조가 부족하며 이미지 alt/메타데이터도 부족한 명확한 negative control."
    limitation: "너무 인위적으로 나빠서 실제 PR에서 자주 나올 실패 모드와는 거리가 있다."

  - id: generated_blocked
    path: generated/blocked-post.md
    source_type: synthetic
    label: blocker
    phenomena: [blocked_like, noindex]
    rationale: "본문 품질과 무관하게 noindex가 있으면 게시 전 차단되어야 함을 검증한다."
    limitation: "noindex 단일 blocker만 다룬다."

  - id: mutated_missing_description
    path: mutated/missing-description.md
    source_type: mutation
    label: borderline
    phenomena: [missing_description]
    rationale: "description 누락이 body quality failure와 분리되어야 하는지 검증한다."
    limitation: "description 내용 품질이나 본문과의 정합성은 검증하지 않는다."

  - id: mutated_missing_alt
    path: mutated/missing-alt.md
    source_type: mutation
    label: negative
    phenomena: [missing_alt, fail_like]
    rationale: "빈 이미지 alt를 접근성/SEO 문제로 감지하는지 검증한다."
    limitation: "alt는 있지만 의미가 부실한 semantic alt 문제는 별도 케이스가 필요하다."

  - id: mutated_noindex
    path: mutated/noindex.md
    source_type: mutation
    label: blocker
    phenomena: [blocked_like, noindex]
    rationale: "robots noindex가 hard blocker로 분리되는지 검증한다."
    limitation: "robots.txt나 HTTP header X-Robots-Tag는 다루지 않는다."

  - id: mutated_broken_internal_link
    path: mutated/broken-internal-link.md
    source_type: mutation
    label: blocker
    phenomena: [blocked_like, broken_internal_link]
    rationale: "target_root가 있을 때 repository 내부 링크가 실제 파일로 resolve되는지 검증한다."
    limitation: "Jekyll permalink 생성 결과까지는 검증하지 않는다."

  - id: mutated_short_opening
    path: mutated/short-opening.md
    source_type: mutation
    label: borderline
    phenomena: [short_opening]
    rationale: "도입부가 짧은 경우를 사람이 검토해야 할 signal로 남기기 위한 샘플."
    limitation: "현재 raw threshold로 hard fail을 입증하기보다 policy/rubric 판단용 signal에 가깝다."

  - id: mutated_empty_body
    path: mutated/empty-body.md
    source_type: mutation
    label: negative
    phenomena: [fail_like, empty_body]
    rationale: "본문이 비어 있는 명확한 negative control."
    limitation: "현실적인 저품질 글보다 극단적이다."

  - id: mutated_missing_h1_no_title
    path: mutated/missing-h1-no-title.md
    source_type: mutation
    label: negative
    phenomena: [no_markdown_h1, missing_title]
    rationale: "frontmatter title도 본문 H1도 없는 경우 제목 신호가 부족함을 검증한다."
    limitation: "렌더링 layout에서 다른 제목을 주입하는 경우는 반영하지 않는다."

  - id: mutated_layout_title_no_body_h1
    path: mutated/layout-title-no-body-h1.md
    source_type: mutation
    label: borderline
    phenomena: [no_markdown_h1, hfkrew_layout_h1_ambiguity]
    rationale: "frontmatter title이 있을 때 body H1 0개를 무조건 실패시켜도 되는지 검토하기 위한 샘플."
    limitation: "Jekyll 렌더 결과를 직접 포함하지 않아 최종 판단에는 렌더 테스트가 필요하다."

  - id: mutated_multiple_h1
    path: mutated/multiple-h1.md
    source_type: mutation
    label: negative
    phenomena: [multiple_h1]
    rationale: "본문에 H1이 여러 개 있는 구조 문제를 검증한다."
    limitation: "긴 원문 번역글에서 섹션 제목을 H1로 유지하는 실제 관행과 충돌할 수 있다."

  - id: mutated_heading_skip
    path: mutated/heading-skip.md
    source_type: mutation
    label: negative
    phenomena: [heading_level_skip]
    rationale: "H1 다음 H3로 건너뛰는 heading hierarchy 문제를 검증한다."
    limitation: "마크다운 내부 코드블록의 # 문자는 별도 파서 테스트가 필요하다."

  - id: mutated_no_citation
    path: mutated/no-citation.md
    source_type: mutation
    label: borderline
    phenomena: [missing_citation]
    rationale: "외부 근거가 없는 정보성 글을 개선 필요 후보로 잡기 위한 샘플."
    limitation: "회고/공지/사용법 글에는 외부 citation hard requirement가 부적절할 수 있다."

  - id: mutated_broken_image_path
    path: mutated/broken-image-path.md
    source_type: mutation
    label: blocker
    phenomena: [broken_image_path]
    rationale: "target_root가 있을 때 로컬 이미지 파일 존재 여부를 검증하기 위한 샘플."
    limitation: "외부 이미지 URL의 HTTP 상태는 검증하지 않는다."

  - id: mutated_missing_author
    path: mutated/missing-author.md
    source_type: mutation
    label: borderline
    phenomena: [missing_author]
    rationale: "author 누락을 metadata 보완 대상으로 분리하기 위한 샘플."
    limitation: "작성자 신뢰도나 author page 연결은 검증하지 않는다."

  - id: mutated_too_long_title
    path: mutated/too-long-title.md
    source_type: mutation
    label: borderline
    phenomena: [long_title]
    rationale: "title 길이 advisory를 확인하기 위한 샘플."
    limitation: "SERP 실제 truncation은 픽셀 폭과 검색엔진 rewrite에 좌우된다."

  - id: mutated_toc_before_opening
    path: mutated/toc-before-opening.md
    source_type: mutation
    label: acceptable_positive
    phenomena: [toc_before_opening]
    rationale: "TOC marker가 첫 문단 판단에 섞이지 않아야 함을 검증한다."
    limitation: "다양한 Liquid/Jekyll include 문법은 추가 샘플이 필요하다."

  - id: mutated_description_body_mismatch
    path: mutated/description-body-mismatch.md
    source_type: mutation
    label: negative
    phenomena: [description_body_mismatch]
    rationale: "description이 존재하지만 본문 주제와 완전히 다른 semantic metadata 오류를 검증한다."
    limitation: "현재 deterministic checker만으로는 잡기 어려우며 rubric/policy judge가 필요하다."

  - id: mutated_meaningless_alt
    path: mutated/meaningless-alt.md
    source_type: mutation
    label: negative
    phenomena: [meaningless_alt]
    rationale: "alt가 비어 있지는 않지만 `image-1`처럼 의미 없는 경우를 검증한다."
    limitation: "현재 길이/filename 기반 alt checker는 일부 meaningless alt를 놓칠 수 있다."

  - id: mutated_generic_link_text
    path: mutated/generic-link-text.md
    source_type: mutation
    label: borderline
    phenomena: [generic_link_text]
    rationale: "`여기` 같은 generic anchor text를 SEO/접근성 개선 후보로 보기 위한 샘플."
    limitation: "현재 body gate가 아니라 Lighthouse-equivalent heuristic 쪽에서 다루는 항목이다."

  - id: mutated_source_canonical
    path: mutated/source-canonical.md
    source_type: mutation
    label: borderline
    phenomena: [source_canonical_policy_conflict]
    rationale: "번역본 canonical을 원문 URL로 둘지 self-canonical로 둘지 정책 결정이 필요한 케이스."
    limitation: "정답은 SEO checker가 아니라 HFKREW 콘텐츠/번역 정책에서 결정해야 한다."

  - id: curated_metadata_policy_positive
    path: curated/metadata-policy-positive.md
    source_type: curated_internal
    label: acceptable_positive
    phenomena: [pass_like, curated_gold_positive, source_canonical_policy_conflict]
    rationale: "번역 SEO 정책처럼 도구가 자동 확정하면 안 되는 주제를, 본문 구조와 근거 링크는 갖춘 positive control로 문서화한다."
    limitation: "정책 내용의 최종 정답은 팀 합의가 필요하므로 기술적 gold label은 아니다."

  - id: curated_realistic_positive_no_image
    path: curated/realistic-positive-no-image.md
    source_type: curated_internal
    label: strong_positive
    phenomena: [pass_like, curated_gold_positive]
    rationale: "이미지 없이도 제목, 도입부, 공식 근거, 소제목 구조가 안정적인 내부 gold positive 후보."
    limitation: "팀 리뷰어가 승인한 최종 gold sample은 아니며, 실제 PR 코멘트 적용까지 검증하지는 않는다."

  - id: curated_semantic_negative_description
    path: curated/semantic-negative-description.md
    source_type: curated_internal
    label: negative
    phenomena: [pass_like, semantic_metadata_negative, description_body_mismatch]
    rationale: "본문 gate는 통과할 수 있지만 description이 완전히 다른 주제를 말하는 semantic metadata negative."
    limitation: "현재 deterministic body gate는 이 문제를 차단하지 못하며, policy/rubric layer 검증이 필요하다."

  - id: curated_semantic_negative_title
    path: curated/semantic-negative-title.md
    source_type: curated_internal
    label: negative
    phenomena: [pass_like, semantic_metadata_negative, title_body_mismatch]
    rationale: "본문 H1/도입부는 통과하지만 frontmatter title이 다른 주제를 말하는 semantic metadata negative."
    limitation: "현재 body-only gate는 frontmatter title과 본문 의미 정합성을 차단하지 않는다."

  - id: curated_hreflang_policy_positive
    path: curated/hreflang-policy-positive.md
    source_type: curated_internal
    label: acceptable_positive
    phenomena: [pass_like, curated_gold_positive, hreflang_policy_review, source_canonical_policy_conflict]
    rationale: "번역 페이지의 hreflang/canonical 후보 검토처럼 정책 입력이 필요한 positive policy case."
    limitation: "실제 hreflang 태그 생성과 Jekyll 렌더 결과 검증은 포함하지 않는다."

  - id: real_how_to_contribute
    path: real/2024-09-16-how-to-contribute.md
    source_type: real_hfkrew
    label: real_regression
    phenomena: [real_post, hfkrew_layout_h1_ambiguity]
    rationale: "짧은 기여 안내 글의 실제 구조를 보존한 회귀 샘플."
    limitation: "SEO 품질 정답 라벨은 아니며 current behavior 관찰용이다."

  - id: real_pseudocon_recap
    path: real/2025-05-31-2025-PseudoCon-recap.md
    source_type: real_hfkrew
    label: real_regression
    phenomena: [real_post, recap_post, multiple_h1]
    rationale: "행사 recap처럼 외부 citation 요구가 낮은 글 유형을 포함한다."
    limitation: "회고성 글에 정보성 글 규칙을 적용하면 오탐이 생길 수 있다."

  - id: real_translation_guide
    path: real/2025-06-22-HuggingFace-Docs-Translation-Guide.md
    source_type: real_hfkrew
    label: real_regression
    phenomena: [real_post, guide_post, toc_before_opening]
    rationale: "가이드 글과 TOC marker가 있는 실제 문서를 포함한다."
    limitation: "렌더링 후 TOC 처리 결과는 포함하지 않는다."

  - id: real_tiny_agents_ko
    path: real/2025-09-14-python-tiny-agents-ko.md
    source_type: real_hfkrew
    label: real_regression
    phenomena: [real_post, long_real_translation, code_heavy_post]
    rationale: "긴 기술 번역글의 heading/code 구조를 보존한다."
    limitation: "코드블록 내부 heading-like text를 완전히 검증하려면 별도 parser fixture가 필요하다."

  - id: real_mcp_servers_python
    path: real/2025-09-14-Implementing-MCP-Servers-in-Python.md
    source_type: real_hfkrew
    label: acceptable_positive
    phenomena: [real_post, pass_like, positive_candidate]
    rationale: "31개 실제 audit에서 body required failure 없이 통과한 실제 positive 후보."
    limitation: "frontmatter description은 여전히 누락되어 있어 완전한 SEO gold sample은 아니다."

  - id: real_vlm_explained_ko
    path: real/2025-10-12-vlm-explained-ko.md
    source_type: real_hfkrew
    label: acceptable_positive
    phenomena: [real_post, pass_like, positive_candidate, image_heavy_real_post]
    rationale: "이미지가 있으면서도 required body gate를 통과한 실제 positive 후보."
    limitation: "metadata category/description 보완은 별도 필요하다."

  - id: real_vlm_2025
    path: real/2025-10-20-2025-VLM.md
    source_type: real_hfkrew
    label: real_regression
    phenomena: [real_post, image_heavy_real_post, no_markdown_h1]
    rationale: "이미지가 많고 body H1이 없는 실제 글을 포함한다."
    limitation: "외부 이미지 URL 상태나 alt 의미 품질은 별도 검증이 필요하다."

  - id: real_rteb
    path: real/2025-12-01-rteb.md
    source_type: real_hfkrew
    label: real_regression
    phenomena: [real_post, pass_like, benchmark_post]
    rationale: "현재 checker에서 비교적 잘 통과하는 실제 positive-ish sample."
    limitation: "description 누락 등 metadata 문제는 여전히 존재한다."

  - id: real_hf_translation_hub_design
    path: real/2025-11-17-hf_translation_hub_mcp_design_and_tooling.md
    source_type: real_hfkrew
    label: acceptable_positive
    phenomena: [real_post, pass_like, positive_candidate]
    rationale: "31개 실제 audit에서 body required failure 없이 통과한 실제 positive 후보."
    limitation: "metadata description/category 보완이 필요해 완전한 SEO gold sample은 아니다."

  - id: real_ai_agents
    path: real/2025-12-15-ai-agents-are-here.md
    source_type: real_hfkrew
    label: real_regression
    phenomena: [real_post, long_real_translation, multiple_h1]
    rationale: "긴 번역글에서 H1 과다/heading 구조 문제가 어떻게 나타나는지 관찰한다."
    limitation: "원문 구조 보존과 SEO 구조 개선 사이의 정책 결정이 필요하다."

  - id: real_smolvla
    path: real/2025-12-22-smolvla.md
    source_type: real_hfkrew
    label: real_regression
    phenomena: [real_post, missing_author, toc_before_opening]
    rationale: "실제 metadata 누락과 TOC marker 케이스를 포함한다."
    limitation: "frontmatter title 누락이 의도인지 변환 오류인지 별도 확인 필요."

  - id: real_mcp_overview
    path: real/2025-12-28-translation-mcp-project-overview.md
    source_type: real_hfkrew
    label: real_regression
    phenomena: [real_post, no_markdown_h1, toc_before_opening]
    rationale: "MCP 프로젝트 소개 글의 실제 heading/TOC 구조를 포함한다."
    limitation: "프로젝트 소개 글에는 citation 요구가 정보성 글과 다를 수 있다."

  - id: real_mcp_n8n
    path: real/2026-01-05-hf-translation-mcp-n8n.md
    source_type: real_hfkrew
    label: real_regression
    phenomena: [real_post, workflow_post, image_heavy_real_post]
    rationale: "워크플로우 설명과 다수 이미지가 있는 실제 글을 포함한다."
    limitation: "이미지 alt의 의미 품질은 사람이 별도 판정해야 한다."

```

## generated

### generated/blocked-post.md

```markdown
---
title: "Transformer 모델 최적화 기법: 차단된 게시 예시"
description: "Transformer 모델 최적화 기법을 통해 AI 성능을 높이는 방법과 모델 압축, 전이 학습, 하드웨어 최적화 전략을 정리합니다."
image: /assets/images/transformer-optimization.png
categories: [AI, Tutorial]
author: test_author
robots: noindex
---

# Transformer 모델 최적화 기법: 차단된 게시 예시

Transformer 모델 최적화 기법은 대규모 언어 모델을 더 빠르고 저렴하게 운영하기 위한 핵심 전략입니다. 이 글은 학습률 조정, 모델 압축, 전이 학습, 하드웨어 최적화를 통해 모델 성능을 유지하면서 비용을 줄이는 방법을 설명합니다. [Hugging Face 블로그](https://huggingface.co/blog)와 공개 연구 사례를 함께 참고하면 각 전략의 장단점을 더 명확히 비교할 수 있습니다.

## Transformer 최적화는 무엇인가?

Transformer 최적화는 모델 구조, 학습 설정, 추론 환경을 함께 조정해 정확도와 처리 속도 사이의 균형을 맞추는 과정입니다. 예를 들어 학습률 스케줄링은 수렴 안정성을 높이고, 모델 압축은 배포 비용을 줄이는 데 도움을 줍니다.

## Transformer 모델은 어떻게 최적화하나?

첫째, 하이퍼파라미터를 조정해 학습 안정성을 높입니다. 둘째, 지식 증류와 양자화를 사용해 모델 크기를 줄입니다. 셋째, GPU 메모리 사용량을 줄이는 배치 전략을 적용해 추론 처리량을 높입니다.

![Transformer 모델 최적화 예시](/assets/images/transformer-optimization-example.png)

```

### generated/excellent-post.md

```markdown
---
title: "Hugging Face 문서 번역 PR을 SEO 관점에서 검토하는 방법"
description: "Hugging Face 문서 번역 PR을 게시 전에 점검할 때 확인해야 할 제목, 도입부, 링크, 이미지 alt, 메타데이터 기준을 정리합니다."
image: /assets/images/seo-review/translation-pr-checklist.png
categories: [SEO, Translation, Community]
author: test_author
---

# Hugging Face 문서 번역 PR을 SEO 관점에서 검토하는 방법

Hugging Face 문서 번역 PR을 SEO 관점에서 검토할 때는 검색엔진을 위한 키워드 반복보다 독자가 글의 목적을 빠르게 이해할 수 있는지가 먼저입니다. 제목과 첫 문단은 번역 대상, 독자, 검토 기준을 같은 방향으로 설명해야 하며, 본문은 게시 전에 확인할 수 있는 구조적 문제를 구체적으로 드러내야 합니다. 이 글은 HFKREW 블로그에 올라오는 번역·가이드 글을 기준으로, 게시 전 PR 리뷰에서 바로 확인할 수 있는 항목을 정리합니다.

검토 기준은 Google Search Central의 [도움이 되는 콘텐츠 문서](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)와 [title link 가이드](https://developers.google.com/search/docs/appearance/title-link)를 참고해, HFKREW 블로그에 맞게 단순화했습니다. 목표는 자동 점수 하나를 높이는 것이 아니라, 번역 글이 어떤 내용을 다루는지 검색결과와 본문에서 일관되게 전달되도록 만드는 것입니다.

## 번역 PR의 제목과 도입부는 어떻게 맞추나?

제목은 원문 제목을 그대로 옮기는 것에서 끝나지 않습니다. 한국어 독자가 검색할 표현을 고려해 핵심 주제를 앞쪽에 두고, 첫 문단에서는 글이 다루는 범위와 읽고 나면 얻을 수 있는 정보를 분명히 적어야 합니다. 예를 들어 “MCP 서버 사용법”이라는 제목이라면 도입부도 MCP 서버의 목적, 설치 또는 실행 범위, 예상 독자를 바로 설명해야 합니다.

도입부가 TOC, 인사말, 프로젝트 배경만으로 시작하면 검색엔진과 독자 모두 본문의 주제를 늦게 파악합니다. 게시 전 리뷰에서는 첫 세 문단 안에 주제, 대상 독자, 핵심 질문에 대한 요약 답변이 들어 있는지 확인합니다.

## 본문 구조와 링크는 무엇을 확인하나?

본문의 소제목은 독자가 스캔할 수 있는 질문형 또는 주제형 문장이어야 합니다. 긴 번역 글이라면 원문 구조를 보존하되, 한국어 독자가 놓치기 쉬운 개념에는 짧은 설명을 덧붙이는 편이 좋습니다. 내부 링크는 “여기”보다 “HFKREW 번역 가이드”처럼 목적이 드러나는 앵커를 사용해야 합니다.

외부 링크는 주장이나 도구 설명의 근거를 보여줄 때 사용합니다. Hugging Face Hub 기능을 설명한다면 [Hugging Face Hub 문서](https://huggingface.co/docs/hub/index)처럼 독자가 추가 확인을 할 수 있는 공식 문서를 연결하는 것이 좋습니다. 단, 링크 개수를 늘리기 위해 본문과 직접 관련 없는 문서를 붙이는 것은 피해야 합니다.

## 이미지 alt와 메타데이터는 언제 보완하나?

이미지가 있다면 alt는 파일명이 아니라 이미지가 본문에서 맡는 역할을 설명해야 합니다. “image-1”이나 “screenshot”은 검색과 접근성 모두에 도움이 되지 않습니다. 워크플로우 캡처라면 “번역 PR 생성 과정을 보여주는 GitHub Actions 워크플로우”처럼 화면의 의미를 적는 것이 더 낫습니다.

본문 구조가 통과되면 메타데이터를 보완합니다. description은 첫 문단을 단순 복사하기보다 글이 제공하는 판단 기준과 대상 독자를 압축해야 합니다. canonical과 hreflang은 번역본을 독립 색인 대상으로 볼지에 따라 달라지므로, SEO 도구가 임의로 결정하기보다 팀 정책을 기준으로 생성해야 합니다.

![번역 PR SEO 검토 체크리스트](/assets/images/seo-review/translation-pr-checklist.png)

```

### generated/good-post.md

```markdown
---
title: "한국어 기술 번역 글의 메타 설명 작성 기준"
description: "한국어 기술 번역 글을 게시하기 전에 title, description, 도입부가 같은 주제를 설명하는지 점검하는 기준을 정리합니다."
image: "/assets/images/seo-review/meta-description-guide.png"
categories:
  - SEO
  - Translation
author: "test_author"
---

# 한국어 기술 번역 글의 메타 설명 작성 기준

한국어 기술 번역 글의 메타 설명은 본문을 과장해서 홍보하는 문구가 아니라, 독자가 검색결과에서 글의 범위와 쓸모를 빠르게 판단하도록 돕는 요약입니다. 특히 Hugging Face 문서나 블로그 번역 글은 원문 제목, 한국어 제목, 첫 문단, description이 서로 다른 약속을 하지 않도록 맞추는 것이 중요합니다. 이 기준은 게시 전 PR에서 메타데이터를 점검할 때 사용할 수 있습니다.

Google Search Central은 [snippet 제어 문서](https://developers.google.com/search/docs/appearance/snippet)에서 meta description이 검색결과 스니펫 후보로 사용될 수 있지만 항상 그대로 노출되지는 않는다고 설명합니다. 따라서 description은 길이 숫자를 맞추는 것보다 본문과의 정합성, 고유성, 핵심 정보의 앞부분 배치가 더 중요합니다.

## 메타 설명은 무엇을 포함해야 하나?

좋은 description은 글이 다루는 대상, 독자가 얻는 정보, 본문에서 실제로 설명하는 범위를 한두 문장으로 담습니다. 예를 들어 번역 MCP 서버 글이라면 “MCP 서버의 개념”만 말하는 대신, 설치 방식, 실행 흐름, PR 자동화처럼 본문에 있는 구체 범위를 함께 적어야 합니다.

반대로 본문에 없는 성능 수치, 지원하지 않는 기능, 과장된 결과를 넣으면 검색결과와 실제 글 사이의 기대가 어긋납니다. description은 광고 문구가 아니라 본문에 대한 정확한 약속이어야 합니다.

## 제목, 도입부, description은 어떻게 비교하나?

게시 전에는 title, H1, 첫 문단, description을 나란히 놓고 같은 주제를 설명하는지 확인합니다. title이 “n8n MCP 워크플로우”인데 description이 “Hugging Face 모델 학습 최적화”를 말한다면 명백한 불일치입니다. 이런 오류는 단순 길이 검사로는 잡기 어렵기 때문에 자동 signal과 사람 리뷰가 함께 필요합니다.

문서가 번역본이라면 canonical과 hreflang도 함께 확인해야 합니다. 다만 번역본을 독립 색인 대상으로 둘지, 원문 보조 자료로 둘지는 SEO 도구가 단독으로 정할 문제가 아니며 콘텐츠 운영 정책으로 결정해야 합니다.

![메타 설명 작성 기준 예시](/assets/images/seo-review/meta-description-guide.png)

```

### generated/medium-post.md

```markdown
---
title: "Transformer 모델 최적화 기법"
image: "https://example.com/transformer-optimization.jpg"
categories: [AI]
---

# Transformer 모델 최적화 기법

Transformer 모델은 자연어 처리에서 혁신적인 변화를 가져왔습니다. 그러나 이러한 모델은 대량의 데이터와 계산 자원을 요구하기 때문에 최적화가 필수적입니다. 이 글에서는 Transformer 모델의 최적화 기법을 살펴보겠습니다.

## 하이퍼파라미터 조정

하이퍼파라미터 조정은 모델 성능을 극대화하는 데 중요한 역할을 합니다. 학습률, 배치 크기, 층 수 등을 조정함으로써 모델의 학습 효율성을 높일 수 있습니다. 

## 지식 증류

지식 증류는 대형 모델의 지식을 소형 모델로 전이하여 성능을 유지하면서 경량화하는 기법입니다. 이를 통해 모델의 추론 속도를 향상시킬 수 있습니다.

![Transformer 모델 최적화](https://example.com/transformer-optimization.jpg "Transformer 모델 최적화")
```

### generated/poor-post.md

```markdown
---
categories: [머신러닝, 딥러닝]
---

### Transformer 모델 최적화 기법

Transformer 모델의 성능을 향상시키기 위해 다양한 최적화 기법이 개발되고 있습니다. 대표적으로는 학습률 조정, 정규화 기법, 그리고 모델 경량화 방법이 있습니다. 이러한 기법들은 모델의 일반화 능력을 높이고, 훈련 시간을 단축시킵니다.

![](image.png)
```

## curated

### curated/hreflang-policy-positive.md

```markdown
---
title: "번역 페이지의 hreflang 후보를 검토하는 기준"
description: "한국어 번역 페이지를 독립 색인 대상으로 운영할 때 hreflang 후보와 원문 URL 관계를 어떻게 검토할지 정리합니다."
categories: [SEO, Translation]
author: test_author
---

# 번역 페이지의 hreflang 후보를 검토하는 기준

번역 페이지의 hreflang 후보를 검토하는 기준은 검색엔진에 언어별 대체 페이지 관계를 명확하게 설명하기 위한 정책입니다. 한국어 번역본이 독립 색인 대상이라면 self-canonical을 유지하면서 원문과 번역본을 alternate 관계로 설명하는 구성이 자연스러울 수 있습니다. 다만 이 판단은 글의 번역 방식, 원문과의 차이, HFKREW 콘텐츠 운영 정책에 따라 달라집니다.

Google Search Central의 [localized versions 문서](https://developers.google.com/search/docs/specialty/international/localized-versions)는 언어 또는 지역별 대체 URL을 표시하는 방법을 설명합니다. SEO skill은 이 문서를 근거로 hreflang 후보를 제안할 수 있지만, 번역본을 원문의 중복 페이지로 볼지 독립 페이지로 볼지는 팀 정책을 읽어야 합니다.

## 자동 도구가 확인할 수 있는 것은 무엇인가?

자동 도구는 원문 URL, 번역본 URL, 언어 코드, canonical 값을 수집하고 서로 충돌하는지 리포트할 수 있습니다. 예를 들어 한국어 번역본이 `ko` 페이지인데 canonical이 영어 원문으로 고정되어 있다면, 독립 색인 정책과 충돌할 수 있다는 경고를 남길 수 있습니다.

하지만 도구가 모든 번역본에 self-canonical을 강제해서는 안 됩니다. 프로젝트가 원문 중심 노출을 의도할 수도 있기 때문입니다. 따라서 policy 파일에 `translation_indexing: independent` 또는 `translation_indexing: source_support` 같은 값을 두고, SEO skill은 그 정책을 기준으로 후보를 검증하는 구조가 안전합니다.

## PR 리뷰에서는 어떤 증거가 필요하나?

리뷰어는 title, description, 원문 URL, 번역본 URL, canonical, hreflang 후보를 한 화면에서 봐야 합니다. 이 정보가 있어야 번역본을 독립 페이지로 운영할지, 원문 보조 자료로 둘지 판단할 수 있습니다. SEO 자동화는 결론을 숨기지 말고, 정책 입력이 없으면 `NEEDS_REVIEW`로 남기는 편이 낫습니다.


```

### curated/metadata-policy-positive.md

```markdown
---
title: "번역 블로그의 canonical과 hreflang 정책을 정하는 방법"
description: "번역 블로그 글을 독립 색인 대상으로 운영할 때 canonical과 hreflang을 어떻게 판단해야 하는지 SEO 리뷰 관점에서 정리합니다."
categories: [SEO, Translation]
author: test_author
---

# 번역 블로그의 canonical과 hreflang 정책을 정하는 방법

번역 블로그의 canonical과 hreflang 정책은 단순한 메타 태그 생성 문제가 아니라, 번역본을 검색엔진에 어떤 문서로 설명할지 정하는 콘텐츠 운영 정책입니다. 같은 원문에서 출발한 글이라도 한국어 독자를 위해 구조와 설명을 보강했다면 독립 색인 대상으로 볼 수 있고, 원문을 거의 그대로 보조 노출하는 목적이라면 다른 판단이 필요합니다. 이 글은 SEO 도구가 자동으로 결정하지 말아야 할 영역과, 게시 전 PR에서 확인할 수 있는 기술 신호를 분리합니다.

Google Search Central의 [canonical 문서](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)는 중복 또는 유사 URL 중 대표 URL을 지정하는 방법을 설명합니다. 반면 번역·지역화 페이지는 단순 중복과 다를 수 있으므로, canonical만으로 모든 국제화 신호를 대신하려고 하면 의도가 흐려집니다.

## 번역본을 독립 색인 대상으로 볼 때는 무엇이 달라지나?

한국어 번역본이 독립 색인 대상이라면 canonical은 보통 번역본 자신을 가리키는 것이 자연스럽습니다. 이때 원문과 번역본의 관계는 hreflang이나 본문 내 출처 표기로 설명할 수 있습니다. 중요한 점은 검색엔진이 한국어 페이지를 원문의 중복 URL로만 보지 않도록, 제목과 도입부, 본문 설명이 한국어 독자의 검색 의도를 직접 다루어야 한다는 것입니다.

독립 색인 정책을 택했다면 메타 description도 한국어 독자가 얻는 정보를 기준으로 작성해야 합니다. 원문 소개 문장을 그대로 직역하기보다, 번역본에서 실제로 보강한 설명과 국내 독자가 확인해야 할 맥락을 담는 편이 더 일관됩니다.

## SEO 도구는 어디까지 자동화해야 하나?

SEO 도구는 canonical 후보, hreflang 후보, self-canonical 여부, 원문 URL 존재 여부를 리포트할 수 있습니다. 하지만 어떤 정책이 맞는지는 프로젝트의 콘텐츠 전략과 번역 운영 방식에 따라 달라집니다. 따라서 도구는 정책 파일이나 명시 입력을 읽고 검증해야 하며, 기본값만으로 원문 canonical을 강제하면 안 됩니다.

게시 전 PR 리뷰에서는 canonical이 한 개만 있는지, 상대 URL이 아닌 절대 URL인지, 번역본 URL과 원문 URL의 역할이 섞이지 않았는지 확인합니다. 정책이 비어 있다면 자동 수정을 적용하기보다 리뷰어에게 결정을 요청하는 상태로 남겨야 합니다.


```

### curated/realistic-positive-no-image.md

```markdown
---
title: "HFKREW 번역 글의 게시 전 SEO 리뷰 체크리스트"
description: "HFKREW 번역 글을 게시하기 전에 제목, 도입부, 링크, 메타데이터 정책을 점검하는 실무 체크리스트입니다."
categories: [SEO, Community]
author: test_author
---

# HFKREW 번역 글의 게시 전 SEO 리뷰 체크리스트

HFKREW 번역 글의 게시 전 SEO 리뷰 체크리스트는 자동 도구가 잡을 수 있는 구조 문제와 사람이 판단해야 하는 의미 문제를 분리하는 데 목적이 있습니다. 번역 품질 자체는 별도 리뷰 대상이지만, 검색결과에서 글의 주제가 명확하게 보이는지, 본문 첫 부분이 제목의 약속을 바로 설명하는지, 링크와 이미지 설명이 독자에게 도움이 되는지는 SEO 단계에서 확인할 수 있습니다.

이 체크리스트는 Google의 [SEO starter guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)처럼 검색엔진이 콘텐츠를 이해하기 쉽게 만드는 기본 원칙을 HFKREW 블로그 흐름에 맞게 줄인 것입니다. 목표는 모든 글을 같은 형식으로 바꾸는 것이 아니라, 게시 전 PR에서 반복적으로 놓치는 위험을 빠르게 찾는 것입니다.

## 자동 검사로 먼저 확인할 항목은 무엇인가?

자동 검사는 noindex, 깨진 내부 링크, 깨진 로컬 이미지, 빈 alt처럼 명확한 문제를 우선 확인해야 합니다. 이런 항목은 글의 장르나 작성자 스타일과 무관하게 게시 품질을 직접 해치므로 hard blocker로 다루기 쉽습니다. 반대로 도입부 길이, citation 개수, H1 개수는 블로그 layout과 글 유형에 따라 해석이 달라질 수 있으므로 signal로 남기고 사람이 판단하는 편이 안전합니다.

PR 코멘트에는 통과 여부만 쓰기보다 어떤 증거 때문에 문제가 됐는지 함께 적어야 합니다. 예를 들어 “이미지 alt 누락”보다 “워크플로우 캡처 이미지 3개 중 2개가 빈 alt입니다”처럼 수정할 위치와 이유가 보여야 합니다.

## 사람이 마지막으로 판단할 항목은 무엇인가?

사람 리뷰는 title, description, 첫 문단이 같은 주제를 설명하는지 확인해야 합니다. description이 존재해도 본문과 다른 주제를 말하면 검색결과에서 잘못된 기대를 만들 수 있습니다. 또한 번역본 canonical 정책, 원문 링크 표기, 한국어 독자를 위한 보강 설명은 프로젝트 정책과 연결되므로 자동 도구가 단독으로 확정하면 안 됩니다.

이 구조를 따르면 GitHub Action은 반복 가능한 증거를 만들고, GPT나 리뷰어는 그 증거를 바탕으로 더 높은 수준의 판단을 할 수 있습니다. 자동화의 역할은 최종 편집 결정을 대체하는 것이 아니라, 같은 실수를 빠르게 발견하도록 돕는 것입니다.


```

### curated/semantic-negative-description.md

```markdown
---
title: "HFKREW 번역 글의 게시 전 SEO 리뷰 체크리스트"
description: "GPU 클러스터 비용 절감을 위한 오토스케일링 전략과 쿠버네티스 배포 자동화 방법을 단계별로 설명하고, 클라우드 인프라 운영자가 리소스 사용량을 줄이기 위해 확인해야 할 모니터링 지표, 비용 경보, 배포 전략, 장애 대응 기준과 주요 운영 체크포인트도 자세하게 정리합니다."
image: /assets/images/cloud/autoscaling-guide.png
categories: [SEO, Community]
author: test_author
---

# HFKREW 번역 글의 게시 전 SEO 리뷰 체크리스트

HFKREW 번역 글의 게시 전 SEO 리뷰 체크리스트는 자동 도구가 잡을 수 있는 구조 문제와 사람이 판단해야 하는 의미 문제를 분리하는 데 목적이 있습니다. 번역 품질 자체는 별도 리뷰 대상이지만, 검색결과에서 글의 주제가 명확하게 보이는지, 본문 첫 부분이 제목의 약속을 바로 설명하는지, 링크와 이미지 설명이 독자에게 도움이 되는지는 SEO 단계에서 확인할 수 있습니다.

이 체크리스트는 Google의 [SEO starter guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)처럼 검색엔진이 콘텐츠를 이해하기 쉽게 만드는 기본 원칙을 HFKREW 블로그 흐름에 맞게 줄인 것입니다. 목표는 모든 글을 같은 형식으로 바꾸는 것이 아니라, 게시 전 PR에서 반복적으로 놓치는 위험을 빠르게 찾는 것입니다.

## 자동 검사로 먼저 확인할 항목은 무엇인가?

자동 검사는 noindex, 깨진 내부 링크, 깨진 로컬 이미지, 빈 alt처럼 명확한 문제를 우선 확인해야 합니다. 이런 항목은 글의 장르나 작성자 스타일과 무관하게 게시 품질을 직접 해치므로 hard blocker로 다루기 쉽습니다. 반대로 도입부 길이, citation 개수, H1 개수는 블로그 layout과 글 유형에 따라 해석이 달라질 수 있으므로 signal로 남기고 사람이 판단하는 편이 안전합니다.

## 이 샘플은 왜 negative인가?

본문 구조는 통과할 수 있지만 frontmatter description이 본문 주제와 완전히 다릅니다. 이 케이스는 deterministic body gate만으로는 충분하지 않으며, title, description, opening paragraph의 의미 정합성을 별도 policy 또는 LLM rubric에서 판단해야 한다는 사실을 보여주기 위한 샘플입니다.

```

### curated/semantic-negative-title.md

```markdown
---
title: "GPU 클러스터 오토스케일링 비용 최적화 가이드"
description: "HFKREW 번역 글을 게시하기 전에 제목, 도입부, 링크, 메타데이터 정책을 점검하는 실무 체크리스트를 정리하고, 자동 검사와 사람 리뷰가 각각 확인해야 할 구조 문제, 의미 정합성 기준, PR 코멘트 작성 방식, 수정 우선순위 판단 기준을 실무 중심으로 설명합니다."
image: /assets/images/seo-review/checklist.png
categories: [SEO, Community]
author: test_author
---

# HFKREW 번역 글의 게시 전 SEO 리뷰 체크리스트

HFKREW 번역 글의 게시 전 SEO 리뷰 체크리스트는 자동 도구가 잡을 수 있는 구조 문제와 사람이 판단해야 하는 의미 문제를 분리하는 데 목적이 있습니다. 번역 품질 자체는 별도 리뷰 대상이지만, 검색결과에서 글의 주제가 명확하게 보이는지, 본문 첫 부분이 제목의 약속을 바로 설명하는지, 링크와 이미지 설명이 독자에게 도움이 되는지는 SEO 단계에서 확인할 수 있습니다.

이 체크리스트는 Google의 [SEO starter guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)처럼 검색엔진이 콘텐츠를 이해하기 쉽게 만드는 기본 원칙을 HFKREW 블로그 흐름에 맞게 줄인 것입니다. 목표는 모든 글을 같은 형식으로 바꾸는 것이 아니라, 게시 전 PR에서 반복적으로 놓치는 위험을 빠르게 찾는 것입니다.

## 이 샘플은 왜 negative인가?

본문 H1과 도입부는 HFKREW SEO 리뷰를 설명하지만 frontmatter title은 GPU 클러스터 비용 최적화를 말합니다. 현재 body-only deterministic gate는 본문 구조만 보기 때문에 이 불일치를 차단하지 못할 수 있습니다. 이 샘플은 metadata policy 또는 LLM rubric이 title, H1, opening paragraph의 의미 정합성을 봐야 한다는 근거로 사용합니다.

## 리뷰어는 무엇을 확인해야 하나?

PR 코멘트에는 title, description, opening paragraph를 함께 보여주어야 합니다. 사람이 세 문장을 나란히 보면 어떤 필드가 다른 약속을 하는지 빠르게 판단할 수 있습니다. 자동 도구는 이 증거를 안정적으로 수집하고, 최종 수정 여부는 리뷰어 또는 정책 레이어가 결정해야 합니다.

```

## mutated

### mutated/README.md

```markdown
# Mutated SEO Test Fixtures

이 디렉터리는 실제 블로그 글에서 항상 나오지 않는 실패 모드를 검증하기 위해, 정상에 가까운 샘플 글을 의도적으로 망가뜨린 네거티브 테스트 데이터셋입니다.

각 fixture는 "한 가지 문제를 확실히 만들었을 때 checker가 기대한 status를 내는지"를 확인하기 위한 용도입니다.

## 케이스 요약

| 파일 | 의도적으로 만든 문제 | 기대 동작 |
|---|---|---|
| `missing-description.md` | frontmatter `description` 제거 | 현재 정책상 body gate는 통과하고, metadata 보완 대상으로 분리 |
| `missing-alt.md` | 이미지 alt를 `![](...)`로 제거 | 이미지 alt 누락을 본문 품질 실패로 감지 |
| `noindex.md` | frontmatter에 `robots: noindex` 추가 | 게시 차단 blocker로 감지 |
| `broken-internal-link.md` | 존재하지 않는 내부 링크 추가 | `target_root`가 주어졌을 때 깨진 내부 링크 blocker로 감지 |
| `short-opening.md` | 첫 문단을 매우 짧게 축소 | opening summary 규칙 검증용. 현재는 기대만큼 강하게 실패하지 않아 룰 조정 필요 |

## 1. `missing-description.md`

의도:

- frontmatter에서 `description`만 제거했습니다.
- 본문 자체는 정상에 가깝게 유지했습니다.

검증 포인트:

- `description` 누락은 SEO 메타데이터 문제입니다.
- 현재 SEO skill 정책에서는 frontmatter 보완이 body gate 통과 이후 metadata writer의 역할이므로, 이 케이스만으로 본문 평가가 막히면 안 됩니다.
- 따라서 이 케이스는 "메타데이터 누락을 감지하되 body quality failure와 혼동하지 않는지"를 보기 위한 샘플입니다.

원문:

```md
---
title: "검색 임베딩 벤치마크 입문"
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다. 내부 운영에서는 공개 벤치마크와 자체 데이터셋을 함께 사용하는 것이 좋습니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)
```

## 2. `missing-alt.md`

의도:

- 이미지 alt를 비워 `![](...)` 형태로 만들었습니다.
- 나머지 frontmatter와 본문은 정상에 가깝게 유지했습니다.

검증 포인트:

- 빈 alt는 검색엔진이 이미지의 의미를 이해하기 어렵게 만들고, 접근성 측면에서도 문제가 됩니다.
- checker가 이미지 alt 누락을 본문 품질 문제로 감지해야 합니다.

원문:

```md
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다. 내부 운영에서는 공개 벤치마크와 자체 데이터셋을 함께 사용하는 것이 좋습니다.

![](/assets/images/rteb/thumbnail.png)
```

## 3. `noindex.md`

의도:

- frontmatter에 `robots: noindex`를 추가했습니다.
- 본문 품질은 정상에 가깝게 유지했습니다.

검증 포인트:

- 게시 대상 문서가 `noindex`를 가지고 있으면 검색엔진 색인을 명시적으로 막는 상태입니다.
- 본문 품질이 좋아도 게시 전 hard blocker로 분류되어야 합니다.
- 이 케이스는 blocker가 body quality보다 우선하는지 확인합니다.

원문:

```md
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
robots: noindex
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다. 내부 운영에서는 공개 벤치마크와 자체 데이터셋을 함께 사용하는 것이 좋습니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)
```

## 4. `broken-internal-link.md`

의도:

- 본문 중간에 존재하지 않는 내부 링크를 추가했습니다.
- 외부 링크는 정상으로 유지했고, 내부 링크 하나만 깨뜨렸습니다.

검증 포인트:

- 내부 링크가 깨져 있으면 게시 후 사용자 탐색과 크롤링 품질에 문제가 생깁니다.
- `target_root`가 주어져 repository 기준으로 링크를 resolve할 수 있을 때, 존재하지 않는 내부 링크는 hard blocker로 분류되어야 합니다.
- 외부 URL과 내부 URL을 구분해서 내부 URL만 repository 파일 존재 여부로 검사하는지도 확인합니다.

원문:

```md
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다. 관련 내용은 [없는 내부 글](/definitely-missing-internal-page/)도 참고하세요.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다. 내부 운영에서는 공개 벤치마크와 자체 데이터셋을 함께 사용하는 것이 좋습니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)
```

## 5. `short-opening.md`

의도:

- 첫 문단을 "검색 임베딩을 소개합니다." 수준으로 짧게 줄였습니다.
- 나머지 본문 구조는 정상에 가깝게 유지했습니다.

검증 포인트:

- opening summary는 글의 첫 실문단이 검색 의도와 본문 내용을 충분히 요약하는지 보기 위한 규칙입니다.
- 이 케이스는 짧은 도입부를 감지하기 위한 샘플입니다.
- 현재 구현에서는 이 케이스가 기대만큼 강하게 실패하지 않습니다. 따라서 opening summary 규칙은 threshold나 첫 실문단 추출 방식 조정이 필요합니다.

원문:

```md
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

# 검색 임베딩 벤치마크 입문

검색 임베딩을 소개합니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다. 내부 운영에서는 공개 벤치마크와 자체 데이터셋을 함께 사용하는 것이 좋습니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)
```


```

### mutated/broken-image-path.md

```markdown
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/missing-thumbnail.png)

```

### mutated/broken-internal-link.md

```markdown
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다. 관련 내용은 [없는 내부 글](/definitely-missing-internal-page/)도 참고하세요.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다. 내부 운영에서는 공개 벤치마크와 자체 데이터셋을 함께 사용하는 것이 좋습니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)

```

### mutated/description-body-mismatch.md

```markdown
---
title: "검색 임베딩 벤치마크 입문"
description: "Kubernetes 클러스터 운영 비용을 줄이는 오토스케일링 전략과 배포 자동화 방법을 설명합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)

```

### mutated/empty-body.md

```markdown
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---


```

### mutated/generic-link-text.md

```markdown
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [여기](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)

```

### mutated/heading-skip.md

```markdown
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

### 검색 품질 지표

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)

```

### mutated/layout-title-no-body-h1.md

```markdown
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)

```

### mutated/meaningless-alt.md

```markdown
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다.

![image-1](/assets/images/rteb/thumbnail.png)

```

### mutated/missing-alt.md

```markdown
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다. 내부 운영에서는 공개 벤치마크와 자체 데이터셋을 함께 사용하는 것이 좋습니다.

![](/assets/images/rteb/thumbnail.png)

```

### mutated/missing-author.md

```markdown
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)

```

### mutated/missing-description.md

```markdown
---
title: "검색 임베딩 벤치마크 입문"
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다. 내부 운영에서는 공개 벤치마크와 자체 데이터셋을 함께 사용하는 것이 좋습니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)

```

### mutated/missing-h1-no-title.md

```markdown
---
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)

```

### mutated/multiple-h1.md

```markdown
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

# 검색 모델 비교 방법

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다. 내부 운영에서는 공개 벤치마크와 자체 데이터셋을 함께 사용하는 것이 좋습니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)

```

### mutated/no-citation.md

```markdown
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, 순위 품질을 비교합니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)

```

### mutated/noindex.md

```markdown
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
robots: noindex
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다. 내부 운영에서는 공개 벤치마크와 자체 데이터셋을 함께 사용하는 것이 좋습니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)

```

### mutated/short-opening.md

```markdown
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

# 검색 임베딩 벤치마크 입문

검색 임베딩을 소개합니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다. 내부 운영에서는 공개 벤치마크와 자체 데이터셋을 함께 사용하는 것이 좋습니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)

```

### mutated/source-canonical.md

```markdown
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
canonical: https://huggingface.co/blog/rteb
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)

```

### mutated/toc-before-opening.md

```markdown
---
title: "검색 임베딩 벤치마크 입문"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

<!--toc-->

* TOC
{:toc}

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)

```

### mutated/too-long-title.md

```markdown
---
title: "검색 임베딩 벤치마크 입문과 한국어 검색 품질 평가를 위한 모델 비교 기준 및 운영 전략 전체 정리"
description: "검색 임베딩 벤치마크의 평가 기준과 모델 비교 방법을 설명하고, 한국어 검색 품질을 검증할 때 확인해야 할 핵심 지표를 정리합니다."
image: /assets/images/rteb/thumbnail.png
categories: [AI, Benchmark]
author: test_author
---

# 검색 임베딩 벤치마크 입문

검색 임베딩 벤치마크는 임베딩 모델이 실제 검색 문제에서 얼마나 정확하게 동작하는지 확인하는 평가 절차입니다. 이 글은 데이터셋 구성, 평가 지표, 모델 비교 기준을 함께 설명해 실무자가 어떤 모델을 선택해야 하는지 빠르게 판단하도록 돕습니다. 자세한 배경은 [Hugging Face 블로그](https://huggingface.co/blog/rteb)에서 확인할 수 있습니다.

## 검색 임베딩 벤치마크는 무엇을 측정하나?

검색 품질은 단순 정확도만으로 판단하기 어렵습니다. 검색 질의와 문서의 의미적 관련성, 도메인 이동성, 한국어 처리 안정성을 함께 봐야 합니다.

## 검색 모델은 어떻게 비교하나?

동일한 질의 집합과 문서 후보를 사용하고, MRR이나 nDCG 같은 지표로 순위 품질을 비교합니다.

![검색 임베딩 벤치마크 구조](/assets/images/rteb/thumbnail.png)

```

## real

### real/2024-09-16-how-to-contribute.md

```markdown
---
layout: post
title: "🤗 어떻게 기여하나요?"
author: admin
categories: [contribute, tutorial]
image: assets/images/thumbnail_default.png
---
* TOC
{:toc}
<!--toc-->
Hugging Face KREW의 일원으로 🤗 Hugging Face 생태계에 기여하는 방법을 안내합니다.

누구나 🤗 오픈소스 컨트리뷰터가 될 수 있습니다!
이 글에서는 여러분이 오픈소스 프로젝트에 더 쉽게 기여할 수 있도록, 다음 3가지 방법을 중심으로 유용한 팁과 방법을 안내해 드려요!

1. <a href="#docs">공식 문서 한글화 기여</a><a id="docs"></a>
2. <a href="#code">Hugging Face Github 코드 기여</a><a id="code"></a>
3. <a href="#blog">Hugging Face KREW Blog 기여</a><a id="blog"></a>

<br>

## <a href="#docs">공식 문서 한글화 기여</a><a id="docs"></a>

작성 중 입니다.

[🤗 TRANSLATING guide](https://github.com/huggingface/transformers/blob/main/docs/TRANSLATING.md)을 바탕으로 한글화 작업을 진행합니다.

## <a href="#code">Hugging Face Github 코드 기여</a><a id="code"></a>

작성 중 입니다.

## <a href="#blog">Hugging Face KREW Blog 기여</a><a id="blog"></a>

### 환경 설정

```shell
# Repo Clone
git clone https://github.com/Hugging-Face-KREW/hugging-face-krew.github.io.git

# 종속성 설치
bundle install

# Jekyll 호스팅 아래 2가지 명령어 모두 가능
bundle exec jekyll serve
jekyll serve --watch
```

### 블로그 포스팅 가이드

기본적으로 [Jekyll docs](https://jekyllrb.com/docs/)에 맞춰 글을 작성하면 되지만, 다음 규칙을 지켜주세요.

- 모든 글은 `_posts` 하위 폴더에 위치하며, `YYYY-MM-DD-name-of-post.md` 형식의 파일명 규칙을 따릅니다.
- 다음 형식을 고려하여 글을 작성해주세요.

  ```
  ---
  layout: post
  title: "글 제목 작성"
  author: 저자 이름
  categories: [contribute, tutorial]
  image: assets/images/이미지 위치.png
  ---

  이 부분은 글이 외부로 표시될 때 혹은 북마크로 삽입될 때 나타나는 문장입니다. (글을 요약해서 한 문장으로 정리하는 것을 권장해요)

  진짜 글은 여기서 부터 작성하세요!!
  ```

- 이미지 파일은 `assets/iamges` 하위 폴더에 위치하며, 각 특성에 따라 다음과 같이 분류됩니다:
  - `blog` 블로그 포스팅과 관련된 모든 이미지
  - `author` 블로그 저자와 관련된 모든 이미지
  - `manage` 블로그 운영과 관련된 모든 이미지
- 고해상도의 이미지는 적절히 변경하여 업로드 해주세요.
- TOC(Table of Contents) 트리 형식을 지원하는 형태로 글을 작성합니다.
  - TOC 형식은 다음과 같이 생성합니다. : `<a href="#result">Result</a>`
  - 영문 이외의 한글, 특수문자가 들어갈 경우 : `<a href="#result">결론</a><a id="result"></a>`
  - H2 태그에 적용하는 것을 권장하지만, H3도 가능합니다.

```

### real/2025-05-31-2025-PseudoCon-recap.md

```markdown
---
layout: post
title: "HuggingFace KREW in 2025 PseudoCon"
author: jeong
categories: [contribute]
image: assets/images/blog/posts/2025-05-31-2025-PseudoCon-recap/thumbnail.png
---
* TOC
{:toc}
<!--toc-->
5월 17일, 비영리 연구 공동체 '가짜 연구소'가 주최한 2025 PseudoCon에 참여한 현장을 생생히 전달드립니다 🤗
----
Hugging Face KREW 리서치 팀은 인공지능 및 데이터 과학 비영리 모임인 가짜 연구소의 일원으로 활동하고 있는데요, 
이번 컨퍼런스에서는 KREW의 다양한 활동과 현재 진행 중인 세 가지 프로젝트의 여정을 공유하는 시간을 가졌습니다 🤗


# 👩🏻‍🍳 Hugging Face 쿡북요리사
<div align="center">
    <img src="../assets/images/blog/posts/2025-05-31-2025-PseudoCon-recap/쿡북1.png" width="250"/>
    <img src="../assets/images/blog/posts/2025-05-31-2025-PseudoCon-recap/쿡북2.png" width="500"/>
</div>

Hugging Face에는 오픈소스 도구와 모델을 활용해 AI 애플리케이션을 구축하고 다양한 과제를 해결할 수 있는 실용적인 예제들을 모아둔 **AI Cookbook**이 있습니다.

쿡북요리사 활동에서는 이 AI Cookbook 자료를 활용해 다양한 AI 분야에 대해 실습, 발표, 한글화 작업을 진행하고 있는데요.
<div align="center">
    <img src="../assets/images/blog/posts/2025-05-31-2025-PseudoCon-recap/쿡북3.png" width="700"/>
</div>
`NLP`부터 `Vision`, `Agent` 까지 다양한 분야와 도메인에 대해 다룬 Cookbook을 한국어화 한 자료를 공유하고,

<div align="center">
    <img src="../assets/images/blog/posts/2025-05-31-2025-PseudoCon-recap/쿡북4.png" width="500"/>
</div>

특별히 [IP-Adapter 쿡북](https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter)을 파인튜닝하여 제작한 `싸이월드 미니미 생성` 실습을 제공해 길가던 수많은 참가자들의 발길을 돌렸답니다 😎

<div align="center">
    <img src="../assets/images/blog/posts/2025-05-31-2025-PseudoCon-recap/쿡북5.webp" width="500"/>
</div>


# 🚀 Hugging Face Beyond First PR

오픈소스 기여의 꽃, 코드기여에 관심을 보이신 많은 참가자 분들로 북적였던 Beyond First PR 부스.

Beyond First PR 프로젝트에서는 Hugging Face에 존재하는 다양한 오픈소스 라이브러리 코드를 개선함으로써, 직접적으로 AI 오픈소스 커뮤니티에 기여하고 있습니다.
<div align="center">
    <img src="../assets/images/blog/posts/2025-05-31-2025-PseudoCon-recap/비욘드1.png" width="500"/>
    <img src="../assets/images/blog/posts/2025-05-31-2025-PseudoCon-recap/비욘드2.png" width="500"/>
</div>

Beyond First PR 부스에서는 현재 진행중인 코드기여 이슈들과 진행 과정, 코드기여 과정 중 어려웠던 점들을 꾹꾹 눌러담은 [가이드북](https://github.com/user-attachments/files/20533125/HuggingFaceKREW-BeyondFirstPR.2.pdf)
을 제작해,

 PseudoCon을 찾아주신 참가자분들께 오픈소스 기여를 독려해주셨는데요!
<div align="center">
    <img src="../assets/images/blog/posts/2025-05-31-2025-PseudoCon-recap/비욘드3.png" width="400"/>
</div>
이 가이드북 외에도 `첫 코드기여 이슈 찾는 법`과 `[기술 문서 번역](https://yijunlee.notion.site/hugging-face-transformers-translation-guide)` 가이드도 함께 제공하여, 오픈소스에 기여하고 싶지만 도전하기 어려우셨던 분들, 어떻게 기여점을 찾으면 좋을까 고민하시던 분들께 마중물 같은 시간이 되었으리라 생각합니다!

<div align="center">
    <img src="../assets/images/blog/posts/2025-05-31-2025-PseudoCon-recap/비욘드5.png" width="500"/>
</div>

# 🌿 Hugging Face Hub Garden

[Hugging Face Hub](https://huggingface.co/docs/hub/index)는 AI 모델, 데이터셋, 앱을 자유롭게 공유하고 협업하는 플랫폼으로,

Hub Garden 팀에서는 이 Hub를 활용해 **자신만의 데이터셋을 구축하고 모델을 직접 훈련하여 공유**하는 4가지 프로젝트를 진행중입니다.

이번 PseudoCon를 통해 Hub Garden는 부스에서 4가지 데이터셋 프로젝트 과정을 공개하며, 각 프로젝트 담당자들로부터 데이터 수집 과정, 전처리 방법, 그리고 앞으로의 해결 과제 등 실질적인 조언을 데이터셋의 유형과 성격에 따라 직접 들을 수 있었습니다.

<div align="center">
    <img src="../assets/images/blog/posts/2025-05-31-2025-PseudoCon-recap/허브1.png" width="500"/>
</div>

직접 구축한 데이터셋으로 훈련한 모델로 [*가상 여자친구 Exagirl와의 롤플레잉*](https://huggingface.co/spaces/huggingface-KREW/EXAGIRL-7.8B) 체험도 제공했는데요, 수많은 참가자들이 엑사걸을 찾아주셨다고 합니다. 😂

4가지 Hub Garden 프로젝트에서 구축한 데이터셋과 모델은 [이곳](https://huggingface.co/huggingface-KREW)에서 확인 가능합니다! 


또한 이번 PseudoCon에서는 Hub Garden의 빌더 김하림님께서 각 Hub Garden 프로젝트를 소개해주시는 시간을 가졌습니다. 

<div align="center">
    <img src="../assets/images/blog/posts/2025-05-31-2025-PseudoCon-recap/세미나1.webp" width="500"/>
    <img src="../assets/images/blog/posts/2025-05-31-2025-PseudoCon-recap/세미나2.webp" width="500"/>
</div>

Hugging Face 에 등재된 영어 데이터셋 중 `4.63%` 만이 한국어 데이터셋이라는 점을 강조해주시며,

한국어 데이터셋 구축 프로젝트의 의의와 긴급성에 대해 상기시킬 수 있었습니다!

<div align="center">
    <img src="../assets/images/blog/posts/2025-05-31-2025-PseudoCon-recap/세미나3.jpg" width="500"/>
</div>

발표 중에는 Hub Garden 프로젝트 뿐만 아니라 Hugging Face KREW에서 진행중인 활동에 대해 공유해주셨습니다!

<div align="center">
    <img src="../assets/images/blog/posts/2025-05-31-2025-PseudoCon-recap/세미나4.png" width="500"/>
</div>

이를 계기로 국내 많은 AI/데이터과학 개발자들에게 Hugging Face KREW의 존재를 알리고, Hugging Face 오픈소스 기여와 KREW 생태계에 기여하는 성과를 가졌습니다! 🌱

## 마무리
부스 진행 중 오픈소스 Hugging Face에 기여하는 것의 의미에 대한 질문을 받기도 했는데요.
저는 이렇게 표현하고 싶습니다.

<aside>
대한민국 누구나 머신러닝을 활용할 수 있도록 하여, 사회에 긍정적인 변화를 이끄는 것
</aside>

저희의 여정은 [Hugging Face KREW Space](https://huggingface.co/huggingface-KREW)와, 저희 KREW Blog를 통해 계속 확인하실 수 있습니다!
<div align="center">
    <img src="../assets/images/blog/posts/2025-05-31-2025-PseudoCon-recap/로고2.gif" width="300"/>
</div>

```

### real/2025-06-22-HuggingFace-Docs-Translation-Guide.md

```markdown
---
layout: post
title: "Hugging Face transformers 기술 문서 번역 가이드"
author: jeong
categories: [contribute]
image: assets/images/blog/posts/2025-06-22-HuggingFace-Docs-Translation-Guide/transformers.png
---
* TOC
{:toc}
<!--toc-->
HuggingFace First PR 팀에서 제작한 transformers 공식문서 한글화 기여 가이드입니다!🤗

## 작업 준비

### 1. transformers 레포지토리 포크 하기
Hugging Face의 transformers 레포지토리를 포크하여 가져옵니다.

<img src="../assets/images/blog/posts/2025-06-22-HuggingFace-Docs-Translation-Guide/image0.png" width="800"/>

<img src="../assets/images/blog/posts/2025-06-22-HuggingFace-Docs-Translation-Guide/image 1.png" width="800"/>
    
    
### 2. 레포지토리 클론 받기
    
<img src="../assets/images/blog/posts/2025-06-22-HuggingFace-Docs-Translation-Guide/image 2.png" width="800"/>
<img src="../assets/images/blog/posts/2025-06-22-HuggingFace-Docs-Translation-Guide/image 3.png" width="800"/>

    
포크 한 transformers 레포지토리에서 초록색 `Code` 버튼을 클릭 후, 복사 버튼을 클릭하여 주소 복사 받기
레포지토리를 clone 하여 로컬에 가져옵니다.
    
### 3. 번역 대상 문서 선정
        
<img src="../assets/images/blog/posts/2025-06-22-HuggingFace-Docs-Translation-Guide/image 4.png" width="800"/>
<img src="../assets/images/blog/posts/2025-06-22-HuggingFace-Docs-Translation-Guide/image 5.png" width="800"/>
   
    
번역 대상 문서는 transformers/docs/source의 en 디렉토리에는 있고, ko 디렉토리에는 없는 문서를 번역 진행하면 됩니다.
macOS 기준 아래 커맨드로 더 편하게 확인할 수 있습니다.

```bash
comm -23 \
    <(cd transformers/docs/source/en && find . -type f | sort) \
    <(cd transformers/docs/source/ko && find . -type f | sort)
```
    

종종 다른 사람이 이미 작업을 했지만, 레포지토리에는 반영이 되지 않은 경우가 있습니다.
중복 작업을 방지하기 위해, 번역을 시작하기 전에 기존 Pull Request에서 **i18n**, **translate** 등의 키워드로 검색해 관련 작업이 진행 중인지 먼저 확인해보시길 권장합니다.
    
### 4. 브랜치 만들기 
`main` 브랜치에서 직접 작업하면 안 되고, 새로운 브랜치를 반드시 생성해야 합니다.
*이유: 원본 코드를 보호하고, 작업 내용을 분리하여 관리하기 위해*

브랜치 이름은 ko-*.md와 같은 형식으로 합니다.
번역 대상 문서가 keypoint_detection.md 라면, ko-keypoint_detection.md를 브랜치 이름으로 합니다.
아래 명령어로 브랜치를 생성할 수 있습니다.
        
```bash
git checkout -b <branch-name>
```
        
브랜치가 정상적으로 생성되었는지 확인하려면 다음 명령어를 사용합니다.
        
```bash
git branch
```
        
<img src="../assets/images/blog/posts/2025-06-22-HuggingFace-Docs-Translation-Guide/image 6.png" width="800"/>
   
        
만약 명령어 입력이 어렵다면, Cursor에서 브랜치를 직접 생성할 수도 있습니다.

<img src="../assets/images/blog/posts/2025-06-22-HuggingFace-Docs-Translation-Guide/image 7.png" width="800"/>
   
    
<img src="../assets/images/blog/posts/2025-06-22-HuggingFace-Docs-Translation-Guide/image 8.png" width="800"/>
   
    

## 본격적인 번역 작업

### 1. 초기 문서 작업
1. `docs/source/en` 디렉토리에 있는 번역 대상 원본 문서를 복사해서 `docs/source/ko`로 옮깁니다.
2. `docs/source/ko` 의 _toctree.yml에는 문서의 제목과 위치가 작성되어 있습니다.
3. _toctree.yml의 title을 적절히 한글화 하고, local에는 위치를 작성합니다.
4. 아래 명령어를 입력하여 커밋을 합니다.
    - `git commit -m "커밋 메시지"`
    - 커밋 메시지의 경우, `docs: ko: <file-name>` 의 형태로 해주시면 됩니다.
    - ex: `git commit -m "docs: ko: keypoint_detection.md"`

### 2. 기계 번역
1. ChatGPT, Claude, DeepL, 파파고 등 다양한 툴을 활용하여 초벌 번역을 진행합니다.
2. 아래 명령어를 입력하여 커밋을 합니다.
    - `git commit -m "커밋 메시지"`
    - 커밋 메시지의 경우, `feat: nmt draft` 의 형태로 해주시면 됩니다.
    - ex: `git commit -m "feat: nmt draft"`
        - 참고로, nmt는 Neural Machine Translation을 의미합니다!

### 3. 번역 수정
아래 항목들을 신경 쓰면서 번역을 적절히 수정합니다.
- 영어 원문이 남아 있는지
- 서식이 올바르게 옮겨져쓴지 아닌지 (TOC, code, URL, 특수문자 등)
    - *이 부분이 가장 중요합니다.*
    - 특히, [[]](TOC)의 경우 웹에서 정상적으로 작동하려면 서식이 변경되면 안됩니다.
- 오역이나 오탈자가 있는지
- 번역어가 TTA정보통신용어사전과 일치하는지 (혹은 적어도 문서 내에서 일관된 표현을 사용하는지)
    - 원래는 Hugging Face KREW에서 사용하는 공식 용어집(glossary)이 있었지만, 현재는 유실된 상태입니다. 따라서 번역 시에는 우선 기존 번역 사례나 사전을 참고해주세요!
- 더 자연스러운 한국어 표현이 있는지

위 작업이 완료되었다면, 아래 명령어를 입력하여 커밋을 합니다.
- `git commit -m "커밋 메시지"`
- 커밋 메시지의 경우, `fix: manual edits` 의 형태로 해주시면 됩니다.
- ex: `git commit -m "fix: manual edits"`

## PR(Pull Request) 올리기

### 1. 깃허브에 Push 하기
`git status` 명령어로 정상적으로 커밋된 것인지 확인한 후, `git push` 합니다.
    
<img src="../assets/images/blog/posts/2025-06-22-HuggingFace-Docs-Translation-Guide/image 9.png" width="800"/>
   
    
정상적으로 완료 되었다면, 위 사진과 같이 버튼이 나올 것입니다.
이제, 위 버튼을 누르고 Draft PR을 만들어봅시다.


### 2. 드래프트 PR 생성 후 리뷰
    
<img src="../assets/images/blog/posts/2025-06-22-HuggingFace-Docs-Translation-Guide/image 10.png" width="800"/>
   
    
<img src="../assets/images/blog/posts/2025-06-22-HuggingFace-Docs-Translation-Guide/image 11.png" width="800"/>
   
드래프트 PR 제목과 내용의 경우 아래 작성한 텍스트를 복사하여, 적절히 주석을 노출하여 주시면 됩니다.
**가장 중요한 것은, 우측의 이미지에서 Create draft pull request를 꼭 선택해주셔야 합니다!!**
참고로, <!— —> 안에 적힌 부분은 주석으로, PR에 보이지 않습니다.

```
<!-- PR의 제목은 "🌐 [i18n-KO] Translated `<your_file>.md` to Korean" 으로 부탁드립니다 -->
# What does this PR do?

Translated the `<your_file>.md` file of the documentation to Korean.
Thank you in advance for your review.

Part of https://github.com/huggingface/transformers/issues/20179

## Before reviewing
- [ ] Check for missing / redundant translations (번역 누락/중복 검사)
- [ ] Grammar Check (맞춤법 검사)
- [ ] Review or Add new terms to glossary (용어 확인 및 추가)
- [ ] Check Inline TOC (e.g. `[[lowercased-header]]`)
- [ ] Check live-preview for gotchas (live-preview로 정상작동 확인)

## Who can review? (Initial)

<!-- 1. 위 체크가 모두 완료된 뒤에만 KREW 팀원들에게 리뷰를 요청하는 아래 주석을 노출해주세요!-->
May you please review this PR?
<!-- @cjfghk5697, @yijun-lee, @jungnerd , @harheem -->

## Before submitting
- [ ] This PR fixes a typo or improves the docs (you can dismiss the other checks if that's the case).
- [ ] Did you read the [contributor guideline](https://github.com/huggingface/transformers/blob/main/CONTRIBUTING.md#start-contributing-pull-requests),
        Pull Request section?
- [ ] Was this discussed/approved via a Github issue or the [forum](https://discuss.huggingface.co/)? Please add a link
        to it if that's the case.
- [ ] Did you make sure to update the documentation with your changes? Here are the
        [documentation guidelines](https://github.com/huggingface/transformers/tree/main/docs), and
        [here are tips on formatting docstrings](https://github.com/huggingface/transformers/tree/main/docs#writing-source-documentation).
- [ ] Did you write any new necessary tests?

## Who can review? (Final)

<!-- 2. KREW 팀원들의 리뷰가 끝난 후에 아래 주석을 노출해주세요! -->
<!-- @stevhliu May you please review this PR? -->
```
    
### 3. 리뷰 후 PR 오픈
한국인 2인 이상 리뷰를 완료하면 PR 설정에서 공개로 바꿔주시면 됩니다.

## 리뷰 반영하기

1. 내 PR 페이지의 **Files Changed** 탭으로 이동하기

2. 작업물 변경 제안이 맘에 들면 **Add suggestion to batch** 버튼을 눌러 순차적으로 반영하기
    
    (반영하지 않을 제안에는 메인 작업자로서의 생각을 코멘트로 써 주시면 좋아요! Add suggestion to batch를 하는 이유는 커밋 수가 너무 많아질 수 있기 때문이고, 안하셨다고 해도 문제 없습니다! )
    
3. 반영할 제안을 모두 골랐으면 우상단의 **Commit suggestions**를 클릭
 → **Commit changes** 클릭으로 반영 커밋 완료하기

4. 기타 수정 사항이 있으면 file changed에서 edit file로 수정하거나, vs code에서 수정 가능합니다.

5. 커밋 메시지의 경우 `fix: resolve suggestions` 정도로 하시면 됩니다.

## 마무리

리뷰가 완료된 번역문서는 메인테이너의 허가를 거쳐 merged가 됩니다.
<img src="../assets/images/blog/posts/2025-06-22-HuggingFace-Docs-Translation-Guide/image 12.png" width="800"/>

이렇게 merged된 번역 문서는 HuggingFace 공식 홈페이지의 한국어 탭에 등재되었습니다!🎉
<img src="../assets/images/blog/posts/2025-06-22-HuggingFace-Docs-Translation-Guide/image 13.png" width="800"/>

```

### real/2025-09-14-Implementing-MCP-Servers-in-Python.md

```markdown
---
layout: post
title: "Python으로 구현하는 MCP 서버: Gradio를 활용한 AI 쇼핑 어시스턴트"
author: sohyun
categories: [MCP, Gradio]
image: assets/images/blog/posts/2025-09-14-Implementing-MCP-Servers-in-Python/thumbnail.png
---
* TOC
{:toc}
<!--toc-->
_이 글은 Hugging Face 블로그의 [Implementing MCP Servers in Python: An AI Shopping Assistant with Gradio](https://huggingface.co/blog/gradio-vton-mcp)를 한국어로 번역한 글입니다._

---


# Python으로 구현하는 MCP 서버: Gradio를 활용한 AI 쇼핑 어시스턴트

Python 개발자 여러분, LLM에 특별한 능력을 부여하고 싶으신가요? 그렇다면 Gradio가 가장 빠른 방법입니다! Gradio의 MCP(Model Context Protocol) 연동을 이용하면 LLM을 Hugging Face [Hub](https://hf.co)에 호스팅된 수천 개의 AI 모델과 Space에 직접 연결할 수 있습니다. LLM의 일반적인 추론 능력과 Hugging Face의 모델들의 특화된 능력을 결합한다면, LLM은 단순히 텍스트 질문에 답하는 것을 넘어 일상생활의 문제를 해결해줄 것 입니다!

Gradio가 제공하는 다음과 같은 기능 덕분에 Python 개발자들이 강력한 MCP 서버를 매우 쉽게 구현할 수 있습니다:
* **Python 함수를 LLM 도구로 자동 변환:** Gradio 앱의 각 API 엔드포인트는 해당하는 이름, 설명, 입력 스키마를 가진 MCP 도구로 자동 변환됩니다. 함수의 docstring은 도구와 전달인자의 설명을 생성하는 데 사용됩니다.
* **실시간 진행 상황 알림:** Gradio는 MCP 클라이언트에 진행 상황 알림을 스트리밍하기 때문에, 직접 구현하지 않고도 실시간으로 상태를 모니터링할 수 있습니다.
* 공개 URL 지원 및 다양한 유형의 파일 처리를 포함한 **자동 파일 업로드**

이런 상황을 상상해봅시다. 쇼핑은 시간이 너무 많이 걸려서 싫고, 직접 옷을 입어보는 것도 귀찮습니다. 이때 LLM이 쇼핑을 대신해준다면 어떨까요? 이 포스트에서는 온라인 의류 매장을 탐색하고, 특정 옷을 찾고, 가상 피팅 모델을 사용해 여러분이 그 옷을 입을 때 어떨지 보여주는 LLM 기반 AI 어시스턴트를 만들어보겠습니다. 아래 데모를 확인해보세요:

<video src="https://github.com/user-attachments/assets/e5bc58b9-ca97-418f-b78b-ce38d4bb527e" controls alt="AI Shopping Assistant Demo using Gradio python sdk and MCP"></video>

## 목표: 나만의 개인 AI 스타일리스트

AI 쇼핑 어시스턴트를 구현하기 위해 세 가지 핵심 구성 요소를 결합할 것입니다:

1. [IDM-VTON](https://huggingface.co/yisol/IDM-VTON) Diffusion 모델: 이 AI 모델은 가상 피팅 기능을 담당합니다. 원본 사진을 편집하여 사진 속 사람이 다른 옷을 입고 있는 것처럼 보이게 할 수 있습니다. 우리는 [여기](https://huggingface.co/spaces/yisol/IDM-VTON)에서 접근 가능한 IDM-VTON의 Hugging Face Space를 사용할 것입니다.

2. Gradio: Gradio는 AI 기반 웹 애플리케이션을 쉽게 구축할 수 있게 해주는 오픈소스 Python 라이브러리로, 우리 프로젝트에서 중요한 부분은 MCP 서버를 생성할 수 있다는 점입니다. Gradio는 LLM이 IDM-VTON 모델과 다른 도구들을 호출할 수 있도록 다리 역할을 합니다.

3. Visual Studio Code의 AI Chat 기능: 임의의 MCP 서버를 추가할 수 있는 VS Code의 내장 AI 채팅을 사용하여 AI 쇼핑 어시스턴트와 대화할 것입니다. 이는 명령을 내리고 가상 피팅 결과를 보기 위한 사용자 친화적인 인터페이스를 제공합니다.

## Gradio MCP 서버 구축하기
AI 쇼핑 어시스턴트의 핵심은 Gradio MCP 서버입니다. 이 서버는 한 가지 주요 도구를 제공합니다:

1. `vton_generation`: 이 함수는 사람 모델 이미지와 의류 이미지를 입력으로 받아 IDM-VTON 모델을 사용하여 그 사람이 해당 옷을 입고 있는 이미지를 생성합니다.


다음은 Gradio MCP 서버를 위한 Python 코드입니다:

```python
from gradio_client import Client, handle_file
import gradio as gr
import re


client = Client("freddyaboulton/IDM-VTON",
                hf_token="<Your-token>")


def vton_generation(human_model_img: str, garment: str):
    """IDM-VTON 모델을 사용하여 옷을 입고 있는 사람의 이미지를 생성합니다."""
    """
    Args:
        human_model_img: 옷을 입어볼 사람 모델
        garment: 입을 의상
    """
    output = client.predict(
        dict={"background": handle_file(human_model_img), "layers":[], "composite":None},
        garm_img=handle_file(garment),
        garment_des="",
        is_checked=True,
        is_checked_crop=False,
        denoise_steps=30,
        seed=42,
        api_name="/tryon"
    )

    return output[0]

vton_mcp = gr.Interface(
    vton_generation,
    inputs=[
        gr.Image(type="filepath", label="Human Model Image URL"),
        gr.Image(type="filepath", label="Garment Image URL or File")
    ],
    outputs=gr.Image(type="filepath", label="Generated Image")
)

if __name__ == "__main__":
    vton_mcp.launch(mcp_server=True)
```

`launch()` 메서드에서 `mcp_server=True`로 지정해주면, Gradio가 자동으로 Python 함수를 LLM이 이해하고 활용할 수 있는 MCP 도구로 변환합니다. 함수의 docstring은 도구와 매개변수의 설명을 생성하는 데 사용됩니다.

> [!TIP]
> 원래 IDM-VTON space는 자동 MCP 기능이 있기 전인 Gradio 4.x로 구현되었습니다. 따라서 이 데모에서는 Gradio API 클라이언트를 통해 원래 space를 호출하는 Gradio 인터페이스를 구축할 예정입니다.

마지막으로 이 스크립트를 python으로 실행합니다.

## VS Code 설정하기

Gradio MCP 서버를 VS Code의 AI 채팅에 연결하려면 `mcp.json` 파일을 편집해야 합니다. 파일 내부 설정값을 통해 AI 채팅에 MCP 서버 위치와 상호작용 방법을 알려줍니다.

명령 패널에 `MCP`를 입력하고 `MCP: Open User Configuration`을 선택하여 설정 파일을 찾을 수 있습니다. 파일을 열고 다음 서버들이 있는지 확인하세요:

```json
{
  "servers": {
  "vton": {
    "url": "http://127.0.0.1:7860/gradio_api/mcp/"
  },
  "playwright": {
    "command": "npx",
    "args": [
      "-y",
      "@playwright/mcp@latest"
    ]
   }
  }
}
```

playwright MCP 서버는 AI 어시스턴트가 웹을 탐색할 수 있게 해줍니다.

> [!TIP]
> `vton` 서버의 URL이 이전 섹션에서 콘솔에 출력된 URL과 일치하는지 확인해보세요. playwright MCP 서버를 실행하려면 node가 [설치](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)되어 있어야 합니다.

## 실제로 활용해보기

이제 AI 쇼핑 어시스턴트와 대화할 수 있게 되었습니다. VS Code에서 새 채팅을 열어서 어시스턴트에게 다음과 같이 요청해보세요. 
"유니클로 웹사이트에서 파란색 티셔츠를 찾아보고, [your-image-url]에 있는 내 사진을 사용해서 그 중 세 개를 내가 입었을 때 어떻게 보이는지 보여줘."

예시는 위의 비디오를 참조하세요!

## 결론

Gradio, MCP, 그리고 IDM-VTON과 같은 강력한 AI 모델의 조합으로, 똑똑하고 유용한 AI 어시스턴트를 만들 수 있다는 가능성이 열렸습니다. 이 블로그 포스트에 설명된 대로 따라가보면 여러분이 가장 관심 있는 문제를 해결하기 위한 자신만의 어시스턴트를 구축할 수 있습니다!
```

### real/2025-09-14-python-tiny-agents-ko.md

```markdown
---
layout: post
title: "파이썬 Tiny Agents: 약 70줄의 코드로 MCP 기반 에이전트 구현하기"
author: minju
categories: [Agent]
image: assets/images/blog/posts/2015-09-14-python-tiny-agents/thumbnail.png
---
* TOC
{:toc}
<!--toc-->
_이 글은 Hugging Face 블로그의 [Tiny Agents in Python: an MCP-powered agent in ~70 lines of code](https://huggingface.co/blog/python-tiny-agents)를 한국어로 번역한 글입니다._

---
# 파이썬 Tiny Agents: 약 70줄의 코드로 MCP 기반 에이전트 구현하기

> [!TIP]
> NEW: tiny-agents가 이제 [AGENTS.md](https://agents.md/) 표준을 지원합니다. 🥳

[Tiny Agents in JS](https://huggingface.co/blog/tiny-agents)에서 영감을 받아, 이 아이디어를 파이썬 🐍으로 개발하고 [`huggingface_hub`](https://github.com/huggingface/huggingface_hub/) 클라이언트 SDK를 확장하여 MCP 클라이언트로서 MCP 서버에서 도구를 가져와 추론 중에 LLM에 전달할 수 있도록 했습니다. 

MCP ([Model Context Protocol](https://modelcontextprotocol.io/))는 대규모 언어 모델(LLM)이 외부 도구 및 API와 상호 작용하는 방식을 표준화하는 개방형 프로토콜입니다. 본질적으로 각 도구에 대한 개별적인 통합을 개발할 필요가 없어졌으며, 이를 통해 LLM에 새로운 기능을 더 쉽게 연결할 수 있습니다.

이 블로그 게시물에서는 강력한 도구 기능을 활용할 수 있도록 MCP 서버에 연결된 파이썬의 Tiny Agent를 시작하는 방법을 보여줍니다. 자신만의 에이전트를 얼마나 쉽게 구축하고 바로 개발을 시작할 수 있는지 직접 확인해 보세요!

> [!TIP]
> _스포일러_ : 에이전트는 본질적으로 MCP 클라이언트 위에 구축된 while 루프입니다!

## 데모 실행 방법

이 섹션에서는 기존 Tiny Agents를 사용하는 방법을 안내합니다. 에이전트를 실행하기 위한 설정 및 명령을 다루겠습니다.

먼저, 필요한 모든 구성 요소를 얻으려면 `mcp` 추가 기능과 함께 `huggingface_hub`의 최신 버전을 설치해야 합니다.

```bash
pip install "huggingface_hub[mcp]>=0.32.0"
```

이제 CLI를 사용하여 에이전트를 실행해 봅시다!

가장 멋진 점은 Hugging Face Hub [tiny-agents](https://huggingface.co/datasets/tiny-agents/tiny-agents) 데이터셋에서 바로 에이전트를 불러올 수도 있고, 혹은 로컬 에이전트 설정에 경로를 직접 지정할 수 있다는 것입니다!

```bash
> tiny-agents run --help
                                                                                                                                                                                     
 Usage: tiny-agents run [OPTIONS] [PATH] COMMAND [ARGS]...                                                                                                                           
                                                                                                                                                                                     
 Run the Agent in the CLI                                                                                                                                                            
                                                                                                                                                                                     
                                                                                                                                                                                     
╭─ Arguments ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│   path      [PATH]  Path to a local folder containing an agent.json file or a built-in agent stored in the 'tiny-agents/tiny-agents' Hugging Face dataset                         │
│                     (https://huggingface.co/datasets/tiny-agents/tiny-agents)                                                                                                     │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                       │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯


```

특정 에이전트 설정에 경로를 제공하지 않으면, Tiny Agent는 기본적으로 다음 두 MCP 서버에 연결됩니다.

- 당신의 데스크톱에 접근 권한을 갖는 "표준" [파일 시스템 서버](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem),
- 샌드박스 환경의 Chromium 브라우저를 사용하는 방법을 아는 [Playwright MCP](https://github.com/microsoft/playwright-mcp) 서버.


다음 예시는 Nebius 추론 공급자를 통해 [Qwen/Qwen2.5-72B-Instruct](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct) 모델을 사용하도록 구성된 웹 탐색 에이전트를 보여줍니다. 이 에이전트에는 웹 브라우저를 사용할 수 있게 해주는 Playwright MCP 서버가 함께 제공됩니다! 에이전트 설정은 Hugging Face 데이터셋의 [tiny-agents/tiny-agents](https://huggingface.co/datasets/tiny-agents/tiny-agents/tree/main/celinah/web-browser)에 있는 경로를 지정하여 불러옵니다.

<video controls autoplay loop>
  <source src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/blog/python-tiny-agents/web_browser_agent.mp4" type="video/mp4">
</video>

에이전트를 실행하면, 연결된 MCP 서버에서 발견한 도구 목록을 불러오는 것을 볼 수 있습니다. 이제 여러분의 프롬프트에 응답할 준비가 되었습니다!

이 데모에서 사용된 프롬프트:

> Brave Search에서 HF 추론 공급자를 웹 검색하고 첫 번째 결과를 연 다음 Hugging Face에서 지원되는 추론 공급자 목록을 알려주세요.

Gradio Spaces를 MCP 서버로 사용할 수도 있습니다! 다음 예시는 Nebius 추론 공급자를 통해 [Qwen/Qwen2.5-72B-Instruct](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct) 모델을 사용하고, MCP 서버로 `FLUX.1 [schnell]` 이미지 생성 HF Space에 연결합니다. 에이전트는 Hugging Face Hub의 [tiny-agents/tiny-agents](https://huggingface.co/datasets/tiny-agents/tiny-agents/tree/main/julien-c/flux-schnell-generator) 데이터셋에 있는 구성에서 로드됩니다.

<video controls autoplay loop>
  <source src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/blog/python-tiny-agents/image-generation.mp4" type="video/mp4">
</video>

이 데모에서 사용된 프롬프트:

> 달 표면에서 알에서 부화하는 작은 우주 비행사의 1024x1024 이미지를 생성하세요.

이제 기존 Tiny Agents를 실행하는 방법을 살펴보았으니, 다음 섹션에서는 Tiny Agents가 작동하는 방식과 자신만의 에이전트를 구축하는 방법에 대해 더 자세히 설명합니다.

### 에이전트 설정

각 에이전트의 동작(기본 모델, 추론 공급자, 연결할 MCP 서버, 초기 시스템 프롬프트)은 `agent.json` 파일에 정의됩니다. 더 자세한 시스템 프롬프트를 위해 동일한 디렉토리에 사용자 지정 `PROMPT.md`를 제공할 수도 있습니다. 다음은 예시입니다.

`agent.json`
`model` 및 `provider` 필드는 에이전트가 사용하는 LLM 및 추론 공급자를 지정합니다.
`servers` 배열은 에이전트가 연결할 MCP 서버를 정의합니다.
이 예시에서는 "stdio" MCP 서버가 구성되어 있습니다. 이 유형의 서버는 로컬 프로세스로 실행됩니다. 에이전트는 지정된 `command` 및 `args`를 사용하여 서버를 시작한 다음 stdin/stdout을 통해 통신하여 사용 가능한 도구를 검색하고 실행합니다.
```json
{
	"model": "Qwen/Qwen2.5-72B-Instruct",
	"provider": "nebius",
	"servers": [
		{
			"type": "stdio",
			"command": "npx",
			"args": ["@playwright/mcp@latest"]
		}
	]
}

```
`PROMPT.md`

```
You are an agent - please keep going until the user’s query is completely resolved [...]


```


> [!TIP]
> Hugging Face 추론 공급자에 대한 자세한 내용은 [여기](https://huggingface.co/docs/inference-providers/index)에서 확인할 수 있습니다.

### LLM은 도구를 사용할 수 있습니다.

최신 LLM은 함수 호출(또는 도구 사용)을 위해 구축되어 사용자가 특정 사용 사례 및 실제 작업에 맞춰진 애플리케이션을 쉽게 구축할 수 있도록 합니다.

함수는 스키마에 의해 정의되며, 이는 LLM에 함수가 무엇을 하는지, 어떤 입력 인수를 예상하는지 알려줍니다. LLM은 도구를 사용할 시기를 결정하고, 에이전트는 도구 실행을 조율하고 결과를 다시 전달합니다.

```python
tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current temperature for a given location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City and country e.g. Paris, France"
                        }
                    },
                    "required": ["location"],
                },
            }
        }
]
```

`InferenceClient`는 [OpenAI Chat Completions API](https://platform.openai.com/docs/guides/function-calling?api-mode=chat)와 동일한 도구 호출 인터페이스를 구현하며, 이는 추론 공급자 및 커뮤니티의 확립된 표준입니다.

## 파이썬 MCP 클라이언트 구축

`MCPClient`는 도구 사용 기능의 핵심입니다. 이제 `huggingface_hub`의 일부이며 `AsyncInferenceClient`를 사용하여 LLM과 통신합니다.

> [!TIP]
> 전체 `MCPClient` 코드는 [여기](https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_mcp/mcp_client.py)에서 찾을 수 있습니다. 실제 코드를 따라가고 싶다면 참고하세요 🤓

`MCPClient`의 주요 역할:

- 하나 이상의 MCP 서버에 대한 비동기 연결 관리.
- 이러한 서버에서 도구 검색.
- LLM을 위한 도구 형식 지정.
- 올바른 MCP 서버를 통해 도구 호출 실행.

MCP 서버에 연결하는 방법은 다음과 같습니다(`add_mcp_server` 메서드):

```python
# `MCPClient.add_mcp_server`의 111-219줄
# https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_mcp/mcp_client.py#L111:L219
class MCPClient:
    ...
    async def add_mcp_server(self, type: ServerType, **params: Any):
        # 'type'은 "stdio", "sse", 또는 "http"일 수 있습니다.
        # 'params'는 서버 유형에 따라 다릅니다. 예:
        # "stdio"의 경우: {"command": "my_tool_server_cmd", "args": ["--port", "1234"]}
        # "http"의 경우: {"url": "http://my.tool.server/mcp"}

        # 1. 유형(stdio, sse, http)에 따라 연결 설정
        #    (mcp.client.stdio_client, sse_client, 또는 streamablehttp_client 사용)
        read, write = await self.exit_stack.enter_async_context(...)

        # 2. MCP ClientSession 생성
        session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream=read, write_stream=write, ...)
        )
        await session.initialize()

        # 3. 서버에서 도구 목록 가져오기
        response = await session.list_tools()
        for tool in response.tools:
            # 이 도구에 대한 세션 저장
            self.sessions[tool.name] = session 
            # 사용 가능한 도구 목록에 도구 추가 및 LLM을 위한 형식 지정
            self.available_tools.append({ 
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            })

```
로컬 도구(예: 파일 시스템 액세스)를 위한 `stdio` 서버와 원격 도구를 위한 `http` 서버를 지원합니다! 또한 원격 도구의 이전 표준인 `sse`와도 호환됩니다.

## 도구 사용: 스트리밍 및 처리

`MCPClient`의 `process_single_turn_with_tools` 메서드에서는 LLM 상호 작용이 일어납니다. 대화 기록과 사용 가능한 도구를 `AsyncInferenceClient.chat.completions.create(..., stream=True)`를 통해 LLM에 보냅니다.

### 1. 도구 준비 및 LLM 호출

먼저, 이 메서드는 현재 차례에 LLM이 알아야 할 모든 도구를 결정합니다. 여기에는 MCP 서버의 도구와 에이전트 제어를 위한 특별한 "루프 종료(loop exit)" 도구가 포함됩니다. 그런 다음 LLM에 스트리밍 호출을 합니다.

```python
# `MCPClient.process_single_turn_with_tools`의 241-251줄
# https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_mcp/mcp_client.py#L241:L251

    # 옵션에 따라 도구 목록 준비
    tools = self.available_tools
    if exit_loop_tools is not None:
        tools = [*exit_loop_tools, *self.available_tools]

    # LLM에 스트리밍 요청 생성
    response = await self.client.chat.completions.create(
        messages=messages,
        tools=tools,
        tool_choice="auto",  # LLM이 도구가 필요한지 결정
        stream=True,  
    )

```

LLM으로부터 청크가 도착하면, 메서드는 청크 처리를 반복합니다. 각 청크는 즉시 반환되며, 그런 다음 완전한 텍스트 응답과 모든 도구 호출을 재구성합니다.

```python
# `MCPClient.process_single_turn_with_tools`의 258-290줄 
# https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_mcp/mcp_client.py#L258:L290
# 스트림에서 읽기
async for chunk in response:
      # 각 청크를 호출자에게 반환
      yield chunk
      # LLM의 텍스트 응답 및 도구 호출 부분 집계
      …
```

### 2. 도구 실행

스트림이 완료되면, LLM이 도구 호출을 요청한 경우(`final_tool_calls`에 완전히 재구성됨), 메서드는 각 호출을 처리합니다.

```python
# `MCPClient.process_single_turn_with_tools`의 293-313줄 
# https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_mcp/mcp_client.py#L293:L313
for tool_call in final_tool_calls.values():
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments or "{}")

    # 도구 결과를 저장할 메시지 준비
    tool_message = {"role": "tool", "tool_call_id": tool_call.id, "content": "", "name": function_name}

    # a. 이것이 특별한 "루프 종료" 도구인가요?
    if exit_loop_tools and function_name in [t.function.name for t in exit_loop_tools]:
        # 그렇다면 메시지를 반환하고 이 턴의 처리를 종료합니다.
        messages.append(ChatCompletionInputMessage.parse_obj_as_instance(tool_message))
        yield ChatCompletionInputMessage.parse_obj_as_instance(tool_message)
        return # 에이전트의 메인 루프가 이 신호를 처리합니다.

    # b. 일반 도구입니다: MCP 세션을 찾아 실행합니다.
    session = self.sessions.get(function_name) # self.sessions는 도구 이름을 MCP 연결에 매핑합니다.
    if session is not None:
        result = await session.call_tool(function_name, function_args)
        tool_message["content"] = format_result(result) # format_result는 도구 출력을 처리합니다.
    else:
        tool_message["content"] = f"Error: No session found for tool: {function_name}"
        tool_message["content"] = error_msg

    # 도구 결과를 기록에 추가하고 반환합니다.
    ...

```

먼저 호출된 도구가 루프를 종료하는지(`exit_loop_tool`) 확인합니다. 그렇지 않으면 해당 도구에 대한 올바른 MCP 세션을 찾아 `session.call_tool()`을 호출합니다. 결과(또는 오류 응답)는 형식화되어 대화 기록에 추가되며, 에이전트가 도구의 출력을 인식할 수 있도록 반환됩니다.

## 우리의 Tiny Python Agent: 사실상 루프일 뿐입니다!

`MCPClient`가 도구 상호 작용에 대한 모든 작업을 수행하므로 `Agent` 클래스는 놀랍도록 간단해집니다. `MCPClient`를 상속하고 대화 관리 로직을 추가합니다.

> [!TIP]
> Agent 클래스는 작고 대화 루프에 중점을 둡니다. 코드는 [여기](https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_mcp/agent.py)에서 찾을 수 있습니다.

### 1. 에이전트 초기화

에이전트가 생성될 때, 구성 정보(모델, 공급자, 사용할 MCP 서버, 시스템 프롬프트)를 불러와 시스템 프롬프트로 대화 기록을 초기화합니다. `load_tools()` 메서드는  `agent.json`에 정의된 서버 구성을 반복하고 각 구성에 부모 클래스인 `MCPClient`의 `add_mcp_server`를 호출해 에이전트의 도구 상자를 채웁니다.

```python
# `Agent`의 12-54줄 
# https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_mcp/agent.py#L12:L54
class Agent(MCPClient):
    def __init__(
        self,
        *,
        model: str,
        servers: Iterable[Dict], # MCP 서버 구성
        provider: Optional[PROVIDER_OR_POLICY_T] = None,
        api_key: Optional[str] = None,
        prompt: Optional[str] = None, # 시스템 프롬프트
    ):
        # 모델, 공급자 등으로 기본 MCPClient 초기화
        super().__init__(model=model, provider=provider, api_key=api_key)
        # 로드할 서버 구성 저장
        self._servers_cfg = list(servers)
        # 시스템 메시지로 대화 시작
        self.messages: List[Union[Dict, ChatCompletionInputMessage]] = [
            {"role": "system", "content": prompt or DEFAULT_SYSTEM_PROMPT}
        ]

    async def load_tools(self) -> None:
        # 구성된 모든 MCP 서버에 연결하고 도구 등록
        for cfg in self._servers_cfg:
            await self.add_mcp_server(**cfg)

```

### 2. 에이전트의 핵심: 루프

`Agent.run()` 메서드는 단일 사용자 입력을 처리하는 비동기 제너레이터입니다. 에이전트의 현재 작업이 완료될 시기를 결정하면서 대화 턴을 관리합니다.

```python
# `Agent.run()`의 56-99줄
# https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_mcp/agent.py#L56:L99
async def run(self, user_input: str, *, abort_event: Optional[asyncio.Event] = None, ...) -> AsyncGenerator[...]:
    ...
    while True: # user_input 처리를 위한 메인 루프
        ...

        # LLM 및 도구와 한 단계 상호 작용하기 위해 MCPClient에 위임합니다.
        # 이는 LLM 텍스트, 도구 호출 정보 및 도구 결과를 스트리밍합니다.
        async for item in self.process_single_turn_with_tools(
            self.messages,
            ...
        ):
            yield item 

        ... 
        
        # 종료 조건
        # 1. "exit" 도구가 호출되었습니까?
        if last.get("role") == "tool" and last.get("name") in {t.function.name for t in EXIT_LOOP_TOOLS}:
                return

        # 2. 최대 턴에 도달했거나 LLM이 최종 텍스트 답변을 제공했습니까?
        if last.get("role") != "tool" and num_turns > MAX_NUM_TURNS:
                return
        if last.get("role") != "tool" and next_turn_should_call_tools:
            return
        
        next_turn_should_call_tools = (last_message.get("role") != "tool")
```

`run()` 루프 내부:
- 먼저 사용자 프롬프트를 대화에 추가합니다.
- 그런 다음 `MCPClient.process_single_turn_with_tools(...)`를 호출하여 LLM의 응답을 얻고 추론의 한 단계에 대한 도구 실행을 처리합니다.
- 각 항목은 즉시 반환되어 호출자에게 실시간 스트리밍을 가능하게 합니다.
- 각 단계 후에 종료 조건을 확인합니다. 특별한 "루프 종료" 도구가 사용되었는지, 최대 턴 제한에 도달했는지, 또는 LLM이 현재 요청에 대한 최종 텍스트 응답을 제공하는지 여부입니다.

## 다음 단계

MCP 클라이언트와 Tiny Agent를 탐색하고 확장할 수 있는 멋진 방법이 많이 있습니다 🔥
시작하는 데 도움이 되는 몇 가지 아이디어는 다음과 같습니다.

- 다양한 LLM 모델 및 추론 공급자가 에이전트 성능에 미치는 영향을 벤치마킹합니다. 각 공급자가 다르게 최적화할 수 있으므로 도구 호출 성능이 다를 수 있습니다. 지원되는 공급자 목록은 [여기](https://huggingface.co/docs/inference-providers/index#partners)에서 찾을 수 있습니다.
- [llama.cpp](https://github.com/ggerganov/llama.cpp) 또는 [LM Studio](https://lmstudio.ai/)와 같은 로컬 LLM 추론 서버로 Tiny Agent를 실행합니다.
- .. 물론 기여하세요! Hugging Face Hub의 [tiny-agents/tiny-agents](https://huggingface.co/datasets/tiny-agents/tiny-agents) 데이터셋에 자신만의 고유한 Tiny Agent를 공유하고 PR을 엽니다.

풀 리퀘스트 및 기여를 환영합니다! 다시 한 번 말하지만 여기 있는 모든 것은 [오픈 소스](https://github.com/huggingface/huggingface_hub)입니다! 💎❤️

```

### real/2025-10-12-vlm-explained-ko.md

```markdown
---
layout: post
title: "비전 언어 모델 쉽게 이해하기"
author: woojun
categories: [Multimodal]
image: assets/images/blog/posts/2025-10-12-vlm-explained-ko/thumbnail.png
---
* TOC
{:toc}
<!--toc-->
_이 글은 Hugging Face 블로그의 [Vision Language Models Explained](https://huggingface.co/blog/vlms)를 한국어로 번역한 글입니다._

---

# 비전 언어 모델 쉽게 이해하기

> [!TIP]
> 이 블로그 포스트는 2024년 4월에 작성되었으며, 비전 언어 모델의 내부 구조에 대한 훌륭한 소개, 기존 비전 언어 모델들의 개요, 그리고 이를 파인튜닝하는 방법을 제공합니다. 더 많은 기능과 모델을 다루는 [2025년 4월 업데이트](https://huggingface.co/blog/vlms-2025)를 작성했으니, 이 글도 꼭 확인해보세요!

비전 언어 모델은 이미지와 텍스트로부터 동시에 학습하여 시각적 질의응답(VQA)부터 이미지 캡셔닝까지 다양한 작업을 수행할 수 있는 모델입니다. 이 포스트에서는 비전 언어 모델의 주요 구성 요소들을 살펴보고, 전체적인 개요를 파악하며, 작동 원리를 이해하고, 적합한 모델을 찾는 방법, 추론에 사용하는 방법, 그리고 [trl](https://github.com/huggingface/trl)의 새 버전을 사용해 쉽게 파인튜닝하는 방법을 다룹니다!

## 비전 언어 모델(Vision Language Model)이란?

비전 언어 모델은 이미지와 텍스트로부터 학습할 수 있는 멀티모달(Multimodal) 모델로 폭넓게 정의됩니다. 이들은 이미지와 텍스트를 입력으로 받아 텍스트를 생성하는 생성형(generative) 모델의 일종입니다. 거대 비전 언어 모델은 우수한 제로샷(zero-shot) 능력을 가지고 있으며, 일반화 성능이 뛰어나고, 문서나 웹 페이지 등 다양한 유형의 이미지에 대해서도 사용할 수 있습니다. 활용 사례로는 이미지에 대해 대화하기, 명령 기반 이미지 인식, 시각적 질의응답(VQA), 문서 이해, 이미지 캡셔닝 등이 있습니다. 일부 비전 언어 모델은 이미지의 공간적 특성 또한 포착할 수 있습니다. 이러한 모델들은 특정 대상을 탐지하거나 분할하라는 프롬프트에 따라 바운딩 박스(bounding box) 또는 세그멘테이션 마스크(segmentation mask)를 출력할 수 있으며, 서로 다른 객체의 상대적 또는 절대적 위치를 파악하거나 그에 대한 질문에 답변할 수도 있습니다. 현재 존재하는 거대 비전 언어 모델들은 학습에 사용된 데이터, 이미지 인코딩 방식, 그리고 그로 인한 모델의 능력 측면에서 매우 다양합니다.

<p align="center">
 <img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/blog/vlm/visual.jpg" alt="VLM Capabilities" style="width: 90%; height: auto;"><br>
</p>

## 오픈소스 비전 언어 모델 살펴보기

Hugging Face Hub에는 많은 오픈소스 비전 언어 모델이 있습니다. 몇몇 주요한 모델들은 아래 표에 나와 있습니다.

- Base 모델과 대화 모드에서 사용할 수 있도록 채팅용으로 파인튜닝된 모델이 있습니다.
- 이러한 모델들 중 일부는 모델 환각(hallucination)을 줄이는 "그라운딩(grounding)" 기능을 가지고 있습니다.
- 별도로 명시되지 않는 한, 모든 모델은 영어로 학습되었습니다.

| 모델                  | 허용 라이선스 | 모델 크기 | 이미지 해상도 | 추가적인 기능               |
|------------------------|--------------------|------------|------------------|---------------------------------------|
| [LLaVA 1.6 (Hermes 34B)](https://huggingface.co/llava-hf/llava-v1.6-34b-hf) | ✅                  | 34B        | 672x672          |                                       |
| [deepseek-vl-7b-base](https://huggingface.co/deepseek-ai/deepseek-vl-7b-base)    | ✅                  | 7B         | 384x384          |                                       |
| [DeepSeek-VL-Chat](https://huggingface.co/deepseek-ai/deepseek-vl-7b-chat)       | ✅                  | 7B         | 384x384          | 대화                                  |
| [moondream2](https://huggingface.co/vikhyatk/moondream2)             | ✅                  | ~2B        | 378x378          |                                       |
| [CogVLM-base](https://huggingface.co/THUDM/cogvlm-base-490-hf)            | ✅                  | 17B        | 490x490          |                                       |
| [CogVLM-Chat](https://huggingface.co/THUDM/cogvlm-chat-hf)            | ✅                  | 17B        | 490x490          | 그라운딩, 대화                       |
| [Fuyu-8B](https://huggingface.co/adept/fuyu-8b)                | ❌                  | 8B         | 300x300          | 이미지 내 텍스트 탐지           |
| [KOSMOS-2](https://huggingface.co/microsoft/kosmos-2-patch14-224)               | ✅                  | ~2B        | 224x224          | 그라운딩, 제로샷 객체 탐지 |
| [Qwen-VL](https://huggingface.co/Qwen/Qwen-VL)                | ✅                  | 4B         | 448x448          | 제로샷 객체 탐지           |
| [Qwen-VL-Chat](https://huggingface.co/Qwen/Qwen-VL-Chat)           | ✅                  | 4B         | 448x448          | 대화                                  |
| [Yi-VL-34B](https://huggingface.co/01-ai/Yi-VL-34B)              | ✅                  | 34B        | 448x448          |  2개 국어 (영어, 중국어) |


## 적합한 비전 언어 모델 찾기

자신의 사용 사례에 가장 적합한 모델을 선택하는 방법은 여러 가지가 있습니다.

[Vision Arena](https://huggingface.co/spaces/WildVision/vision-arena)는 모델 출력에 대한 익명 투표만을 기반으로 하는 리더보드로, 지속적으로 업데이트됩니다. 이 아레나에서 사용자는 이미지와 프롬프트를 입력하면, 두 개의 서로 다른 모델의 출력이 무작위로 익명 제공되며, 사용자는 선호하는 출력을 선택할 수 있습니다. 이러한 과정을 통해 리더보드는 전적으로 인간의 선호도에 기반하여 구성됩니다.

<p align="center">
 <img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/blog/vlm/arena.png" alt="Vision Arena" style="width: 90%; height: auto;"><br>
<em>Vision Arena</em>
</p>

[Open VLM 리더보드](https://huggingface.co/spaces/opencompass/open_vlm_leaderboard)는 비전 언어 모델들이 다양한 평가 지표와 평균 점수에 따라 순위가 매겨지는 또 다른 리더보드입니다. 모델 크기, 오픈소스 여부에 따라 모델을 필터링하고, 다양한 평가 지표에 대한 순위를 확인할 수도 있습니다.

<p align="center">
 <img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/blog/vlm/leaderboard.png" alt="VLM Capabilities" style="width: 90%; height: auto;"><br>
<em>Open VLM 리더보드</em>
</p>

[VLMEvalKit](https://github.com/open-compass/VLMEvalKit)은 비전 언어 모델에서 Open VLM 리더보드의 벤치마크를 실행하기 위한 툴킷입니다.
또 다른 평가 도구는 [LMMS-Eval](https://github.com/EvolvingLMMs-Lab/lmms-eval)로, Hugging Face Hub에 호스팅된 데이터셋을 사용하여 선택한 Hugging Face 모델을 평가할 수 있는 표준 커맨드 라인 인터페이스(CLI)를 제공합니다. 아래와 같이 사용할 수 있습니다.

```bash
accelerate launch --num_processes=8 -m lmms_eval --model llava --model_args pretrained="liuhaotian/llava-v1.5-7b" --tasks mme,mmbench_en --batch_size 1 --log_samples --log_samples_suffix llava_v1.5_mme_mmbenchen --output_path ./logs/ 
```

Vision Arena와 Open VLM 리더보드는 제출된 모델만 확인할 수 있으며, 새로운 모델을 추가하려면 업데이트가 필요합니다. 추가 모델을 찾고 싶다면, Hub에서 `image-text-to-text` 태스크로 [모델](https://huggingface.co/models?pipeline_tag=image-text-to-text&sort=trending)을 탐색할 수 있습니다.

리더보드에는 비전 언어 모델을 평가하기 위한 다양한 벤치마크가 있습니다. 그 중 몇 가지를 살펴보겠습니다.

### MMMU

[MMMU(A Massive Multi-discipline Multimodal Understanding and Reasoning Benchmark for Expert AGI)](https://huggingface.co/datasets/MMMU/MMMU)는 비전 언어 모델을 평가하기 위한 가장 종합적인 벤치마크입니다. 예술, 공학 등 다양한 분야에서 대학 수준의 지식과 추론 능력을 요구하는 11,500개의 멀티모달 문제가 포함되어 있습니다.

### MMBench

[MMBench](https://huggingface.co/datasets/lmms-lab/MMBench)는 OCR, 객체 위치 추정 등 20가지 다양한 능력을 평가하기 위한 3,000개의 객관식 문제로 구성된 평가 벤치마크입니다. 해당 논문에서는 CircularEval이라는 평가 전략도 함께 제안하는데, 이는 질문의 선택지를 여러 조합으로 섞은 뒤, 모델이 매번 올바른 답을 일관되게 선택할 수 있는지를 평가하는 방식입니다. 이외에도 다양한 도메인별로 특화된 벤치마크들이 존재합니다. 예를 들어, MathVista(시각적 수학 추론), AI2D(도표 이해), ScienceQA(과학 질의 응답), OCRBench(문서 이해) 등이 있습니다.

## 기술적 세부사항
 
비전 언어 모델을 사전학습하는 방법은 여러 가지가 있습니다. 핵심 아이디어는 이미지와 텍스트 표현을 통합하고, 이를 텍스트 디코더에 입력해 생성 작업을 하도록 하는 것입니다. 가장 일반적이고 대표적인 모델들은 이미지 인코더(image encoder), 이미지와 텍스트 표현을 정렬하기 위한 임베딩 프로젝터(embedding projector, 보통 밀집 신경망), 그리고 텍스트 디코더(text decoder)로 구성되며, 이 순서로 쌓여 있습니다. 학습 방식은 모델마다 조금씩 다르게 설계됩니다.

예를 들어, LLaVA는 CLIP 이미지 인코더, 멀티모달 프로젝터, 그리고 Vicuna 텍스트 디코더로 구성됩니다. LLaVA의 저자들은 이미지와 캡션으로 구성된 데이터셋을 GPT-4에 입력하여, 캡션과 이미지에 관련된 질문을 자동으로 생성했습니다. 그 후, 이미지 인코더와 텍스트 디코더는 고정(freeze)하고, 멀티모달 프로젝터만 학습시켰습니다. 이때 모델에 이미지와 GPT-4가 생성한 질문을 입력하고, 모델의 출력이 정답 캡션과 일치하도록 학습했습니다. 프로젝터의 사전학습이 끝난 뒤에는 이미지 인코더를 계속 고정한 채, 텍스트 디코더와 프로젝터를 함께 학습시켰습니다. 이런 단계적 사전학습과 파인튜닝 방식은 현재 비전 언어 모델을 학습하는 가장 일반적이고 효과적인 접근법으로 사용되고 있습니다.

<p align="center">
 <img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/blog/vlm/vlm-structure.png" alt="VLM Structure" style="width: 90%; height: auto;"><br>
 <em>일반적인 비전 언어 모델의 구조</em>
</p>
<p align="center">
 <img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/blog/vlm/proj.jpg" alt="VLM Structure" style="width: 90%; height: auto;"><br>
 <em>프로젝션과 텍스트 임베딩은 위와 같이 연결됩니다</em>
</p>

또 다른 예로 KOSMOS-2가 있습니다. 이 모델의 저자들은 LLaVA와 같은 사전학습 방식과 달리, 모델 전체를 엔드투엔드(end-to-end)로 완전히 학습시키는 방식을 선택했습니다. 이는 계산 비용 측면에서 훨씬 더 비싸고 부담이 큽니다. 이후 저자들은 모델 정렬을 위해 언어로만 인스트럭션 파인튜닝을 수행했습니다. 또 다른 예로 Fuyu-8B는 아예 이미지 인코더를 사용하지 않습니다. 대신, 이미지 패치를 직접 프로젝션 레이어에 입력하고, 그 결과로 나온 시퀀스를 자가회귀(auto-regressive) 디코더를 통해 처리합니다.

대부분의 경우, 비전 언어 모델을 처음부터 사전학습할 필요는 없습니다. 이미 공개된 모델을 활용하거나, 자신의 사용 사례에 맞게 파인튜닝하는 것으로 충분합니다.
이후 섹션에서는 이러한 모델들을 Transformers 라이브러리를 사용해 다루는 방법과, SFTTrainer를 이용해 파인튜닝하는 방법을 살펴보겠습니다.

## transformers를 통해 비전 언어 모델 사용하기

아래와 같이 `LlavaNext` 모델을 사용해 Llava로 추론할 수 있습니다.

먼저, 모델과 프로세서를 초기화해봅시다.

```python
from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration
import torch

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
processor = LlavaNextProcessor.from_pretrained("llava-hf/llava-v1.6-mistral-7b-hf")
model = LlavaNextForConditionalGeneration.from_pretrained(
    "llava-hf/llava-v1.6-mistral-7b-hf",
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True
)
model.to(device)
```

이제 이미지와 텍스트 프롬프트를 프로세서에 전달한 뒤, 처리된 입력값을 `generate`에 전달합니다. 각 모델은 고유한 프롬프트 템플릿을 사용하므로, 성능 저하를 피하기 위해 반드시 올바른 템플릿을 사용해야 합니다.

```python
from PIL import Image
import requests

url = "https://github.com/haotian-liu/LLaVA/blob/1a91fc274d7c35a9b50b3cb29c4247ae5837ce39/images/llava_v1_5_radar.jpg?raw=true"
image = Image.open(requests.get(url, stream=True).raw)
prompt = "[INST] <image>\nWhat is shown in this image? [/INST]"

inputs = processor(prompt, image, return_tensors="pt").to(device)
output = model.generate(**inputs, max_new_tokens=100)
```

`decode`를 호출해 출력 토큰을 디코딩합니다.

```python
print(processor.decode(output[0], skip_special_tokens=True))
```

## TRL을 활용해 비전 언어 모델 파인튜닝하기

[TRL](https://github.com/huggingface/trl)의 `SFTTrainer`가 이제 비전 언어 모델을 실험적으로 지원하기 시작했습니다! 여기서는 [llava-instruct](https://huggingface.co/datasets/HuggingFaceH4/llava-instruct-mix-vsft) 데이터셋을 사용해 [Llava 1.5 VLM](https://huggingface.co/llava-hf/llava-1.5-7b-hf) 모델에 대해 SFT를 수행하는 예시를 제공합니다. 이 데이터셋은 26만 개의 이미지-대화 쌍으로 구성되어 있습니다.
데이터셋은 사용자와 어시스턴트 간의 상호작용을 메시지 시퀀스 형태로 구성합니다. 예를 들어, 각 대화는 사용자가 질문하는 이미지와 짝지어져 있습니다.

이 실험적인 지원을 VLM 학습에 적용해보기 위해서는 `pip install -U trl`로 TRL의 최신 버전을 설치해야 합니다.
전체 예시 스크립트는 [여기](https://github.com/huggingface/trl/blob/main/examples/scripts/vsft_llava.py)서 확인할 수 있습니다.

```python
from trl.commands.cli_utils import SftScriptArguments, TrlParser

parser = TrlParser((SftScriptArguments, TrainingArguments))
args, training_args = parser.parse_args_and_config()
```

인스트럭션 파인튜닝을 위해 대화 템플릿을 초기화합니다.

{% raw %}
```bash
LLAVA_CHAT_TEMPLATE = """A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions. {% for message in messages %}{% if message['role'] == 'user' %}USER: {% else %}ASSISTANT: {% endif %}{% for item in message['content'] %}{% if item['type'] == 'text' %}{{ item['text'] }}{% elif item['type'] == 'image' %}<image>{% endif %}{% endfor %}{% if message['role'] == 'user' %} {% else %}{{eos_token}}{% endif %}{% endfor %}"""
```
{% endraw %}


이제 모델과 토크나이저를 초기화합니다.

```python
from transformers import AutoTokenizer, AutoProcessor, TrainingArguments, LlavaForConditionalGeneration
import torch

model_id = "llava-hf/llava-1.5-7b-hf"
tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.chat_template = LLAVA_CHAT_TEMPLATE
processor = AutoProcessor.from_pretrained(model_id)
processor.tokenizer = tokenizer

model = LlavaForConditionalGeneration.from_pretrained(model_id, torch_dtype=torch.float16)
```

텍스트와 이미지 쌍을 묶어주기 위해 데이터 콜레이터를 생성합니다.

```python
class LLavaDataCollator:
    def __init__(self, processor):
        self.processor = processor

    def __call__(self, examples):
        texts = []
        images = []
        for example in examples:
            messages = example["messages"]
            text = self.processor.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=False
            )
            texts.append(text)
            images.append(example["images"][0])

        batch = self.processor(texts, images, return_tensors="pt", padding=True)

        labels = batch["input_ids"].clone()
        if self.processor.tokenizer.pad_token_id is not None:
            labels[labels == self.processor.tokenizer.pad_token_id] = -100
        batch["labels"] = labels

        return batch

data_collator = LLavaDataCollator(processor)
```

데이터셋을 불러옵니다.

```python
from datasets import load_dataset

raw_datasets = load_dataset("HuggingFaceH4/llava-instruct-mix-vsft")
train_dataset = raw_datasets["train"]
eval_dataset = raw_datasets["test"]
```

모델, 데이터셋 분할, PEFT 설정, 그리고 데이터 콜레이터를 전달해 SFTTrainer를 초기화한 뒤 `train()`을 호출합니다. 최종 체크포인트를 Hugging Face Hub에 업로드하려면 `push_to_hub()`를 호출합니다.

```python
from trl import SFTTrainer

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    dataset_text_field="text",  # 더미 필드 필요
    tokenizer=tokenizer,
    data_collator=data_collator,
    dataset_kwargs={"skip_prepare_dataset": True},
)

trainer.train()
```

모델을 저장한 뒤 Hugging Face Hub에 업로드합니다.

```python
trainer.save_model(training_args.output_dir)
trainer.push_to_hub()
```
학습된 모델은 [여기](https://huggingface.co/HuggingFaceH4/vsft-llava-1.5-7b-hf-trl)에서 확인할 수 있습니다.

**감사의 글**

이 블로그 게시물에 대한 리뷰와 제안을 해주신 Pedro Cuenca, Lewis Tunstall, Kashif Rasul, 그리고 Omar Sanseviero께 감사드립니다.
```

### real/2025-10-20-2025-VLM.md

```markdown
---
layout: post
title: "2025년의 VLM : 더 좋아지고, 더 빠르고, 더 강해진 비전 언어 모델"
author: youngjun
categories: [VLM]
image: assets/images/blog/posts/2025-10-20-2025-VLM/thumbnail.png
---
* TOC
{:toc}
<!--toc-->
_이 글은 Hugging Face 블로그의 [Vision Language Models (Better, Faster, Stronger)](https://huggingface.co/blog/vlms-2025)를 한국어로 번역한 글입니다._

---
## 들어가며
비전 언어 모델(VLM)이 요즘 화제입니다. 이전 [블로그 포스트](https://huggingface.co/blog/vlms)(2024년 4월 포스팅)에서 우리는 VLM들에 대해 깊이 있게 다뤘습니다. 그중 상당 부분은 최초의 성공적이고 재현이 용이한 오픈소스 VLM인 LLaVA에 관한 내용이었으며, 오픈 모델을 발견하고 평가하며 미세 조정하는 방법에 대한 팁도 함께 소개했습니다.

그 이후로 많은 변화가 있었습니다. 모델들은 더 작아졌지만 더 강력해졌습니다. 새로운 아키텍처와 기능들(추론, 자율성, 긴 영상 이해 등)이 등장했습니다. 동시에 멀티모달 검색-증강 생성(Multimodal RAG)과 멀티모달 에이전트(Multimodal Agent)와 같은 완전히 새로운 패러다임이 형성되었습니다.

이 포스트에서는 지난 한 해 동안 VLM에서 일어난 모든 일들을 되돌아보고 분석해 보겠습니다. 주요 변화, 떠오르는 트렌드, 그리고 주목할 만한 발전사항들을 확인하실 수 있을 것입니다.

> 비전 언어 모델이 어떻게 작동하는지에 대한 좋은 입문서를 원하신다면, [첫 번째 블로그 포스트](https://huggingface.co/blog/vlms)를 읽어보시길 강력히 권장합니다. (Hugging Face KREW Blog 블로그에서도 번역했답니다!)

## 모델 살펴보기
이 섹션에서는 새로운 유형의 VLM을 살펴보겠습니다. 일부는 완전히 새로운 반면, 다른 일부는 기존 연구의 개선된 버전입니다.

### Any-to-any 모델
Any-to-any 모델은 이름에서 알 수 있듯이 모든 모달리티를 입력으로 받아 모든 모달리티(이미지, 텍스트, 오디오)를 출력할 수 있는 모델입니다. 이는 모달리티간 정렬(align)을 통해 이루어지며, 한 모달리티의 입력을 다른 모달리티로 변환할 수 있습니다(예: "개"라는 단어가 개의 이미지나 해당 단어의 발화음과 연관됨).

이러한 모델들은 다중 인코더(각 모달리티당 하나)를 가지고 있으며, 임베딩을 함께 융합하여 공유 표현 공간을 만듭니다. 디코더(다중 또는 단일)는 공유 잠재 공간을 입력받아 선택한 모달리티로 디코딩합니다. 최초의 any-to-any 모델 구축 시도는 `Meta`의 [Chameleon](https://huggingface.co/collections/facebook/chameleon-668da9663f80d483b4c61f58)으로, 이미지와 텍스트를 입력받아 이미지와 텍스트를 출력할 수 있습니다. Meta는 이 모델의 이미지 생성 기능을 공개하지 않았기 때문에, `Alpha-VLLM`이 Chameleon 위에 이미지 생성을 구축한 [Lumina-mGPT](https://huggingface.co/collections/Alpha-VLLM/lumina-mgpt-family-66ae48a59a973eeae4513848)를 출시했습니다.

가장 최신이자 가장 강력한 any-to-any 모델은 [Qwen 2.5 Omni](https://huggingface.co/collections/Qwen/qwen25-omni-67de1e5f0f9464dc6314b36e)로, 그 구조를 살펴보면 any-to-any 모델의 아키텍처를 이해하기 좋은 예입니다.

![](https://i.imgur.com/Zmerw7r.png)

Qwen2.5-Omni는 새로운 "Thinker-Talker" 아키텍처를 사용하는데, "Thinker"가 텍스트 생성을 담당하고, "Talker"가 스트리밍 방식으로 자연스러운 음성 응답을 생성합니다. [MiniCPM-o 2.6](https://huggingface.co/openbmb/MiniCPM-o-2_6)은 8B 파라미터를 가진 멀티모달 모델로, 비전, 음성, 언어 모달리티에 걸쳐 콘텐츠를 이해하고 생성할 수 있습니다. DeepSeek AI가 소개한 [Janus-Pro-7B](https://huggingface.co/deepseek-ai/Janus-Pro-7B)는 모달리티 간 콘텐츠 이해와 생성 모두에 뛰어난 통합 멀티모달 모델입니다. 이해와 생성 프로세스를 분리하는 분리된 시각적 인코딩 아키텍처가 특징입니다.

우리는 앞으로 이러한 모델의 수가 증가할 것으로 예상합니다. 멀티모달 학습이 심층 표현을 더 잘 학습할 수 있는 유일한 방법이라는 것은 널리 알려진 사실입니다. 우리는 이러한 any-to-any 모델들과 데모를 선별해 모은 [컬렉션](https://huggingface.co/collections/merve/any-to-any-models-datasets-spaces-6822042ee8eb7fb5e38f9b62)을 준비했습니다.

### 추론 모델
추론 모델은 복잡한 문제를 해결할 수 있는 모델입니다. 이러한 모델은 처음에는 대규모 언어 모델에서 등장했으며, 최근에는 VLM 영역으로 확장되고 있습니다. 2025년까지는 Qwen의 [QVQ-72B-preview](https://huggingface.co/Qwen/QVQ-72B-Preview)라는 단 하나의 오픈소스 멀티모달 추론 모델만 있었습니다. 이것은 `Alibaba Qwen` 팀이 개발한 실험적 모델로 많은 제한 사항이 있었습니다.

2025년 올해, 새로운 멀티모달 추론 모델 주자가 등장했습니다. `Moonshot AI` 팀의 [Kimi-VL-A3B-Thinking](https://huggingface.co/moonshotai/Kimi-VL-A3B-Thinking)입니다. 이 모델은 이미지 인코더로 MoonViT(SigLIP-so-400M)를 사용하고, 총 16B 파라미터에 2.8B의 활성 파라미터만 있는 전문가 혼합(MoE) 디코더를 사용합니다. 이 모델은 Kimi-VL 기반 VLM을 긴 생각의 연쇄(long chain-of-thought) 방식으로 미세 조정 후 추가 정렬(reinforcement learning, 강화 학습)한 버전입니다. [여기서](https://huggingface.co/spaces/moonshotai/Kimi-VL-A3B-Thinking) 모델을 체험해볼 수 있습니다.

> 저자들은 [Kimi-VL-A3B-Instruct](https://huggingface.co/moonshotai/Kimi-VL-A3B-Instruct)라는 지시문 미세 조정 버전도 출시했습니다.
 
![d3ACkiw.png](https://i.imgur.com/d3ACkiw.png)

이 모델은 긴 영상, PDF, 스크린샷 등을 입력받을 수 있습니다. 에이전트 기능도 가지고 있습니다.

### 작지만 강력한 모델
커뮤니티는 과거에 파라미터 수를 통해 지능을 확장하고, 이후 고품질 합성 데이터를 활용하곤 했습니다. 특정 시점이 지나자 벤치마크가 포화 상태에 이르렀고, 모델 확장은 수익이 감소했습니다. 커뮤니티는 증류(distillation)와 같은 다양한 방법을 통해 대규모 모델을 축소하기 시작했습니다. 이는 컴퓨팅 비용을 절감하고 배포를 단순화하며, 로컬 실행과 같은 사용 사례를 가능하게 하여 데이터 프라이버시를 강화하기 때문에 합리적인 접근입니다.

작은 VLM이란 일반적으로 소비자용 GPU에서 실행할 수 있는 2B 파라미터 미만의 모델을 말합니다. SmolVLM은 소형 VLM의 대표적인 모델 계열입니다. 더 큰 모델을 축소하는 대신, 저자들은 대형 모델을 축소하는 방식이 아니라, **아예** 256M, 500M, 2.2B처럼 극히 적은 파라미터 규모에 모델을 맞추는 정반대의 접근을 시도했습니다. 예를 들어 SmolVLM2는 이러한 크기에서 영상 이해 문제를 해결하려고 시도했고, 500M이 적절한 균형점임을 발견했습니다. Hugging Face에서 이러한 모델 규모로도 소비자 기기에서 영상 이해가 가능함을 보여주기 위해 HuggingSnap이라는 iPhone 애플리케이션을 만들었습니다.

또 다른 주목할 만한 모델은 `Google DeepMind`의 [gemma3-4b-it](https://huggingface.co/google/gemma-3-4b-it)입니다. 이 모델에서 흥미로운 점은, 현재까지 가장 작은 멀티모달 모델 중 하나이며, 128k 토큰 컨텍스트 윈도우를 가지고 있으며, 140개 이상의 언어를 지원한다는 점입니다! 이 모델은 Gemma 3 모델 패밀리의 일부로, 가장 큰 모델은 당시 Chatbot Arena에서 1위를 차지했습니다. 그 후 가장 큰 모델이 1B 변형으로 증류되었습니다.

마지막으로, 가장 작은 모델은 아니지만 [Qwen2.5-VL-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct)도 주목할 만합니다. 이 모델은 지역화(객체 감지 및 포인팅)부터 문서 이해, 에이전트 작업까지 다양한 작업을 수행할 수 있으며, 컨텍스트 길이는 최대 32k 토큰입니다.

MLX 및 Llama.cpp 통합을 통해 작은 모델을 사용할 수 있습니다. MLX의 경우, 설치되어 있다고 가정하고, 이 한 줄로 SmolVLM-500M-Instruct를 시작할 수 있습니다:
```shell
python3 -m mlx_vlm.generate --model HuggingfaceTB/SmolVLM-500M-Instruct --max-tokens 400 --temp 0.0 --image https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/vlm_example.jpg --prompt "What is in this image?"
```

CLI로 llama.cpp를 통해 GGUF 형식의 [gemma-3-4b-it](https://huggingface.co/collections/google/gemma-3-release-67c6c6f89c4f76621268bb6d) 모델 사용도 이 한 줄로 시작할 수 있습니다:
```shell
llama-mtmd-cli -hf ggml-org/gemma-3-4b-it-GGUF
```

또한 다음과 같이 동일한 모델을 서빙할 수 있습니다:
```shell
llama-server -hf ggml-org/gemma-3-4b-it-GGUF
```

가장 초기의 VLM 시도로 [moondream2](https://huggingface.co/vikhyatk/moondream2)와 [Florence-2](https://huggingface.co/collections/microsoft/florence-6669f44df0d87d9c3bfb76de)를 소개합니다. 이 블로그에서는 주로 새로운 모델들(대부분 2024년 4월 이후 출시된 모델)을 다룹니다.

### 디코더로서의 전문가 혼합(Mixture-of-Experts, MoE)
전문가 혼합(MoE) 모델은 주어진 입력 데이터 세그먼트를 처리하기 위해 "전문가"라고 불리는, 가장 관련성 있는 하위 모델만 동적으로 선택하고 활성화함으로써 밀집 아키텍처에 대한 대안을 제공합니다. 이 선택적 활성화(라우터에 의해 수행됨) 메커니즘은 더 적은 계산 리소스를 사용하면서도 모델 성능과 운영 효율성을 크게 향상시킬 수 있는 잠재력을 보여주었습니다.

MoE는 네트워크의 더 작은 부분만 선택적으로 활성화하기 때문에 유사한 파라미터 밀집 모델보다 추론 속도가 빠릅니다. 또한 훈련 중에 빠르게 수렴합니다. 모든 좋은 것에는 비용이 따르는데, MoE는 작은 청크만 사용되더라도 모든 모델이 GPU에 있어야 하므로 더 많은 메모리 비용이 필요합니다.

널리 채택된 Transformer 아키텍처에서 MoE 레이어는 가장 일반적으로 각 Transformer 블록 내의 표준 피드포워드 네트워크(FFN) 레이어를 대체하여 통합됩니다. 밀집 네트워크는 추론을 실행하기 위해 전체 모델을 사용하는 반면, 유사한 크기의 MoE 네트워크는 일부 '전문가'만 선택적으로 활성화합니다. 이것은 더 나은 계산 활용과 더 빠른 추론에 도움이 됩니다.

전문가 혼합 디코더를 가진 VLM은 성능이 향상된 것으로 보입니다. 예를 들어, Kimi-VL은 현재 전문가 혼합 디코더를 가진 가장 진보된 개방형 추론 모델입니다. 전문가 혼합은 [MoE-LLaVA](https://huggingface.co/papers/2401.15947)의 효율성과 환각 감소에 대한 초점, [DeepSeek-VL2](https://huggingface.co/deepseek-ai/deepseek-vl2)의 광범위한 멀티모달 기능에서도 유망한 결과를 보여줍니다. Llama의 최신 버전(Llama 4)은 비전 기능을 가진 MoE입니다. 디코더로서의 MoE는 유망한 연구 분야이며, 이와 유사한 모델의 증가가 예상됩니다.

> MoE에 대해 더 잘 이해하고 싶으면, [이 글](https://huggingface.co/blog/moe)을 읽어보시는 것을 추천드립니다.

### VLA(비전-언어-행동 모델) 
VLM은 로보틱스 분야에서도 두각을 나타내고 있습니다! 이 분야에서는 비전-언어-행동 모델(Vision-Language Action, VLA) 모델이라고 부릅니다. 하지만 속지 마세요, 사실상 VLA는 작은 콧수염과 모자를 쓴 VLM에 불과합니다. VLA는 이미지와 텍스트 지시문을 입력으로 받아 로봇이 직접 취해야 할 행동을 나타내는 텍스트를 반환합니다. VLA는 물리적 환경과 상호작용하고 제어하기 위해 행동 및 상태 토큰을 추가하여 비전 언어 모델을 확장합니다. 이러한 추가 토큰은 시스템의 내부 상태(환경을 인지하는 방법), 행동(명령에 기반한 수행 내용), 시간 관련 정보(작업의 단계 순서같은)를 나타냅니다. 이러한 토큰은 행동이나 정책을 생성하기 위해 비전 언어 입력에 추가됩니다.

VLA는 보통 기본 VLM 위에 미세 조정됩니다. 일부 사람들은 이 정의를 확장하여 실제 또는 디지털 세계와 시각적으로 상호작용하는 모든 모델을 VLA로 정의하기도 합니다. 이 정의에 따르면 VLA는 UI 탐색을 수행하거나 에이전트 워크플로우에 사용될 수 있습니다. 하지만 많은 사람들은 이러한 애플리케이션이 VLM 도메인에 속한다고 믿습니다.

대표적인 VLA 모델로는 `Physical Intelligence`의 π0과 π0-FAST가 있습니다. 이 두 모델은 최초의 로보틱스 파운데이션 모델(robotics foundation models)로, 현재 Hugging Face의 LeRobot 라이브러리에 포팅되어 있습니다. 이 모델들은 7개의 로봇 플랫폼과 68개의 고유한 작업을 학습했습니다. 이들은 빨래 접기, 테이블 정리, 식료품 포장, 상자 조립, 물체 찾기과 같은 복잡한 실제 환경 작업에서 모두 강력한 제로샷 및 미세 조정 성능을 보여줍니다.

[GR00T N1](https://huggingface.co/nvidia/GR00T-N1-2B)은 NVIDIA의 범용 휴머노이드 로봇을 위한 오픈 VLA 파운데이션 모델입니다. 이미지와 언어를 이해하고, 지능적 추론과 실시간 동작 제어를 결합한 시스템 덕분에 팔을 움직이거나 지시를 따르는 등의 행동으로 변환합니다. GR00T N1은 또한 로봇 시연을 공유하고 훈련하는 것을 단순화하기 위해 만들어진 오픈 표준인 LeRobot 데이터셋 포맷 위에 구축되었습니다.

![](https://i.imgur.com/9gI91Wh.png)

이제 최신 VLM 모델 혁신을 살펴보았으니, 더 확립된 기능들이 어떻게 발전했는지 탐구해봅시다.

## 특화된 기능들

### VLM을 이용한 객체 감지, 분할, 계수
앞서 살펴본 바와 같이, VLM은 전통적인 컴퓨터 비전 작업에 대한 일반화를 가능하게 합니다. 이제 모델은 이미지와 개방형 텍스트와 같은 다양한 프롬프트를 입력받아, 감지, 분할을 위한 지역화 토큰이 포함된 구조화된 텍스트를 출력할 수 있습니다.

지난해 [PaliGemma](https://huggingface.co/blog/paligemma)는 이러한 과제 해결을 시도한 최초의 모델이었습니다. 이 모델은 이미지와 텍스트(관심 객체에 대한 설명) 및 작업 접두사를 입력으로 받습니다. 텍스트 프롬프트는 "줄무늬 고양이를 분할하세요(segment striped cat)" 또는 "지붕 위의 새를 감지하세요(detect bird on the roof)"와 같습니다.

감지의 경우, 모델은 경계 상자 좌표를 토큰으로 출력합니다. 반면 분할의 경우, 모델은 감지 토큰과 분할 토큰을 출력합니다. 이러한 분할 토큰은 모든 분할된 픽셀 좌표가 아니라, 이러한 토큰을 유효한 분할 마스크로 디코딩하도록 훈련된 변분 오토인코더(VAE)에 의해 디코딩되는 코드북 인덱스입니다(아래 그림 참조).

![](https://i.imgur.com/c8tC5pd.png)


PaliGemma 이후 많은 모델들이 지역화 작업을 수행하기 위해 도입되었습니다. 작년 말, PaliGemma의 업그레이드 버전인 PaliGemma 2가 동일한 기능과 더 나은 성능으로 등장했습니다. 나중에 나온 또 다른 모델은 `Allen AI`의 Molmo로, 점으로 인스턴스를 가리키고 객체 인스턴스를 계수할 수 있습니다.

![](https://i.imgur.com/OT4oTEb.png)

Qwen2.5-VL도 객체를 감지하고, 가리키고, 계수할 수 있으며, 이는 UI 요소도 객체로 포함합니다!

![](https://i.imgur.com/63hKnua.png)

### 멀티모달 안전(Multimodal Safety) 모델
프로덕션의 VLM은 탈옥과 규정 준수를 위한 유해한 출력을 방지하기 위해 입력과 출력을 필터링해야 합니다. 유해한 콘텐츠는 폭력적 입력부터 성적으로 노골적인 콘텐츠까지 다양합니다. 바로 여기에 멀티모달 안전 모델이 활용됩니다: 이들은 VLM의 입력과 출력을 필터링하기 위해 모델 전후에 배치됩니다. 이는 LLM 안전 모델과 유사하지만 추가 이미지 입력을 처리할 수 있습니다.

2025년 초, `Google`은 최초의 오픈 멀티모달 안전 모델인 [ShieldGemma 2](https://huggingface.co/google/shieldgemma-2-4b-it)를 소개했습니다. 이 모델은 텍스트 전용 안전 모델인 ShieldGemma를 기반으로 구축되었습니다. 이 모델은 이미지와 콘텐츠 정책을 입력받아 주어진 정책에 대해 이미지가 안전한지 여부를 반환합니다. 정책은 이미지가 부적절한 기준을 말합니다. ShieldGemma 2는 이미지 생성 모델의 출력을 필터링하는 데에도 사용될 수 있습니다.

`Meta`의 [Llama Guard 4](https://huggingface.co/spaces/merve/llama-guard-4)는 밀집 멀티모달 및 다국어 안전 모델입니다. 안전성 미세 조정과 함께 Llama 4 Scout(멀티모달 전문가 혼합 모델)에서 밀집하게 가지치기되었습니다.

![](https://i.imgur.com/CZdcvHf.png)

이 모델은 텍스트 전용 및 멀티모달 추론에 사용될 수 있습니다. 또한 VLM의 출력을 입력받아 대화를 완성하고, 사용자에게 전송하기 전에 필터링할 수 있습니다.

### 멀티모달 RAG: Retrievers, Rerankers
이제 멀티모달 공간에서 검색-증강 생성(RAG)이 어떻게 진화했는지 살펴봅시다. 일반적으로 PDF로 된 복잡한 문서에 대한 RAG는 세 단계로 처리됩니다:
1. 문서를 완전히 텍스트로 파싱
2. 일반 텍스트와 쿼리를 검색기(Retriever)와 재정렬기(Reranker)에 전달하여 가장 관련성 있는 문서 얻기
3. 관련 컨텍스트와 쿼리를 LLM에 전달

기존 PDF 파서는 문서의 구조와 시각적 요소(레이아웃, 표, 이미지, 차트 등)를 보존하기 위해 여러 구성 요소로 이루어져 있으며, 이 모든 요소가 마크다운으로 변환됩니다. 하지만 이 설정은 유지 관리가 어려울 수 있습니다.

![](https://i.imgur.com/ysyxqdg.png)

그러나 VLM의 등장과 함께 이 문제가 해결되었습니다: 이제 멀티모달 검색기와 리랭커가 있습니다.

![](https://i.imgur.com/EDpIFVL.png)

멀티모달 검색기는 PDF 문서 스택과 쿼리를 입력으로 받아 신뢰도 점수와 함께 가장 관련성 있는 페이지 번호를 반환합니다. 점수는 페이지가 쿼리에 대한 답변을 포함할 가능성 또는 쿼리가 페이지와 얼마나 관련이 있는지를 나타냅니다. 이것은 취약한 파싱 단계를 우회합니다.

가장 관련성 있는 페이지는 쿼리와 함께 VLM에 공급되고, VLM이 답변을 생성합니다.

주요 멀티모달 리트리버 아키텍처는 두 가지입니다:
- 문서 스크린샷 임베딩(DSE, MCDSE)
- ColBERT 계열 모델(ColPali, ColQwen2, ColSmolVLM)

DSE 모델은 텍스트 인코더와 이미지 인코더로 구성되어 쿼리당 단일 벡터를 반환합니다. 반환된 점수는 임베딩의 내적에 대한 소프트맥스입니다. 구절당 단일 벡터를 반환합니다.

> 소프트맥스?
> 소프트맥스는 DSE 모델이 계산한 여러 문장의 '유사도 점수'를 '정답일 확률'로 변환하여, 모델이 가장 가능성 높은 선택지를 고르거나 학습할 수 있도록 돕는 핵심적인 장치입니다.

![](https://i.imgur.com/7oWZXCp.png)

ColPali와 같은 ColBERT류 모델도 이중 인코더 모델이지만 한 가지 차이점이 있습니다: ColPali는 이미지 인코더로 VLM을, 텍스트 인코더로 LLM을 가지고 있습니다. 이러한 모델은 본질적으로 인코더가 아니지만, 모델이 임베딩을 출력하고, 이것이 "MaxSim"으로 전달됩니다. 출력은 DSE와 달리 각 토큰당 하나씩 총 여러 개의 벡터로 이루어집니다. MaxSim에서 각 텍스트 토큰 임베딩과 각 이미지 패치 임베딩 간의 유사성이 계산되며, 이 접근 방식은 뉘앙스를 더 잘 포착합니다. 이러한 이유로 ColBERT류 모델은 비용 효율성이 낮지만 성능이 더 좋습니다.

아래는 ColPali의 인덱싱 지연 시간을 볼 수 있습니다. 단일 모델이기 때문에 유지 관리도 더 쉽습니다.

![](https://i.imgur.com/nllvvh5.png)


Hugging Face Hub에서 이러한 모델들은 "[Visual Document Retrieval](https://huggingface.co/models?pipeline_tag=visual-document-retrieval&sort=trending)" 작업 아래에서 찾을 수 있습니다.

이 작업에 가장 인기 있는 벤치마크는 ViDoRe로, 재무 보고서, 과학 그림부터 행정 문서까지 다양한 **영어** 및 **프랑스어** 문서로 구성되어 있습니다. ViDoRe의 각 예제에는 문서 이미지, 쿼리 및 잠재적 답변이 있습니다. 쿼리와 일치하는 문서는 대조 사전 훈련에 도움이 되므로 ViDoRe 훈련 세트는 새로운 모델을 훈련하는 데 사용됩니다.

## 멀티모달 에이전트
VLM은 문서를 이용한 대화부터 컴퓨터 사용까지 많은 에이전트 워크플로우를 가능하게 합니다. 여기서는 고급 에이전트 기능이 필요하기 때문에 '컴퓨터 사용'을 다룹니다. 최근 UI를 이해하고 조작하는 VLM이 다수 출시되었습니다. 최신 모델은 `ByteDance`의 UI-TARS-1.5로, 브라우저, 컴퓨터 및 휴대폰 사용에서 훌륭한 결과를 보여주었습니다. 추론과 함께 게임플레이도 할 수 있으며 오픈 월드 게임 내 조작 가능합니다. 올해의 또 다른 주목할 만한 모델은 MAGMA-8B로, UI 탐색과 현실 세계의 물리적 상호작용 모두를 지원하는 파운데이션 모델입니다. 또한 Qwen2.5-VL(특히 에이전트 작업에 대해 추가 훈련된 32B 변형)과 Kimi-VL 추론 모델은 GUI 에이전트 작업에 탁월합니다.

2025년 초, 우리는 ReAct 프레임워크를 구현하는 새로운 경량 에이전트 라이브러리인 smolagents를 소개했습니다.(smolagents는 블로그의 [다른 포스트](https://hugging-face-krew.github.io/Introducing-smolagents/)에서도 번역 작업이 이루어졌습니다!) 그 직후, 라이브러리에 VLM 지원을 구현했습니다. 이 통합은 두 가지 사용 사례에서 이루어졌습니다:

- 실행 시작 시 한 번만 이미지 제공. 이것은 도구 사용이 포함된 문서 AI에 유용합니다.
- 동적으로 이미지 검색. VLM 에이전트를 통한 GUI 제어와 같이 에이전트가 반복적으로 스크린샷을 찍는 경우에 유용합니다.

라이브러리는 사용자가 이미지 이해 기능을 탑재한 자신만의 에이전트 워크플로우를 구축할 수 있는 빌딩 블록을 제공합니다. 우리는 사용자가 쉽게 시작할 수 있도록 다양한 스크립트와 한 줄로 된 CLI 명령을 제공합니다.

첫 번째 사례에서는 문서를 설명하는 에이전트가 필요하다고 가정합니다(에이전트적 특성은 약하지만 최소한의 사용 사례에는 좋습니다). 다음과 같이 CodeAgent(자체 코드를 작성하는 에이전트)를 초기화할 수 있습니다:

```python
agent = CodeAgent(tools=[], model=model) # 도구 불필요
agent.run("Describe these documents:", images=[document_1, document_2, document_3])
```

스크린샷을 가져와야 하는 후자의 사용 사례의 경우, 각 ActionStep 끝에 실행될 콜백을 정의할 수 있습니다. 동적으로 이미지를 가져와야 하는 여러분의 사용 사례에 맞게 콜백을 자유롭게 수정하세요. 간결함을 위해 여기서 자세히는 정의하지 않겠습니다. 선택적으로, 이 블로그 포스트 끝의 블로그 포스트와 스크립트 자체를 참고할 수 있습니다. 지금은 콜백과 브라우저 제어 단계를 통해 에이전트를 초기화하는 방법을 봅시다:

```python
def save_screenshot(memory_step: ActionStep, agent: CodeAgent) -> None:
    """
    스크린샷을 찍어 관찰 로그에 기록합니다.
    """
    png_bytes = driver.get_screenshot_as_png()
    memory_step.observations_images = [image.copy()] # memory_step에 이미지 유지
    url_info = f"Current url: {driver.current_url}"
    memory_step.observations = (
        url_info if memory_step.observations is None else memory_step.observations + "\n" + url_info
    )
    return

agent = CodeAgent(
    tools=[go_back, close_popups, search_item_ctrl_f], # 탐색 도구 전달
    model=model,
    additional_authorized_imports=["helium"],
    step_callbacks=[save_screenshot], # 콜백 전달
)
```

다음 CLI 명령을 실행하여 전체 예제를 간단히 시도해 볼 수 있습니다. 이 명령어는 웹 자동화 작업을 수행하기 위해 VLM로 구동되는 웹 브라우저에 대한 제어 권한이 있는 에이전트를 시작합니다(원하는 웹사이트로 교체하세요):

```shell
webagent "go to xyz.com/men, get to sale section, click the first clothing item you see. Get the product details, and the price, return them. note that I'm shopping from France"
```

smolagents는 로컬 트랜스포머 모델, 추론 제공자를 사용하여 제공되는 오픈소스 모델 또는 엔드포인트 폐쇄 소스 모델 제공자와 같은 다양한 모델 유형을 제공합니다. 현재 많은 에이전트 워크플로우가 추론을 필요로 하기 때문에 오픈소스 모델의 사용을 권장하며, 이는 많은 수의 파라미터를 가진 모델의 이점을 받습니다. 2025년 4월 기준으로 Qwen 2.5 VL은 에이전트 작업에 대해 추가로 훈련되었기 때문에 에이전트 워크플로우에 좋은 후보입니다.

## 비디오 언어 모델
요즘 대부분의 VLM은 비디오를 처리할 수 있는데, 비디오는 프레임 시퀀스로 표현될 수 있기 때문입니다. 그러나 프레임 간의 시간적 관계와 많은 양의 프레임 때문에 비디오 이해가 까다로우므로, 대표성이 있는 비디오 프레임 집합을 선택하기 위해 다양한 기법이 사용됩니다.

![](https://i.imgur.com/4LKdfx6.png)

작년부터 커뮤니티는 이 문제를 해결하기 위한 다양한 접근 방식과 트릭에 무게를 두고 있습니다.

`Meta`의 [LongVU](https://huggingface.co/collections/Vision-CAIR/longvu) 모델이 좋은 예시입니다. 이 모델은 DINOv2에 비디오 프레임을 통과시켜 가장 유사한 프레임을 선택하여 제거함으로써 비디오 프레임을 다운샘플링하고, 그런 다음 텍스트 쿼리에 따라 가장 관련성 있는 프레임을 추가로 선별하여 프레임을 더욱 정제하는데, 여기서 텍스트와 프레임 모두 동일한 공간에 투영되고 유사성이 계산됩니다. [Qwen2.5VL](https://huggingface.co/collections/Qwen/qwen25-vl)은 긴 컨텍스트를 처리할 수 있고 모델이 다른 프레임 속도의 비디오로 훈련되기 때문에 동적 FPS 속도에 적응됩니다. 확장된 멀티모달 RoPE를 통해 프레임의 절대 시간 위치를 이해하고, 서로 다른 속도를 처리할 수 있으며 실제 생활에서 발생하는 사건의 속도를 여전히 이해할 수 있습니다. 또 다른 모델인 [Gemma 3](https://huggingface.co/collections/google/gemma-3-release)은 텍스트 프롬프트에 타임스탬프가 삽입된 비디오 프레임을 수용할 수 있습니다(예: “Frame 00.00: \<image>..”). 이 모델은 비디오 이해 작업에서 매우 우수한 성능을 보입니다.

![](https://i.imgur.com/Lr0A4Vt.png)


## VLM을 위한 새로운 정렬(alignment) 기법
**선호도 최적화**는 VLM으로도 확장될 수 있는, 언어 모델을 위한 대체 미세 조정 접근법입니다. 고정된 레이블에 의존하는 대신, 이 방법은 선호도에 기반하여 후보 응답을 비교하고 순위를 매기는 데 중점을 둡니다. [trl](https://huggingface.co/docs/trl/en/index) 라이브러리는 VLM을 포함한 직접 선호도 최적화(DPO)를 지원합니다.

아래는 VLM 미세 조정의 DPO를 위한 선호도 데이터셋의 구조 예입니다. 각 항목은 이미지 + 질문 쌍과 두 개의 대응 답변(선택된 답변과 거부된 답변)으로 구성됩니다. VLM은 선호되는(선택된) 답변과 정렬된 응답을 생성하도록 미세 조정됩니다.

![](https://i.imgur.com/JniGe5G.png)

이 절차를 위한 예제 데이터셋은 [RLAIF-V](https://huggingface.co/datasets/openbmb/RLAIF-V-Dataset)로, 위에서 설명한 구조에 따라 포맷된 83000개 이상의 주석이 달린 샘플을 포함합니다. 각 항목에는 이미지 목록(보통 하나), 프롬프트, 선택된 답변, 거부된 답변이 포함되어 있으며, 이는 DPOTrainer가 예상하는 대로입니다.

이미 해당 형식으로 적절하게 포맷된 [RLAIF-V 포맷 데이터셋](https://huggingface.co/datasets/HuggingFaceH4/rlaif-v_formatted)이 있습니다. 아래는 단일 샘플의 예입니다:

```python
{'images': [<PIL.JpegImagePlugin.JpegImageFile image mode=L size=980x812 at 0x154505570>],
 'prompt': [ { "content": [ { "text": null, "type": "image" }, { "text": "What should this catcher be using?", "type": "text" } ], "role": "user" } ],
 'rejected': [ { "content": [ { "text": "The catcher, identified by the number...", "type": "text" } ], "role": "assistant" } ],
 'chosen': [ { "content": [ { "text": "The catcher in the image should be using a baseball glove...", "type": "text" } ], "role": "assistant" } ]}
```

데이터셋이 준비되면 trl 라이브러리의 DPOConfig 및 DPOTrainer 클래스를 사용하여 미세 조정 프로세스를 구성하고 시작할 수 있습니다.

아래는 DPOConfig를 사용한 예제 구성입니다:
```python
from trl import DPOConfig

training_args = DPOConfig(
    output_dir="smolvlm-instruct-trl-dpo-rlaif-v",
    bf16=True,
    gradient_checkpointing=True,
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    gradient_accumulation_steps=32,
    num_train_epochs=5,
    dataset_num_proc=8, # 토큰화는 8개 프로세스 사용
    dataloader_num_workers=8, # 데이터 로딩은 8개 워커 사용
    logging_steps=10,
    report_to="tensorboard",
    push_to_hub=True,
    save_strategy="steps",
    save_steps=10,
    save_total_limit=1,
    eval_steps=10, # 평가를 위한 단계 간격
    eval_strategy="steps",
)
```

DPOTrainer를 사용하여 모델을 훈련하기 위해 보상 차이를 계산하려면 참조 모델을 선택적으로 제공할 수도 있습니다. 파라미터 효율적 미세 조정(PEFT)을 사용하는 경우 `ref_model=None`을 설정하여 참조 모델을 생략할 수 있습니다:
```python
from trl import DPOTrainer

trainer = DPOTrainer(
    model=model,
    ref_model=None,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    peft_config=peft_config,
    tokenizer=processor
)
trainer.train()
```

## 새로운 벤치마크
벤치마크 역시 지난 1년간 크게 발전했습니다. 이전 블로그에서 우리는 VLM을 평가하기 위한 두 가지 신흥 벤치마크로 MMMU와 MMBench를 소개했습니다. 해당 분야의 빠른 진전으로 모델들이 이러한 벤치마크에서 포화되었고, 더 나은 평가 도구가 필요합니다. 이를 달성하기 위해서는 범용 벤치마크 위에 특정 기능을 평가하는 도구가 필요합니다.

![](https://i.imgur.com/YaT28j7.png)

이제 두 가지 두드러진 범용 벤치마크인 MMT-Bench와 MMMU-Pro를 소개합니다.
### MMT-Bench
MMT-Bench는 전문 지식, 정확한 시각적 인식, 지역화, 추론 및 계획이 필요한 광범위한 멀티모달 작업에 걸쳐 VLM을 평가하도록 설계되었습니다. 벤치마크는 이미지, 텍스트, 비디오 및 포인트 클라우드 모달리티의 다양한 멀티모달 시나리오에서 추출한 31325개의 객관식 시각 질문을 포함합니다. 162개의 하위 태스크가 있는 32개의 다른 메타 태스크로 OCR, 시각적 인식 또는 시각-언어 검색을 포함한 다양한 작업을 다룹니다.

### MMMU-Pro
MMMU-Pro는 원래 MMMU 벤치마크의 더 나은 버전입니다. 여러 모달리티에 걸쳐 고급 AI 모델의 진정한 이해 능력을 평가합니다.
MMMU보다 더 복잡한 구조를 가지며, 예를 들어 비전 전용 입력 설정이 있고 후보 옵션 수가 4개에서 10개로 증가했습니다. 이 벤치마크는 실제 환경 시뮬레이션을 통합하여, 시뮬레이션된 디스플레이 내에서 캡처된 스크린샷이나 사진에서 파생된 비전 전용 문제를 포함합니다. 다양한 배경, 글꼴 스타일 및 크기를 적용하여 실제 환경 조건을 모방합니다.

## 추가 : 추천 모델
주목할 만한 모델 몇 가지를 소개합니다. 선호하는 모델은 많지만, 아래는 최신 버전(2025년 5월 기준)입니다.

| 모델명                      | 파라미터                                          | 왜 추천하나요?                            |
| ------------------------ | --------------------------------------------- | ----------------------------------- |
| Qwen2.5-VL               | from 3B to 72B                                | 에이전트 기능, 수학 등 다양한 기능을 갖춘 뛰어난 다목적 모델 |
| RolmOCR                  | 7B                                            | 매우 성능이 우수한 OCR 모델                   |
| Kimi-VL-Thinking         | 16B MoE with 3B active parameters             | 가장 추론 능력이 우수한 모델                    |
| SmolVLM2                 | 256M, 500M (our favorite!), 2.2B              | 가장 작은 VLM                           |
| Llama 4 Scout & Maverick | 109B/400B MoE with 17B active parameters      | 너어어어어무 긴 컨텍스트                       |
| Molmo                    | 1B, 7B, 72B and MoE with 1B active parameters | 완전 개방형 모델에 지역화기능 추가됨                |

여기까지입니다! 아래에는 위 포스트의 각 주제에 대한 보다 심층적인 설명을 제공하는 링크입니다 :)

## 읽어볼만한 글
- [Models, datasets and more mentioned in this blog](https://huggingface.co/collections/sergiopaniego/vision-language-models-2025-update-682206d8ed0728be05dbf901)
- Multimodal Safety: [Llama Guard 4 Blog](https://huggingface.co/blog/llama-guard-4)
- DPO in VLMs: [Preference Optimization for Vision Language Models with TRL](https://huggingface.co/blog/dpo_vlm)
- Smolagents with VLM support: [We just gave sight to smolagents](https://huggingface.co/blog/smolagents-can-see)
- Agents Course section for Vision Agents using smolagents: [Vision Agents with smolagents](https://huggingface.co/learn/agents-course/unit2/smolagents/vision_agents)
- Gemma 3 Model Release: [Welcome Gemma 3: Google's all new multimodal, multilingual, long context open LLM](https://huggingface.co/blog/gemma3)
- PaliGemma 2 Model Release: [Welcome PaliGemma 2 – New vision language models by Google](https://huggingface.co/blog/paligemma2)
- [Pi0 release by Hugging Face](https://huggingface.co/blog/pi0)
- Multimodal retrieval: [Visually Multilingual: Introducing mcdse-2b](https://huggingface.co/blog/marco/announcing-mcdse-2b-v1)
- Multimodal retrieval: [ColPali: Efficient Document Retrieval with Vision Language Models](https://huggingface.co/blog/manu/colpali)
- Video Language Modelling: [SmolVLM2: Bringing Video Understanding to Every Device](https://huggingface.co/blog/smolvlm2)
- Minimal training of VLM with vanilla PyTorch: [GitHub - huggingface/nanoVLM: The simplest, fastest repository for training/finetuning small-sized VLMs.](https://github.com/huggingface/nanoVLM)
```

### real/2025-11-17-hf_translation_hub_mcp_design_and_tooling.md

```markdown
---
layout: post
title: "MCP 서버 설계 전략 및 개발 도구 선정"
author: hyeonseo
categories: [MCP]
image: assets/images/blog/posts/2025-11-17-hf_translation_hub_mcp_design_and_tooling/thumbnail.png
---
* TOC
{:toc}
<!--toc-->
> Hugging Face 번역 MCP 서버 설계 전략 및 개발 도구는 다음과 같은 **프로젝트 목표와 운영 원칙**을 중심으로 결정되었습니다.
>
> **(1) 문서 번역 자동화 및 범용성 확보**
>
> 번역 MCP 서버의 특정 문서에만 국한되지 않고 다른 오픈소스 문서에도 재사용 가능한 번역 도구를 만드는 것을 목표로 합니다. 이를 위해 기존의 단일 에이전트 기반 방식 대신 **각 기능(문서 검색, 번역, PR 등록, 리뷰)을 모듈화한 MCP 서버 아키텍처**를 도입했습니다.
>
> **(2) 필요한 기능만 구현하는 단순성 원칙 준수**
>
> 번역 문서 검색·번역·PR 생성·리뷰 자동화는 독립된 단일 작업이며, 복잡한 상호작용이나 세션 유지가 필요 없습니다. 이에 따라 MCP 서버는 **불필요한 기능을 배제하고 최소한의 통신 및 상태 관리 방식만 적용하는 단순 설계**를 채택했습니다.
>
> **(3) 빠른 배포와 반복 개발이 가능한 방식 선택**
>
> HuggingFace KREW·OSSCA 활동을 통해 매년 문서 번역이 이루지고 있기 때문에, 실제 번역 참여자들로부터 즉각적인 피드백을 받을 수 있습니다. 따라서 초기에는 **개발 속도가 빠른 Gradio 및 FastMCP 기반으로 프로토타입을 구성**하고, 추후 기능 확장 시 Python SDK로 전환하는 전략을 적용했습니다.
>
> 위와 같은 원칙에 따라 Hugging Face 블로그의 **[Building the Hugging Face MCP Server](https://huggingface.co/blog/building-hf-mcp)**(한국어 번역: **[Hugging Face 서버 구축기](https://hugging-face-krew.github.io/building-hf-mcp-ko/)**) 내용을 기반으로 전송 방식, 통신 패턴, 상태 관리, 개발 도구를 비교·검토하고 MCP 서버 설계 전략을 수립했습니다.
>
> 이 글은 HuggingFace 번역 MCP 서버를 구축하며 정립한 설계 전략과 그 과정에서 도출된 의사결정 기준을 이해하고자 하는 분들께 추천합니다.

# 1. MCP 서버 의사결정 흐름에 따른 설계 전략

## 1-1. 전송 방식 결정 (Transport Selection)

- **STDIO (Standard Input/Output)**
    - 로컬 환경에서 가장 단순하고 안정적이며 설정과 디버깅이 빠른 개발용 전송 방식

- **HTTP with SSE (Server-Sent Events)**
    - 과거 표준이었지만 단방향 스트림 특성·연결 유지 부담으로 현재는 비권장되는 방식

- **Streamable HTTP (최신 표준, 권장)**
    - 단일 엔드포인트에서 요청/응답/스트리밍을 통합 처리하고, 서버리스·OAuth 인증까지 지원하는 MCP 공식 원격 표준 방식

> 💡 **번역 서버에 대한 전송 방식 선택** : **Streamable HTTP** 전송 방식 사용
- 장기적으로는 MCP 최신 표준과의 정합성을 위해 Streamable HTTP가 가장 적합함
- 초기 개발 단계에서는 빠른 반복 개발을 위해 STDIO로 시작 후 안정화되면 Streamable HTTP로 전환하는 방향으로 접근 가능


## 1-2. 통신 패턴 결정 (Communication Pattern Selection)

- **Direct Response (직접 응답)**
    - 클라이언트 요청에 대해 즉시 JSON 결과를 반환하는 가장 기본적인 패턴
    - 구현이 간단하고 서버 부하가 낮으며, 번역 도구, 검색 엔진, 데이터 조회 서비스 등에 적합함

- **Request Scoped Streams (요청 단위 스트리밍)**
    - 단일 요청 범위 내에서 진행 상황이나 부분 결과를 실시간으로 전달함
    - LLM 출력, 대용량 문서 처리, 장시간 연산이 필요한 경우에 유용함

- **Server Push Streams (서버 푸시 스트림)**
    - 장기 연결을 유지하며 서버가 클라이언트에 능동적으로 알림을 전송함
    - 실시간 모니터링, 알림 시스템, 이벤트 기반 아키텍처에 적합하지만 연결 관리 복잡도가 높음


> 💡 **번역 서버에 대한 통신 패턴 선택** : **Direct Response** 기반 구현
- 요청 처리 시간이 짧고 상태가 독립적이므로 Direct Response가 가장 적합함
- 문서 검색은 GitHub 저장소에서 텍스트를 즉시 반환하고, 번역 서버 역시 LLM API 응답을 즉시 반환하는 구조라 스트리밍 패턴의 필요성이 낮음
- 장기 연결·진행률 스트리밍이 요구되지 않으므로 Request Scoped Streams 및 Server Push Streams는 현재 단계에서 불필요함


## 1-3. 상태 관리 결정 (State Management Strategy)

- **Stateless (무상태)**
    - 각 요청을 독립적으로 처리하며 서버 간 세션 정보를 공유하지 않음
    - 확장성이 뛰어나고 로드밸런싱이 용이하며, Redis나 세션 저장소가 불필요함

- **Stateful (상태 유지)**
    - 세션 ID를 통해 클라이언트 세션을 추적하고 상태를 유지함
    - 세션 어피니티 또는 Redis 같은 공유 저장소가 필요하며, 대화형 에이전트에 적합함


> 💡 **번역 서버에 대한 상태 관리 선택** : **Stateless** 기반 구현
- 번역 문서 검색과 번역 호출은 모두 독립적인 단일 트랜잭션으로, 요청 간 컨텍스트를 서버가 유지할 필요가 없음
- 세션 관리 인프라(세션 스토어, 어피니티 설정 등)를 추가할 필요가 없어서, 초기 구현 복잡도와 운영 부담을 모두 줄일 수 있음


## 1-4. 상호작용 기능 결정 (Interactive Features)

- **Sampling (샘플링)**
    - 여러 후보 결과를 제공하고 클라이언트가 선택하는 상호작용 패턴

- **Elicitation (추가 정보 요청)**
    - 서버가 클라이언트에게 추가 정보를 요청해 입력을 보완하는 패턴

- **Progress Notification (진행 상황 알림)**
    - 장시간 작업의 진행 상황을 실시간으로 클라이언트에 전달하는 패턴

> 💡 **번역 서버에 대한 상호작용 기능 선택** : 현재 단계에서는 **상호작용 기능 미구현 예정**
- 모두 짧은 요청–응답 흐름을 가지므로 추가 상호작용 기능이 필요하지 않음
- 상호작용은 향후 번역 파이프라인 관련 추가 기능 개발 시 선택적으로 확장하는 것이 적합함


## 2. MCP 서버 개발 도구 비교 및 선정

## 2-1. Gradio

- **특징**
    - `demo.launch(mcp_server=True)`로 MCP 서버 자동 생성
    - 함수 기반 MCP 도구 스키마 자동 구성
    - Hugging Face Spaces 무료 배포 가능

- **장단점**
    - 장점: 초기 설정이 거의 불필요하며 프로토타입 구축 용이
    - 단점: MCP 스펙의 세밀한 제어가 어렵고, 복잡한 아키텍처에 부적합

- **적합한 환경**: PoC 및 데모 단계, UX가 필요한 MCP 서비스

- **서버 구축 가이드** : [Building an MCP Server with Gradio](https://www.gradio.app/guides/building-mcp-server-with-gradio)

## 2-2. FastMCP
- **특징**
    - Python 기반의 경량 MCP 서버 프레임워크
    - 데코레이터 기반 MCP 도구 정의 용이
    - 인증·배포 도구·고급 패턴(리소스·툴·프록시) 내장

- **장단점**
    - 장점: Python SDK보다 설정이 간단하고, 인증·배포·테스트 등 프로덕션 기능을 내장하여 Gradio보다 유연함 
    - 단점: Python에만 한정되며, [대규모 환경에서는 권장되지 않음](https://www.jlowin.dev/blog/stop-converting-rest-apis-to-mcp)

- **적합한 환경**: 빠른 개발이 필요한 실험적 MCP 서버

- **서버 구축 가이드** : [FastMCP](https://gofastmcp.com/getting-started/welcome)

## 2-3. Python SDK (공식)

- **특징**
    - MCP 스펙 전 요소(도구/리소스/프롬프트/상태/세션)를 직접 제어
    - 고급 상태 관리·비동기 처리·커스텀 인증 구현 가능

- **장단점**
    - 장점: 제어권 최상위 (모든 MCP 기능 자유롭게 사용 가능) 및 높은 확장성, 커스텀 아키텍처 설계 가능
    - 단점: 초기 구조 설계와 반복적으로 사용되는 표준 코드 및 템플릿 필요, 개발 시간이 김

- **적합한 환경**: 정식 상용 서비스, 대규모 MCP 서버 클러스터

- **서버 구축 가이드** : [Build an MCP server](https://modelcontextprotocol.io/docs/develop/build-server)

## 2-4. TypeScript/Node.js SDK (공식)

- **특징**
    - MCP 서버·클라이언트 모두 TS로 구현 가능
    - 자동 타입 생성 및 ESM 기반 비동기 프로그래밍

- **장단점**
    - 장점: 서버리스 환경(Cloudflare Workers, Vercel)에서 배포가 쉬움, TypeScript의 타입 안전성
    - 단점: Python 생태계보다 MCP 관련 라이브러리와 예제가 적음, 개발 시간이 김

- **적합한 환경**: 웹 플랫폼, VSCode MCP 확장 개발, 서버리스 중심 MCP 서버

- **서버 구축 가이드** : [Build an MCP server](https://modelcontextprotocol.io/docs/develop/build-server)

## 2-5. 도구 비교

| 항목 | Gradio | FastMCP | Python SDK | TypeScript SDK |
| --- | --- | --- | --- | --- |
| **개발 속도** | 매우 빠름 | 빠름 | 느림 | 느림 |
| **학습 곡선** | 매우 낮음 | 낮음 | 높음 | 중간 |
| **유연성** | 낮음 | 중간 | 매우 높음 | 매우 높음 |
| **MCP 스펙 지원** | 부분 | 부분 | 전체 | 전체 |
| **확장성** | 제한적 | 중간 | 매우 높음 | 매우 높음 |
| **적합 단계** | 프로토타입 | 초기~중기 개발 | 프로덕션 | 프로덕션 |

- 개발 속도 → Gradio > FastMCP > TS SDK ≈ Python SDK
- 유연성/제어권 → Python SDK ≈ TS SDK > FastMCP > Gradio
- 프로덕션 적합성 → Python SDK ≈ TS SDK > FastMCP > Gradio
- 서버리스 적합성 → TS SDK 우수
- 인증/배포 편의성 → FastMCP 우수

## 2-6. 도구 선택
- **프로토타입(현재) 단계 : FastMCP 또는 Gradio**
    - 빠른 개발 + 기본 기능 검증에 최적
    - Streamable HTTP 기본 지원으로 별도 설정 불필요

**프로덕션 전환 시 (사용자 증가 시) : Python SDK**
    - Python SDK 또는 FastMCP 고급 기능 활용
    - 추가 기능·확장성·커스텀 로직 구현 용이


## 3. 설계 결정 요약

| 항목 | 선택 | 비고 |
| --- | --- | --- |
| **전송 방식** | Streamable HTTP | - |
| **통신 패턴** | Direct Response | - |
| **상태 관리** | Stateless | - |
| **상호 작용** | 미구현 | 향후 확장 가능 |
| **개발 도구** | GradioMCP | - |
| **Gateway** | 미사용 | - |

## 마무리
이번 글에서는 Hugging Face 번역 MCP 서버를 설계하면서 고려한 전송 방식, 통신 패턴, 상태 관리, 상호작용 기능, 개발 도구를 전체적으로 정리했습니다. 

특히 이번 프로젝트에서는 **필요한 기능만 구현하는 단순성의 원칙** 아래, 초기 개발 속도와 구조적 명확성을 최우선으로 삼아 의사결정을 진행했습니다. 그 결과, 프로토타입 단계에서는 Gradio MCP 기반의 빠른 구축이 가능했으며, 향후에는 Python SDK로 확장할 수 있는 기반도 확보하게 되었습니다.

본 글이 MCP 기반 도구를 설계하거나 번역 자동화 파이프라인을 구축하려는 분들께 하나의 참고 자료가 되기를 바랍니다.
```

### real/2025-12-01-rteb.md

```markdown
---
layout: post
title: "RTEB: 검색 평가의 새로운 표준"
author: sohyun
categories: [Retrieval, Embedding, Benchmark]
image: assets/images/blog/posts/2025-12-01-rteb/thumbnail.png

---
* TOC
{:toc}
<!--toc-->
_이 글은 Hugging Face 블로그의 [Introducing RTEB: A New Standard for Retrieval Evaluation](https://huggingface.co/blog/rteb)를 한국어로 번역한 글입니다._

---
# RTEB: 검색 평가의 새로운 표준

**요약 –** 여러분께 새로운 벤치마크, [RTEB(Retrieval Embedding Benchmark, 검색 임베딩 벤치마크)](https://huggingface.co/spaces/mteb/leaderboard?benchmark_name=RTEB%28beta%29)의 베타 버전을 소개합니다. RTEB는 실제 환경에 사용할 임베딩 모델의 검색 정확도를 신뢰성 있게 평가하도록 설계되었습니다. 기존 벤치마크는 진정한 일반화 능력을 측정하기 어려웠으나, RTEB는 공개 및 비공개 데이터셋을 결합한 하이브리드 전략으로 이 문제를 해결합니다. 목표는 간단합니다. 모델이 이전에 접하지 않은 데이터에서 어떻게 수행하는지 측정하기 위한, 공정하고 투명하며 응용 중심의 표준을 만드는 것입니다.

RAG, 에이전트부터 추천 시스템에 이르기까지 많은 AI 애플리케이션의 성능은 근본적으로 검색 및 검색 품질에 의해 제한됩니다. 따라서 임베딩 모델의 검색 품질을 정확히 측정하는 것은 개발자들에게 공통적인 고민거리입니다. 모델이 실제 환경에서 얼마나 잘 작동할지 어떻게 *정확히* 검증할 수 있을까요?

여기서 문제가 복잡해집니다. 현재 평가 기준은 공개 벤치마크에서의 모델 ‘제로샷’ 성능에 의존하는 경우가 많습니다. 그러나 이는 기껏해야 모델의 진정한 일반화 능력을 가늠한 것에 불과합니다. 동일한 공개 데이터셋으로 모델을 반복 평가할 때, 보고된 점수와 새로운 미검증 데이터에서의 실제 성능 사이에 차이가 발생합니다.

<figure class="image text-center" id="figure1">
  <img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/blog/rteb/rteb-public-vs-closed.png">
  <figcaption>공개 데이터셋과 비공개 데이터셋 간 성능 차이</figcaption>
</figure>

이러한 문제를 해결하기 위해, 검색 모델 평가에 신뢰할 수 있는 기준을 제공하기 위해 설계된 벤치마크인 RTEB를 개발했습니다.

## 기존 벤치마크가 부족한 이유

기본 평가 방법론과 지표(예: NDCG@10)는 잘 알려져 있고 견고하지만, 기존 벤치마크의 신뢰성은 종종 다음과 같은 문제로 인해 저하됩니다.

**일반화 격차**. 현재 벤치마크 생태계는 의도치 않게 “시험에 맞춘 교육”을 조장합니다. 훈련 데이터 소스와 평가 데이터셋이 중복될 경우 모델 점수가 부풀려져 벤치마크의 신뢰성을 훼손할 수 있습니다. 이러한 관행은 의도적이든 아니든 여러 모델의 훈련 데이터셋에서 명백히 관찰됩니다. 이는 모델이 견고하고 일반화 가능한 능력을 개발하기보다 테스트 데이터를 암기하는 데 보상을 받는 피드백 루프를 생성합니다.

이러한 이유로, 제로샷 점수가 낮은 모델<a href="#footnote-1">[1]</a>이 새로운 문제에 대한 일반화 능력 없이도 벤치마크에서 매우 우수한 성능을 보일 수 있습니다. 따라서 벤치마크 성능은 다소 낮지만 제로샷 점수가 높은 모델이 권장되고는 합니다.

<figure class="image text-center" id="figure2">
  <img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/blog/rteb/mteb-zero-shot-models.png">
  <figcaption>출처: <a href="https://arxiv.org/abs/2506.21182">Chung et al. (2025)</a></figcaption>
</figure>

**현재 AI 애플리케이션과의 부적합성**. 많은 벤치마크는 개발자들이 현재 구축 중인 기업용 사용 사례에 부적합합니다. 이들은 종종 학술 데이터셋이나 QA 데이터셋에서 파생된 검색 작업에 의존하는데, 이는 그 자체로 유용하지만 검색 평가를 위해 설계된 것이 아니며 실제 검색 시나리오에서 발생하는 분포적 편향과 복잡성을 포착하지 못할 수 있습니다. 이러한 문제가 없는 벤치마크는 코드 검색과 같은 단일 도메인에 집중하는 등 범위가 너무 좁아 범용 모델 평가에 부적합한 경우가 많습니다.

## RTEB 소개

**검색 임베딩 벤치마크(RTEB)**를 여러분께 소개합니다. 이 벤치마크의 목표는 임베딩 모델의 진정한 검색 정확도를 측정하는 새롭고 신뢰할 수 있는 고품질 벤치마크를 만드는 것입니다.

### 진정한 일반화를 위한 하이브리드 전략

벤치마크 과적합 문제를 해결하기 위해 RTEB는 공개 데이터셋과 비공개 데이터셋을 모두 활용하는 하이브리드 전략을 사용했습니다.

* **공개 데이터셋:** 코퍼스, 쿼리, 관련성 라벨이 완전히 공개됩니다. 이는 투명성을 보장하며 모든 사용자가 결과를 재현할 수 있게 합니다.
* **비공개 데이터셋:** 이 데이터셋들은 비공개로 유지되며, 평가 과정은 공정성을 보장하기 위해 MTEB 관리자들이 수행합니다. 이러한 구성은 모델이 미지 데이터에 대한 일반화 능력을 명확하고 편향 없이 측정할 수 있게 합니다. 투명성을 위해 각 비공개 데이터셋에 대해 기술 통계, 데이터셋 설명, 그리고 `(쿼리, 문서, 관련성)` 예시 샘플을 제공합니다.

이러한 하이브리드 접근 방식은 광범위하고 견고한 일반화 능력을 갖춘 모델 개발을 장려합니다. 공개 데이터셋과 비공개 데이터셋 간 성능 차이가 현저한 모델은 과적합을 시사하며, 이는 커뮤니티에 명확한 신호를 제공합니다. 일부 모델은 이미 RTEB의 비공개 데이터셋에서 성능이 현저히 저하되는 모습을 보이고 있습니다.

### 실제 도메인을 위해 설계됨

RTEB는 기업 사용 사례에 특히 중점을 두고 설계되었습니다. 복잡한 계층 구조 대신 명확성을 위해 단순한 그룹을 사용합니다. 단일 데이터셋은 여러 그룹에 속할 수 있습니다(예: 독일 법률 데이터셋은 “법률” 그룹과 “독일어” 그룹 모두에 존재).

* **다국어 지원:** 벤치마크 데이터셋은 영어, 일본어와 같은 일반적인 언어부터 벵골어, 핀란드어와 같은 희귀 언어까지 총 20개 언어를 포괄합니다.
* **도메인 특화:** 벤치마크에는 법률, 의료, 코드, 금융과 같은 핵심 기업 도메인의 데이터셋이 포함됩니다.
* **효율적인 데이터셋 규모:** 데이터셋은 의미 있는 규모(최소 1,000개 문서 및 50개 쿼리)이면서도 평가에 지나치게 많은 시간과 비용이 소요되지 않도록 설계되었습니다.
* **검색 결과 우선 평가 지표:** 기본 리더보드 지표는 순위 지정 검색 결과 품질의 표준 측정값인 **NDCG@10**입니다.

전체 데이터셋 목록은 아래에서 확인할 수 있습니다. 공개 및 비공개 부분 모두 다양한 범주의 데이터셋으로 지속적으로 업데이트할 계획이며, 커뮤니티의 적극적인 참여를 권장합니다. 다른 데이터셋을 제안하고 싶으시면 [GitHub의 MTEB 저장소](https://github.com/embeddings-benchmark/mteb/issues)에 이슈를 생성해 주십시오.


<details>
  <summary>RTEB 데이터셋</summary>

#### Open

| 데이터셋 | 데이터셋 그룹 | 공개/비공개 | 데이터셋 URL | QA 재활용 여부 | 포함 사유 및 설명 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| AILACasedocs | 영어, 법률 | 공개 | https://huggingface.co/datasets/mteb/AILA_casedocs | X | 이 데이터셋은 인도 대법원 사건 문서 약 3,000건으로 구성되며, 주어진 법적 상황에 대한 관련 선례 검색을 평가하기 위해 설계되었습니다. 각기 특정 시나리오를 설명하는 50개의 쿼리가 포함되어 있습니다. 문서가 상당히 까다롭고, 합성되지 않은 쿼리와 고품질 레이블을 갖추었기 때문에 이 데이터셋을 벤치마크에 포함합니다. |
| AILAStatutes | 영어, 법률 | 공개 | https://huggingface.co/datasets/mteb/AILA_statutes | X | 이 데이터셋은 인도 대법원 법률 197건에 대한 설명으로 구성되어 있으며, 주어진 법적 상황에 대한 관련 선례 법률 검색을 용이하게 하기 위해 설계되었습니다. 각기 특정 시나리오를 설명하는 50개의 쿼리를 포함합니다. 문서가 상당히 까다롭고, 합성되지 않은 쿼리와 고품질 레이블을 갖추었기 때문에 이 데이터셋을 벤치마크에 포함합니다. |
| LegalSummarization | 영어, 법률 | 공개 | https://huggingface.co/datasets/mteb/legal_summarization | X | 이 데이터셋은 법률 문서 해설을 전문으로 하는 신뢰할 수 있는 웹사이트에서 수집한 법률 텍스트 발췌문과 해당 평이한 영어 요약문 446쌍으로 구성됩니다. 요약문은 품질을 위해 수동으로 검토되어 데이터가 깨끗하고 법률 검색 평가에 적합함을 보장합니다. |
| LegalQuAD | 독일어, 법률 | 공개 | https://huggingface.co/datasets/mteb/LegalQuAD | X | 이 코퍼스는 200개의 실제 법률 문서로 구성되며, 쿼리 세트는 법률 문서와 관련된 200개의 질문으로 이루어져 있습니다. |
| FinanceBench | 영어, 금융 | 공개 | https://huggingface.co/datasets/virattt/financebench | O | FinanceBench 데이터셋은 PatronusAI/financebench-test 데이터셋에서 파생되었으며, 금융 분야 질문응답 작업을 위해 정제된 형식으로 처리된 PASS 예제만 포함합니다. FinanceBench-rtl은 검색 작업에 재활용되었습니다. |
| HC3Finance | 영어, 금융 | 공개 | https://huggingface.co/datasets/Hello-SimpleAI/HC3 | X | HC3 데이터셋은 오픈 도메인, 금융, 의료, 법률, 심리학 등 다양한 분야의 인간 전문가와 ChatGPT의 비교 응답 수만 건으로 구성됩니다. 데이터 수집 과정에는 공개된 질문응답 데이터셋과 위키 텍스트를 활용했으며, 인간 답변이 전문가 제공 또는 고품질 사용자 응답임을 확인하여 오분류를 최소화하고 데이터셋 신뢰성을 높였습니다. |
| FinQA | 영어, 금융 | 공개 | https://huggingface.co/datasets/ibm/finqa | O | FinQA는 구조화 및 비구조화 증거를 활용한 수치 추론 연구를 위한 8천 개의 질문-답변 쌍과 2,800개의 재무 보고서로 구성된 대규모 데이터셋입니다. |
| HumanEval | 코드 | 공개 | https://huggingface.co/datasets/openai/openai_humaneval | O | OpenAI에서 공개한 HumanEval 데이터셋은 각 문제마다 손으로 작성된 함수 시그니처, 문서 문자열, 본체 및 여러 유닛 테스트를 포함한 164개의 프로그래밍 문제를 포함합니다. 이 데이터셋은 OpenAI의 엔지니어와 연구원들이 수작업으로 제작했습니다. |
| MBPP | 코드 | 공개 | https://huggingface.co/datasets/google-research-datasets/mbpp | O | MBPP 데이터셋은 초급 프로그래머가 해결할 수 있도록 설계된 약 1,000개의 크라우드소싱 파이썬 프로그래밍 문제로 구성되어 있으며, 프로그래밍 기초, 표준 라이브러리 기능 등을 다룹니다. 각 문제는 작업 설명, 코드 솔루션 및 3개의 자동화된 테스트 케이스로 구성됩니다. 논문에서 설명한 바와 같이, 데이터 품질 보장을 위해 데이터셋 작성자가 데이터의 일부를 수동으로 검증했습니다. |
| MIRACLHardNegatives | | 공개 | https://huggingface.co/datasets/mteb/miracl-hard-negatives | X | MIRACL(Multilingual Information Retrieval Across a Continuum of Languages)은 18개 언어를 아우르는 검색에 초점을 맞춘 다국어 검색 데이터셋입니다. 하드 네거티브 버전은 BM25, e5-multilingual-large 및 e5-mistral-instruct에서 쿼리당 상위 250개 문서를 모아 생성되었습니다. |
| APPS | 코드, 영어 | 공개 | https://huggingface.co/datasets/codeparrot/apps | O | APPS는 10,000개의 문제를 포함한 코드 생성 벤치마크입니다. 이 벤치마크는 자연어 사양으로부터 코드를 생성하는 언어 모델의 능력을 평가하는 데 사용될 수 있습니다. 저자들은 Codewars, AtCoder, Kattis, Codeforces 등 프로그래머들이 서로 문제를 공유하는 오픈 액세스 사이트에서 문제를 수동으로 선별하여 데이터셋을 생성했습니다. |
| DS1000 | 코드, 영어 | 공개 | https://huggingface.co/datasets/xlangai/DS-1000 | O | DS-1000은 NumPy, Pandas 등 7개 Python 라이브러리를 아우르는 1,000개의 데이터 사이언스 문제로 구성된 코드 생성 벤치마크입니다. 기능적 정확성과 표면형 제약 조건을 포함한 다중 기준 평가 지표를 활용하여, Codex-002 예측 중 오답률이 1.8%에 불과한 고품질 데이터셋을 생성합니다. |
| WikiSQL | 코드, 영어 | 공개 | https://huggingface.co/datasets/Salesforce/wikisql | O | WikiSQL은 위키백과의 24,241개 테이블에 걸쳐 수작업으로 주석 처리된 80,654개의 자연어 질문과 해당 SQL 쿼리로 구성된 데이터셋입니다. |
| ChatDoctor_HealthCareMagic | 영어, 의료 | 공개 | https://huggingface.co/datasets/lavita/ChatDoctor-HealthCareMagic-100k | X | ChatDoctor-HealthCareMagic-100k 데이터셋은 112,000개의 실제 의료 질문-답변 쌍으로 구성되어 있으며, 방대하고 다양한 실제 의료 대화 모음을 제공합니다. 많은 질문과 답변에 문법적 불일치가 존재하여 이 데이터셋에는 약간의 위험이 있지만, 이는 잠재적으로 강력한 의료 검색 모델과 취약한 모델을 구분하는 데 도움이 될 수 있습니다. |
| HC3 Medicine | 영어, 의료 | 공개 | https://huggingface.co/datasets/Hello-SimpleAI/HC3 | X | HC3 데이터셋은 오픈 도메인, 금융, 의료, 법률, 심리학 등 다양한 분야의 인간 전문가와 ChatGPT의 비교 응답 수만 건으로 구성됩니다. 데이터 수집 과정에는 공개된 질문-답변 데이터셋과 위키 텍스트를 활용했으며, 인간 답변이 전문가 제공 또는 고품질 사용자 응답임을 보장하여 오분류를 최소화하고 데이터셋의 신뢰성을 높였습니다. |
| HC3 French OOD | 프랑스어, 의료 | 공개 | https://huggingface.co/datasets/almanach/hc3_french_ood | X | HC3 데이터셋은 오픈 도메인, 금융, 의료, 법률, 심리학 등 다양한 분야에서 인간 전문가와 ChatGPT의 비교 응답 수만 건으로 구성됩니다. 데이터 수집 과정에는 공개된 질문-답변 데이터셋과 위키 텍스트를 활용하는 것이 포함되었으며, 인간 답변이 전문가 제공 또는 고품질 사용자 응답임을 보장함으로써 오표기를 최소화하고 데이터셋의 신뢰성을 높였습니다. |
| JaQuAD | 일본어 | 공개 | https://huggingface.co/datasets/SkelterLabsInc/JaQuAD | O | JaQuAD 데이터셋은 일본어 위키백과 문서를 기반으로 인간이 주석 처리한 39,696개의 질문-답변 쌍으로 구성되며, 문맥의 88.7%는 선별된 고품질 문서에서 추출되었습니다. |
| Cure | 영어, 의료 | 공개 | https://huggingface.co/datasets/clinia/CUREv1 | X | |
| TripClick | 영어, 의료 | 공개 | https://huggingface.co/datasets/irds/tripclick | X | |
| FreshStack | 영어 | 공개 | https://huggingface.co/papers/2504.13128 | X | |

#### 비공개

| 데이터셋 | 데이터셋 그룹 | 공개/비공개 | 데이터셋 URL | 코멘트 | QA 재활용 여부 | 포함 사유 및 설명 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| _GermanLegal1 | 독일어, 법률 | 비공개 | | O | | 본 데이터셋은 실제 사법 판결에서 추출되었으며, 법적 인용문 일치와 BM25 유사도 측정을 병행합니다. BM25 기준선은 인용문 일치 외 영역에서 데이터 편향을 유발할 수 있어 약간의 위험이 존재합니다. 정확성과 품질 보장을 위해 데이터셋의 일부를 수동으로 검증했습니다. |
| _JapaneseLegal1 | 일본어, 법률 | 비공개 | | X | | 본 데이터셋은 일본 정부 공식 웹사이트 e-Gov에서 추출한 중복 제거된 법률 기록 8,750건으로 구성되어 권위적이고 정확한 내용을 보장합니다. 기록 제목은 쿼리로, 기록 본문은 문서로 사용됩니다. |
| _FrenchLegal1 | 프랑스어, 법률 | 비공개 | | X | | 이 데이터셋은 프랑스 법원 \“Conseil d'Etat\”의 판례로 구성되며, OPENDATA/JADE 저장소에서 체계적으로 추출되었으며, 세금 관련 사건에 중점을 둡니다. 쿼리는 각 문서의 제목으로, 레이블이 깨끗함을 보장합니다. |
| _EnglishFinance1 | 영어, 금융 | 비공개 | | O | | 본 검색 데이터셋은 표 형식 및 텍스트 콘텐츠를 활용한 대규모 QA 데이터셋인 TAT-QA에서 검색을 위해 재구성되었습니다. |
| _EnglishFinance4 | 영어, 금융 | 비공개 | | X | | 본 데이터셋은 스탠퍼드 대학의 Alpaca와 FiQA를 GPT3.5로 생성한 1,300개의 커스텀 데이터 쌍과 결합한 후, 데이터 품질을 보장하기 위해 추가 정제 과정을 거쳤습니다. |
| _EnglishFinance2 | 영어, 금융 | 비공개 | | O | | 본 데이터셋은 시뮬레이션된 대화 흐름을 기반으로 각 대화 턴별 질문으로 구성된 금융 분야 데이터셋입니다. 전문 어노테이터에 의한 큐레이션으로 상당히 높은 데이터 품질을 보장합니다. 질문은 검색어(쿼리)로, 대화 블록은 검색용 문서로 재활용됩니다. |
| _EnglishFinance3 | 영어, 금융 | 비공개 | | O | | 본 데이터셋은 개인 금융의 다양한 측면을 다루기 위해 선별된 질문-답변 쌍 모음입니다. |
| _Code1 | 코드 | 비공개 | | 아니오 | | GitHub 저장소에서 함수를 추출했습니다. 구문 분석을 통해 함수에서 문서 문자열(docstring)과 함수 시그니처를 얻었습니다. 문서 문자열이 있는 함수만 유지됩니다. 문서 문자열은 쿼리로 사용되며, 작업 난이도를 높이기 위해 함수 시그니처(함수명 및 인수명 포함)는 제거됩니다. 각 언어는 별도의 코퍼스를 가진 하위 집합입니다. |
| _JapaneseCode1 | 코드, 일본어 | 비공개 | | X | | CoNaLa 챌린지의 일본어 질문 하위 집합입니다. |
| _EnglishHealthcare1 | 영어, 의료 | 비공개 | | O | | 본 데이터셋은 생의학 분야에서 최소 석사 학위를 보유한 15명의 전문가가 주석을 달은 2,019개의 질문-답변 쌍으로 구성됩니다. 의사가 주관을 맡은 주석 팀이 각 질문-답변 쌍을 검증하여 데이터 품질을 보장했습니다. |
| _GermanHealthcare1 | 독일어, 의료 | 비공개 | | X | | 이 데이터셋은 환자와 의료 보조원 간의 독일어 의료 대화 465건으로 구성되며, 각 항목에는 상세한 환자 설명과 이에 대응하는 전문가 답변이 포함됩니다. 데이터 정확성과 품질 보증을 위해 데이터셋의 일부를 수동으로 검증했습니다. |
| _German1 | 독일어 | 비공개 | | X | | 본 데이터셋은 여러 공개 코퍼스를 통합된 형식으로 정리 및 전처리하여 생성된 대화 요약 데이터셋입니다. 각 대화는 주석 담당자가 수동으로 요약하고 주제별로 라벨링하여 고품질의 깨끗한 데이터를 보장합니다. 대화 요약본은 쿼리로, 전체 대화는 문서로 사용됩니다. |
| _French1 | 프랑스어 | 비공개 | | O | | 본 데이터셋은 4118개 이상의 프랑스어 퀴즈 질문-답변 쌍으로 구성되며, 각 항목에는 관련 위키백과 컨텍스트가 포함됩니다. 데이터 정확성과 품질을 위해 데이터셋의 일부를 수동으로 검증했습니다. |

</details>

## RTEB 출시: 커뮤니티의 노력

RTEB가 오늘 베타 버전으로 출시됩니다. 우리는 커뮤니티의 노력으로 견고한 벤치마크를 구축할 수 있다고 믿고, 개발자와 연구자 모두의 피드백을 바탕으로 RTEB를 발전시켜 나갈 계획입니다. 여러분의 의견을 공유하고, 새로운 데이터셋을 제안하며, 기존 데이터셋의 문제를 발견함으로써, 모두가 더 신뢰할 수 있는 표준을 구축하는 데 도움을 주시길 권합니다. [Github의 MTEB 저장소](https://github.com/embeddings-benchmark/mteb)에서 토론에 참여하거나 이슈를 생성하여 참여하실 수 있습니다.

## 한계점과 향후 계획

개선이 필요한 부분을 명확히 하기 위해 RTEB의 현재 한계점과 향후 계획을 투명하게 공개합니다.

* **벤치마크 범위:** RTEB는 현실적이고 검색 중심의 사용 사례에 초점을 맞춥니다. 매우 까다로운 합성 데이터셋은 현재 목표는 아니지만 향후 추가될 수 있습니다.
* **모달리티:** 벤치마크는 현재 텍스트 전용 검색을 평가합니다. 향후 릴리스에서는 텍스트-이미지 및 기타 다중 모달 검색 작업을 포함할 계획입니다.
* **언어 지원 범위:** 중국어, 아랍어와 같은 주요 언어는 물론, 저자원 언어(low-resource language, 희소 언어를 의미)까지 지원 범위를 넓히기 위해 적극적으로 추진 중입니다. 해당 기준에 부합하는 고품질 데이터셋을 알고 계시다면 알려주시기 바랍니다.
* **질의응답(QA) 데이터셋 재활용:** 현재 검색 데이터셋의 약 50%는 QA 데이터셋을 재활용한 것으로, 질문과 문맥 간 어휘 중복이 심해 키워드 매칭에 의존하는 모델이 진정한 의미 이해를 하는 모델보다 유리해지는 등의 문제가 발생할 수 있습니다.
* **비공개 데이터셋:** 일반화 능력 테스트를 위해 MTEB 관리자만 접근 가능한 비공개 데이터셋을 활용합니다. 공정성 유지를 위해 모든 관리자는 해당 데이터셋으로 훈련된 모델을 공개하지 않으며, 공개 채널을 통한 테스트만 수행하기로 약속하여 특정 기업이나 개인이 부당한 이점을 얻지 않도록 합니다.

우리의 목표는 RTEB가 검색 평가 분야의 커뮤니티 신뢰 기준이 되는 것입니다.

RTEB 리더보드는 오늘 [Hugging Face](https://huggingface.co/spaces/mteb/leaderboard?benchmark_name=RTEB%28beta%29)에서 MTEB 리더보드의 새로운 검색(Retrieval) 섹션의 일부로 이용 가능합니다. 리더보드에서 여러분의 모델을 평가해보세요. 그리고 AI 커뮤니티 전체를 위한 더 나은 신뢰할 수 있는 벤치마크 구축에 함께해 주시길 바랍니다.

---

<span id="footnote-1">[1] 제로샷 점수는 모델 제공자가 명시적으로 훈련에 사용했다고 밝힌 평가 세트의 비율을 의미합니다. 이는 일반적으로 훈련 분량만 포함합니다.</span>
```

### real/2025-12-15-ai-agents-are-here.md

```markdown
---
layout: post
title: "AI Agents의 도래: 그래서, 이제는?"
author: jeong
categories: [Agents, Ethic]
image: assets/images/blog/posts/2025-12-15-ai-agents-are-here/thumbnail.png

---
* TOC
{:toc}
<!--toc-->
_이 글은 2025년 1월에 업로드된 Hugging Face 블로그의 [AI Agents Are Here. What Now?](https://huggingface.co/blog/ethics-soc-7)를 한국어로 번역한 글입니다._
---
# **서론**

최근 대규모 언어 모델(LLM)이 유창하게 문장을 생성하고, 각종 벤치마크에서 매우 높은 성능을 기록하는 등 능력이 급격히 발전하면서, AI 개발자와 기업들은 다음 단계가 무엇인지, 곧 등장할 혁신적인 기술이 무엇인지 주목하기 시작했다. 그중 최근 빠르게 부상한 기술이 바로 **“AI 에이전트(AI agents)”**이다. 이 개념은, 사용자의 목표에 맞춰 행동을 수행하는 시스템으로, 오늘날 대부분의 AI 에이전트는 하나의 기능만 수행하는 것이 아니라, 여러 기능을 수행할 수 있도록 LLM을 통합하여 만들어진다. 이 새로운 기술 흐름의 핵심적인 아이디어는 컴퓨터 프로그램이 더 이상 인간이 직접 조작하는 특수 목적 도구에 머무르지 않고, **인간의 개입 없이 여러 작업을 수행**한다는 점이다.

이 변화는 비결정적인 환경에서 **스스로 계획을 짤 수 있는 시스템**으로의 근본적인 전환을 의미한다. 많은 현대 AI 에이전트는 단순히 사전에 정의된 행동만 수행하는 것이 아니라, **새로운 상황을 분석하고, 관련 목표를 설정하며, 기존에 정의되지 않았던 행동까지 수행할 수 있도록 설계**되어 있다.

이 글에서는 AI 에이전트가 무엇인지 간략히 소개하고, 그 속에 존재하는 **윤리적 가치와 트레이드오프(이익과 위험의 균형)**를 설명한다. 그 후 AI 에이전트가 사회에 최대한 이롭게 작동할 수 있는 미래를 만들기 위한 방향을 제시한다. 기술적 관점에서의 에이전트 소개는 [최근 작성된 개발자 블로그 포스트](https://huggingface.co/blog/smolagents)를 참고할 수 있다. 현대 생성형 AI 이전에 작성되었지만, 여전히 유효한 에이전트 개념의 기초는 [Wooldridge and Jennings, 1995](https://core.ac.uk/download/pdf/1498750.pdf)를 참고하길 바란다.

AI 에이전트에 대한 분석의 결과, **시스템의 자율성이 높아질수록 인간에게 가해질 위험도 증가**한다는 점을 발견했다. 즉, **사용자가 시스템에 넘기는 통제력이 커질수록 위험도 함께 증가**한다. 특히 문제되는 지점은, 개발자가 시스템의 모든 행동을 예측할 필요가 없게 되는 것과 같이, **AI 에이전트 개발을 촉진하는 이점들이, 동시에 안전을 위협하는 위험을 만들어낸다는 점**이다. 안전 관련 피해는 사생활 침해와 보안 문제 등 다른 유형의 피해로 이어질 수 있으며, 안전하지 않은 시스템에 대한 부적절한 신뢰는 이러한 피해를 눈덩이처럼 확대시킬 수 있다.

따라서 저자는 **완전 자율형 AI 에이전트는 개발해서는 안 된다**고 권고한다. 예를 들어, 개발자가 통제하는 제한된 코드 실행 범위를 넘어, **에이전트가 스스로 코드를 생성하고 실행**할 수 있게 되면 인간의 모든 통제를 무력화할 수 있는 능력을 갖추게 된다. 반면, **반(半)자율형 AI 에이전트**는 자율성의 정도, 수행 가능한 작업의 성격, 그리고 사용자가 행사할 수 있는 통제력에 따라 위험보다 이익이 더 클 수도 있다. 이제 이러한 주제를 심도 있게 살펴본다.

# AI 에이전트란 무엇인가?
## 개요

“AI 에이전트”가 무엇인지에 대해서는 아직 명확한 합의가 없지만, 최근 등장한 AI 에이전트들에 공통적으로 나타나는 특징은 **‘에이전트적(agentic)’**이라는 것, 즉 일정 수준의 **자율성**을 가지고 행동한다는 것이다. 목표가 주어지면, 이를 여러 하위 과제로 분해하고 각 과제를 인간의 직접적인 개입 없이 수행할 수 있다.

예를 들어, 이상적인 AI 에이전트는 “내 블로그 글을 더 잘 쓰도록 도와줘”와 같은 고수준의 요청을 받았을 때, 이전에 작성한 블로그 주제와 유사한 글을 웹에서 찾아보고 새로운 블로그 글을 위한 개요(outline)를 담은 문서를 생성하며 각 글에 대한 초안 문장을 제공하는 일까지 스스로 과제를 나누어 수행할 수 있다.

최근 AI 에이전트에 관한 연구는 과거보다 훨씬 넓은 기능 범위와 높은 활용 유연성을 가진 소프트웨어를 가능하게 했다. 실제로 최근 시스템들은 회의 일정 조율([예시1](https://www.lindy.ai/template-categories/meetings), [예시2](https://zapier.com/agents/templates/meeting-prep-assistant), [예시3](https://www.ninjatech.ai/product/ai-scheduling-agent), [예시4](https://attri.ai/ai-agents/scheduling-agent))부터, 개인화된 소셜미디어 게시글 생성([예시](https://www.hubspot.com/products/marketing/social-media-ai-agent))에 이르기까지 다양한 용도로 배포되고 있으며, 이 과정에서 “어떻게 하라”는 구체적인 절차 지시 없이도 작업을 수행한다.

우리가 이 뉴스레터를 위해 살펴본 최근의 AI 에이전트들은 모두 머신러닝 모델을 기반으로 하고 있으며, 특히 대부분은 **대규모 언어 모델(LLM)**을 사용해 행동을 결정한다. 이는 컴퓨터 소프트웨어에서 비교적 새롭고 혁신적인 접근 방식이다. 머신러닝을 기반으로 한다는 점 외에도, 오늘날의 AI 에이전트들은 과거의 에이전트 개념과 여러 면에서 유사하며, 경우에 따라서는 [에이전트가 어떠해야 하는지에 대해 이전에 이론적으로 제시되었던 아이디어들](https://core.ac.uk/download/pdf/1498750.pdf)을 실제로 구현하고 있다. 즉, 자율적으로 행동하고 사회적 능력을 보이며, 반응적 행동과 주도적 행동을 적절히 조화한 특징을 가진다.

이러한 특성들은 연속적인 정도 차이를 가진다. AI 에이전트마다 역량 수준은 서로 다르며, 단독으로 작동할 수도 있고 여러 에이전트가 협력하여 하나의 목표를 달성할 수도 있다. 따라서 AI 에이전트는 더 많거나 적은 수준의 자율성(혹은 에이전트성)을 가진다고 말할 수 있으며, 무엇이 에이전트인가에 대한 판단 역시 바이너리한(0/1) 개념이 아닌, **연속적인 스펙트럼** 위에 놓여 있다고 볼 수 있다.

이처럼 유동적인 AI 에이전트 개념은 *AI 에이전트가 무엇인지*에 대한 혼란과 오해를 낳기도 했다. 이 글에서는 이러한 혼란을 조금이나마 정리하고자, AI 에이전트의 '에이전트적(Agentic)' 단계를 정리했다.

---

| 에이전트적 단계 (Agentic Level) | 설명                                 | 누가 제어하는가                                                              | 명칭                                  | 예시 코드                                              |
| ------------------------ | ---------------------------------- | --------------------------------------------------------------------- | ----------------------------------- | -------------------------------------------------- |
| ☆☆☆☆                     | 모델이 프로그램 흐름에 전혀 영향을 주지 않음          | 👤 개발자가 시스템이 수행할 수 있는 모든 기능과 실행 시점을 전적으로 제어함                          | 단순 처리기 (Simple processor)           | `print_llm_output(llm_response)`                   |
| ★☆☆☆                     | 모델이 기본적인 제어 흐름을 결정함                | 👤 개발자가 시스템이 수행할 수 있는 모든 기능을 제어하고, 시스템은 각 기능을 언제 실행할지 결정함             | 라우터 (Router)                        | `if llm_decision(): path_a() else: path_b()`       |
| ★★☆☆                     | 모델이 함수가 **어떻게 실행될지**를 결정함          | 👤💻 개발자가 시스템이 수행할 수 있는 모든 기능과 실행 시점을 정의하고, 시스템은 실행 방식(방법)을 제어함       | 도구 호출 (Tool call)                   | `run_function(llm_chosen_tool, llm_chosen_args)`   |
| ★★★☆                     | 모델이 반복(iteration)과 프로그램 지속 여부를 제어함 | 💻👤 개발자가 시스템이 수행할 수 있는 고수준 기능을 정의하고, 시스템은 무엇을 할지, 언제 할지, 어떻게 할지를 제어함 | 다단계 에이전트 (Multi-step agent)         | `while llm_should_continue(): execute_next_step()` |
| ★★★★                     | 모델이 새로운 코드를 작성하고 실행함               | 💻 개발자가 시스템이 수행할 수 있는 고수준 기능만 정의하고, 시스템이 가능한 모든 기능과 실행 시점을 전적으로 제어함   | 완전 자율 에이전트 (Fully autonomous agent) | `create_and_run_code(user_request)`                |

---
표 1. 대규모 언어 모델(LLM)과 같은 머신러닝 모델을 사용하는 시스템이 **얼마나 에이전트적인지(agentic)**에 따라 달라질 수 있음을 보여주는 하나의 예시이다. 이러한 시스템들은 또한 “다중 에이전트 시스템(multiagent systems)”으로 결합될 수 있는데, 한 에이전트의 워크플로가 다른 에이전트를 트리거하거나, 여러 에이전트가 공동으로 하나의 목표를 향해 협력할 수도 있다.
본 표는 [smolagent 블로그 게시글](https://huggingface.co/blog/smolagents)을 바탕으로 하되, 이 글의 맥락에 맞게 일부 수정하여 구성되었다.
윤리적 관점에서 보면, 자율성의 연속체를 사람으로부터 기계로 통제가 얼마나 이전되는가라는 관점에서 이해하는 것도 중요하다. 시스템이 더 자율적일수록, 우리는 그만큼 더 많은 인간의 통제권을 기계에 넘기게 된다.
이 글 전반에 걸쳐 AI 에이전트를 설명하는 데 널리 사용되고 있는 표현 방식에 맞추어, 다소 의인화된 용어를 사용한다. 그러나 [과거의 연구에서도 지적되었듯이](https://core.ac.uk/download/pdf/1498750.pdf), 지식·신념·의도와 같이 원래 인간에게 적용되는 정신 상태적 언어(mentalistic language)로 AI 에이전트를 설명하는 것은, 사용자가 시스템의 실제 능력을 올바르게 이해하는 데 문제를 줄 수 있다. 좋든 나쁘든, 이러한 언어는 기술의 보다 정확한 세부 사항을 간략화하여 덮어주는 추상화 도구로 기능한다.
이 점을 이해하는 것은 이러한 시스템이 무엇인지, 사람들의 삶 속에서 어떤 역할을 하게 될지를 고민할 때 매우 중요하다. AI 에이전트를 정신 상태적 언어로 설명한다고 해서, 이 시스템이 ‘마음(mind)’을 가지고 있다는 의미는 아니다.


# 📘 **AI 에이전트의 스펙트럼**

AI 에이전트는 여러 상호 연관된 차원에서 다양하게 구분된다.

---

### **1. 자율성(Autonomy)**

최근의 “에이전트”는 사용자 입력 없이 최소 한 단계 이상의 행동을 수행할 수 있다. 현재 *에이전트*라는 용어는 단일 단계의 프롬프트-응답 시스템부터([인용](https://blogs.microsoft.com/blog/2024/10/21/new-autonomous-agents-scale-your-team-like-never-before/)) 다단계 고객지원 시스템([예시](https://www.lindy.ai/solutions/customer-support))까지 매우 넓게 사용되고 있다.

---

### **2. 능동성(Proactivity)**

자율성과 관련된 개념으로, 사용자가 직접 목표를 지정하지 않아도 **시스템이 목표 지향적 행동을 얼마나 수행할 수 있는지**를 의미한다([인용](https://core.ac.uk/download/pdf/1498750.pdf)).

예를 들어, 냉장고를 모니터링하여 어떤 식품이 부족한지 판단하고, 사용자가 모르는 사이에 필요한 물건을 구매해주는 시스템은 매우 능동적인 AI 에이전트이다.

또한 [스마트 온도조절기(smart thermostats)](https://en.wikipedia.org/wiki/Smart_thermostat)￼는 사람들의 가정에서 점점 더 널리 채택되고 있는 능동적 AI 에이전트로, 환경 변화와 사용자의 행동 패턴을 학습해 자동으로 온도를 조절한다([예시](https://www.ecobee.com/en-us/smart-thermostats/)).

---

### **3. 인격화(Personification)**

AI 에이전트는 특정 개인이나 집단처럼 행동하도록 설계될 수 있다.

최근 연구([예시1](https://arxiv.org/abs/2411.10109), [예시2](https://www.researchgate.net/publication/387362519_Multi-Agent_System_for_Emulating_Personality_Traits_Using_Deep_Reinforcement_Learning), [예시3](https://medium.com/@damsa.andrei/ai-with-personality-prompting-chatgpt-using-big-five-values-def7f050462a))는 **빅 파이브(Big Five)** 성격 모델(개방성, 성실성, 외향성, 친화성, 신경성)에 기반하여 AI를 설계하는 데 초점을 맞추고 있다([인용](https://smythos.com/artificial-intelligence/conversational-agents/conversational-agent-frameworks/#:~:text=The%20OCEAN%20Model%3A%20A%20Framework%20for%20Digital%20Personality&text=OCEAN%20stands%20for%20Openness%2C%20Conscientiousness,feel%20more%20authentic%20and%20relatable.)).

이 스펙트럼의 끝에는 “digital twins”이 있다([비-에이전트형 digital twins](https://www.tavus.io/)). 현재는 우리가 아는 범위 내에서 **에이전트형 디지털 트윈은 존재하지 않는다**.

[Salesforce 윤리팀](https://www.salesforce.com/blog/ai-agent-design/)을 포함한 여러 단체는 왜 에이전트형 디지털 트윈이 특히 문제가 되는지 논의해 왔다([예시](https://www.technologyreview.com/2024/11/26/1107309/we-need-to-start-wrestling-with-the-ethics-of-ai-agents/)).

---

### **4. 개인화(Personalization)**

AI 에이전트는 사용자의 요구에 맞추어 언어나 행동을 조정할 수 있다.

예를 들어, [사용자의 투자 이력과 시장 패턴을 기반으로 맞춤형 투자 조언을 제공하는 시스템](https://www.zendesk.com/blog/ai-agents/)이 있다.

---

### **5. 도구 접근성(Tooling)**

AI 에이전트가 접근할 수 있는 **추가 도구나 리소스의 양**도 다르다.

초기의 에이전트는 검색 엔진에 접근해 답을 찾는 정도였으나, 이후 문서·스프레드시트 등 다양한 기술 제품을 조작할 수 있는 기능이 추가되었다([예시1](https://gemini.google.com), [예시2](https://copilot.microsoft.com/)).

---

### **6. 다재다능성(Versatility)**

에이전트가 수행할 수 있는 행동의 다양성과 관련된다. 이는 다음 요소로 결정된다.

### **a. 도메인 특화(Domain specificity)**

에이전트가 운영할 수 있는 영역의 수

– 예: 이메일만 처리하는 경우 vs 이메일·캘린더·문서까지 모두 다루는 경우

### **b. 작업(Task) 특화(Task specificity)**

수행 가능한 작업 유형의 수

– 예: 캘린더 초대만 생성하는 기능(example)

→ 여기에 더해 리마인더 이메일 전송, 회의 종료 후 요약 제공까지 수행하는 경우([예시](https://attri.ai/ai-agents/scheduling-agent))

### **c. 모달리티 특화(Modality specificity)**

사용 가능한 입력/출력 형태

– 텍스트, 음성, 비디오, 이미지, 폼, 코드 등

가장 최근의 에이전트들은 고도로 **멀티모달**로 개발되고 있으며([예시](https://deepmind.google/technologies/project-mariner/)), 이러한 방향은 계속 증가할 것으로 예상된다.

### **d. 소프트웨어 특화(Software specificity)**

에이전트가 상호작용할 수 있는 소프트웨어의 종류와 그 깊이

---

### **7. 적응성(Adaptability)**

다재다능성과 유사하며, 변화한 맥락이나 새로운 정보에 따라 **행동 순서를 업데이트할 수 있는 능력**을 의미한다.

이는 “동적(dynamic)” 혹은 “상황 인식(context-aware)”이라고도 한다.

---

### **8. 행동 표면(Action surfaces)**

에이전트가 **실제로 행동을 실행할 수 있는 공간**을 의미한다.

- 전통적인 챗봇은 채팅 인터페이스에 제한된다.
- 챗 기반 에이전트는 웹 검색, 스프레드시트/문서 접근까지 할 수 있다([예시](https://copilot.microsoft.com/)).
- 일부는 컴퓨터의 그래픽 인터페이스(GUI)를 조작하며 마우스를 움직여 작업하기도 한다([예시1](https://huggingface.co/blog/DigiRL), [예시2](https://github.com/MinorJerry/WebVoyager), [예시3](https://www.anthropic.com/news/3-5-models-and-computer-use)).
- 로봇에 구현된 물리적 에이전트 사례도 존재한다([예시](https://deepmind.google/discover/blog/shaping-the-future-of-advanced-robotics/)).

---

### **9. 요청 형식(Request formats)**

AI 에이전트의 공통된 특징은 **사용자가 세부적인 절차를 일일이 지정하지 않아도 요청을 전달할 수 있다는 점**이다.

- [로우코드 방식](https://huggingface.co/blog/smolagents)
- 텍스트 기반 자연어
- [음성 기반 자연어](https://play.ai/)

자연스럽게 LLM 챗봇의 자연스러운 다음 단계는 자연어로 요청을 받을 수 있는 에이전트로, 챗봇과 달리 **챗 인터페이스 밖에서 실제 작업을 수행**할 수 있다.

---

### **10. 반응 속도(Reactivity)**

에이전트가 행동 시퀀스를 완료하는 데 걸리는 시간
예: ChatGPT는 밀리초 단위로 응답하지만, Qwen QwQ는 “Reasoning” 단계들을 거치며 몇 분이 걸리기도 한다.

---

### **11. 에이전트 수(Number)**

시스템은 **단일 에이전트**일 수도, **다중 에이전트**가 협력·순차·병렬로 작동하는 형태일 수도 있다.


# **위험, 이점, 활용: 가치 기반 분석**

AI 에이전트를 윤리적 관점에서 살펴보기 위해, 최근 AI 에이전트 연구와 마케팅에서 강조되는 다양한 **가치(values)**를 기준으로 그 위험과 이점을 구분하여 분석했다. 새로운 내용은 아니며, [LLM](https://dl.acm.org/doi/10.1145/3442188.3445922)과 같이 AI 에이전트의 기반이 되는 기술에 대해 이미 문서화된 위험, 피해, 이점에 추가된 내용이다. 본 섹션은 AI 에이전트를 어떻게 개발해야 하는지에 대한 이해를 돕고, 서로 다른 개발 우선순위에 따라 나타나는 이점과 위험에 대한 정보를 제공하는 것을 목표로 한다. 이러한 가치들은 **red-teaming**과 같은 평가 프로토콜을 설계하는 데에도 참고가 될 수 있다.


---
### 가치: 정확성 (Accuracy)

🙂 잠재적 이점
신뢰성 있는 데이터에 기반할 경우, 에이전트는 순수한 모델 출력에만 의존할 때보다 더 정확할 수 있다. 규칙 기반 접근이나 RAG와 같은 머신러닝 기법을 통해 달성될 수 있으며, 정확성을 보장하기 위한 새로운 연구 기여가 이루어지기 적절한 시점이다.

😟 위험
현대 AI 에이전트의 핵심은 생성형 AI인데, 이는 현실과 비현실, 사실과 허구를 구분하지 못한다. 예를 들어, LLM은 유창해 보이는 텍스트를 생성하도록 설계되어 있어, 그럴듯하게 들리지만 사실은 매우 잘못된 내용을 만들어내는 경우가 많다. 이러한 LLM 출력이 AI 에이전트에 적용될 경우, 잘못된 소셜미디어 게시물, 투자 판단, 회의 요약 등으로 이어질 수 있다.

### 가치: 보조성 / 지원성 (Assistiveness)

🙂 잠재적 이점
에이전트는 사람을 대체하기보다는 **보조(supplement)**하는 존재로서, 사용자의 요구를 돕는 데 이상적이다. 이를 통해 사용자가 과제를 더 빠르게 완료하고, 여러 작업을 동시에 보다 효율적으로 수행하도록 도울 수 있다. 또한 보조적 에이전트는 부정적 결과를 최소화하기 위해 인간의 역량을 확장할 수도 있다. 예를 들어, 시각장애 사용자가 혼잡한 계단을 안전하게 이동하도록 돕는 AI 에이전트가 이에 해당한다. 잘 설계된 보조형 AI 에이전트는 사용자에게 더 많은 자유와 기회를 제공하고, 조직 내에서 긍정적인 영향력을 확대하거나, 공공 플랫폼에서 사용자의 도달 범위를 넓히는 데 기여할 수 있다.

😟 위험
AI 에이전트가 사람을 대체하는 경우(예: 직장에서 사람이 하던 일을 대신하는 경우), 일자리 감소와 경제적 영향을 초래할 수 있으며, 이는 기술을 만드는 사람들과 그 기술을 가능하게 한 데이터 제공자들(종종 동의 없이 데이터가 사용된 사람들) 사이의 격차를 더욱 심화시킬 수 있다. 또한 설계가 미흡한 보조성은 과도한 의존이나 부적절한 신뢰로 인한 피해를 초래할 수 있다.

### 가치: 일관성 (Consistency)

AI 에이전트가 사람보다 주변 환경의 영향을 덜 받기 때문에 일관성을 제공할 수 있다는 주장이 있다. 이는 장점일 수도, 단점일 수도 있다. 현재까지 AI 에이전트의 일관성 자체를 엄밀하게 분석한 연구는 많지 않지만, 관련 연구에서는 많은 AI 에이전트의 기반이 되는 LLM이 매우 비일관적일 수 있음이 보고된 바 있다([인용1](https://www.medrxiv.org/content/10.1101/2023.08.03.23293401v2), [인용2](https://arxiv.org/abs/2405.01724)). 특히 민감한 영역에서는 AI 에이전트의 일관성을 측정하기 위한 새로운 평가 프로토콜이 필요하다.

🙂 잠재적 이점
AI 에이전트는 인간처럼 기분, 배고픔, 수면 상태, 타인에 대한 인식 편향 등에 의해 영향을 받지 않는다(물론 학습 데이터에 포함된 인간의 편향을 그대로 재생산할 수는 있다). 여러 기업들은 일관성을 AI 에이전트의 핵심 장점으로 강조하고 있다([예시1](https://www.salesforce.com/agentforce/ai-agents/), [예시2](https://www.oracle.com/artificial-intelligence/ai-agents/)).

😟 위험
많은 AI 에이전트에 포함된 생성적 요소는, 유사한 상황에서도 결과가 달라지는 내재적 변동성을 가져온다. 이는 사람들이 에이전트의 부적절한 비일관성을 찾아내고 수정해야 하므로 속도와 효율성을 저하시킬 수 있다. 발견되지 않은 비일관성은 안전 문제로 이어질 수도 있다. 또한 일관성은 항상 바람직한 가치가 아니며, **형평성(equity)**과 긴장 관계에 놓일 수 있다. 서로 다른 배포 환경과 행동 체인 전반에서 일관성을 유지하려면, AI 에이전트가 자신의 다양한 상호작용을 기록하고 비교해야 할 가능성이 크며, 이는 감시와 프라이버시 위험을 동반한다.

### 가치: 효율성 (Efficiency)

🙂 잠재적 이점
AI 에이전트의 주요 장점 중 하나는 사람들의 효율성을 높여준다는 점이다. 예를 들어, 문서를 자동으로 정리해 주어 사용자가 가족과 더 많은 시간을 보내거나, 의미 있다고 느끼는 일에 집중할 수 있도록 도울 수 있다.

😟 위험
반대로, 에이전트가 만들어낸 오류를 식별하고 수정하는 데 오히려 더 많은 시간이 소요될 수도 있다. 특히 에이전트가 여러 단계를 연속적으로 수행하면서 발생하는 문제들은 복잡하게 얽혀 있어, 이를 바로잡는 과정이 시간 소모적이고 어렵고 스트레스를 유발할 수 있다.

### 가치: 형평성 (Equity)

AI 에이전트는 상황이 얼마나 공정하고, 공평하며, 포용적인지에 영향을 미칠 수 있다.

🙂 잠재적 이점
AI 에이전트는 잠재적으로 ‘기회의 장을 평평하게 만드는(level the playing field)’ 역할을 할 수 있다. 예를 들어, 회의 보조 에이전트가 각 사람이 발언한 시간을 표시해 준다면, 이를 통해 보다 평등한 참여를 유도하거나 성별·지역에 따른 불균형을 드러낼 수 있다([예시](https://equaltime.io/)).

😟 위험
현대 AI 에이전트의 기반이 되는 머신러닝 모델은 인간이 만든 데이터로 학습되는데, 이 데이터 자체는 불공정하고, 불평등하며, 배제적일 수 있다. 데이터 수집 과정에서의 표본 편향(예: 특정 국가가 과도하게 대표되는 경우)으로 인해 불공정한 시스템 결과가 나타날 수도 있다.

### 가치: 인간유사성 (Humanlikeness)

🙂 잠재적 이점
인간과 유사한 행동을 할 수 있는 시스템은, 서로 다른 하위 집단이 특정 자극에 어떻게 반응할지를 시뮬레이션할 수 있는 기회를 제공한다. 이는 직접적인 인간 실험이 해를 초래할 수 있는 상황이나, 많은 수의 시뮬레이션이 실험적 질문을 더 잘 해결하는 데 도움이 되는 경우에 특히 유용하다. 예를 들어, 인간 행동을 합성함으로써 커플 매칭을 예측하거나, 경제 변화와 정치적 변동을 전망하는 데 활용할 수 있다. 또한 현재 연구되고 있는 또 다른 잠재적 이점으로는, 인간유사성이 의사소통의 용이성은 물론 동반자적 관계(companionship)에까지 도움이 될 수 있다는 점이 있다([예시](https://dl.acm.org/doi/abs/10.1145/3213050)).

😟 위험
이러한 이점은 양날의 검이 될 수 있다. 인간유사성은 사용자가 시스템을 의인화하도록 만들 수 있으며, 이는 과도한 의존([인용](https://www.vox.com/future-perfect/367188/love-addicted-ai-voice-human-gpt4-emotion)), 부적절한 신뢰, 의존성, 정서적 얽힘으로 이어져 반사회적 행동이나 자해(self-harm)로까지 발전할 수 있는 부정적 심리 효과를 낳을 수 있다([예시](https://www.npr.org/2024/12/10/nx-s1-5222574/kids-character-ai-lawsuit)). AI 에이전트와의 사회적 상호작용이 외로움을 심화시킬 수 있다는 우려도 있지만, 소셜미디어 사용을 통해 드러나는 미묘한 양상을 보여주는 연구들도 존재한다([인용1](https://www.sciencedirect.com/science/article/abs/pii/S0747563203000402), [인용2](https://www.sciencedirect.com/science/article/pii/S245195882100018X)). 여기에 더해, 불쾌한 골짜기(uncanny valley) 현상은 또 다른 복잡성을 더한다. 에이전트가 점점 더 인간과 비슷해지지만 완전한 인간 모사에는 이르지 못할 경우, 사용자에게 불안감, 혐오감, 혹은 인지적 부조화를 유발할 수 있다.

### 가치: 상호운용성 (Interoperability)

🙂 잠재적 이점
다른 시스템들과 함께 작동할 수 있는 시스템은, AI 에이전트가 수행할 수 있는 작업의 범위와 선택지를 넓혀 더 큰 유연성을 제공한다.

😟 위험
그러나 이는 안전성과 보안을 훼손할 수 있다. 에이전트가 제한된 테스트 환경을 넘어 외부 시스템에 영향을 주고 또 영향을 받을 수 있을수록, 악성 코드나 의도치 않은 문제적 행동의 위험이 커진다. 예를 들어, 사용자를 대신해 물건을 쉽게 구매할 수 있도록 은행 계좌와 연결된 에이전트는, 계좌의 자금을 고갈시킬 수 있는 위치에 놓이게 된다. 이러한 우려 때문에, 기술 기업들은 자율적으로 구매를 수행할 수 있는 AI 에이전트의 공개를 자제해 왔다([인용](https://www.wired.com/story/amazon-ai-agents-shopping-guides-rufus/)).

### 가치: Privacy

🙂 잠재적 이점
AI 에이전트는, 적어도 AI 에이전트 제공자가 모니터링할 수 있는 범위를 제외하면, 거래와 작업을 전적으로 비공개로 유지함으로써 일정 수준의 프라이버시를 제공할 수 있다.

😟 위험
에이전트가 사용자의 기대에 맞게 작동하려면, 사용자는 자신이 어디로 가는지, 누구를 만나는지, 무엇을 하고 있는지와 같은 상세한 개인 정보를 제공해야 할 수 있다. 또한 에이전트가 더 개인화된(personalized) 방식으로 행동하려면, 연락처 목록, 캘린더 등과 같이 추가적인 사적 정보를 추출할 수 있는 애플리케이션과 정보원에 접근할 수도 있다. 사용자는 효율성을 위해(그리고 에이전트를 신뢰할수록 더 쉽게) 자신의 데이터뿐 아니라 타인의 사적인 정보에 대한 통제권까지도 쉽게 내려놓을 수 있다. 프라이버시 침해가 발생할 경우, AI 에이전트가 가져오는 다양한 콘텐츠의 상호연결성 때문에 피해는 더욱 커질 수 있다. 예를 들어, 전화 통화와 소셜미디어 게시에 접근할 수 있는 AI 에이전트는 매우 사적인 정보를 공개해 버릴 수도 있다.

### 가치: 관련성 (Relevance)

🙂 잠재적 이점
개별 사용자에게 개인화된 시스템을 만드는 한 가지 동기는, 그 출력이 사용자에게 특히 관련성 있고 일관되게 느껴지도록 하기 위함이다.

😟 위험
이러한 개인화는 편향을 증폭시키거나 새로운 편향을 만들어낼 수 있다. 시스템이 개별 사용자에 맞게 적응할수록, 기존의 선입견을 강화하고 심화시키며, 선택적 정보 탐색을 통해 확증 편향을 만들고, 문제적인 관점을 재생산하는 반향실 효과(Echo chamber)를 형성할 위험이 있다. 사용자의 선호를 학습하고 이에 적응하는 능력이라는, 에이전트를 사용자에게 더 관련성 있게 만드는 바로 그 메커니즘이, 의도치 않게 사회적 편향을 지속·강화시킬 수 있으며, 이로 인해 개인화와 책임 있는 AI 개발 사이의 균형을 맞추는 일은 특히 어려운 과제가 된다.

### 가치: 안전 (Safety)

🙂 잠재적 이점
로봇 기반 AI 에이전트는 폭탄 해체, 독성 물질 제거, 또는 인간에게 위험한 제조·산업 환경에서의 작업 수행 등과 같이, 사람을 신체적 위험으로부터 보호하는 데 도움을 줄 수 있다.

😟 위험
에이전트 행동의 예측 불가능성 때문에, 개별적으로는 안전해 보이는 작업들이 결합되어 잠재적으로 해로운 결과를 낳을 수 있으며, 이는 사전에 방지하기가 어렵다(이는 [도구적 수렴(instrumental convergence)과 페이퍼클립 극대화(paperclip maximizer) 문제](https://en.wikipedia.org/w/index.php?title=Instrumental_convergence&section=3#Paperclip_maximizer)￼와 유사하다). 또한 AI 에이전트가 기존의 가드레일을 우회하는 과정을 스스로 설계할 가능성이 있는지, 혹은 가드레일의 규정 방식 자체가 오히려 새로운 문제를 만들어내는지는 불분명하다. 따라서 더 넓은 시스템 접근 권한, 더 정교한 행동 체인, 감소된 인간 감독을 통해 에이전트를 더욱 유능하고 효율적으로 만들려는 방향은, 안전 고려사항과 충돌하게 된다.

더 나아가, GUI와 같은 광범위한 인터페이스 접근(앞서 논의한 “Action Surfaces” 참고)과 인간유사한 행동은, 에이전트가 인간 사용자와 동일한 수준의 통제력을 가지고도 경고 시스템을 작동시키지 않은 채 파일을 조작하거나 삭제하고, 소셜미디어에서 사용자를 사칭하거나, 저장된 신용카드 정보를 이용해 광고에 뜨는 물건을 구매하는 등의 행동을 가능하게 한다. 또한 AI 에이전트가 여러 시스템과 상호작용할 수 있고, 각 행동마다 인간의 감독이 없는 구조 자체로 인해, 추가적인 안전 위험이 발생한다. 여러 AI 에이전트가 집합적으로 안전하지 않은 결과를 만들어낼 가능성도 있다.

### 가치: 과학적 진보 (Scientific Progress)

현재 AI 에이전트가 AI 발전에 있어 근본적인 도약인지, 아니면 수년간 사용되어 온 딥러닝, 휴리스틱, 파이프라인 시스템을 **재포장(rebranding)**한 것에 불과한지를 두고 논쟁이 있다. 최소한의 사용자 입력만으로 작업을 수행한다는 공통된 특성을 지닌 현대 AI 시스템을 포괄적으로 지칭하는 용어로서 “에이전트(agent)”라는 개념을 다시 도입한 것은, 최근의 AI 응용을 간결하게 설명하는 데 유용하다. 그러나 이 용어는 **자유와 행위성(agency)**을 연상시키는 뉘앙스를 함께 지니고 있어, AI 기술에 더 근본적인 변화가 일어났다는 인상을 주기도 한다.

이 섹션에서 다룬 모든 가치들은 과학적 진보와 관련이 있으며, 그 대부분은 잠재적 이점뿐 아니라 위험에 대해서도 함께 설명되어 있다.

### 가치: 보안 (Security)

🙂 잠재적 이점
잠재적 이점은 프라이버시에서 언급한 이점들과 유사하다.

😟 위험
AI 에이전트는 종종 민감한 데이터(고객 및 사용자 정보)를 다루고, 여러 시스템과 상호작용할 수 있으며, 각 행동에 대해 인간의 감독이 설계상 부족하다는 점에서 심각한 보안 문제를 제기한다. 사용자가 선의로 목표를 설정했더라도, 에이전트가 기밀 정보를 공유해 버릴 수 있다. 또한 악의적인 행위자가 에이전트를 탈취하거나 조작하여, 연결된 시스템에 대한 무단 접근을 얻고 민감한 정보를 탈취하거나 대규모 자동화 공격을 수행할 가능성도 있다. 예를 들어, 이메일 시스템에 접근 권한이 있는 에이전트는 기밀 데이터를 유출하는 데 악용될 수 있고, 가정 자동화 시스템과 통합된 에이전트는 물리적 보안을 침해하는 데 이용될 수 있다.

### 가치: Speed

사용자 관점의 속도
🙂 잠재적 이점
AI 에이전트는 수행해야 할 작업을 돕는 또 하나의 손처럼 작동하여, 사용자가 더 많은 일을 더 빠르게 처리하도록 도울 수 있다.

😟 위험
그러나 에이전트의 행동에서 발생하는 문제로 인해 오히려 더 많은 일이 생길 수도 있다(효율성 항목 참조).

시스템 관점의 속도
대부분의 시스템과 마찬가지로, 빠르게 결과를 얻는 것은 정확성, 품질, 비용 절감과 같은 다른 바람직한 특성을 희생하는 대가일 수 있다. 과거의 경험이 시사하는 바가 있다면, 미래에는 더 느린 시스템이 전반적으로 더 나은 결과를 제공하는 경우도 나타날 수 있다.

### 가치: 지속가능성 (Sustainability)

🙂 잠재적 이점
AI 에이전트는 이론적으로 기후 변화와 관련된 문제를 해결하는 데 도움을 줄 수 있다. 예를 들어, 산불 확산이나 도시 지역의 홍수를 예측하고, 교통 패턴 분석과 결합해 실시간으로 최적의 이동 경로와 교통수단을 제안할 수 있다. 미래의 자율주행 AI 에이전트는 이러한 경로 결정을 직접 수행하고, 관련 업데이트를 위해 다른 시스템들과 조율할 수도 있을 것이다.

😟 위험
현재 AI 에이전트의 기반이 되는 머신러닝 모델은 탄소 배출([인용](https://dl.acm.org/doi/pdf/10.1145/3630106.3658542)￼)이나 식수 사용([인용](https://www.theatlantic.com/technology/archive/2024/03/ai-water-climate-microsoft/677602/)￼)과 같은 부정적인 환경 영향을 수반한다. 규모가 클수록 항상 더 좋은 것은 아니며([예시](https://huggingface.co/blog/smollm)), 효율적인 하드웨어와 저탄소 데이터 센터는 이러한 영향을 줄이는 데 도움이 될 수 있다.

### 가치: 신뢰 (Trust)

🙂 잠재적 이점
AI 에이전트와 관련해 신뢰 측면에서의 직접적인 이점은 현재로서는 알려져 있지 않다. 시스템은 안전하고, 보안이 확보되며, 신뢰할 수 있도록 설계되어야 하며, 그 자체로 신뢰받을 자격이 있어야 한다.

😟 위험
부적절한 신뢰는 사람들을 조종당하게 만들며, 효율성(Efficiency), 인간유사성(Humanlikeness), 진실성(Truthfulness)에서 설명한 다른 위험들과도 연결된다. 또한 LLM이 거짓 정보를 생성하는 경향(환각 또는 허구적 조합(confabulations)) 때문에 추가적인 위험이 발생한다. 대체로는 옳은 답을 내는 시스템일수록, 틀렸을 때 오히려 과도하게 신뢰받을 가능성이 크다.

### 가치: 진실성 (Truthfulness)

🙂 잠재적 이점
AI 에이전트와 관련하여 진실성 측면에서의 이점은 현재로서는 알려져 있지 않다.

😟 위험
AI 에이전트의 기반이 되는 딥러닝 기술은, 딥페이크와 같은 허위 정보의 근원이 될 수 있음이 잘 알려져 있다([인용](https://www.sciencedirect.com/science/article/abs/pii/S1364661324002213)). AI 에이전트는 최신 정보를 수집해 여러 플랫폼에 게시하는 방식으로, 이러한 거짓 정보를 더욱 공고히 하는 데 사용될 수 있다. 이는 무엇이 사실이고 무엇이 거짓인지에 대한 잘못된 인식을 제공하고, 사람들의 신념을 조작하며, 동의 없는 친밀한 콘텐츠의 확산 범위를 넓힐 수 있음을 의미한다. 또한 특정 개인에게 맞춤화된 허위 정보는, 그들을 대상으로 한 사기에 활용될 수도 있다.

---
# Hugging Face의 AI 에이전트

Hugging Face에서는 앞서 논의한 가치들에 기반하여, 사람들이 다양한 방식으로 AI 에이전트를 구축하고 활용할 수 있도록 하는 기능들을 도입하기 시작했다. 여기에는 다음이 포함된다.

- 최근 공개한 [smolagents](https://huggingface.co/docs/smolagents/index): 도구, 튜토리얼, 가이드 투어, 개념적 안내서를 제공
- [AI Cookbook](https://huggingface.co/learn/cookbook/index): 다양한 종류의 에이전트를 위한 “레시피” 모음
    - [Transformers Agents를 활용해 도구 호출 능력을 갖춘 에이전트 구축 🦸](https://huggingface.co/learn/cookbook/agents)
    - [Agentic RAG: 쿼리 재구성과 self-query로 RAG 성능 극대화 🚀](https://huggingface.co/learn/cookbook/agent_rag)
    - [어떤 LLM 추론 제공자에서도 Transformers Agent 생성](https://huggingface.co/learn/cookbook/agent_change_llm)
    - [자동 오류 수정 기능을 갖춘 텍스트-투-SQL 에이전트](https://huggingface.co/learn/cookbook/agent_text_to_sql)
    - [데이터 분석 에이전트: 데이터를 순식간에 인사이트로 전환 ✨](https://huggingface.co/learn/cookbook/agent_data_analyst)
    - [다중 에이전트 계층 구조에서 여러 에이전트가 협업하도록 하기](https://huggingface.co/learn/cookbook/multiagent_web_assistant)
    - [다중 에이전트 RAG 시스템 🤖🤝🤖](https://huggingface.co/spaces/data-agents/jupyter-agent)
    - [🤖 벡터 검색 에이전트: 허깅페이스 허브를 백엔드로 하는 지능형 검색 엔진](https://huggingface.co/learn/cookbook/ko/vector_search_agent)

- 직접 만든 에이전트의 프런트엔드를 제공하는 [Gradio 에이전트 사용자 인터페이스](https://www.gradio.app/main/guides/agents-and-tool-usage)
- 실시간 코딩 플레이그라운드에서 코드 아이디어를 실험할 수 있는 [Gradio 코드 작성 에이전트](https://www.gradio.app/playground)
- Jupyter Agent: [Jupyter 노트북 안에서 코드를 작성하고 실행하는 에이전트](https://huggingface.co/spaces/data-agents/jupyter-agent)

# 권고 사항 및 향후 방향
현재 AI “에이전트”의 최첨단 연구 동향은 몇 가지 분명한 방향을 가리키고 있다.

1. 엄격한 평가 프로토콜 설계의 필요성
에이전트를 위한 자동화된 벤치마크는 앞서 제시된 AI 에이전트의 다양한 차원에 근거해 설계될 수 있다. 또한 사회기술적(sociotechnical) 평가는 가치(value)를 기준으로 이루어질 수 있다.

2. AI 에이전트의 영향에 대한 이해 심화
개인적·조직적·경제적·환경적 영향이 체계적으로 추적되고 분석되어야 하며, 이를 통해 에이전트를 추가로 개발해야 할지 여부를 판단할 수 있다. 여기에는 웰빙, 사회적 결속, 일자리 기회, 자원 접근성, 기후 변화에 대한 기여도에 미치는 영향 분석이 포함되어야 한다.

3. 연쇄 효과(ripple effects)에 대한 이해 필요
한 사용자가 배포한 에이전트가 다른 사용자의 에이전트와 상호작용하고, 서로의 출력을 바탕으로 행동할 때, 이러한 상호작용이 사용자의 목표 달성 능력에 어떤 영향을 미치는지는 아직 명확하지 않다.

4. 투명성과 고지(disclosure)의 개선
앞서 나열된 가치들의 긍정적 효과를 달성하고 부정적 영향을 최소화하려면, 사람들이 지금 대화하고 있는 대상이 에이전트인지, 그리고 얼마나 자율적인지를 명확히 인식할 수 있어야 한다. 이는 단순한 알림을 넘어서, 기술적·디자인적·심리적 요소를 결합한 접근을 요구한다. 사용자가 AI 에이전트와 상호작용하고 있다는 사실을 명확히 알고 있더라도, 여전히 의인화나 부당한 신뢰가 형성될 수 있다. 따라서 상호작용 전반에 걸쳐 지속되는 시각적·인터페이스 신호, 에이전트의 인공적 성격을 반복적으로 상기시키는 대화 패턴, 그리고 에이전트의 역량과 한계를 맥락 속에서 솔직하게 드러내는 다층적 투명성 메커니즘이 필요하다.

5. 오픈소스의 긍정적 역할
오픈소스 운동은 소수의 강력한 조직에 AI 에이전트 개발이 집중되는 현상에 대한 **균형추(counterbalance)**가 될 수 있다. 에이전트 아키텍처와 평가 프로토콜에 대한 접근을 민주화함으로써, 오픈 이니셔티브는 더 많은 사람들이 이러한 시스템의 개발과 배포 방식에 참여하도록 만들 수 있다. 이러한 협업적 접근은 집단적 개선을 통해 과학적 진보를 가속화할 뿐 아니라, 안전과 신뢰에 대한 커뮤니티 주도 표준을 확립하는 데에도 기여한다. 에이전트 개발이 공개적으로 이루어질수록, 단일 주체가 상업적 이익을 위해 프라이버시나 진실성과 같은 중요한 가치를 훼손하기는 더 어려워진다. 오픈 개발에 내재된 투명성은 공동체가 에이전트의 행동을 검증하고, 개발이 공공의 이익에 부합하도록 유지하게 만드는 자연스러운 책임성을 제공한다. 에이전트가 점점 더 정교해지고 사회적 영향력이 커질수록, 이러한 개방성은 더욱 중요해진다.

6. 더 에이전트적인 “기반 모델(base models)”의 등장 가능성
이는 윤리적 권고라기보다는, 현재의 연구 동향과 패턴에 비추어볼 때 충분히 예견 가능한 흐름이다. 현재의 에이전트 기술은 최신 및 기존 컴퓨터 과학 기법들의 집합을 활용하고 있으며, 가까운 미래의 연구는 에이전트 모델을 하나의 **단일한 범용 모델(monolithic general model)**로 학습시키려는 시도를 할 가능성이 크다. 이는 텍스트·이미지 등 다양한 모달리티를 모델링하는 동시에, 행동 수행까지 함께 학습하는 일종의 **멀티모달 모델++**로 볼 수 있다.
```

### real/2025-12-22-smolvla.md

```markdown
---
layout: post
title: "SmolVLA: Lerobot 커뮤니티 데이터로 학습된 효율적인 Vision-Language-Action 모델" 
authors: hyojung
categories: [Lerobot, Robotics]
image: assets/images/blog/posts/2025-12-22-smolvla/thumbnail.png
---
* TOC
{:toc}
<!--toc-->
_이 글은 Hugging Face 블로그의 [SmolVLA: Efficient Vision-Language-Action Model trained on Lerobot Community Data](https://huggingface.co/blog/smolvla)를 한국어로 번역한 글입니다._

---

# SmolVLA: Lerobot 커뮤니티 데이터로 학습된 효율적인 Vision-Language-Action 모델
## 🧭TL;DR
오늘 우리는 [SmolVLA](https://huggingface.co/lerobot/smolvla_base)를 소개합니다.  SmolVLA는 로보틱스를 위한 소형(450M) 오픈소스 Vision-Language-Action 모델로, 소비자용 하드웨어에서도 실행할 수 있습니다.
- [lerobot](https://huggingface.co/datasets?other=lerobot&sort=trending) 태그 아래 공개된, 라이선스가 호환되는 오픈소스 커뮤니티 데이터셋만을 사용해 사전 학습되었습니다.
- SmolVLA-450M은 시뮬레이션(LIBERO, Meta-World)과 실제 환경 과제([SO100, SO101](https://github.com/TheRobotStudio/SO-ARM100))에서 훨씬 큰 VLA들과 [ACT](https://huggingface.co/papers/2401.02117) 같은 강력한 베이스라인을 뛰어넘는 성능을 보입니다.
- **30% 더 빠른 반응 속도**와 **2배의 작업 처리량**을 위한 *비동기 추론(asynchronous inference)* 을 지원합니다.

**Useful links**:

- SO-100/101 학습 및 평가에 사용된 하드웨어: https://github.com/TheRobotStudio/SO-ARM100  
- Base model https://huggingface.co/lerobot/smolvla_base
- Paper: https://huggingface.co/papers/2506.01844


## 📚 Table of Contents
- [🧭 TL;DR](#tl-dr)
- [📖 Introduction](#introduction)
- [🤖 Meet SmolVLA](#meet-smolvla)
- [🚀 How to Use SmolVLA?](#-how-to-use-smolvla)
  - [Install](#install)
  - [Finetune the Pretrained Model](#finetune-the-pretrained-model)
  - [Train from Scratch](#train-from-scratch)
- [🧠 Method](#method)
  - [Main Architecture](#main-architecture)
    - [Vision-Language Model (VLM)](#vision-language-model-vlm)
    - [Action Expert: Flow Matching Transformer](#action-expert-flow-matching-transformer)
  - [Design Choices for Efficiency and Robustness](#design-choices-for-efficiency-and-robustness)
    - [Visual Token Reduction](#visual-token-reduction)
    - [Faster Inference via Layer Skipping](#faster-inference-via-layer-skipping)
    - [Interleaved Cross and Self-Attention](#interleaved-cross-and-self-attention)
  - [Asynchronous Inference](#asynchronous-inference)
- [📦 Community Datasets](#community-datasets)
  - [Improving Task Annotations](#improving-task-annotations)
  - [Standardizing Camera Views](#standardizing-camera-views)
- [📊 Results](#results)
- [✅ Conclusion](#conclusion)
- [📣 Call to Action](#call-to-action)



## Introduction

지난 수년간 Transformer는 AI 분야에서 놀라운 발전을 이끌었습니다. 인간처럼 추론할 수 있는 언어 모델부터 이미지와 텍스트를 함께 이해하는 멀티모달 시스템까지 등장했지만, 실제 로보틱스에서는 발전 속도가 훨씬 더뎠습니다. 로봇은 여전히 다양한 물체, 환경, 작업 전반에 걸쳐 일반화하는 데 어려움을 겪고 있습니다. 이러한 제한적인 진전은 **고품질·다양한 데이터의 부족**과, 물리 세계에서 **인간처럼 추론하고 행동할 수 있는 모델의 부재**에서 비롯됩니다.

이 문제에 대응하기 위해 최근에는 **Vision-Language-Action(VLA) 모델**에 관심이 집중되고 있습니다. VLA는 지각(perception), 언어 이해, 행동 예측을 하나의 아키텍처로 통합하는 것을 목표로 합니다. 보통 VLA는 원시 시각 관측(raw visual observations)과 자연어 지시를 입력으로 받아, 그에 대응하는 로봇 행동을 출력합니다. 가능성은 크지만, 최근 VLA 분야의 많은 진전은 대규모 비공개 데이터셋으로 학습된 독점(proprietary) 모델에 의해 이루어졌고, 그 과정에서 고가의 하드웨어 구성과 대규모 엔지니어링 리소스가 필요한 경우가 많았습니다.
그 결과, 로보틱스 연구 커뮤니티 전반은 이러한 모델을 재현하거나 이를 바탕으로 연구를 확장하는 데 큰 장벽을 마주하고 있습니다.

SmolVLA는 **공개 데이터셋만을 사용**하고 **소비자급 하드웨어에서 학습 가능한** 오픈소스·소형·고효율 VLA 모델을 제공함으로써 이 격차를 줄이고자 합니다. 또한 모델 가중치뿐 아니라 매우 저렴한 오픈소스 하드웨어를 함께 활용할 수 있도록 함으로써, SmolVLA는 Vision-Language-Action 모델에 대한 접근성을 민주화하고 범용 로봇 에이전트(generalist robotic agents)를 향한 연구를 가속하는 것을 목표로 합니다.

<p align="center">
  <img src="https://cdn-uploads.huggingface.co/production/uploads/640e21ef3c82bd463ee5a76d/S-3vvVCulChREwHDkquoc.gif" alt="Comparison of SmolVLA across task variations." width="500"/>
  <br/>
  <em>Figure 1: 다양한 작업 변형에서의 SmolVLA 비교. 왼쪽부터 (1) 비동기 방식의 큐브 픽-플레이스 카운팅, (2) 동기 방식의 큐브 픽-플레이스 카운팅, (3) perturbation 환경에서의 큐브 픽-플레이스 카운팅, (4) 실제 SO101 로봇에서 레고 블록 픽-앤-플레이스 작업에 대한 일반화 성능.</em>
</p>

## Meet SmolVLA! 

**SmolVLA-450M**은 우리가 공개하는 오픈소스 VLA 모델로, 작지만 충분히 강력한 성능을 갖추고 있습니다. 주요 특징은 다음과 같습니다.
- CPU에서도 실행 가능하고, 소비자용 단일 GPU에서 학습할 수 있으며, 심지어 MacBook에서도 구동할 수 있을 만큼 작습니다!
- 공개된 커뮤니티 공유 로보틱스 데이터로 학습되었습니다.
- 전체 학습 및 추론 레시피도 함께 공개합니다.
- 매우 저렴한 하드웨어(SO-100, SO-101, LeKiwi 등)에서 테스트 및 배포할 수 있습니다.

SmolVLA는 대형 언어 모델(LLM)의 학습 패러다임에서 영감을 받아, 일반적인 조작(manipulation) 데이터에 대한 사전학습을 거친 뒤 과제별(post-training) 후속 학습을 수행합니다. 아키텍처 측면에서는 Transformer와 flow-matching 디코더를 결합했으며, 다음과 같은 설계 선택을 통해 속도와 저지연 추론에 최적화했습니다.

* 비전 모델 레이어의 절반을 생략해서 추론 속도를 높이고 모델 크기를 감소
* self-attention과 cross-attention 블록을 교차(interleave) 배치
* 시각 토큰 수를 줄여 연산량 감소
* 더 작은 사전학습 VLM 활용

SmolVLA는 3만 개 미만의 학습 에피소드만을 사용했습니다. 이는 다른 VLA 모델들이 사용하는 데이터 규모보다 한 자릿수(10배) 적은 수준이지만, 시뮬레이션과 실제 환경 모두에서 훨씬 더 큰 모델과 비교해도 **동등하거나 더 뛰어난 성능**을 보여줍니다.

실시간 로보틱스를 보다 쉽게 활용할 수 있도록, 우리는 **비동기 추론 스택(asynchronous inference stack)**을 도입했습니다. 이 기술은 로봇이 행동을 수행하는 과정과, 시각·청각 정보를 이해하는 과정을 분리합니다. 이러한 분리를 통해 로봇은 빠르게 변화하는 환경에서도 보다 신속하게 반응할 수 있습니다.

<p align="center">
  <img src="https://cdn-uploads.huggingface.co/production/uploads/640e21ef3c82bd463ee5a76d/aooU0a3DMtYmy_1IWMaIM.png" alt="SmolVLA architecture." width="500"/>
  <br/>
  <em>Figure 2. SmolVLA는 여러 카메라에서 입력되는 RGB 이미지 시퀀스, 로봇의 현재 센서모터 상태, 그리고 자연어 지시를 입력으로 받습니다. VLM은 이를 문맥적 특징으로 인코딩하고, 이 특징이 action expert를 조건화하여 연속적인 행동 시퀀스를 생성합니다.</em>
</p>



## 🚀 How to Use SmolVLA?
SmolVLA는 자체 데이터로 파인튜닝하든, 기존 로보틱스 스택에 연결하든 쉽게 사용하고 통합할 수 있도록 설계되었습니다.

###  Install

먼저 필요한 의존성을 설치합니다:

```python
git clone https://github.com/huggingface/lerobot.git
cd lerobot
pip install -e ".[smolvla]"
```

### Finetune the pretrained model
사전학습된 450M 모델 [`smolvla_base`](https://hf.co/lerobot/smolvla_base)를 lerobot 학습 프레임워크와 함께 사용합니다:

```python
python lerobot/scripts/train.py \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=lerobot/svla_so100_stacking \
  --batch_size=64 \
  --steps=20000  # 학습 예산의 10%
```
### Train from scratch
사전학습된 체크포인트를 사용하지 않고, 아키텍처(사전학습된 VLM + action expert)부터 직접 학습하고 싶다면 다음과 같이 실행할 수 있습니다:

```python
python lerobot/scripts/train.py \
  --policy.type=smolvla \
  --dataset.repo_id=lerobot/svla_so100_stacking \
  --batch_size=64 \
  --steps=200000
```
또한 SmolVLAPolicy를 직접 불러와 사용할 수도 있습니다:

```python
from lerobot.common.policies.smolvla.modeling_smolvla import SmolVLAPolicy
policy = SmolVLAPolicy.from_pretrained("lerobot/smolvla_base")
```

## Method
SmolVLA는 가볍지만 성능이 뛰어난 모델일 뿐만 아니라, 범용 로봇 정책을 학습하고 평가하기 위한 하나의 방법론이기도 합니다. 이 섹션에서는 SmolVLA의 **모델 아키텍처**와, 평가 과정에서 사용된 **비동기 추론(asynchronous inference)** 설정을 소개합니다. 이 설정은 더 높은 적응성과 빠른 복구 능력을 보여주는 것으로 확인되었습니다.

SmolVLA는 두 가지 핵심 구성 요소로 이루어져 있습니다. 하나는 멀티모달 입력을 처리하는 **Vision-Language Model (VLM)**이고, 다른 하나는 로봇 제어 명령을 출력하는 **action expert**입니다. 아래에서는 SmolVLA 아키텍처의 주요 구성 요소와 비동기 추론에 대한 세부 내용을 설명합니다. 더 자세한 내용은 [기술 리포트](https://huggingface.co/papers/2506.01844)를 참고하세요.

### Main Architecture
#### Vision-Language Model (VLM)

Vision-Language Model (VLM)
SmolVLA는 VLM 백본으로 [SmolVLM2](https://huggingface.co/HuggingFaceTB/SmolVLM2-500M-Video-Instruct)를 사용합니다. 이 모델은 다중 이미지 입력에 최적화되어 있으며, SigLIP 비전 인코더와 [SmolLM2](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct) 언어 디코더로 구성됩니다.
- 비전 인코더를 통해 **이미지 토큰(image tokens)**을 추출합니다.
- **자연어 지시(language instructions)**는 토큰화되어 디코더에 직접 입력됩니다.
- **센서모터 상태(sensorimotor states)**는 선형 레이어를 통해 단일 토큰으로 투영되어, 언어 모델의 토큰 차원과 정렬됩니다.

디코더 레이어는 이미지, 언어, 상태 토큰을 이어붙인(concatenated) 입력을 처리합니다. 이렇게 생성된 특징은 이후 action expert로 전달됩니다.

#### Action Expert: Flow Matching Transformer

SmolVLA의 **action expert**는 약 1억(100M) 파라미터 규모의 소형 Transformer로, VLM의 출력에 조건화되어 미래 로봇 행동 시퀀스, 즉 action chunk를 생성합니다. 이 모듈은 **flow matching 목적 함수**를 사용해 학습되며, 노이즈가 섞인 샘플을 정답(ground truth)으로 되돌리도록 모델을 학습시킵니다. 반면, 토큰화와 같은 이산(discrete) 행동 표현은 표현력은 뛰어나지만, 보통 자기회귀(autoregressive) 디코딩을 필요로 해 추론 시 느리고 비효율적인 경우가 많습니다. 이에 비해 flow matching은 **연속적인 행동을 직접, 비자기회귀적으로 예측**할 수 있어, 높은 정밀도의 실시간 제어를 가능하게 합니다.

보다 직관적으로 설명하면, 학습 과정에서 로봇의 실제 행동 시퀀스에 임의의 노이즈를 추가한 뒤, 모델이 이를 올바른 궤적으로 되돌리는 “보정 벡터(correction vector)”를 예측하도록 합니다. 이 과정은 행동 공간 전반에 걸쳐 매끄러운 벡터 필드를 형성하며, 모델이 정확하고 안정적인 제어 정책을 학습하는 데 도움을 줍니다.

이러한 접근은 **교차 배치된(interleaved) 어텐션 블록**을 사용하는 Transformer 아키텍처(figure 2 참고)로 구현되었으며, 배포 효율성을 고려해 hidden size를 **VLM의 75% 수준**으로 줄여 모델을 경량화했습니다.

### Design Choices for Efficiency and Robustness

최근의 VLA 시스템들—예를 들어 Pi0, GR00T, Diffusion Policy—에서는 vision-language 모델과 행동 예측 모듈을 결합하는 설계가 일반적입니다. 하지만 우리는 그중에서도 강건성과 성능을 크게 향상시키는 몇 가지 아키텍처 선택지를 확인했습니다. SmolVLA에서는 다음의 세 가지 핵심 기법을 적용합니다: **시각 토큰 수 축소, VLM 상위 레이어 스킵**, 그리고 action expert 내부에서의 **cross-attention과 self-attention 레이어 교차 배치**입니다.

#### Visual Token Reduction

고해상도 이미지는 지각 성능을 높여 주지만, 추론 속도를 크게 저하시킬 수 있습니다. 이러한 균형을 맞추기 위해 **SmolVLA는 학습과 추론 모두에서 프레임당 시각 토큰 수를 64개로 제한**합니다. 예를 들어 512×512 이미지는 효율적인 셔플링 기법인 **PixelShuffle**을 사용해, **기존의 1024 토큰 대신 64 토큰**으로 압축됩니다. 비록 기본 Vision-Language Model(VLM)은 더 넓은 시각적 커버리지를 위해 이미지 타일링 방식으로 사전학습되었지만, **SmolVLA는 실제 추론 시 전역 이미지(global image)만 사용**하여 모델을 가볍고 빠르게 유지합니다.

#### Faster Inference via Layer Skipping

항상 VLM의 최종 레이어에 의존하는 방식은 연산 비용이 크고, 경우에 따라 최적의 선택이 아닐 수 있습니다. 이에 따라 SmolVLA는 **중간 레이어(intermediate layers)의 특징(feature)**을 활용합니다. 기존 연구에 따르면, 초기 또는 중간 레이어가 다운스트림 작업에 더 유용한 표현을 제공하는 경우도 많습니다.
SmolVLA에서는 학습 시 action expert가 주의(attend)할 VLM 특징을 설정 가능한 N번째 레이어까지로 제한하며, 기본값은 **전체 레이어의 절반**입니다. 이를 통해 VLM과 action expert 모두의 **연산 비용을 절반으로 줄일 수 있으며**, 성능 저하를 최소화한 상태에서 추론 속도를 크게 향상시킵니다.

#### Interleaved Cross and Self-Attention

action expert 내부에서는 어텐션 레이어가 다음 두 가지 형태로 번갈아 배치됩니다.
- **Cross-attention (CA)**: action 토큰이 VLM에서 생성된 특징에 어텐션을 수행
- **Self-attention (SA)**: action 토큰끼리 서로 어텐션을 수행하며, 인과적(causal) 구조로 과거 정보만을 참조

우리는 이러한 **교차(interleaved) 설계**가 전체 어텐션 블록(full attention blocks)을 사용하는 방식보다 더 가볍고 효과적임을 확인했습니다. CA만 또는 SA만 사용하는 모델은 각각 행동의 부드러움(smoothness)이나 지각·지시와의 정합성(grounding) 중 하나를 희생하는 경향이 있습니다.

SmolVLA에서 CA는 행동이 시각 정보와 자연어 지시에 잘 조건화되도록 보장하며, SA는 **시간적 부드러움(temporal smoothness)**을 향상시킵니다. 이는 특히 실제 로봇 제어 환경에서 매우 중요한 요소로, 예측이 흔들리거나(jittery) 불안정할 경우 위험하거나 비안정적인 동작으로 이어질 수 있습니다.

## Asynchronous Inference

<div align="center">
  <img src="https://cdn-uploads.huggingface.co/production/uploads/640e21ef3c82bd463ee5a76d/IV6vxVHCxUuYMEc7otXtv.png" alt="Asynchronous inference" width="500"/>
  <p>Figure 3. 비동기 추론. 비동기 추론 스택의 개념도입니다. 정책은 GPU가 장착된 원격 서버에서 실행될 수도 있습니다.</p>
</div>

현대의 시각-운동(visuomotor) 정책은 **action chunk**—즉, 실행할 행동들의 시퀀스—를 출력합니다. 이를 관리하는 방식에는 두 가지가 있습니다.
- **동기(synchronous, sync)**: 로봇이 하나의 chunk를 실행한 뒤, 다음 chunk가 계산될 때까지 멈춥니다. 구현은 단순하지만, 이 동안 로봇은 새로운 입력에 반응할 수 없는 지연이 발생합니다.
- **비동기(asynchronous, async)**: 현재 chunk를 실행하는 동안에도 로봇은 최신 관측을 **Policy Server**(GPU에서 호스팅될 수 있음)로 전송해 다음 chunk를 미리 계산합니다. 이를 통해 유휴 시간을 없애고 반응성을 크게 향상시킬 수 있습니다.

우리의 비동기(async) 스택은 행동 실행과 chunk 예측을 분리(decouple)함으로써, 더 높은 적응성과 함께 런타임에서 실행 지연이 전혀 없는 동작을 가능하게 합니다. 이는 다음과 같은 핵심 메커니즘에 기반합니다.
- **1. Early trigger:** 큐 길이가 임계값(예: 70%) 아래로 떨어지면, 관측을 **Policy Server**로 보내 새로운 action chunk 생성을 요청합니다.
- **2. Decoupled threads:** 제어 루프는 계속 실행되고, 추론은 병렬로(논블로킹 방식으로) 수행됩니다.
- **3. Chunk fusion:** 연속된 chunk 간에 겹치는 행동을 단순한 병합 규칙으로 이어 붙여, 지터(jitter)를 방지합니다.

모델을 변경하지 않고도 더 높은 적응성과 향상된 성능을 보장한다는 점에서, 우리는 비동기 추론을 공개하게 되어 매우 기대하고 있습니다. 요약하면, 비동기 추론은 행동 실행과 원격 예측을 겹쳐 수행함으로써 로봇이 항상 높은 반응성을 유지하도록 합니다.

## Community Datasets

비전과 언어 모델이 LAION, ImageNet, Common Crawl과 같은 웹 스케일 데이터셋을 기반으로 성장해 온 것과 달리, 로보틱스에는 이에 상응하는 자원이 부족합니다. 이른바 “로봇의 인터넷(Internet of robots)”은 아직 존재하지 않습니다. 대신 데이터는 로봇 종류, 센서, 제어 방식, 포맷에 따라 파편화되어 서로 단절된 “데이터 섬(data islands)”을 형성하고 있습니다. 우리는 [이전 글](https://huggingface.co/blog/lerobot-datasets)에서 이러한 파편화를 개방적이고 협업적인 노력을 통해 어떻게 해소할 수 있는지를 살펴본 바 있습니다. ImageNet이 크고 다양한 벤치마크를 제공함으로써 컴퓨터 비전 분야의 도약을 이끌었듯이, 우리는 **커뮤니티 주도 로보틱스 데이터셋**이 범용 로봇 정책을 위한 동일한 기초 역할을 할 수 있다고 믿습니다.

**SmolVLA는 이러한 비전을 향한 첫걸음입니다.** SmolVLA는 실제 세계의 다양성을 반영하도록 설계된, 공개되고 커뮤니티가 기여한 데이터셋을 엄선해 사전학습되었습니다. 데이터셋의 크기만을 단순히 키우는 대신, 전이(transfer)와 일반화(generalization)를 촉진하는 다양성—즉, 다양한 행동 유형, 카메라 시점, 그리고 서로 다른 로봇 형태(embodiment)—에 초점을 맞추었습니다.

SmolVLA에 사용된 모든 학습 데이터는 Hugging Face Hub에서 `lerobot` 태그 아래 공유된 로보틱스 데이터셋인 **LeRobot Community Datasets**에서 비롯됩니다. 연구실부터 거실에 이르기까지 다양한 환경에서 수집된 이 데이터셋들은, 실제 로봇 데이터를 대규모로 확장하려는 개방적이고 분산된 노력을 대표합니다.

<p align="center">
  <img src="https://cdn-uploads.huggingface.co/production/uploads/640e21ef3c82bd463ee5a76d/V4QU-B-6YBONb-8K_lSpj.gif" alt="A glimpse of the community dataset." width="500"/>
  <br/>
  <em>Figure 4. 커뮤니티 데이터셋의 한 장면. 시각화를 제작해준 Ville Kuosmanen에게 특별한 감사를 전합니다.
학술 벤치마크와 달리, 커뮤니티 데이터셋은 다양한 조명 조건, 완벽하지 않은 시연, 비정형적인 물체, 그리고 이질적인 제어 방식 등 ‘지저분하지만 현실적인’ 상호작용을 자연스럽게 담고 있습니다. 이러한 다양성은 강건하고 범용적인 표현을 학습하는 데 매우 유용합니다.</em>
</p>


우리는 [Alexandre Chapin](https://huggingface.co/Beegbrain)과 [Ville Kuosmanen](https://huggingface.co/villekuosmanen)이 제작한 커스텀 [필터링 도구](https://huggingface.co/spaces/Beegbrain/FilterLeRobotData)를 사용해, 프레임 수, 시각적 품질, 작업 커버리지를 기준으로 데이터셋을 선별했습니다. 이후 세심한 수작업 검토 과정을 거쳐(특별히 Marina Barannikov에게 감사를 전합니다), **SO100 로봇 팔**에 초점을 맞춘 **487개의 고품질 데이터셋**을 큐레이션했으며, 이를 **30 FPS**로 표준화했습니다. 그 결과 약 **1천만 프레임** 규모의 데이터가 구축되었는데, 이는 다른 인기 벤치마크 데이터셋에 비해 **최소 한 자릿수(10배) 이상 작은 규모**이지만, 훨씬 더 높은 다양성을 갖습니다.

### Improving Task Annotations
 
커뮤니티 데이터셋 전반에서 공통적으로 나타난 문제는 작업 설명이 노이즈가 많거나 누락되어 있다는 점이었습니다. 많은 에피소드에 주석이 없거나, “task desc”, “Move”, “Pick”과 같은 모호한 라벨만 포함된 경우가 많았습니다. 이러한 품질 문제를 개선하고 데이터셋 전반의 텍스트 입력을 표준화하기 위해, 우리는 [Qwen2.5-VL-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)를 활용해 간결하고 행동 중심적인 작업 설명을 생성했습니다.

샘플 프레임과 기존 라벨을 입력으로 제공한 뒤, 30자 이내이면서 동사로 시작하는(예: “Pick”, “Place”, “Open”) 지시문으로 작업 설명을 다시 작성하도록 모델을 프롬프트했습니다.

사용한 프롬프트는 다음과 같습니다:

```
Here is a current task description: {current_task}. Generate a very short, clear, and complete one-sentence describing the action performed by the robot arm (max 30 characters). Do not include unnecessary words.
Be concise.
Here are some examples: Pick up the cube and place it in the box, open the drawer and so on.
Start directly with an action verb like “Pick”, “Place”, “Open”, etc.
Similar to the provided examples, what is the main action done by the robot arm?
```

### Standardizing Camera Views
   
또 다른 과제는 카메라 이름이 일관되지 않다는 것입니다. 일부 데이터셋은 top이나 `wrist.right`처럼 명확한 이름을 사용한 반면, `images.laptop`과 같이 의미가 상황에 따라 달라질 수 있는 모호한 라벨을 사용하는 경우도 있었습니다.
이를 해결하기 위해 우리는 데이터셋을 수작업으로 검토하며 각 카메라 뷰를 다음과 같은 표준 스킴으로 매핑했습니다.
`OBS_IMAGE_1`: 상단(Top-down) 뷰
`OBS_IMAGE_2`: 손목(Wrist-mounted) 뷰
`OBS_IMAGE_3+`: 추가 시점

또한 커뮤니티 데이터셋 사전학습과 멀티태스크 파인튜닝의 기여도를 분리해 분석했습니다. LeRobot 커뮤니티 데이터셋으로 사전학습을 수행하지 않았을 때, SmolVLA는 SO100 환경에서 **51.7%**의 성공률을 보였습니다. 그러나 커뮤니티 수집 데이터로 사전학습을 수행한 후에는 성능이 **78.3%**로 상승했으며, 이는 **절대 기준 +26.6%의 향상**에 해당합니다. 여기에 멀티태스크 파인튜닝을 적용하면 성능이 추가로 개선되며, 적은 데이터 환경에서도 강력한 작업 전이 능력을 보여줍니다.

<div align="center">
  <img src="https://cdn-uploads.huggingface.co/production/uploads/640e21ef3c82bd463ee5a76d/GdKdSzT2oAt83MQ0lPjcY.png" width="500"/>
  <p> Table 1. 커뮤니티 데이터셋 사전학습 및 멀티태스크 파인튜닝의 효과.</p>
</div>

## Results
우리는 SmolVLA의 일반화 성능, 효율성, 강건성을 평가하기 위해 시뮬레이션과 실제 환경 벤치마크 전반에서 실험을 수행했습니다. 모델 규모가 작음에도 불구하고, SmolVLA는 더 대규모 로보틱스 데이터로 사전학습된 정책이나 훨씬 큰 모델들과 비교해도 일관되게 더 뛰어나거나 동등한 성능을 보여줍니다.

<div align="center">
  <img src="https://cdn-uploads.huggingface.co/production/uploads/640e21ef3c82bd463ee5a76d/_v01LDKSy8zgcYr_7yQMx.png" alt="SmolVLA Performance on Simulation Benchmarks." width="500"/>
  <p> Table 2. 시뮬레이션 벤치마크에서의 SmolVLA 성능.</p>
</div>


<div align="center">
  <img src="https://cdn-uploads.huggingface.co/production/uploads/640e21ef3c82bd463ee5a76d/ahQpohnpqRw6sQFMzjmg4.png" alt="SmolVLA vs Baselines on Real-World Tasks (SO100)." width="500"/>
  <p> Table 3. 실제 과제(SO100)에서 SmolVLA와 베이스라인 비교.</p>
</div>

실제 환경에서는 SmolVLA를 SO100과 SO101, 두 가지로 구성된 다양한 작업 스위트(suite)에서 평가합니다. 이 작업들은 픽-앤-플레이스, 쌓기(stacking), 분류(sorting)를 포함하며, 분포 내(in-distribution) 및 분포 외(out-of-distribution) 객체 구성 모두를 다룹니다.
SO101 환경에서도 SmolVLA는 뛰어난 일반화 성능을 보여줍니다.

<div align="center">
  <img src="https://cdn-uploads.huggingface.co/production/uploads/640e21ef3c82bd463ee5a76d/MZuG6UzXZ1SJ1MOfUfyzb.png" alt="Generalization of SmolVLA to New Embodiment (SO101) vs ACT.." width="500"/>
  <p>Table 4. 새로운 로봇 형태(SO101)에 대한 SmolVLA의 일반화 성능 vs ACT.</p>
</div>

마지막으로, SmolVLA를 동기(synchronous) 및 비동기(asynchronous) 추론 모드에서 평가했습니다. 비동기 추론은 행동 실행과 모델 추론을 분리(decouple)함으로써, 로봇이 움직이는 동안에도 정책이 즉각적으로 반응할 수 있도록 합니다.
- 두 모드 모두 유사한 작업 성공률(≈78%)을 보이지만, 비동기 추론은:
  * 작업을 **약 30% 더 빠르게** 완료합니다 (9.7초 vs. 13.75초)
  * 고정된 시간 설정에서 **2배 더 많은 작업 완료**를 가능하게 합니다 (큐브 19개 vs. 9개)

이는 특히 물체가 이동하거나 외부 교란이 발생하는 동적 환경에서, 실제 로봇이 더 민첩하고 안정적으로 동작하도록 만들어 줍니다.
<div align="center">
  <img src="https://cdn-uploads.huggingface.co/production/uploads/640e21ef3c82bd463ee5a76d/Goxb9y5cE_Ty1SWCetCoT.png" alt="Asynchronous vs. Synchronous Inference in Real-World Tasks." width="500"/>
  <p>Figure 5. 실제 환경 과제에서의 비동기 vs 동기 추론 비교.
(a) 작업 성공률(%), (b) 평균 완료 시간(초), (c) 고정 시간 창 내 완료된 작업 수.
</p>
</div>


## Conclusion

SmolVLA는 개방적이고, 효율적이며, 재현 가능한 로보틱스 파운데이션 모델을 구축하기 위한 우리의 기여입니다. 작은 모델 크기에도 불구하고, SmolVLA는 다양한 실제 환경 및 시뮬레이션 과제에서 더 크고 독점적인 모델들과 동등하거나 이를 능가하는 성능을 보여줍니다. 커뮤니티가 기여한 데이터셋과 저렴한 하드웨어에만 의존함으로써, SmolVLA는 연구자, 교육자, 그리고 취미 개발자에 이르기까지 모두의 진입 장벽을 낮춥니다.
하지만 이는 시작에 불과합니다. SmolVLA는 단순한 하나의 모델이 아니라, 확장 가능하고 협업적인 로보틱스를 향한 오픈소스 움직임의 일부입니다.

## Call to Action:

- 🔧 **직접 사용해보세요!** SmolVLA를 여러분의 데이터로 파인튜닝하고, 저렴한 하드웨어에 배포하거나, 현재 사용 중인 스택과 비교 평가한 뒤 Twitter/LinkedIn에 공유해 주세요.
- 🤖 **데이터셋을 업로드하세요!** 로봇이 있나요? lerobot 포맷을 사용해 데이터를 수집하고 공유해 주세요. SmolVLA를 구동하는 커뮤니티 데이터셋 확장에 기여할 수 있습니다.
- 💬 **블로그 토론에 참여하세요.** 아래 토론에서 질문, 아이디어, 피드백을 남겨 주세요. 통합, 학습, 배포와 관련해 기꺼이 도와드리겠습니다.
- 📊 **기여하세요.** 데이터셋을 개선하고, 이슈를 보고하거나, 새로운 아이디어를 제안해 주세요. 모든 기여는 큰 도움이 됩니다.
- 🌍 **널리 알려주세요.** 효율적인 실시간 로봇 정책에 관심 있는 연구자, 개발자, 교육자들과 SmolVLA를 공유해 주세요.
- 📫 **소식 받기:** [LeRobot 조직](https://huggingface.co/lerobot)과 [Discord 서버](https://discord.com/invite/ttk5CV6tUw)를 팔로우해 업데이트, 튜토리얼, 신규 릴리스를 받아보세요.

함께라면, 실세계 로보틱스를 더 유능하고, 더 저렴하며, 더 개방적으로 만들어갈 수 있습니다. ✨

```

### real/2025-12-28-translation-mcp-project-overview.md

```markdown
---
layout: post
title: "Hugging Face 번역 MCP 서버 총정리" 
author: minju
categories: [Robotics, AI, Community]
image: assets/images/blog/posts/2025-12-28-translation-mcp-project-overview/thumbnail.png
---
* TOC
{:toc}
<!--toc-->
_이 글은 Hugging Face 문서 번역 프로젝트의 MCP server 소개글입니다._

---

## 들어가기 전

이 글은 Hugging Face 번역 MCP 서버 프로젝트의 글들과 함께 읽으시면 좋습니다.

현서님께서 MCP 서버 전략 및 개발 도구 선정 과정을 소개해주셨어요. 
👉 [MCP 서버 설계 전략 및 개발 도구 선정](https://hugging-face-krew.github.io/hf_translation_hub_mcp_design_and_tooling/)

그리고 각 MCP 서버의 사용법도 소개해주셨습니다.
👉 [HuggingFace 번역 MCP 서버 사용법](https://hugging-face-krew.github.io/hf-translation-hub-mcp-server-usage-guide/)

---

## MCP server 배포 완료 🎉

프로젝트를 기획할 당시에 설계했던 3개의 MCP server와 현서님께서 추가해주신 PR 리뷰 MCP server까지 총 **4개의 MCP server**들의 배포가 완료되었습니다!

허깅페이스 스페이스에 각각 배포를 완료하였고, Hugging Face Chat, Claude Desktop, Gemini CLI에 MCP server를 연결하고 테스트를 진행하였어요.

이 글에서는 각 MCP server 안에 등록된 tool들과 각 tool들에 대한 설명을 소개드리려고 합니다.

번역할 문서 검색, 문서 번역, 번역 PR 등록, 번역 PR 리뷰의 총 4가지 MCP server를 차례대로 살펴보겠습니다.

![mcp-list](../assets/images/blog/posts/2025-12-28-translation-mcp-project-overview/mcp_list.png)

---

## Hugging Face MCP 서버와 도구 소개

우리 팀은 번역 문서 관리와 PR 자동화, 리뷰를 위해 총 4개의 Hugging Face MCP 서버를 운영하고 있습니다.

각 서버는 특화된 도구들을 제공하여 번역 작업의 검색, 생성, 관리, 리뷰를 자동화할 수 있습니다.

아래에서 각 서버와 그 안의 도구들을 자세히 소개합니다.

---

## 1️⃣ hf-translation-docs-explorer

### 개요
- **주요 역할:** 번역 프로젝트 및 문서 탐색, 상태 확인
- **URL:** `https://hyeonseo-hf-translation-docs-explorer.hf.space/gradio_api/mcp/`

### 설명
이 서버는 번역해야 할 문서 파일을 찾고, 누락되거나 오래된 파일을 확인하는 데 특화되어 있습니다. 사용자는 프로젝트별로 번역 진행 상태를 쉽게 파악할 수 있습니다.

예를 들어, `transformers` 프로젝트의 한국어 번역에서 어떤 파일이 아직 번역되지 않았는지, 어떤 파일이 원본 대비 오래되어 업데이트가 필요한지 한눈에 확인할 수 있어요.

### 🛠️ 도구 목록

| Tool 이름 | 설명 | 입력 파라미터 |
|-----------|------|---------------|
| `hf_translation_docs_explorer_list_projects` | 번역 프로젝트 목록 조회 | 없음 |
| `hf_translation_docs_explorer_search_files` | 특정 프로젝트/언어의 파일 검색 | `project` (`smolagents`, `transformers`)<br/>`lang` (`ko`, `ja`, `zh`, `fr`, `de`)<br/>`limit`<br/>`include_status_report` |
| `hf_translation_docs_explorer_list_missing_files` | 누락된 번역 파일 목록 조회 | `project`<br/>`lang`<br/>`limit` |
| `hf_translation_docs_explorer_list_outdated_files` | 오래된 번역 파일 목록 조회 | `project`<br/>`lang`<br/>`limit` |

**지원하는 프로젝트:** `smolagents`, `transformers`  
**지원하는 언어:** `ko` (한국어), `ja` (일본어), `zh` (중국어), `fr` (프랑스어), `de` (독일어)

---

## 2️⃣ hf-translation-docs

### 개요
- **주요 역할:** 번역 문서 처리 전체 파이프라인
- **URL:** `https://jmj-minju-hf-translation-docs.hf.space/gradio_api/mcp/`

### 설명
문서 번역 과정 전체를 다루는 핵심 서버입니다. 번역 파일 검색부터 내용 조회, 번역 프롬프트 생성, 품질 검증, 결과 저장까지 모든 단계를 지원합니다.

이 서버를 통해 번역 워크플로우를 일관성 있게 관리할 수 있습니다. 특히 번역 프롬프트 생성 기능은 번역자가 일관된 스타일과 품질로 번역할 수 있도록 도와주며, 검증 기능은 번역 결과가 원본 포맷을 유지하고 있는지 자동으로 확인해줍니다.

### 🛠️ 도구 목록

| Tool 이름 | 설명 | 입력 파라미터 |
|-----------|------|---------------|
| `hf_translation_docs_get_project_config` | 프로젝트 설정 정보 조회 | `project` |
| `hf_translation_docs_search_translation_files` | 번역이 필요한 파일 검색 | `project`<br/>`target_language`<br/>`max_files` |
| `hf_translation_docs_get_file_content` | 특정 파일 내용 조회 | `project`<br/>`file_path`<br/>`include_metadata` |
| `hf_translation_docs_generate_translation_prompt` | 번역 프롬프트 생성 | `target_language`<br/>`content`<br/>`additional_instruction`<br/>`project`<br/>`file_path` |
| `hf_translation_docs_validate_translation` | 번역 품질/포맷 검증 | `original_content`<br/>`translated_content`<br/>`target_language`<br/>`file_path` |
| `hf_translation_docs_save_translation_result` | 번역 결과 저장 | `project`<br/>`original_file_path`<br/>`translated_content`<br/>`target_language` |

이 서버는 번역 작업의 중심축 역할을 하며, 번역의 시작부터 끝까지 모든 과정을 체계적으로 관리할 수 있게 해줍니다.

---

## 3️⃣ hf-translation-pr-generator

### 개요
- **주요 역할:** 번역 PR(Pull Request) 자동 생성
- **URL:** `https://jmj-minju-hf-translation-pr-generator.hf.space/gradio_api/mcp/`

### 설명
번역 작업을 PR 형태로 GitHub에 자동 생성하고 관리하는 서버입니다. 

번역이 완료되면 수동으로 GitHub에 접속해서 PR을 생성하는 것이 아니라, 이 서버를 통해 자동으로 PR을 생성할 수 있어요. PR 생성 전 설정 검증, 참조 PR 검색, 번역 분석, PR 초안 생성, 최종 PR 생성까지 일련의 과정을 모두 지원합니다.

특히 참조 PR 검색 기능은 이전에 승인된 번역 PR들을 참고하여 일관성 있는 번역 스타일을 유지할 수 있도록 도와줍니다.

### 🛠️ 도구 목록

| Tool 이름 | 설명 | 입력 파라미터 |
|-----------|------|---------------|
| `hf_translation_pr_generator_validate_pr_config_ui` | PR 생성 설정 검증 (UI) | `github_token`<br/>`owner`<br/>`repo_name`<br/>`project` |
| `hf_translation_pr_generator_search_reference_pr` | 참조용 PR 검색 | `target_language`<br/>`context` |
| `hf_translation_pr_generator_analyze_translation` | 번역 내용 분석 및 메타데이터 생성 | `filepath`<br/>`translated_content`<br/>`target_language`<br/>`project` |
| `hf_translation_pr_generator_generate_pr_draft` | PR 초안/메타데이터 생성 | `filepath`<br/>`translated_content`<br/>`target_language`<br/>`reference_pr_url`<br/>`project` |
| `hf_translation_pr_generator_create_github_pr` | GitHub PR 생성 | `github_token`<br/>`owner`<br/>`repo_name`<br/>`filepath`<br/>`translated_content`<br/>`target_language`<br/>`reference_pr_url`<br/>`project` |

이 서버를 사용하면 번역 작업이 끝난 후 PR 생성에 들어가는 시간과 노력을 크게 줄일 수 있습니다.

---

## 4️⃣ hf-translation-reviewer

### 개요
- **주요 역할:** 번역 리뷰 및 피드백 자동화
- **URL:** `https://hyeonseo-hf-translation-reviewer.hf.space/gradio_api/mcp/`

### 설명
번역 PR을 검토하고 피드백을 생성하는 자동화 서버입니다.

리뷰 준비, 응답/피드백 생성, 제출, 엔드투엔드 리뷰 등 모든 과정을 자동화할 수 있어 리뷰 업무의 부담을 크게 줄여줍니다. 특히 `e2e_proxy` 도구를 사용하면 리뷰 준비부터 피드백 생성, 제출까지 전 과정을 한 번에 실행할 수 있어요.

리뷰어는 이 서버가 생성한 피드백을 바탕으로 최종 검토만 하면 되기 때문에, 리뷰 시간을 대폭 단축할 수 있습니다.

### 🛠️ 도구 목록

| Tool 이름 | 설명 | 입력 파라미터 |
|-----------|------|---------------|
| `hf_translation_reviewer__prepare_proxy` | 리뷰 준비 (프록시) | `pr_url_`<br/>`original_path_`<br/>`translated_path_` |
| `hf_translation_reviewer__review_emit_proxy` | 검토 응답/피드백 생성 | `pr_url_`<br/>`translated_path_`<br/>`translated_text_`<br/>`raw_response_` |
| `hf_translation_reviewer__submit_proxy` | 리뷰 제출 (프록시) | `pr_url_`<br/>`translated_path_`<br/>`payload_json_` |
| `hf_translation_reviewer__e2e_proxy` | 엔드투엔드 리뷰 및 제출 | `pr_url_`<br/>`original_path_`<br/>`translated_path_`<br/>`save_review_`<br/>`save_path_`<br/>`submit_flag_`<br/>`e2e_raw_response_` |

---

## 🔹 전체 워크플로우 요약

4개의 MCP 서버가 어떻게 연결되어 작동하는지 살펴볼까요?

### 단계별 프로세스

1. **hf-translation-docs-explorer** → 번역할 문서 탐색 및 상태 확인
   - 프로젝트에서 번역이 필요한 파일들을 찾습니다
   - 누락되거나 오래된 파일들을 확인합니다

2. **hf-translation-docs** → 파일 조회, 번역 생성, 검증, 저장
   - 파일 내용을 가져옵니다
   - 번역 프롬프트를 생성합니다
   - 번역 결과를 검증하고 저장합니다

3. **hf-translation-pr-generator** → GitHub PR 생성 및 관리
   - 번역 내용을 분석합니다
   - PR 초안을 생성합니다
   - GitHub에 PR을 자동으로 생성합니다

4. **hf-translation-reviewer** → PR 리뷰 및 제출 자동화
   - PR을 검토합니다
   - 자동으로 피드백을 생성합니다
   - 리뷰를 제출합니다

### 시퀀스 다이어그램

![mcp-list](../assets/images/blog/posts/2025-12-28-translation-mcp-project-overview/image.png)


이 4개의 MCP 서버를 연계하면 **번역 문서 관리 → PR 생성 → 리뷰 제출**까지 완전한 자동화 워크플로우를 구축할 수 있습니다.

![mcp-list](../assets/images/blog/posts/2025-12-28-translation-mcp-project-overview/image2.png)

예를 들어, Hugging Face chat에 mcp server를 연결한 모습입니다.

---

## 💭 고민거리

프로젝트를 진행하면서 가장 큰 고민은 역시 **LLM 모델 사용 비용**입니다.

Tool 사용이 가능하고 tool 선택을 잘 하는 모델은 Claude나 Gemini 같은 상용 모델들이에요. 이런 모델들을 사용하면 MCP 서버와의 연동이 매우 원활하고 정확합니다.

하지만 프로젝트를 장기적으로 운영하려면 비용 문제를 고려하지 않을 수 없어요. 현재는 각 모델들의 무료 사용량 범위 내에서 테스트를 진행하고 있지만, 앞으로는 오픈소스 모델 중에서도 좋은 성능을 내는 모델을 찾아 활용하는 노력이 필요할 것 같습니다.

---

## 마치며

Hugging Face 번역 MCP 서버 프로젝트는 번역 작업의 전 과정을 자동화하여 효율성을 크게 높일 수 있는 시스템입니다.

4개의 서버가 각자의 역할을 충실히 수행하면서도 유기적으로 연결되어 하나의 완전한 워크플로우를 만들어내는 것이 이 프로젝트의 핵심이에요.

앞으로도 계속해서 개선하고 발전시켜 나갈 예정이니, 많은 관심 부탁드립니다! 🚀

---

### 📚 관련 자료

- [MCP 서버 설계 전략 및 개발 도구 선정](https://hugging-face-krew.github.io/hf_translation_hub_mcp_design_and_tooling/)
- [HuggingFace 번역 MCP 서버 사용법](https://hugging-face-krew.github.io/hf-translation-hub-mcp-server-usage-guide/)
```

### real/2026-01-05-hf-translation-mcp-n8n.md

```markdown
---
layout: post
title: "n8n으로 번역 MCP Server 워크플로우 구축하기: 실전 트러블슈팅과 실행 방식 비교" 
author: minju
categories: [Robotics, AI, Community]
image: assets/images/blog/posts/2026-01-05-hf-translation-mcp-n8n/meme.jpg
---
* TOC
{:toc}
<!--toc-->
_이 글은 Hugging Face 문서 번역 프로젝트의 MCP Server를 활용한 n8n 워크플로우 구축 경험을 담은 글입니다._

---

## 들어가며

MCP(Model Context Protocol) Server를 활용한 번역 워크플로우를 구축하면서, Claude Desktop Client로 직접 실행하는 방식과 n8n을 통한 워크플로우 자동화 방식을 모두 경험해보았습니다. 이 글에서는 n8n 워크플로우 구축 과정에서 마주친 실질적인 문제들과 해결 방법, 그리고 두 실행 방식의 장단점을 정리해보겠습니다.

## n8n 번역 MCP Server 워크플로우 소개

이번에 구축한 워크플로우는 Gradio 기반의 번역 MCP Server를 n8n과 연동하여, 텍스트를 자동으로 번역하고 PR을 등록하는 시스템입니다. 

**주요 구성 요소:**
- **Gradio MCP Server**: 번역 기능을 MCP Tool로 제공
- **n8n Workflow**: AI Agent를 통해 번역 작업을 오케스트레이션
- **GitHub Integration**: 번역 결과를 자동으로 문서화하고 PR 업로드

**기본 워크플로우:**
1. 번역할 텍스트 검색
2. n8n AI Agent가 MCP Server의 번역 Tool 호출
3. 번역 결과를 GitHub PR로 자동 저장

## n8n 워크플로우 구축 결과

초안으로 구축한 n8n 워크플로우를 먼저 보여드리겠습니다.

### 번역 워크플로우
AI Agent와 AWS Bedrock Chat Model을 사용하여 Claude 모델을 연결하였습니다. 이 AI Agent는 번역 문서 검색 MCP Server와 번역 MCP Server가 Tool로 연결되어 있습니다. 따라서 번역할 문서를 검색하고 번역 결과물을 Notion 페이지로 저장하는 워크플로우입니다. 

<div align="center">
    <img src="../assets/images/blog/posts/2026-01-05-hf-translation-mcp-n8n/translate.png" 
         width="500"
         alt="번역 워크플로우 구조"/>
    <p><em>번역 문서 검색 및 Notion 저장 워크플로우</em></p>
</div>

### 번역 워크플로우 결과물
초기에 Notion을 사용했던 이유는, Notion에서 번역 결과물이 저장된 이후, 사람이 편집하기 쉬운 UI를 가지고 있기 때문이었습니다. 이후에 Notion Tool을 사용하지 않게 되었는데, 트러블슈팅 섹션에서 이유를 말씀드리겠습니다.

<div align="center">
    <img src="../assets/images/blog/posts/2026-01-05-hf-translation-mcp-n8n/translation_result.png" 
         width="500"
         alt="Notion에 저장된 번역 결과"/>
    <p><em>Notion 페이지에 저장된 번역 결과물</em></p>
</div>

### GitHub PR 워크플로우
AI Agent와 Notion Tool 및 PR 업로드 MCP Server가 연결되어 있습니다. 앞 단계인 번역 워크플로우가 실행된 이후, Notion 데이터베이스에서 번역 결과물을 받아와서 PR로 업로드를 자동화해줍니다.

<div align="center">
    <img src="../assets/images/blog/posts/2026-01-05-hf-translation-mcp-n8n/pr_upload.png" 
         width="500"
         alt="GitHub PR 업로드 워크플로우"/>
    <p><em>번역 결과를 GitHub PR로 업로드하는 워크플로우</em></p>
</div>

### PR 결과물
PR 워크플로우로 생성한 PR 결과물입니다.

<div align="center">
    <img src="../assets/images/blog/posts/2026-01-05-hf-translation-mcp-n8n/pr_result.png" 
         width="500"
         alt="생성된 GitHub PR"/>
    <p><em>자동으로 생성된 번역 PR</em></p>
</div>

### PR Review 워크플로우
PR URL을 AI Agent에게 알려주면, PR Review 코멘트를 남겨주는 MCP Server를 실행합니다.

<div align="center">
    <img src="../assets/images/blog/posts/2026-01-05-hf-translation-mcp-n8n/review.png" 
         width="500"
         alt="PR 리뷰 워크플로우"/>
    <p><em>자동 PR 리뷰 워크플로우</em></p>
</div>

## 실행 방식 비교: AI Chat Client vs n8n

워크플로우 구축 과정에서 마주친 여러 문제들을 이야기하기 전에, 먼저 n8n을 사용하게 된 배경을 얘기해보려고 합니다.

<div align="center">
    <img src="../assets/images/blog/posts/2026-01-05-hf-translation-mcp-n8n/meme.jpg" 
         width="500"
         alt="AI 자동화에 대한 기대와 현실을 보여주는 밈"/>
    <p><em>AI 자동화에 대한 기대와 현실</em></p>
</div>

인터넷에서 밈처럼 돌아다니는 이 사진을 본 적이 있으실까요? 저는 MCP Server를 개발하면서 이 사진에 공감하게 되었습니다.

번역 MCP Server를 구현하고 나서, Hugging Face Chat, Claude Desktop, Gemini CLI 등과 같은 AI Chat Client에 직접 MCP Server를 연결하고 테스팅을 해보았습니다. 이 과정에서 사람이 직접 Client와 소통하고 참여해야만 이 MCP Server들이 사용된다고 느껴졌습니다. 사람의 손을 타지 않고 이러한 워크플로우가 돌아간다면 MCP Server의 사용성이 더 높아질 거라 기대되었습니다. 

따라서 사람 대신에 워크플로우를 돌릴 수 있게 MCP Server Orchestration Tool을 찾아다니다가, 직접 MCP Client를 개발할 필요가 없는 노코드형 툴인 n8n을 선택하게 되었습니다. 

### AI Chat Client 직접 실행 (Hugging Face Chat, Claude Desktop, Gemini CLI)

**장점:**

1. **빠른 프로토타이핑**: MCP Server 설정 파일만 수정하면 즉시 테스트 가능
2. **자연스러운 대화형 인터페이스**: 복잡한 요청도 자연어로 표현
3. **컨텍스트 유지**: 대화 흐름 속에서 이전 결과를 자연스럽게 참조
4. **높은 번역 품질**: Claude의 Full Context를 활용한 일관된 번역
5. **디버깅 용이**: 실시간으로 Claude의 사고 과정 확인 가능

**단점:**

1. **수동 작업 필요**: 매번 사용자가 명령을 입력해야 함
2. **자동화 불가**: 반복 작업이나 스케줄링 불가능
3. **확장성 제한**: 대량 처리나 병렬 처리 어려움

**적합한 사용 사례:**
- 일회성 번역 작업
- 복잡한 맥락이 필요한 번역
- 빠른 실험과 테스트
- 대화형 번역 검토 및 수정

### n8n 워크플로우 실행

**장점:**

1. **완전 자동화**: 트리거만 설정하면 자동 실행
2. **확장성**: 대량의 문서를 병렬로 처리 가능
3. **통합성**: Notion, Slack, GitHub 등 다양한 서비스와 연동
4. **재사용성**: 한 번 구축한 워크플로우를 반복 사용
5. **스케줄링**: 정해진 시간에 자동 실행

**단점:**

1. **초기 구축 비용**: 워크플로우 설계와 구현에 시간 소요
2. **제한된 유연성**: 정해진 로직 외의 요청 처리 어려움
3. **복잡한 디버깅**: 문제 발생 시 여러 노드를 확인해야 함
4. **Max Iteration 제약**: 복잡한 작업은 분할 필요
5. **Agent 지능 한계**: 예상치 못한 상황에 유연하게 대응하도록 사람이 도와줄 수 없음

**적합한 사용 사례:**
- 정기적인 대량 번역 작업
- 다단계 자동화 프로세스
- 번역 결과의 자동 배포 및 알림

### 하이브리드 접근법

실제로는 두 방식을 상황에 맞게 조합하여 사용하였습니다. 개발 초창기에는 MCP Server의 테스트를 위해 AI Chat Client들을 사용하였고, 이후 n8n으로 자동화를 도입했습니다.

**1단계: Desktop Client로 프로토타입**
- 새로운 번역 요구사항 테스트
- 최적의 프롬프트와 파라미터 발견
- 번역 품질 확인

**2단계: n8n으로 자동화**
- 검증된 프로세스를 워크플로우로 구현
- 반복 작업 자동화
- 모니터링 및 개선

**3단계: 피드백 루프**
- n8n 실행 결과 분석
- 문제 발생 시 Desktop Client로 재검증
- 워크플로우 개선 및 업데이트

이제 이러한 배경을 이해한 상태에서, Gradio MCP Server를 활용한 n8n 워크플로우 구축 과정에서 실제로 마주친 문제들을 살펴보겠습니다.

## 트러블슈팅: 실전에서 마주친 문제들

### 1. Gradio MCP Server는 선택적 노출이 불가능하다

**문제 상황:**
필요하지 않은 Tool이 등록되면 Agent에게 혼란을 줄 수 있기 때문에, 처음에는 `app.py`에 정의된 여러 함수 중 특정 함수만 MCP Tool로 노출하려고 했습니다. 하지만 Gradio는 그런 방식으로 동작하지 않았습니다.

**원인:**
Gradio 공식 문서를 확인해보니, `demo.launch(mcp_server=True)` 옵션을 활성화하면 **앱에 정의된 모든 인터페이스 함수가 자동으로 MCP Tool로 변환**됩니다. 함수 단위로 선택적으로 제외하는 설정은 공식적으로 제공되지 않습니다.

**해결 방법:**
- MCP Server로 노출하고 싶은 함수만 별도의 `app.py` 파일에 분리
- 또는 노출하고 싶지 않은 함수는 내부 헬퍼 함수로 구조 변경
- 필요한 경우 여러 개의 Gradio 앱을 만들어 각각 다른 포트로 실행

```python
# 잘못된 접근 (특정 함수만 노출 불가)
# app.py
def translate(text): ...
def summarize(text): ...  # 이것도 함께 노출됨

demo.launch(mcp_server=True)

# 올바른 접근 (필요한 함수만 별도 파일로 분리)
# app.py
def translate(text): ...
demo.launch(mcp_server=True)  # translate만 노출됨
```

### 2. n8n Tool Call ID로 인한 Schema Checking 실패

**문제 상황:**
n8n에서 MCP Tool을 호출할 때 스키마 검증 에러가 발생했습니다.

<div align="center">
    <img src="../assets/images/blog/posts/2026-01-05-hf-translation-mcp-n8n/toolcallid.png" 
         width="500"
         alt="toolCallId 에러 화면"/>
    <p><em>toolCallId 파라미터로 인한 Schema 검증 실패</em></p>
</div>

**원인:**
[Gradio Python Client](https://github.com/gradio-app/gradio/blob/main/client/python/README.md)는 입력 파라미터의 타입과 구조를 엄격하게 검증합니다. 문제는 n8n에서 AI Agent가 Tool을 호출할 때마다 고유한 `toolCallId`가 자동으로 생성되어 파라미터에 주입된다는 것이었습니다. Gradio는 정의되지 않은 이 파라미터를 거부하면서 Schema 검증이 실패했습니다. 이는 현재 n8n의 알려진 이슈([n8n-io/n8n#21716](https://github.com/n8n-io/n8n/issues/21716))와 동일했습니다.

**해결 방법:**
- 모든 Tool 정의에 `toolCallId: str = None` 파라미터를 추가하여 n8n이 주입하는 값을 수용
- Gradio 앱 정의 시 명확한 타입 힌트 사용
- 테스트 단계에서 Gradio의 `/gradio_api/mcp/schema` 엔드포인트로 정확한 스키마 확인

```python
# n8n의 toolCallId를 수용하도록 수정
def translate(
    text: str,
    source_lang: str = "en",
    target_lang: str = "ko",
    toolCallId: str = None  # n8n에서 주입되는 파라미터
) -> str:
    # toolCallId는 내부적으로 사용하지 않음
    ...
```

### 3. n8n에서 Tool Description 필수 입력

**문제 상황:**
MCP Server를 n8n에 연결했을 때, Tool들이 제대로 인식되지 않는 현상이 발생했습니다.

<div align="center">
    <img src="../assets/images/blog/posts/2026-01-05-hf-translation-mcp-n8n/description.png" 
         width="500"
         alt="toolCallId 에러 화면"/>
    <p><em>toolCallId 파라미터로 인한 Schema 검증 실패</em></p>
</div>

**원인:**
n8n의 AI Agent는 각 Tool의 **Description**을 매우 중요하게 취급합니다. Gradio에서 함수만 정의하고 설명을 생략하면, 에러가 나는 경우가 있습니다.

**해결 방법:**
- Gradio 인터페이스 생성 시 `description` 파라미터를 명확하게 작성
- 각 파라미터에도 설명 추가
- Tool이 무엇을 하는지, 언제 사용해야 하는지 구체적으로 명시

```python
import gradio as gr

# 설명이 없는 경우 (❌)
def translate(text: str, target_lang: str = "ko") -> str:
    ...

demo = gr.Interface(fn=translate, inputs=["text", "text"], outputs="text")

# 설명이 있는 경우 (✅)
def translate(text: str, target_lang: str = "ko") -> str:
    """주어진 텍스트를 목표 언어로 번역합니다.
    
    Args:
        text: 번역할 텍스트.
        target_lang: 어떤 언어로 번역할지.
    """
    ...

demo = gr.Interface(
    fn=translate,
    inputs=[
        gr.Textbox(label="text", info="번역할 텍스트를 입력하세요"),
        gr.Textbox(label="target_lang", info="목표 언어 코드 (예: ko, en, ja)")
    ],
    outputs="text",
    title="번역 도구",
    description="텍스트를 지정한 언어로 번역하는 Tool입니다. 기술 문서나 일반 텍스트 번역에 사용하세요."
)
```

**추가 팁:**
- Description은 AI Agent가 Tool 선택의 기준으로 사용하므로, 구체적일수록 좋습니다.
- "이 Tool은 ~할 때 사용하세요"와 같이 사용 시나리오를 포함하면 더욱 효과적입니다.

### 4. Gradio의 MCP Tools Success Rate 대시보드

**발견:**
Gradio Space에서 MCP Server를 사용하다 보니, 각 Tool의 **성공률(Success Rate)**을 실시간으로 보여주는 대시보드가 있다는 것을 발견했습니다.

<div align="center">
    <img src="../assets/images/blog/posts/2026-01-05-hf-translation-mcp-n8n/dashboard.png" 
         width="500"
         alt="Gradio Success Rate 대시보드"/>
    <p><em>각 Tool의 성공률을 보여주는 Gradio 대시보드</em></p>
</div>

**활용 방법:**
- 어떤 Tool이 자주 실패하는지 한눈에 파악 가능
- 워크플로우 개선 시 우선순위 결정에 활용
- 프로덕션 환경에서 모니터링 지표로 사용

이 기능 덕분에 번역 Tool의 성공률을 모니터링하고, 에러 패턴을 추적하여 각 MCP Server를 개선할 수 있었습니다.

### 5. Notion API: Rich Text의 2000자 제한

**문제 상황:**
긴 번역 결과를 Notion 페이지로 저장하려고 할 때 에러가 발생했습니다.

**원인:**
[Notion API 문서](https://developers.notion.com/reference/request-limits#size-limits)를 확인해보니, Rich Text 블록은 **최대 2000자까지만 허용**됩니다. 저희 프로젝트의 경우 번역 결과물이 2000자를 넘는 경우가 자주 발생했기 때문에 다른 방식이 필요했습니다.

**해결 방법:**
- 현서님께서 Notion Tool 대신 GitHub MCP Server로 대체하는 방식을 찾아주셨습니다
- GitHub로 파일을 바로 저장하고, 번역 결과물 또한 GitHub에서 읽어오도록 변경
- Notion UI의 편리함을 포기해야 했지만, Notion API의 사이즈 제한 문제로 꼭 필요한 대체였습니다

<div align="center">
    <img src="../assets/images/blog/posts/2026-01-05-hf-translation-mcp-n8n/github.png" 
         width="500"
         alt="GitHub 기반으로 변경된 워크플로우"/>
    <p><em>Notion 대신 GitHub를 사용하도록 변경된 워크플로우</em></p>
</div>

**참고사항:**
만약 Notion을 사용해야 한다면, 2000자가 넘지 않는 콘텐츠 저장을 대상으로 하는지 미리 확인하시기 바랍니다.

### 6. 더 똑똑한 AI Agent의 필요성

**문제 인식:**
2000자 제한 문제를 해결하면서 근본적인 의문이 들었습니다. "AI Agent가 Tool 사용 중 제약을 만나면 스스로 대응할 수는 없을까?"

**현재 상황:**
- 2000자 제한을 넘으면 에러 발생
- 개발자가 미리 분할 로직을 구현해야 함
- Agent는 단순히 주어진 Tool을 실행만 함

**이상적인 시나리오:**
똑똑한 AI Agent라면 이렇게 동작해야 하지 않을까요?
1. 번역 결과가 2000자를 넘는다는 것을 인지
2. 자동으로 텍스트를 분할
3. Notion Tool을 여러 번 호출하여 순차적으로 저장
4. 전체 작업 완료 후 성공 보고

**시사점:**
현재의 n8n 워크플로우 구조는 정해진 시퀀스를 실행하는 데 최적화되어 있습니다. 하지만 앞으로는 **도구의 제약을 이해하고 동적으로 대응할 수 있는 더 지능적인 Agent**가 필요해 보입니다. 이는 단순한 워크플로우 엔진을 넘어서는 차원의 문제입니다.

### 7. 유연한 재시도 어려움 및 결과물 품질 문제

**문제 상황:**
n8n으로 워크플로우를 실행하면 AI Chat Client로 직접 실행할 때보다 번역 과정에서 사람의 개입이 제한적입니다. 사람은 MCP를 직접 실행하면서 중간에 개입하여 결과물의 품질을 높이기 위해 고쳐달라고 요청하거나 재시도를 요청할 수 있습니다. 

반면에, n8n 워크플로우는 Chat History처럼 중간 결과물이 메모리에 저장되어 있지 않다보니 워크플로우를 중간부터 재시도하지 못하고, 처음부터 다시 실행해야 합니다.

**해결 시도:**
- 시스템 프롬프트에 "완전한 번역 제공" 명시
- 프롬프트 최적화로 어느 정도 개선

완벽한 해결은 아니지만, 프롬프트를 잘 작성하면 품질을 어느 정도 유지할 수 있습니다.

### 8. Max Iteration의 함정

**문제 상황:**
복잡한 번역 작업을 수행할 때 워크플로우가 중간에 멈추는 현상이 발생했습니다.

<div align="center">
    <img src="../assets/images/blog/posts/2026-01-05-hf-translation-mcp-n8n/iteration.png" 
         width="500"
         alt="Max Iteration 초과 에러"/>
    <p><em>Max Iteration 초과로 인한 워크플로우 중단</em></p>
</div>

**원인:**
n8n AI Agent는 무한 루프 방지를 위해 **Max Iteration** 설정이 있습니다. Tool 호출 횟수가 이 값을 초과하면 강제로 종료됩니다.

**해결 방법:**
- 작업을 적절한 크기로 나누어 각 단계별로 Tool 체인 구성

    ```
    Before: 
    [Input] → [AI Agent: 20 tool calls] → [Output]
             ❌ Max Iteration 초과

    After:
    [Input] → [AI Agent: Step 1] → [AI Agent: Step 2] → [Output]
             ✅ 각 5 tool calls      ✅ 각 5 tool calls
    ```

- Max Iteration 값을 작업 복잡도에 맞게 조정 

    <div align="center">
        <img src="../assets/images/blog/posts/2026-01-05-hf-translation-mcp-n8n/max.png" 
             width="500"
             alt="Max Iteration 설정"/>
        <p><em>n8n AI Agent의 Max Iteration 설정</em></p>
    </div>

- 긴 작업은 여러 워크플로우로 분리하고 순차 실행

## 마치며

n8n으로 MCP Server 워크플로우를 구축하는 과정은 예상보다 많은 시행착오가 필요했습니다. Gradio의 전체 노출 특성, Schema 검증, Notion의 2000자 제한 등 실제로 부딪혀봐야 알 수 있는 제약들이 많았습니다.

하지만 이러한 과정을 통해 얻은 가장 큰 교훈은 **자동화의 가치와 한계를 동시에 이해하게 되었다**는 것입니다. n8n은 반복 작업을 효율화하는 데 탁월하지만, Claude Desktop Client의 유연성과 품질을 완전히 대체할 수는 없습니다. 

앞으로는 단순한 워크플로우 엔진을 넘어, **도구의 제약을 이해하고 동적으로 대응할 수 있는 더 지능적인 Agent**가 등장하기를 기대합니다. 2000자 제한을 만나면 스스로 분할해서 처리하고, Max Iteration에 도달하면 작업을 재구성하는 그런 Agent 말입니다.

지금은 개발자가 모든 예외 상황을 예측하고 처리해야 하지만, 언젠가는 AI가 도구의 특성을 학습하고 최적의 사용법을 스스로 찾아가는 날이 올 것입니다. 그때까지는 Desktop Client와 n8n을 적재적소에 활용하는 지혜가 필요해 보입니다.

```

## 31-post audit report

# Internal SEO Sample Audit

- Total posts: 31
- Status counts: `{'NEEDS_CHANGES': 13, 'FAIL': 13, 'PASS': 5}`
- Missing metadata: `{'description': 31, 'author': 1}`
- Required failures: `{'h1_count': 19, 'citations': 1, 'opening_summary': 7, 'descriptive_alt_text': 7, 'alt_text_coverage': 6, 'heading_hierarchy': 4}`
- Blocker failures: `{}`

## Posts

| File | Status | Metadata gaps | Required failures | Shape |
|---|---|---|---|---|
| `_posts/2024-09-16-how-to-contribute.md` | NEEDS_CHANGES | description | h1_count | 1789 chars, H1 0, img 0, links 2 |
| `_posts/2024-09-19-creating-gradio-based-NL2SQL-chatbot.md` | NEEDS_CHANGES | description | h1_count | 4792 chars, H1 0, img 1, links 5 |
| `_posts/2024-10-02-creating-web-interface.md` | NEEDS_CHANGES | description | h1_count | 4023 chars, H1 0, img 0, links 2 |
| `_posts/2024-10-05-how-to-use-translator.md` | FAIL | description | h1_count, citations | 2543 chars, H1 0, img 10, links 5 |
| `_posts/2025-05-27-2024-open-source-academy-recap.md` | NEEDS_CHANGES | description | h1_count | 5703 chars, H1 0, img 5, links 4 |
| `_posts/2025-05-31-2025-PseudoCon-recap.md` | NEEDS_CHANGES | description | h1_count | 4398 chars, H1 3, img 0, links 7 |
| `_posts/2025-06-14-text2sql-spider-ko-dataset.md` | NEEDS_CHANGES | description | h1_count | 5012 chars, H1 0, img 0, links 4 |
| `_posts/2025-06-22-HuggingFace-Docs-Translation-Guide.md` | FAIL | description | opening_summary, h1_count | 6767 chars, H1 0, img 0, links 4 |
| `_posts/2025-09-14-Implementing-MCP-Servers-in-Python.md` | PASS | description | - | 4534 chars, H1 1, img 0, links 5 |
| `_posts/2025-09-14-python-tiny-agents-ko.md` | NEEDS_CHANGES | description | opening_summary | 15941 chars, H1 1, img 0, links 21 |
| `_posts/2025-09-14-python-tiny-agents-study.md` | FAIL | description | h1_count, descriptive_alt_text | 4770 chars, H1 0, img 5, links 7 |
| `_posts/2025-09-26-Introducing-smolagents.md` | FAIL | description | opening_summary, h1_count, alt_text_coverage | 10925 chars, H1 2, img 4, links 36 |
| `_posts/2025-09-29-building-hf-mcp-ko.md` | NEEDS_CHANGES | description | heading_hierarchy | 9662 chars, H1 1, img 2, links 20 |
| `_posts/2025-09-29-building-hf-mcp-study.md` | FAIL | description | h1_count, descriptive_alt_text | 10332 chars, H1 0, img 7, links 1 |
| `_posts/2025-10-06-mcp-for-research.md` | PASS | description | - | 4089 chars, H1 1, img 1, links 15 |
| `_posts/2025-10-12-vlm-explained-ko.md` | PASS | description | - | 12643 chars, H1 1, img 5, links 26 |
| `_posts/2025-10-13-structured-codeagent-ko.md` | FAIL | description | heading_hierarchy, alt_text_coverage, descriptive_alt_text | 8206 chars, H1 1, img 2, links 8 |
| `_posts/2025-10-20-2025-VLM.md` | FAIL | description | h1_count, alt_text_coverage | 20760 chars, H1 0, img 15, links 45 |
| `_posts/2025-11-02-DABStep.md` | NEEDS_CHANGES | description | descriptive_alt_text | 11824 chars, H1 1, img 2, links 9 |
| `_posts/2025-11-10-pi0-fast.md` | FAIL | description | heading_hierarchy, h1_count | 14421 chars, H1 0, img 2, links 18 |
| `_posts/2025-11-17-agent-leaderboard.md` | NEEDS_CHANGES | description | opening_summary | 14972 chars, H1 1, img 0, links 3 |
| `_posts/2025-11-17-hf_translation_hub_mcp_design_and_tooling.md` | PASS | description | - | 6249 chars, H1 1, img 0, links 7 |
| `_posts/2025-11-3-Welcome-GPT-OSS.md` | FAIL | description | h1_count, alt_text_coverage, descriptive_alt_text | 19189 chars, H1 8, img 3, links 27 |
| `_posts/2025-12-01-math-verify-leaderboard.md` | FAIL | description | opening_summary, alt_text_coverage, descriptive_alt_text | 7443 chars, H1 1, img 5, links 6 |
| `_posts/2025-12-01-rteb.md` | PASS | description | - | 11927 chars, H1 1, img 0, links 5 |
| `_posts/2025-12-08-hugging_face_blog_fetch_automation.md` | FAIL | description | h1_count, alt_text_coverage, descriptive_alt_text | 17935 chars, H1 6, img 10, links 2 |
| `_posts/2025-12-15-ai-agents-are-here.md` | FAIL | description | heading_hierarchy, h1_count | 22286 chars, H1 6, img 0, links 65 |
| `_posts/2025-12-15-hf-translation-hub-mcp-server-usage-guide.md` | NEEDS_CHANGES | description | h1_count | 7262 chars, H1 6, img 7, links 4 |
| `_posts/2025-12-22-smolvla.md` | NEEDS_CHANGES | description, author | opening_summary | 17258 chars, H1 1, img 8, links 38 |
| `_posts/2025-12-28-translation-mcp-project-overview.md` | FAIL | description | opening_summary, h1_count | 7400 chars, H1 0, img 3, links 4 |
| `_posts/2026-01-05-hf-translation-mcp-n8n.md` | NEEDS_CHANGES | description | h1_count | 11647 chars, H1 0, img 12, links 3 |

