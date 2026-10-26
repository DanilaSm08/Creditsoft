# CreditSoft 1.0.0

Я реализовал веб-приложение для оценки кредитоспособности: регистрация → вход →
анкета → расчёт нагрузки и рейтинга → подбор предложений → сохранённый результат.
Исходный код: [DanilaSm08/Creditsoft](https://github.com/DanilaSm08/Creditsoft).

## Запуск в PowerShell

Требуются Python 3.12+, Git и Docker Desktop. Команды выполняются из папки проекта.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe tools/bootstrap.py
docker compose up -d --build
```

Приложение: http://127.0.0.1:8080/. Проверка БД: http://127.0.0.1:8080/health/.
При старте выполняются миграции, сборка статики и заполнение каталога.
PostgreSQL сохраняет данные в именованном томе.
Остановка с сохранением данных: `docker compose down`.

## Демонстрация

1. Зарегистрировать пользователя и войти.
2. Заполнить личную часть анкеты.
3. Указать доход 100 000 руб., платежи 15 000 руб., сумму кредита 300 000 руб.,
   срок 36 месяцев, стаж 48 месяцев.
4. Сохранить анкету и выполнить расчёт: нагрузка 15%, рейтинг 900, четыре предложения.
5. Изменить платежи на 80 000 руб. и пересчитать: нагрузка 80%, рейтинг 550,
   подходящих предложений нет.
6. Открыть предыдущий результат: его значения сохраняются после изменения анкеты.
7. Выйти, войти повторно и показать сохранённые данные.

Я также создал запись `demo` для проверки развёртывания.
Пароль хранится в `.local/demo_credentials.json`.
При новом развёртывании командой `python tools/smoke.py` создаётся проверочная запись.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe tools/check.py --stage local --e2e
.\.venv\Scripts\python.exe tools/smoke.py
python -m http.server 8090 --bind 127.0.0.1 --directory artifacts/runs/release
```

HTML-отчёт: http://127.0.0.1:8090/tests.html.
Покрытие: http://127.0.0.1:8090/coverage/.
Я проверил 91 тест на SQLite и PostgreSQL, включая два сценария Chromium.
Покрытие строк и ветвей модулей `core` составляет 100%;
область измерения задана в pyproject.toml.

Для проверки PostgreSQL используются переменные POSTGRES_HOST, POSTGRES_PORT,
POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD.
Порт локального сервера — 55432, пароль — в `.local/postgres_password`.
Артефакты находятся в `artifacts/runs/<этап>/`: JUnit, HTML, coverage,
метрики, карта требований и пакеты wheel/sdist.

## GitHub

Я организовал задачи в [Issues](https://github.com/DanilaSm08/Creditsoft/issues),
объединение изменений — через [Pull requests](https://github.com/DanilaSm08/Creditsoft/pulls),
проверки — в [Actions](https://github.com/DanilaSm08/Creditsoft/actions),
выпуски — в [Releases](https://github.com/DanilaSm08/Creditsoft/releases).

Workflow `.github/workflows/ci.yml` использует Python 3.12, PostgreSQL 16 и Chromium.
Он выполняет Ruff, проверку коммитов, миграций, тесты, измерение покрытия и сборку.
Результаты публикуются в артефакте quality-evidence.

```powershell
git config core.hooksPath .githooks
git switch -c feature/example
git add <files>
git commit -m "feat: добавил новый сценарий"
git push -u origin feature/example
```

Я использую Conventional Commits. Основная ветка принимает изменения через pull request
с успешной обязательной проверкой quality.
Для скриптов GitHub установленный `gh` либо переносимая копия
`.local/github-cli/gh.exe` должны быть авторизованы командой auth login.

## Документация и отчёты

- [Архитектура и последовательность вызовов](docs/ARCHITECTURE.md).
- [Правила скоринга](docs/SCORING.md).
- [Прототип v0.1.0](docs/PROTOTYPE.md).
- [Тестирование](docs/TESTING.md).
- [Выпуск и восстановление](docs/RELEASE.md).
- Отчёты DOCX/PDF: reports/Lab_5 — reports/Lab_8.
- [Архив отчётов в релизе](https://github.com/DanilaSm08/Creditsoft/releases/tag/v1.0.0).
- Данные проверок: docs/evidence; скриншоты: docs/images.

Я формирую отчёты командами tools/collect_evidence.py и tools/build_reports.py.
Зависимости генератора находятся в requirements-reports.txt.
Экспорт PDF: powershell -File tools/render_reports_docker.ps1.
Проверка страниц: python tools/inspect_reports.py.
