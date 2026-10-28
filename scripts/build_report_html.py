"""Make a browser/clipboard version of the talk from its Markdown source."""
import base64
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inline(text):
    escaped = html.escape(text)
    return re.sub(r"https://[^\s]+", lambda m: f'<a style="text-decoration:underline;color:#1155cc" href="{m[0]}">{m[0]}</a>', escaped)


def main():
    source = (ROOT / "artifacts/report.md").read_text(encoding="utf-8")
    parts = []
    for block in source.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("[[FIGURE:"):
            name = block.removeprefix("[[FIGURE:").removesuffix("]]")
            data = base64.b64encode((ROOT / f"artifacts/code/{name}.png").read_bytes()).decode()
            parts.append(f'<p style="margin:16px 0 4px"><img alt="{name}" width="600" src="data:image/png;base64,{data}"></p>')
        elif block.startswith("## "):
            parts.append(f'<h2 style="color:#000;text-decoration:none;font-size:17pt;margin-top:22pt">{inline(block[3:])}</h2>')
        elif block.startswith("# "):
            parts.append(f'<h1 style="color:#000;text-decoration:none;font-size:23pt;margin:0 0 12pt">{inline(block[2:])}</h1>')
        else:
            for line in block.splitlines():
                small = line.startswith(("Слайд", "На слайде", "Рисунок", "Полный текст", "Материалы для"))
                size = "10" if small else "11"
                color = "#444444" if small else "#000000"
                parts.append(f'<p style="font-size:{size}pt;color:{color};text-decoration:none;line-height:1.3;margin:0 0 9pt">{inline(line)}</p>')
    body = '<div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto">' + "\n".join(parts) + "</div>"
    (ROOT / "artifacts/report-clipboard.html").write_text(body, encoding="utf-8")
    (ROOT / "artifacts/report.html").write_text(
        '<!doctype html><html lang="ru"><meta charset="utf-8"><title>Доклад о RAG</title>'
        '<body style="margin:48px;background:white">' + body + '</body></html>', encoding="utf-8")
    spoken = []
    for block in source.split("\n\n"):
        if block.startswith("## Литература"):
            break
        if block.startswith(("#", "Слайд", "На слайде", "Рисунок", "[[", "Полный текст")):
            continue
        spoken.append(block)
    print(f"Spoken words: {len(re.findall(r'\S+', ' '.join(spoken)))}")


if __name__ == "__main__":
    main()
