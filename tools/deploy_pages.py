"""Build the GitHub Pages payload into docs/.

Pages는 Settings > Pages > "Deploy from a branch" > main / docs 로 설정.
docs/에는 위젯 구동에 필요한 최소 파일만 복사한다:
  - index.html      (widget.html 그대로)
  - sprites/*.webm  (애니메이션 클립)
  - .nojekyll       (Jekyll 처리 비활성화)
에셋을 갱신했으면 이 스크립트를 다시 실행해서 docs/를 재생성한다.
"""
import glob
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")


def main():
    shutil.rmtree(DOCS, ignore_errors=True)
    os.makedirs(os.path.join(DOCS, "sprites"))

    shutil.copy(os.path.join(ROOT, "widget.html"),
                os.path.join(DOCS, "index.html"))
    open(os.path.join(DOCS, ".nojekyll"), "w").close()

    webms = sorted(glob.glob(os.path.join(ROOT, "sprites", "anim_*.webm")))
    for f in webms:
        shutil.copy(f, os.path.join(DOCS, "sprites", os.path.basename(f)))

    total = sum(os.path.getsize(os.path.join(DOCS, "sprites", f))
                for f in os.listdir(os.path.join(DOCS, "sprites")))
    print(f"docs/ built: index.html + {len(webms)} webm "
          f"({total / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
