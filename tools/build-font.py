"""
把 cwTeX Q 圓體裁成「只含 index.html 用到的字」，並以 base64 嵌回 index.html。

為什麼：完整字型約 7MB，手機載入太慢；裁切後通常只有幾十 KB。
注意：之後只要改了頁面上的中文字（包含 <script> 裡的話題），就要重跑一次，
否則新加的字會改用備用字體（Noto Sans TC）顯示。

用法：
  pip install fonttools brotli
  下載字型：https://github.com/l10n-tw/cwtex-q-fonts-TTFs/raw/master/ttf/cwTeXQYuanZH-Medium.ttf
  python tools/build-font.py path/to/cwTeXQYuanZH-Medium.ttf
"""
import base64
import io
import re
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

HTML = Path(__file__).resolve().parent.parent / "index.html"
START, END = "/*FONT:START*/", "/*FONT:END*/"
FAMILY = "cwTeX Q Yuan"


def main(src: str) -> None:
    html = HTML.read_text(encoding="utf-8")
    # 只收非 ASCII 字元（中文、全形標點）；英數字交給其他字體
    chars = sorted({c for c in html if ord(c) > 0x7F})

    font = TTFont(src)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(chars))
    sub.subset(font)

    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    data = buf.getvalue()
    b64 = base64.b64encode(data).decode("ascii")

    css = (
        f"@font-face{{font-family:\"{FAMILY}\";font-style:normal;font-weight:500;font-display:swap;"
        f"src:url(data:font/woff2;base64,{b64}) format(\"woff2\")}}"
    )
    pattern = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)
    if not pattern.search(html):
        sys.exit(f"找不到 {START} … {END} 標記")
    html = pattern.sub(lambda _: START + css + END, html, count=1)
    HTML.write_text(html, encoding="utf-8", newline="\n")
    print(f"{len(chars)} 個字元 → {len(data)/1024:.1f} KB woff2（base64 後 {len(b64)/1024:.1f} KB）")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
