# Выпуск и восстановление

Я отметил прототип тегом v0.1.0, завершённую версию — v1.0.0.
Выпуски находятся в [GitHub Releases](https://github.com/DanilaSm08/Creditsoft/releases).
Для v1.0.0 я подготовил wheel, sdist, архив исходников, архив результатов проверок,
отчёты DOCX/PDF и SHA256SUMS.txt. Скрипт tools/publish_release.py загружает файлы
и повторно скачивает их для проверки SHA-256.

## Развёртывание

Я использовал Django 5.2, Python 3.12, PostgreSQL 16, Nginx и Gunicorn.
Запрос проходит браузер → Nginx:8080 → Gunicorn:8000 → PostgreSQL:5432.
Модули Django взаимодействуют внутри приложения.

```powershell
.\.venv\Scripts\python.exe tools/bootstrap.py
docker compose up -d --build
.\.venv\Scripts\python.exe tools/smoke.py
docker compose logs --tail 100 web nginx
```

Я проверил /health/, вход, сохранение анкеты, расчёт, предыдущий результат
и сохранность данных после перезапуска.

## Резервное копирование

```powershell
.\.venv\Scripts\python.exe tools/backup.py backup
```

Скрипт сохраняет custom-format pg_dump в .local/backups и проверяет оглавление
командой pg_restore --list. Копия содержит данные пользователей и остаётся локально.

## Восстановление

```powershell
docker compose stop web
.\.venv\Scripts\python.exe tools/backup.py restore .local/backups/<file>.dump --replace-database
docker compose start web
.\.venv\Scripts\python.exe tools/smoke.py
```

Восстановление заменяет содержимое выбранной БД. При откате используется версия
приложения, совместимая со схемой сохранённой копии.

## Формирование отчётов

```powershell
.\.venv\Scripts\python.exe tools/collect_evidence.py
.\.venv\Scripts\python.exe tools/capture_evidence.py
.\.venv\Scripts\python.exe tools/build_reports.py
powershell -File tools/render_reports_docker.ps1
.\.venv\Scripts\python.exe tools/inspect_reports.py
.\.venv\Scripts\python.exe tools/publish_release.py
```
