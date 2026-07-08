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

