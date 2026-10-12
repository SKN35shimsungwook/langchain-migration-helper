# 발표 자료

> **초안 · 2026-10-12** — `[__]` 표시는 실험 결과가 나오면 채웁니다.

| 파일 | 내용 |
|---|---|
| [발표자료.pdf](발표자료.pdf) | 슬라이드 13장 (1920×1080) |
| [발표자료.html](https://skn35shimsungwook.github.io/langchain-migration-helper/presentation/발표자료.html) | 웹으로 보기. 슬라이드마다 "발표자 노트"(발표 대본)를 펼쳐 볼 수 있음 |
| `slides/*.html`, `deck.json` | 슬라이드 원본 (claude.ai 슬라이드에서 만든 것의 사본) |
| `build_slides.py` | 원본을 `발표자료.html` 한 파일로 합치는 스크립트 |

## 슬라이드를 고친 뒤 다시 만드는 방법

1. claude.ai 슬라이드에서 고친 내용을 `slides/` 폴더의 같은 이름 파일에 반영합니다. (Claude에게 "발표 자료 GitHub 사본 업데이트해줘"라고 하면 됩니다.)
2. 웹 버전을 다시 만듭니다.

```bash
python build_slides.py
```

3. PDF는 Edge로 만듭니다. (자세한 명령은 `build_slides.py` 맨 위 설명 참고)
