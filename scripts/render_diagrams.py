"""Draw slide-ready explanatory figures without imitating real product screens."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/code"
FONT = "C:/Windows/Fonts/segoeui.ttf"
MONO = "C:/Windows/Fonts/consola.ttf"


def canvas(title, subtitle):
    image = Image.new("RGB", (1600, 900), "#f7f9fc")
    draw = ImageDraw.Draw(image)
    draw.text((60, 38), title, font=ImageFont.truetype(FONT, 44), fill="#13263e")
    draw.text((62, 106), subtitle, font=ImageFont.truetype(FONT, 26), fill="#526377")
    return image, draw


def text(draw, xy, value, size=30, color="#18334e", mono=False):
    draw.multiline_text(xy, value, font=ImageFont.truetype(MONO if mono else FONT, size),
                        fill=color, spacing=12)


def box(draw, bounds, title, detail):
    x, y, right, bottom = bounds
    draw.rounded_rectangle(bounds, radius=16, fill="white", outline="#bdccdc", width=2)
    text(draw, (x + 24, y + 22), title, 30)
    text(draw, (x + 24, y + 78), detail, 24, "#526377")


def arrow(draw, x1, y, x2):
    draw.line((x1, y, x2, y), fill="#3270ae", width=4)
    draw.polygon([(x2, y), (x2 - 13, y - 9), (x2 - 13, y + 9)], fill="#3270ae")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    image, draw = canvas("Два процесса в RAG", "Один корпус документации TaskBoard 1.0")
    text(draw, (60, 185), "Заранее — подготовка базы", 32)
    for bounds, title, detail in [
        ((60, 250, 380, 420), "Документы", "Markdown\nЗаголовки и версии"),
        ((450, 250, 770, 420), "Фрагменты", "Разделы и части\nСохранённый источник"),
        ((840, 250, 1160, 420), "Embeddings", "bge-m3\nТекст → вектор"),
        ((1230, 250, 1540, 420), "Qdrant", "Вектор + текст\n+ метаданные"),
    ]:
        box(draw, bounds, title, detail)
    for start, end in [(385, 440), (775, 830), (1165, 1220)]:
        arrow(draw, start, 335, end)
    text(draw, (60, 485), "При каждом вопросе — поиск и ответ", 32)
    for bounds, title, detail in [
        ((60, 550, 380, 740), "Вопрос", "Текст → вектор\nТа же bge-m3"),
        ((450, 550, 770, 740), "Поиск", "До 4 фрагментов\nиз Qdrant"),
        ((840, 550, 1160, 740), "Генерация", "Вопрос + контекст\n→ qwen2.5:3b"),
        ((1230, 550, 1540, 740), "Результат", "Ответ\nи источники"),
    ]:
        box(draw, bounds, title, detail)
    for start, end in [(385, 440), (775, 830), (1165, 1220)]:
        arrow(draw, start, 645, end)
    text(draw, (60, 810), "Документы обновляются через индекс. Веса модели при обычном запросе не меняются.", 26)
    image.save(OUT / "00_architecture.png")

    image, draw = canvas("Самостоятельный запуск", "Подготовленные команды для слайда — без ожидания загрузок во время выступления")
    rows = [
        (195, "1  Запустить сервисы", "docker compose up -d qdrant ollama"),
        (325, "2  Заранее скачать модели", "docker compose exec ollama ollama pull bge-m3\ndocker compose exec ollama ollama pull qwen2.5:3b"),
        (510, "3  Построить индекс", "python -m rag_demo index knowledge"),
        (640, "4  Задать вопрос", 'python -m rag_demo ask "Как настроить и запустить TaskBoard?"'),
    ]
    for y, heading, command in rows:
        text(draw, (65, y), heading, 30)
        text(draw, (65, y + 52), command, 27, "#295c8e", mono=True)
    text(draw, (65, 815), "Python выполняется в активированном окружении .venv. Команды полностью приведены в README.", 24)
    image.save(OUT / "06_deployment.png")

    image, draw = canvas("Тот же корпус в AnythingLLM", "Схема действий по документации продукта — не снимок работающего интерфейса")
    box(draw, (60, 200, 780, 450), "1  Запуск и подключение моделей",
        "docker compose --profile ready up -d anythingllm\nБраузер: localhost:3001\nOllama: http://ollama:11434\nLLM: qwen2.5:3b   •   Embeddings: bge-m3")
    box(draw, (820, 200, 1540, 450), "2  Рабочее пространство",
        "Создать TaskBoard 1.0\nЗагрузить те же три Markdown-файла\nДобавить их в workspace с индексацией\nНе ограничиваться вложением в чат")
    box(draw, (60, 510, 780, 760), "3  Вопрос по документам",
        "Выбрать Query Mode\nЗадать вопрос о настройке и запуске\nСравнить с вопросом кодовой реализации\nПроверить отказ при отсутствии данных")
    box(draw, (820, 510, 1540, 760), "4  Проверка источников",
        "Раскрыть найденные источники\nСопоставить команды с getting-started.md\nПроверить версию документации\nНе считать наличие ссылки гарантией")
    text(draw, (60, 815), "AnythingLLM строит свой индекс. В этом варианте используется встроенное хранилище LanceDB.", 26)
    image.save(OUT / "07_anythingllm.png")


if __name__ == "__main__":
    main()
