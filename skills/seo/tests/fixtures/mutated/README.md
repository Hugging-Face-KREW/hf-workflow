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

