# TaskBoard 1.0

Учебный проект TaskBoard — небольшой сервис задач. Это документация демонстрационного проекта, а не инструкция запуска самого RAG.

## Требования

Для локального запуска TaskBoard требуются Python 3.12 и PostgreSQL 16. Перед запуском создайте базу данных taskboard. Команды ниже выполняются в корне TaskBoard.

## Настройка и запуск

Скопируйте файл .env.example в .env. Укажите DATABASE_URL=postgresql://localhost:5432/taskboard и APP_PORT=8000. Для своего сервера добавьте собственные учётные данные к DATABASE_URL; не публикуйте их.

Установите зависимости командой pip install -r requirements.txt. Примените миграции командой alembic upgrade head. Запустите приложение командой uvicorn app.main:app --port 8000. Откройте http://localhost:8000/docs для проверки API.

## Проверка запуска

Запрос GET /health должен вернуть JSON {"status":"ok"}. Если база недоступна, проверьте DATABASE_URL и наличие базы taskboard. Этот раздел не описывает настройку HTTPS и промышленное развёртывание.
