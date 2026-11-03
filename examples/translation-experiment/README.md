# PR 기반 번역 실험 준비 도구

`scripts/translation_experiment.py`는 고정 원문·설정을 저장하고, **이미 생성한 완성 번역 파일**을 조건별 Draft PR로 연결한다. 기존 번역·품질 평가기를 대체하지 않으며 모델/API 호출이나 품질 점수 계산을 하지 않는다. 새로운 NVIDIA backend나 청킹 번역도 이 도구에는 포함하지 않는다.

첫 연결 테스트는 원문 1편과 기존 whole 번역 조건 1개로 시작한다. 생성 → Draft PR → 평가 → 필요시 자동수정 → 재평가와 기록 연결을 확인한 뒤, 동일 원문을 사용하는 비교 조건과 문서 수를 늘린다. 각 조건의 PR 본문과 SHA별 결과 댓글이 장기 기록의 중심이며 별도 결과 기록 PR은 필요 없다.

## 지금 준비된 것과 실행 전 남은 것

- 준비됨: 고정 입력/설정 보존, 독립 Git worktree와 최초 후보 커밋, 실험 제목·라벨·Draft PR 생성, managed 루프 선택 연결, SHA와 원문/번역 hash가 일치하는 평가·사용량 기록, 멱등적인 SHA별 결과 댓글, 상세 자료 ZIP 추출.
- 실행 전 확정: 원문·모델·예산, 링크 보호 개선과 알림 변경을 포함하는 workflow SHA, 블로그의 review/feedback 워크플로우 참조 갱신.
- 아직 자동화하지 않음: 모델의 번역 생성, 기존 Actions artifact 자동 다운로드/비용 수집, 리뷰 실행마다 이 기록 도구 호출, artifact 업로드. 첫 테스트에서는 기존 도구로 생성·평가하고 명시적으로 기록한다.
- `--enable-loop`는 두 블로그 워크플로우의 세 참조가 모두 계획의 SHA로 고정됐는지 확인한다. 미배포 상태에서는 PR을 push하기 전에 중단한다.

## 입력 고정

`plan.example.json`을 복사해 모든 `REPLACE_...` 값을 실제 값으로 채운다. `$1`은 예시일 뿐 합의된 실행 예산이 아니다. 모델·프롬프트·전처리·용어 정책·평가기·수정 상한 등 비교에 필요한 설정을 각 arm의 `settings`에 넣는다. 정책 파일은 기준 workflow 커밋에 고정하고, 로컬 수정본을 사용하면 별도로 보존한다.

```bash
python3 scripts/translation_experiment.py prepare \
  --plan /tmp/experiment-plan.json --source /tmp/source.md \
  --output /tmp/translation-runs/smoke-001
```

준비된 run은 덮어쓰지 않는다. 원문을 변경하면 이후 명령이 거절한다. `run.json`의 두 기준 SHA는 브랜치명 대신 전체 40자 커밋이어야 한다.

## 기존 생성 결과 연결

기존 번역 도구에서 이 고정 원문으로 생성한 **frontmatter를 포함하는 최종 게시 파일**을 준비한다. 생성기가 원문을 URL에서 다시 가져온 경우 고정 원문과 동일한지 확인해야 하며, 다르면 같은 실험으로 집계하지 않는다. 이미지 등 추가 자산은 공통 blog base에 준비한다. 현재 stage는 게시 Markdown 한 파일만 커밋한다.

```bash
python3 scripts/translation_experiment.py stage \
  --run /tmp/translation-runs/smoke-001 --arm baseline \
  --checkout /path/to/blog-checkout --candidate /tmp/translated-post.md
```

stage는 지정한 blog base에서 별도 worktree·브랜치를 만들며 기존 checkout의 HEAD/변경을 바꾸지 않는다. 같은 arm은 재사용하지 않는다. 실패 중간에 worktree가 남았다면 먼저 상태를 확인하고 해당 실패 run을 보존한 뒤 새 run으로 재시도한다.

`arms/baseline/manifest.yaml`은 기존 `scripts/run_local_review.py`에 연결할 수 있는 로컬 manifest다. 실행 시에는 `pr.json`에 기록된 worktree와 정확한 SHA를 사용한다. 이 manifest에는 절대 원문 경로가 들어가므로 run 폴더를 옮겼다면 수정해야 한다. 자동수정 후 평가에는 해당 새 SHA를 가리키는 manifest가 필요하다.

## Draft PR과 기존 수정 루프

다음 명령은 **원격 branch/PR을 만들고 자동 평가·수정에 비용이 발생할 수 있다.** 준비만 할 때는 실행하지 않는다.

```bash
python3 scripts/translation_experiment.py publish \
  --run /tmp/translation-runs/smoke-001 --arm baseline --enable-loop
```

