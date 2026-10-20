# -*- coding: utf-8 -*-
r"""
把 cases 下的案例卡 md 批量转成 PDF（md → HTML → Chrome 无头出 PDF）。

用法：
    python cases/_生成PDF.py

产出：cases/PDF/案例0X-xxx.pdf
改了任何案例 md，重跑一次即可。
"""
import html
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, "PDF")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
body {
  font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
  color: #1f2328; margin: 0; font-size: 10.5pt; line-height: 1.7; background: #fff;
}
.page { width: 210mm; min-height: 297mm; padding: 16mm 17mm 15mm 17mm; }
h1 {
  font-size: 19pt; color: #1a3a5c; margin: 0 0 4px 0; padding-bottom: 9px;
  border-bottom: 2.5px solid #1a3a5c; letter-spacing: .5px;
}
h2 {
  font-size: 13pt; color: #1a3a5c; margin: 20px 0 8px 0; padding-bottom: 5px;
  border-bottom: 1px dashed #c3d4e3; page-break-after: avoid;
}
h3 { font-size: 11pt; color: #2c5f8a; margin: 14px 0 5px 0; page-break-after: avoid; }
p { margin: 0 0 7px 0; }
ul { margin: 5px 0 10px 0; padding-left: 21px; }
li { margin-bottom: 4px; }
strong { color: #0d1b2a; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9pt;
       background: #f0f3f6; padding: 1px 4px; border-radius: 3px; color: #a11; }
pre { background: #f6f8fa; border-left: 3px solid #1a3a5c; border-radius: 3px;
      padding: 9px 12px; margin: 9px 0; page-break-inside: avoid; }
pre code { background: none; color: #1a2e44; font-size: 8.8pt; padding: 0;
           line-height: 1.5; white-space: pre-wrap; }
blockquote {
  margin: 10px 0; padding: 8px 13px; background: #f7fafd;
  border-left: 3px solid #1a3a5c; color: #223355; font-size: 10pt;
  page-break-inside: avoid;
}
blockquote p { margin: 0 0 4px 0; }
table { width: 100%; border-collapse: collapse; margin: 9px 0; font-size: 9.5pt;
        page-break-inside: avoid; }
th { background: #eef4fa; color: #1a3a5c; text-align: left; font-weight: 600;
     padding: 6px 9px; border: 1px solid #cfdde9; }
td { padding: 6px 9px; border: 1px solid #e2eaf2; vertical-align: top; }
hr { border: none; border-top: 1px solid #e5e7eb; margin: 15px 0; }
"""


def inline(text):
    out = html.escape(text)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    return out


def md_to_html(md_text, title):
    lines = md_text.split("\n")
    buf, i, n = [], 0, len(lines)

    while i < n:
        s = lines[i].strip()

        if s.startswith("```"):
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            buf.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
            continue

        if not s:
            i += 1
            continue

        if re.fullmatch(r"-{3,}|\*{3,}", s):
            buf.append("<hr>")
            i += 1
            continue

        if s.startswith("|") and i + 1 < n and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                r = lines[i].strip()
                if not re.match(r"^\|[\s:|-]+\|$", r):
                    rows.append([c.strip() for c in r.strip("|").split("|")])
                i += 1
            cols = max(len(r) for r in rows)
            buf.append("<table>")
            for ri, row in enumerate(rows):
                tag = "th" if ri == 0 else "td"
                buf.append("<tr>" + "".join(
                    f"<{tag}>{inline(row[c] if c < len(row) else '')}</{tag}>"
                    for c in range(cols)) + "</tr>")
            buf.append("</table>")
            continue

        if s.startswith(">"):
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            buf.append("<blockquote>" + "".join(
                f"<p>{inline(q)}</p>" for q in quote if q) + "</blockquote>")
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            level, text = len(m.group(1)), m.group(2).replace("`", "")
            tag = {1: "h1", 2: "h2"}.get(level, "h3")
            buf.append(f"<{tag}>{inline(text)}</{tag}>")
            i += 1
            continue

        m = re.match(r"^([-*]|\d+\.)\s+(.*)$", s)
        if m:
            items = []
            while i < n:
                mm = re.match(r"^([-*]|\d+\.)\s+(.*)$", lines[i].strip())
                if not mm:
                    break
                items.append(inline(mm.group(2)))
                i += 1
            buf.append("<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>")
            continue

        buf.append(f"<p>{inline(s)}</p>")
        i += 1

    return (
        f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">'
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head>"
        f'<body><div class="page">' + "\n".join(buf) + "</div></body></html>"
    )


def main():
    if not os.path.exists(CHROME):
        sys.exit(f"找不到 Chrome：{CHROME}")

    os.makedirs(OUT_DIR, exist_ok=True)
    mds = sorted(f for f in os.listdir(BASE) if f.endswith(".md"))
    if not mds:
        sys.exit("cases\\ 下没有 .md 文件")

    for fn in mds:
        src = os.path.join(BASE, fn)
        md = open(src, encoding="utf-8").read()
        stem = fn[:-3]
        html_path = os.path.join(BASE, f"_tmp_{stem}.html")
        pdf_path = os.path.join(OUT_DIR, stem + ".pdf")

        open(html_path, "w", encoding="utf-8").write(md_to_html(md, stem))

        left = len(re.findall(r"【[^】]*】", md))
        flag = ""
        if left:
            flag = f"  ⚠ 还有 {left} 处【】占位符，别直接发出去"

        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--no-pdf-header-footer", "--virtual-time-budget=10000",
             f"--print-to-pdf={pdf_path}",
             "file:///" + html_path.replace("\\", "/")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        os.remove(html_path)

        if os.path.exists(pdf_path):
            kb = os.path.getsize(pdf_path) / 1024
            print(f"  ✓ {stem}.pdf  ({kb:,.0f} KB){flag}")
        else:
            print(f"  ✗ {stem}.pdf 生成失败")

    print(f"\n输出目录：{OUT_DIR}")


if __name__ == "__main__":
    main()
