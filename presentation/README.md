# 발표 자료

> **초안 · 2026-10-13** — `[__]` 표시는 실험 결과가 나오면 채웁니다.

| 파일 | 내용 |
|---|---|
| [발표자료.pdf](발표자료.pdf) | 슬라이드 14장 (1920×1080) |
| [발표자료.html](https://skn35shimsungwook.github.io/langchain-migration-helper/presentation/발표자료.html) | 웹으로 보기. 슬라이드마다 "발표자 노트"(발표 대본)를 펼쳐 볼 수 있음 |
| `slides/*.html`, `deck.json` | 슬라이드 원본 (claude.ai 슬라이드에서 만든 것의 사본) |
| `build_slides.py` | 원본을 `발표자료.html` 한 파일로 합치는 스크립트 |
| `assets.json` | 슬라이드 원본의 이미지 주소(`/_blob/...`)를 저장소 그림 파일로 바꾸는 연결표 |

## 그림에 대해

- 슬라이드 그림은 `docs/images/`의 SVG입니다. **웹 버전(GitHub)에서는 그림이 움직입니다.**
- claude.ai 슬라이드는 보안 처리 때문에 그림의 애니메이션과 `<style>`을 지웁니다. 그래서 claude.ai에는 스타일을 글자마다 직접 적은 **정지 그림**(`docs/images/static/`)을 올려 두었습니다.
- 움직이는 그림으로 발표하려면 GitHub 웹 버전으로 발표하세요.

## 슬라이드를 고친 뒤 다시 만드는 방법

1. claude.ai 슬라이드에서 고친 내용을 `slides/` 폴더의 같은 이름 파일에 반영합니다. (Claude에게 "발표 자료 GitHub 사본 업데이트해줘"라고 하면 됩니다.)
2. 웹 버전을 다시 만듭니다.

```bash
python build_slides.py
```

3. PDF는 Edge로 만듭니다. (자세한 명령은 `build_slides.py` 맨 위 설명 참고)