최초 SHA를 먼저 저장하고, `[실험]` 제목과 `hf-agent:experiment` 라벨의 Draft PR을 만든 다음 `hf-agent:managed`를 붙여 기존 루프를 시작한다. `--enable-loop`를 생략하면 실험 PR만 만들고 루프를 켜지 않는다. 사용자는 이후 같은 명령에 옵션을 붙여 루프를 켤 수 있다. 최초 managed 라벨은 대상 저장소에 이미 있어야 한다.

실험 라벨은 PR 생성 알림·기타 Actions를 일괄 차단하지 않는다. 이번 알림 변경은 **머지 승인 요청만** 생략한다. 실제 리뷰와 피드백의 실행 조건·수정 상한은 배포된 기존 워크플로우를 따른다. 이 도구의 `budget_usd`는 기록용이며 기존 자동 루프의 지출을 강제로 차단하지 않는다. 루프 실행 전 생성·평가·수정의 호출 상한과 예산을 별도로 확인한다.

## 커밋별 결과 보존

수정된 브랜치를 fetch해 해당 SHA가 로컬 checkout에 존재하도록 한 뒤 기록한다. 평가 입력 JSON은 다음 형식이다. 기존 평가 보고서는 `details`에 넣거나 artifact로 보존한다. 아래 hash/SHA는 실제 평가 입력에서 확인한 값이어야 하며, 단순히 사후에 복사해서 맞추면 안 된다.

```json
{
  "head_sha": "평가한 전체 40자 SHA",
  "source_sha256": "run.json의 원문 hash",
  "target_sha256": "평가한 게시 파일 바이트의 SHA-256",
  "summary": "품질 점수, 미해결 오류, 이전 SHA 대비 개선·새 오류, 의미 평가 완료 여부",
  "details": {},
  "elapsed_seconds": null
}
```

사용량 JSON은 아래 형식으로 호출별 실제 모델·비용을 기록한다. 확인 불가능한 비용·시간은 `null`로 남긴다. 한 호출을 여러 revision에 중복 집계하지 않는다. 최초 생성 비용은 최초 SHA에, 수정 호출 비용은 생성된 수정 SHA에 연결한다.

```json
{
  "head_sha": "동일한 전체 SHA",
  "calls": [
    {
      "phase": "generation",
      "model": "실제 사용한 모델",
      "cost_usd": null,
      "elapsed_seconds": null,
      "input_tokens": null,
      "output_tokens": null
    }
  ]
}
```

`phase`는 `generation`, `evaluation`, `repair`, `routing`, `guardrails` 중 하나다. 재시도·실패·비용 미확정 호출도 빠뜨리지 않는다. 여러 평가기가 있으면 세부 평가 결과를 `details`에 함께 보존한다. 이 도구의 hash 검사는 결과의 연결을 검사하며, 기존 신뢰 검증기나 의미 평가를 대신하지 않는다.

```bash
python3 scripts/translation_experiment.py record \
  --run /tmp/translation-runs/smoke-001 --arm baseline \
  --checkout /path/to/blog-checkout --sha FULL_REVISION_SHA \
  --evaluation /tmp/evaluation.json --usage /tmp/usage.json

python3 scripts/translation_experiment.py comment \
  --run /tmp/translation-runs/smoke-001 --arm baseline \
  --sha FULL_REVISION_SHA \
  --artifact-url https://github.com/OWNER/REPO/actions/runs/RUN_ID
```

record는 최초 SHA의 후손인지, 원문/번역 hash와 평가 SHA가 일치하는지 확인한다. revision 기록은 덮어쓰지 않는다. comment는 같은 작성자의 같은 run/arm/SHA 결과 댓글을 갱신해서 재실행 시 댓글이 늘어나지 않는다. 댓글에는 `hf-agent-` 마커가 있어서 기존 피드백 수집기가 새 수정 지시로 해석하지 않는다. 비교군 PR 링크와 최종 결론도 PR에 남긴다.

## 상세 자료 보관

```bash
python3 scripts/translation_experiment.py bundle \
  --run /tmp/translation-runs/smoke-001 --output /tmp/smoke-001.zip
```

원문·설정·후보·커밋별 평가/사용량·댓글을 포함하며 worktree와 `.git`은 제외한다. 환경변수나 API 키는 자동 수집하지 않는다. 직접 넣는 보고서에도 비밀값을 포함하지 않는다. 실행 workflow를 추가할 때 ZIP과 상세 원본을 `actions/upload-artifact`로 업로드하고 90일 보관하도록 연결한다. 이 준비 도구가 업로드까지 수행하지는 않는다. 보관 기한 뒤에도 필요한 결론·수치는 PR에 남긴다.

## 무료 검증

```bash
python3 -m pytest tests/test_translation_experiment.py -q
```

테스트는 임시 Git 저장소와 가짜 GitHub 응답을 사용한다. 실제 모델 호출, 원격 push, PR 생성, 댓글 작성은 없다.
