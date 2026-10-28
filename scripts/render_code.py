"""Create faithful, syntax-highlighted images from real source line ranges."""
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.styles import get_style_by_name

ROOT = Path(__file__).resolve().parents[1]
SPECS = [
    ("01_documents", "rag_demo/documents.py", 11, 31),
    ("02_index", "rag_demo/pipeline.py", 31, 51),
    ("03_search", "rag_demo/pipeline.py", 65, 74),
    ("04_answer", "rag_demo/pipeline.py", 76, 96),
    ("05_api", "rag_demo/api.py", 26, 43),
]


def main():
    destination = ROOT / "artifacts/code"
    destination.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 25)
    title_font = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 25)
    style = get_style_by_name("friendly")
    manifest = []
    for name, filename, first, last in SPECS:
        raw_lines = (ROOT / filename).read_text(encoding="utf-8").splitlines()
        last = min(last, len(raw_lines))
        code = textwrap.dedent("\n".join(raw_lines[first - 1:last])) + "\n"
        lines = code.splitlines()
        width = max(1000, int(max(font.getlength(line) for line in lines)) + 130)
        height = 90 + 35 * len(lines) + 25
        image = Image.new("RGB", (width, height), "#ffffff")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, width, 65), fill="#eef2f6")
        draw.text((26, 16), f"{filename}    |    {first}–{last}",
                  font=title_font, fill="#24364b")
        for i in range(len(lines)):
            draw.text((20, 86 + i * 35), str(first + i), font=font, fill="#8794a3")
        x, y = 95.0, 86
        for token, value in lex(code, PythonLexer()):
            color = style.style_for_token(token)["color"] or "202b39"
            parts = value.split("\n")
            for i, part in enumerate(parts):
                if i:
                    x, y = 95.0, y + 35
                if part:
                    draw.text((x, y), part, font=font, fill=f"#{color}")
                    x += font.getlength(part)
        image.save(destination / f"{name}.png")
        manifest.append({"id": name, "file": filename, "first_line": first,
                         "last_line": last, "width": width, "height": height})
    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
