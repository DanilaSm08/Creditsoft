# CreditSoft 1.0.0

Учебное веб-приложение оценки кредитоспособности по лабораторным работам КПО.
Регистрация → вход → сохранение анкеты → оценка нагрузки и рейтинга → подбор
предложений → просмотр сохранённого результата. Доступ к данным ограничен владельцем.
Банки в каталоге вымышлены; внешние банки и БКИ не вызываются.

## Запуск в Windows / Docker Desktop

Все команды выполняются из этой папки в PowerShell. Требуются Python 3.12+, Git и Docker Compose.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe tools/bootstrap.py
docker compose up -d --build
```

Адрес: http://127.0.0.1:8080/. Проверка БД: http://127.0.0.1:8080/health/.
При старте выполняются миграции, сборка статики и идемпотентное заполнение каталога.
PostgreSQL хранит данные в отдельном томе. Остановка с сохранением данных: `docker compose down`.
`down -v` удаляет данные и для обычной остановки не требуется.

Можно зарегистрировать новую учётную запись. Для проверки на этом компьютере создана
учебная запись `demo`; пароль находится в локальном файле `.local/demo_credentials.json`.
Пароли и ключи не включены в Git и отчёты. При новом развёртывании этот файл создаёт
`tools/smoke.py`, который проверяет реальный интерфейс запущенного приложения.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe tools/check.py --stage local --e2e
.\.venv\Scripts\python.exe tools/smoke.py
```

Первая команда запуска проверок использует SQLite по умолчанию; для PostgreSQL задаются
`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.
Пароль установленной БД лежит в `.local/postgres_password`; порт хоста — 55432.
Результаты: `artifacts/runs/<этап>/tests.html`, `coverage/index.html`, `junit.xml`,
`coverage.xml`, `metrics.json`, `test-map.json`, `dist/`. Сборка wheel/sdist начинается
только после успешных lint, форматирования, проверки миграций и тестов.

Для просмотра HTML из кириллического пути используйте локальный HTTP-сервер:
`python -m http.server 8090 --bind 127.0.0.1 --directory artifacts/runs/release`.
Отчёт: http://127.0.0.1:8090/tests.html, покрытие: http://127.0.0.1:8090/coverage/.
Прямое открытие `file://` в Chromium нарушает работу History API pytest-html.

91 тест, включая два сценария Chromium, проверены на SQLite и PostgreSQL.
100% строк и ветвей относится к измеряемому Python-коду `core`, без миграций и
служебных команд. Это не измерение покрытия HTML/CSS/JavaScript и не гарантия отсутствия ошибок.

## Репозиторий и CI

Рабочий Git-хостинг: http://localhost:3030/student/CreditSoft.
Это отдельный локальный Gitea с Actions, задачами, защищённой веткой main и релизами.
Вход администратора `student`, пароль — `.local/gitea_password`.
Запуск существующего хостинга: `docker compose -f infra/forge.compose.yaml up -d`.
Для первоначального создания: `tools/bootstrap.py`, запуск сервиса `gitea`,
`tools/forge.py init`, затем запуск `runner`. Runner использует локальный Docker Engine.

Разработка ведётся в `feature/*` и `release/*`, слияние — через PR с успешной проверкой
`CreditSoft CI / quality (pull_request)`. Прямой push в main и слияние при упавшем CI
отклонены в реальных проверках. Локальный hook проверяет Conventional Commits;
серверный pipeline повторяет проверку истории.

```powershell
git config core.hooksPath .githooks
git switch -c feature/example
# после изменения и проверки файлов:
git add <files>
git commit -m "feat: describe change"
.\.venv\Scripts\python.exe tools/forge.py push -- -u origin feature/example
```

`.gitea/workflows/ci.yml` фактически выполняется локальным runner. Файл
`.github/workflows/ci.yml` подготовлен для GitHub с PostgreSQL; запуск на GitHub
не подтверждён, поскольку текущая авторизация возвращает 401.
Исходная доска YouGile требует доступа: 30 задач перенесены из таблицы ЛР3 в Gitea,
без имитации экспорта или изменения YouGile. Даты локальных карточек отражают эту сессию.

## Документация и отчёты

- [Архитектура, компоненты и последовательность вызовов](docs/ARCHITECTURE.md).
- [Правила учебного скоринга](docs/SCORING.md).
- [Прототип v0.1.0](docs/PROTOTYPE.md).
- [Тестирование и границы проверок](docs/TESTING.md).
- [Релиз, резервное копирование и восстановление](docs/RELEASE.md).
- Отчёты Word/PDF: `reports/Lab_5` — `reports/Lab_8`; копии Word находятся рядом с ЛР1–4.
- Доказательства: `docs/evidence/`; автоматические графики: `docs/images/statistics/`.
- Повторная сборка отчётов: установить `requirements-reports.txt`, затем выполнить
  `python tools/collect_evidence.py`, `python tools/build_reports.py`. Экспорт PDF:
  `powershell -File tools/render_reports.ps1` (установленный Microsoft Word).
  Если экспорт Word недоступен: `powershell -File tools/render_reports_docker.ps1`
  (изолированный LibreOffice; установленные шрифты Windows подключаются только для чтения).
  Проверка страниц: `python tools/inspect_reports.py`.

Репозиторий содержит воспроизводимый код, конфигурации, снимки результатов и исходники
генераторов. Полные отчёты и архивы проверок приложены к релизу v1.0.0 в локальном Gitea.
Время разработки учитывается по наблюдаемым этапам с автоматизированной помощью;
оно не выдаётся за индивидуальные часы работы студента.
