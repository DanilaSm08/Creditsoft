"""Build four evidence-based Russian DOCX reports using the Lab 1–4 cover style."""

import json
import shutil
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "docs/evidence"
REPORTS = ROOT / "reports"


def read(name):
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


class Report:
    def __init__(self, number, title):
        self.number = number
        self.document = Document()
        self.figures = 0
        self.tables = 0
        doc = self.document
        section = doc.sections[0]
        section.page_width, section.page_height = Cm(21), Cm(29.7)
        section.top_margin = section.bottom_margin = Cm(2)
        section.left_margin, section.right_margin = Cm(2.5), Cm(1.5)
        section.different_first_page_header_footer = True
        normal = doc.styles["Normal"]
        normal.font.name = "Times New Roman"
        normal.font.size = Pt(14)
        normal.paragraph_format.line_spacing = 1.15
        normal.paragraph_format.space_after = Pt(6)
        normal.paragraph_format.first_line_indent = Cm(1.25)
        for name, size in [("Heading 1", 16), ("Heading 2", 14)]:
            style = doc.styles[name]
            style.font.name = "Times New Roman"
            style.font.size = Pt(size)
            style.font.color.rgb = RGBColor(0, 0, 0)
            style.paragraph_format.first_line_indent = Cm(0)
            style.paragraph_format.keep_with_next = True
        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer.paragraph_format.first_line_indent = Cm(0)
        field = OxmlElement("w:fldSimple")
        field.set(qn("w:instr"), "PAGE")
        footer._p.append(field)
        cover = [
            "Министерство науки и высшего образования Российской Федерации",
            "Федеральное государственное бюджетное образовательное учреждение высшего образования",
            "«УЛЬЯНОВСКИЙ ГОСУДАРСТВЕННЫЙ ТЕХНИЧЕСКИЙ УНИВЕРСИТЕТ»",
            "",
            "Факультет информационных систем и технологий",
            "Кафедра «Информационные системы»",
            "",
            "Дисциплина «Конструирование программного обеспечения»",
            "",
            "",
            f"Лабораторная работа №{number}",
            title,
            "",
            "",
        ]
        for text in cover:
            p = doc.add_paragraph(text)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_after = Pt(4)
        for text in [
            "Выполнил:",
            "студент гр. ПИбд-42",
            "Смолин Д.С.",
            "",
            "Проверил:",
            "Романов А. А.",
        ]:
            p = doc.add_paragraph(text)
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_after = Pt(0)
        p = doc.add_paragraph("Ульяновск\n2026")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_before = Pt(28)
        doc.add_page_break()

    def h(self, text):
        self.document.add_heading(text, level=1)

    def p(self, text):
        p = self.document.add_paragraph(text)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    def table(self, caption, headers, rows, widths=None):
        self.tables += 1
        p = self.document.add_paragraph(f"Таблица {self.tables} — {caption}")
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.keep_with_next = True
        table = self.document.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"
        table.autofit = False
        if widths:
            for column, width in zip(table.columns, widths, strict=True):
                column.width = Cm(width)
        header = table.rows[0]
        repeat = OxmlElement("w:tblHeader")
        header._tr.get_or_add_trPr().append(repeat)
        for cell, value in zip(header.cells, headers, strict=True):
            cell.text = str(value)
            shade = OxmlElement("w:shd")
            shade.set(qn("w:fill"), "E7EFF3")
            cell._tc.get_or_add_tcPr().append(shade)
        for values in rows:
            for cell, value in zip(table.add_row().cells, values, strict=True):
                cell.text = str(value)
        for row_index, row in enumerate(table.rows):
            cant_split = OxmlElement("w:cantSplit")
            row._tr.get_or_add_trPr().append(cant_split)
            for index, cell in enumerate(row.cells):
                if widths:
                    cell.width = Cm(widths[index])
                for p in cell.paragraphs:
                    p.paragraph_format.first_line_indent = Cm(0)
                    p.paragraph_format.space_after = Pt(3)
                    p.paragraph_format.line_spacing = 1.0
                    for run in p.runs:
                        run.font.size = Pt(11)
                        run.bold = row_index == 0
        self.document.add_paragraph().paragraph_format.space_after = Pt(0)

    def figure(self, path, caption):
        path = ROOT / path
        if not path.exists():
            raise FileNotFoundError(path)
        self.figures += 1
        with Image.open(path) as img:
            width, height = img.size
        scale = min(16 / width, 15.5 / height)
        p = self.document.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.keep_with_next = True
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(path), width=Cm(width * scale))
        p = self.document.add_paragraph(f"Рисунок {self.figures} — {caption}")
        p.paragraph_format.first_line_indent = Cm(0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.size = Pt(11)

    def finish(self):
        self.h("Источники и воспроизведение")
        self.p(
            "Исходные требования: задания лабораторных работ №5–8 КПО 2026; контекст проекта: Lab_1.docx–Lab_4.docx. Базовый список задач и оценки взяты из ЛР3, архитектура — из ЛР4. Исходные отчёты не изменялись."
        )
        self.p(
            "Рабочая папка: D:\\STUDY\\КПО\\CreditSoft. Репозиторий: http://localhost:3030/student/CreditSoft. Приложение: http://127.0.0.1:8080/. Инструкции: README.md. Доказательства: docs/evidence, изображения: docs/images, полные тестовые отчёты: artifacts/runs. Этот документ сформирован tools/build_reports.py по сохранённым результатам выполнения."
        )
        self.p(
            "Документация инструментов: https://docs.djangoproject.com/en/5.2/; https://docs.pytest.org/; https://playwright.dev/python/; https://docs.gitea.com/usage/actions/overview; https://docs.astral.sh/ruff/; https://www.conventionalcommits.org/ru/v1.0.0/."
        )
        REPORTS.mkdir(exist_ok=True)
        path = REPORTS / f"Lab_{self.number}.docx"
        self.document.save(path)
        shutil.copy2(path, ROOT.parent / path.name)
        print(f"{path.name}: {self.figures} figures, {self.tables} tables")


def lab5(summary, tasks):
    r = Report(5, "Управление исходным кодом и отслеживание метрик")
    r.h("1 Цель и исходные условия")
    r.p(
        "Цель работы — создать управляемый репозиторий CreditSoft, автоматизировать контроль изменений, тестирование, сборку и измерение качества. Предметная область — учебная оценка кредитоспособности физического лица по анкете с подбором предложений из локального каталога."
    )
    r.p(
        "Использован Gitea 1.24.6 — система хостинга Git-проектов с задачами, pull request, Actions и релизами. Сервер и runner act_runner 0.2.13 развёрнуты в Docker на локальном компьютере. GitHub через доступную авторизацию возвращал HTTP 401; работающий хостинг не выдаётся за удалённый GitHub. Файл workflow для GitHub подготовлен, но его выполнение там не подтверждено."
    )
    r.figure(
        "docs/images/infrastructure/repository.png",
        "Реальный репозиторий CreditSoft в локальном Gitea",
    )
    r.h("2 Структура репозитория и правила изменений")
    r.table(
        "Назначение основных каталогов",
        ["Путь", "Содержимое"],
        [
            ("core/", "Модели, формы, прикладная логика, шаблоны и статические ресурсы"),
            ("creditsoft/", "Настройки Django, маршрутизация и WSGI"),
            ("tests/", "Модульные, интеграционные и браузерные проверки"),
            (
                ".gitea/workflows/; .github/workflows/",
                "Действующий локальный CI; подготовленный вариант GitHub",
            ),
            ("tools/; .githooks/", "Сборка, метрики, отчёты, работа с Gitea; проверка сообщений"),
            (
                "infra/; Dockerfile; compose.yaml",
                "Nginx, сервер Gitea/runner, приложение и PostgreSQL",
            ),
            (
                "docs/; reports/; artifacts/",
                "Документация, доказательства, Word/PDF, полные результаты проверок",
            ),
        ],
        [5.2, 11.8],
    )
    r.p(
        "Используется поток коротких веток: main содержит интегрированное состояние; feature/prototype и feature/assessment — функциональные инкременты; release/1.0.0 — подготовка выпуска. Ветка ci/protection-probe содержит только намеренно падающую проверку защиты и в main не сливалась. Изменение проходит локальные проверки, push, PR, серверный CI и merge. Локальные секреты и окружение исключены через .gitignore."
    )
    r.p(
        "Сообщение коммита имеет форму type(scope): description либо type: description. Используются feat, fix, test, docs, ci, chore. Пример: feat: implement questionnaire prototype. Hook commit-msg вызывает tools/commit_message.py; CI повторяет проверку истории, поэтому обход локального hook не отменяет серверную проверку. Автоматические merge-сообщения разрешены отдельно."
    )
    r.table(
        "Проверенные ограничения",
        ["Проверка", "Результат и доказательство"],
        [
            (
                "Некорректное сообщение invalid message",
                "Отклонено, код возврата 1; protection-proof.json",
            ),
            (
                "Прямой push в main",
                "Отклонён; правило запрещает push и force-push; protection-proof.json",
            ),
            (
                "PR №32 с намеренно падающим тестом",
                "Слияние отклонено API HTTP 405 при failure обязательного CI; PR закрыт без merge",
            ),
            (
                "PR №31 / №33",
                "Прототип и основной функционал слиты после успешного обязательного CI",
            ),
            ("Обход администратором", "block_admin_merge_override=true; обход проверок запрещён"),
        ],
        [6, 11],
    )
    r.p(
        "Обязательный контекст: CreditSoft CI / quality (pull_request). Устаревшая относительно main ветка также блокируется. Обязательные одобрения ревью не включены: репозиторий учебный, с одним исполнителем; независимое ревью не имитируется."
    )
    r.figure("docs/images/infrastructure/branches.png", "Настройка защиты основной ветки")
    r.figure(
        "docs/images/infrastructure/merged-prototype.png",
        "Слияние прототипа через pull request №31",
    )
    r.h("3 Pipeline качества и сборки")
    r.p(
        "События push и pull_request запускают checkout, Python 3.12, установку фиксированных зависимостей, проверку коммитов и Chromium. tools/check.py выполняет Ruff, проверку форматирования, проверку отсутствия несозданных миграций, pytest с покрытием и затем сборку wheel/sdist. Сборка не запускается при ошибках предыдущих проверок. Отчёты сохраняются и при неуспехе; публикация готовых пакетов требует успешного этапа качества."
    )
    r.table(
        "Автоматические результаты",
        ["Проверка", "Артефакт / условие"],
        [
            ("Ruff check + format", "lint.json, format.log; 0 замечаний и код завершения 0"),
            ("Django migrations", "migrations.log; makemigrations --check --dry-run"),
            (
                "pytest + Chromium",
                "junit.xml, tests.html, tests.log, test-map.json; все тесты успешны",
            ),
            (
                "coverage.py",
                "coverage.json/xml, HTML; общий порог 85%, строки/ветви показаны отдельно",
            ),
            (
                "Python build",
                "dist/creditsoft-<version>.whl и .tar.gz только после успешных проверок",
            ),
            ("Radon + таймеры", "metrics.json и docs/evidence/metrics/<этап>.json"),
        ],
        [5.5, 11.5],
    )
    r.p(
        "Реальные Gitea Actions выполняют тесты с SQLite; отдельный полный прогон выполнен с PostgreSQL 16, а smoke — через Nginx/Gunicorn. GitHub workflow предусматривает сервис PostgreSQL. Автоматическое развёртывание после merge не включалось: оно является необязательным пунктом задания. Развёртывание Docker Compose выполнено и проверено отдельно."
    )
    r.figure(
        "docs/images/infrastructure/actions.png",
        "История фактически выполненных запусков Gitea Actions",
    )
    r.h("4 Метрики этапов")
    stages = [
        "baseline",
        "prototype-browser",
        "assessment-browser",
        "postgres-regression",
        "release",
    ]
    metrics = [
        read(f"metrics/{name}.json")
        for name in stages
        if (EVIDENCE / f"metrics/{name}.json").exists()
    ]
    r.table(
        "Автоматически измеренные показатели качества",
        ["Этап", "Тесты", "Строки, %", "Ветви, %", "Ruff", "Тесты, с"],
        [
            (
                m["stage"],
                m["tests"]["passed"],
                m["line_coverage_percent"],
                "н/п" if m["stage"] == "baseline" else m["branch_coverage_percent"],
                m["lint_issues"],
                m["test_duration_seconds"],
            )
            for m in metrics
        ],
        [4.4, 1.7, 2.6, 2.4, 1.6, 4.3],
    )
    r.table(
        "Сложность, объём и длительность",
        ["Этап", "CC ср./макс.", "Python-файлы", "SLOC", "Pipeline, с"],
        [
            (
                m["stage"],
                f"{m['mean_complexity']} / {m['max_complexity']}",
                m["source_files"],
                m["source_lines"],
                m["pipeline_seconds"],
            )
            for m in metrics
        ],
        [4.4, 3.1, 3.2, 2, 4.3],
    )
    r.p(
        "Собрано более пяти метрик: ошибки линтера, строковое и ветвевое покрытие, успешные тесты, длительность тестов, средняя и максимальная цикломатическая сложность, объём исходников и длительность pipeline. SLOC/Radon рассчитаны по Python core и creditsoft без миграций. Покрытие относится к core без миграций и management; HTML/CSS/JS в него не входят. На базовом этапе ветвей не было, поэтому показатель ветвевого покрытия неприменим."
    )
    r.p(
        "Время tools/check.py не включает установку Python, зависимостей и браузера в CI. Локальные снимки могли быть сделаны до фиксации текущих изменений: commit обозначает базовый HEAD, а working_tree_dirty — наличие изменений. Проверка в CI относится к точному коммиту из истории Actions. Замеры сделаны после фактических этапов одной сессии, а не задним числом по семестровым датам."
    )
    r.h("5 Выпуск версии и вывод")
    r.p(
        "Прототип помечен аннотированным тегом v0.1.0, завершённая версия — v1.0.0. После успешного PR создаются тег и запись релиза, затем прикладываются wheel/sdist, отчёты и архив доказательств с SHA-256. Воспроизводимые команды и порядок восстановления находятся в docs/RELEASE.md. Репозиторий, ограничения ветки и pipeline реально работают; намеренно падающий контрольный запуск учитывается отдельно от дефектов продукта."
    )
    r.figure("docs/images/infrastructure/releases.png", "Версии проекта в Gitea")
    r.finish()


def lab6(summary, tasks):
    r = Report(6, "Прототипирование")
    r.h("1 Цель и выбранные задачи")
    r.p(
        "Цель прототипа — проверить связный пользовательский путь «регистрация → вход → анкета → валидация → сохранение → повторное открытие» и пригодность Django, ORM, серверных шаблонов и Bootstrap. Выбран вертикальный срез: интерфейс взаимодействует с реальной моделью и базой данных. Рейтинг и предложения в этот этап не входят."
    )
    selected = [
        t
        for t in tasks
        if t["id"] == "PR-01" or t["id"].startswith(tuple(f"CR-0{n}" for n in range(1, 5)))
    ]
    r.table(
        "Состав прототипа по исходному плану",
        ["ID", "Задача", "План, ч"],
        [(t["id"], t["title"], t["planned_hours"]) for t in selected],
        [2.4, 12.3, 2.3],
    )
    r.p(
        f"Всего выбрано {len(selected)} задач, сумма исходных оценок — {sum(t['planned_hours'] for t in selected):g} ч. Реализованный прототип сохранён в теге v0.1.0 и слит через PR №31. Его можно изучать независимо от последующего расширения приложения."
    )
    r.h("2 Реализация и результаты")
    r.p(
        "Django Auth обеспечивает регистрацию с проверкой пароля, хеширование и вход по сессии. Доступ к анкете требует аутентификации. BorrowerProfile хранит сведения о заёмщике, FinancialData — финансовые значения. Владелец определяется сервером по request.user. Обе формы валидируются до записи и сохраняются одной транзакцией; некорректная финансовая часть не оставляет частично обновлённую анкету."
    )
    r.figure("docs/images/prototype/login-desktop.png", "Экран входа работающего прототипа")
    r.figure(
        "docs/images/prototype/questionnaire-desktop.png",
        "Сохранённая анкета с персональной и финансовой частями",
    )
    r.p(
        "Проверяются обязательность, формат паспортных полей, возраст 18–75 лет, допустимые суммы, срок кредита и непротиворечивый стаж. Ошибки показываются рядом с полем, введённые значения сохраняются в форме для исправления. Текущие платежи могут превышать доход: это допустимые входные данные для последующей оценки высокой нагрузки."
    )
    r.figure(
        "docs/images/prototype/validation-desktop.png",
        "Ошибки серверной валидации без частичной записи данных",
    )
    r.figure(
        "docs/images/prototype/questionnaire-mobile.png",
        "Анкета прототипа при ширине экрана 390 px",
    )
    r.h("3 Проверка прототипа")
    m = read("metrics/prototype-browser.json")
    r.table(
        "Фактические результаты этапа",
        ["Показатель", "Результат"],
        [
            ("Тесты", f"{m['tests']['passed']} успешных, включая браузерный сценарий"),
            ("Покрытие измеряемого Python-кода", "100% строк / 100% ветвей"),
            ("Линтер", "0 замечаний Ruff"),
            ("Время тестов", f"{m['test_duration_seconds']} с"),
            (
                "Пользовательский сценарий",
                "Регистрация, вход, неверные данные, сохранение, перезагрузка, мобильная ширина",
            ),
            ("Версия", "v0.1.0; docs/evidence/metrics/prototype-browser.json"),
        ],
        [6, 11],
    )
    r.h("4 Уточнение плана и оценок")
    r.p(
        "Прототип подтвердил возможность выполнить проект модульным монолитом: готовые средства Django закрывают сессии, CSRF, хеширование, формы и транзакции. Отдельный SPA, очередь и микросервисы для выбранного объёма не нужны. Серверная проверка остаётся обязательной независимо от HTML-ограничений. Дополнительно уточнены атомарность двух форм, защита от внешнего перенаправления после входа, границы стажа и поведение на мобильном экране."
    )
    r.p(
        "Следующий инкремент включает CR-05–CR-08: долговую нагрузку, объяснимый рейтинг, каталог, фильтрацию и итоговый экран. Необходимо сохранять снимок входов и предложений, чтобы редактирование анкеты и каталога не меняло уже рассчитанный результат. Правила скоринга оформляются отдельно и проверяются на границах."
    )
    phase = next(p for p in summary["worklog"] if p["phase"] == "prototype")
    r.p(
        f"Измеренная длительность этапа прототипирования — {phase['elapsed_seconds'] / 60:.2f} мин. Это наблюдаемое время этапа с автоматизированной помощью, готовыми библиотеками и параллельной работой инструментов. Оно не равно индивидуальным трудозатратам студента; распределения времени по 13 задачам нет. Исходные оценки не переписывались ради совпадения с фактом. Обсуждение и приёмка преподавателем не проводились; изложены технические выводы, подготовленные для такого обсуждения."
    )
    r.finish()


def lab7(summary, tasks):
    r = Report(7, "Инфраструктура разработки проекта")
    r.h("1 Среда автоматического тестирования")
    r.p(
        "Настроена среда pytest, pytest-django, pytest-cov, pytest-html и pytest-playwright. Зависимости закреплены в requirements-dev.txt, параметры — в pyproject.toml. Быстрый прогон использует SQLite; подтверждающий прогон — PostgreSQL 16. Браузерные сценарии используют Chromium и живой Django test server. CI изолирован в контейнере, тестовая БД отделена от данных рабочего стенда."
    )
    r.table(
        "Уровни проверок",
        ["Уровень", "Что подтверждается"],
        [
            (
                "Модульный",
                "Чистые Decimal-вычисления, граничные баллы, нагрузка, валидация, критерии предложений",
            ),
            (
                "Интеграционный Django + БД",
                "Auth/CSRF, формы и транзакции, фильтрация, снимки результатов, права владельца, повторный расчёт",
            ),
            (
                "Пользовательский Chromium",
                "Полный путь пользователя и отрицательный сценарий; мобильная вёрстка, логотипы, пустые предложения",
            ),
            (
                "Развёрнутый стенд",
                "Nginx → Gunicorn → PostgreSQL, health, вход, анкета, рейтинг 900 и четыре предложения, перезагрузка",
            ),
        ],
        [5, 12],
    )
    r.h("2 Проектирование тестов и ожидаемые результаты")
    r.table(
        "Значимые проверочные случаи",
        ["Вход / действие", "Ожидаемый результат"],
        [
            (
                "Доход 100 000; платежи 15 000; сумма 300 000; стаж 48 месяцев",
                "Нагрузка 15%; баллы 350 + 250 + 300 = 900; 4 предложения по возрастанию ставки",
            ),
            (
                "Нагрузка на границах 10, 30, 50, 70% и сразу выше",
                "Переходы 450 → 350 → 200 → 80 → 0; округление отображения не меняет ветвь расчёта",
            ),
            ("Стаж 0/1/6/12/36 месяцев", "Баллы 0/40/100/180/250; границы включительны"),
            ("Сумма / годовой доход на границах 0.5/1/2", "Баллы 300/220/100, выше 2 — 0"),
            (
                "Пустые поля, Unicode-цифры в паспорте, NaN, нулевой доход, невозможный стаж",
                "Ошибки формы; обе части анкеты не сохраняются частично",
            ),
            (
                "Порог предложения равен рейтингу/сроку/сумме/нагрузке",
                "Граница включается; неактивные предложения исключаются",
            ),
            ("Чужой идентификатор оценки", "404; данные другого пользователя не раскрываются"),
            (
                "Изменение анкеты или каталога после расчёта",
                "Исторический снимок прежний; новый расчёт создаёт новую запись",
            ),
            (
                "POST без CSRF и внешний next при входе",
                "CSRF-запрос отклонён; внешнее перенаправление не выполняется",
            ),
        ],
        [8, 9],
    )
    r.h("3 Соответствие задачам исходного плана")
    r.p(
        "Маркеры requirement связывают тесты с идентификаторами ЛР3. Список собирается при collection в test-map.json; tools/collect_evidence.py проверяет наличие тестов либо отдельного доказательства для каждой из 30 задач. Один сценарий может подтверждать несколько связанных задач; количество привязок не является количеством уникальных тестов."
    )
    rows = []
    for task in tasks:
        files = sorted({test.split("::")[0].removeprefix("tests/") for test in task["tests"]})
        evidence = ", ".join(files) if files else "; ".join(task["artifacts"])
        rows.append((task["id"], task["title"], evidence))
    r.table(
        "Матрица подтверждения всех запланированных задач",
        ["ID", "Планируемый результат", "Тесты / доказательства"],
        rows,
        [2.2, 7.5, 7.3],
    )
    r.h("4 Автоматические отчёты и результаты")
    stages = ["assessment-browser", "postgres-regression", "release"]
    rows = []
    for stage in stages:
        path = EVIDENCE / f"metrics/{stage}.json"
        if path.exists():
            m = json.loads(path.read_text())
            rows.append(
                (
                    stage,
                    m["database"],
                    m["tests"]["passed"],
                    m["tests"]["failures"] + m["tests"]["errors"],
                    f"{m['line_coverage_percent']} / {m['branch_coverage_percent']}",
                    m["test_duration_seconds"],
                )
            )
    r.table(
        "Результаты полного прогона",
        ["Этап", "БД", "Успех", "Ошибки", "Строки / ветви, %", "Время, с"],
        rows,
        [4.1, 2.7, 1.6, 1.9, 3.8, 2.9],
    )
    r.figure("docs/images/infrastructure/tests.png", "Автоматический HTML-отчёт pytest")
    r.figure(
        "docs/images/infrastructure/coverage.png",
        "HTML-отчёт покрытия с детализацией по Python-модулям",
    )
    r.p(
        "Команда tools/check.py --stage release --e2e формирует JUnit XML для CI, HTML со статусом каждого теста, отчёты coverage в JSON/XML/HTML, карту требований и метрики. При падении браузерного теста сохраняются trace и screenshot; успешные сценарии дополнительно сохраняют иллюстрации для отчёта. Gitea Actions публикует каталог результатов как артефакт quality-evidence."
    )
    r.p(
        "Выполнено 91 автоматическое испытание, включая два E2E. 100% строк и ветвей относится только к выбранному Python-коду core; генераторы миграций, management, шаблоны и статика не включены в эту метрику. Тесты не подменяют нагрузочное испытание, внешний аудит безопасности и экспертную проверку экономической модели. Достоверность банковского скоринга не заявляется: формула учебная."
    )
    r.h("5 Выявленные проблемы инфраструктуры")
    r.table(
        "Исправленные дефекты",
        ["ID", "Причина", "Исправление"],
        [(d["id"], d["cause"], d["fix"]) for d in read("defects.json")["defects"]],
        [1.8, 7.2, 8],
    )
    r.p(
        "Четыре дефекта зарегистрированы по фактически встреченным сбоям. Карточки созданы после исправления по журналам; время создания карточки не выдаётся за время обнаружения. Контрольное падение в PR №32 создано намеренно для проверки запрета слияния и не считается дефектом приложения. После исправлений полный регрессионный набор проходит. HTML-отчёт в кириллической папке открывается через HTTP, а не file://: python -m http.server 8090 --bind 127.0.0.1 --directory artifacts/runs/release; адрес http://127.0.0.1:8090/tests.html."
    )
    r.finish()


def lab8(summary, tasks):
    r = Report(8, "Отчёт о релизе")
    r.h("1 Состав завершённой системы")
    r.p(
        "CreditSoft 1.0.0 завершает функции CR-01–CR-08: регистрация и вход, анкета, финансовые сведения, проверка данных, расчёт долговой нагрузки и рейтинга, хранение каталога, подбор предложений, просмотр результата. Приложение запускается через Docker Compose и доступно по http://127.0.0.1:8080/. В качестве данных для демонстрации использованы вымышленные значения; каталог не связан с реальными банками."
    )
    r.figure("docs/images/application/login-desktop.png", "Вход в CreditSoft")
    r.figure(
        "docs/images/application/questionnaire-desktop.png",
        "Ввод, редактирование и сохранение анкеты",
    )
    r.p(
        "Анкета хранит ФИО, дату рождения, реквизиты учебного паспорта, работодателя и стаж. Финансовая часть содержит доход, текущие ежемесячные платежи, желаемую сумму и срок. Сервер проверяет поля и атомарно сохраняет обе части. Сохранённые значения доступны после повторного входа и перезагрузки страницы."
    )
    r.figure(
        "docs/images/application/validation-desktop.png",
        "Сообщения о некорректных данных рядом с полями",
    )
    r.h("2 Расчёт, подбор и сохранение результатов")
    r.p(
        "Нагрузка равна текущим платежам, делённым на доход, и умноженным на 100%. Это нагрузка по существующим обязательствам; платёж по будущему кредиту не моделируется. Рейтинг 0–1000 складывается из трёх объяснимых составляющих: нагрузка до 450 баллов, стаж до 250, отношение суммы кредита к годовому доходу до 300. Применяется Decimal; округление предназначено для отображения, сравнение границ выполняется по исходной величине."
    )
    r.table(
        "Правила рейтинга edu-1.0",
        ["Фактор", "Границы → баллы"],
        [
            ("Нагрузка", "≤10% → 450; ≤30% → 350; ≤50% → 200; ≤70% → 80; >70% → 0"),
            ("Стаж в месяцах", "≥36 → 250; ≥12 → 180; ≥6 → 100; ≥1 → 40; 0 → 0"),
            ("Сумма / (доход × 12)", "≤0,5 → 300; ≤1 → 220; ≤2 → 100; >2 → 0"),
        ],
        [5.5, 11.5],
    )
    r.p(
        "Предложение подходит, если оно активно и одновременно соблюдены минимальный рейтинг, максимальная нагрузка, диапазон суммы и диапазон срока. Все границы включительны. Результат сортируется по ставке и идентификатору. Для дохода 100 000 руб., платежей 15 000 руб., суммы 300 000 руб. и стажа 48 месяцев получаются нагрузка 15%, рейтинг 900 и четыре предложения."
    )
    r.figure(
        "docs/images/application/results-desktop.png",
        "Итоговая оценка, объяснение баллов и предложения",
    )
    r.figure(
        "docs/images/application/results-no-offers.png",
        "Корректное состояние при отсутствии подходящих предложений",
    )
    r.figure("docs/images/application/results-mobile.png", "Результат расчёта на мобильном экране")
    r.p(
        "Assessment сохраняет снимок входных финансовых данных, баллов, версии правил и подобранных предложений. Паспорт в снимок результата повторно не записывается. Изменения анкеты или каталога не меняют старую оценку; интерфейс сообщает об изменении анкеты. Новый POST создаёт следующую оценку, GET читает сохранённую. Доступ к чужому результату возвращает 404."
    )
    r.h("3 Компоненты и последовательность вызовов")
    r.table(
        "Реализованные части системы",
        ["Компонент", "Назначение"],
        [
            (
                "HTML/CSS/JavaScript + Bootstrap",
                "Формы, сообщения, карточки предложений и адаптивное представление",
            ),
            ("accounts.py / Django Auth", "Регистрация, хеширование пароля, вход, сессии и выход"),
            (
                "questionnaire.py / forms.py / validation.py",
                "Обработка анкеты, проверка и координация сохранения",
            ),
            (
                "repository.py / models.py",
                "ORM, транзакции, связь пользователя с анкетой, каталогом и оценками",
            ),
            ("scoring.py", "Чистый расчёт нагрузки, баллов и текстовых объяснений"),
            ("offers.py", "Отбор активных предложений по всем ограничениям"),
            ("results.py", "Создание снимка и выдача результатов владельцу"),
            (
                "Nginx → Gunicorn/Django → PostgreSQL",
                "Раздача статики и проксирование → выполнение Python → долговременное хранение",
            ),
        ],
        [6.5, 10.5],
    )
    r.p(
        "При открытии формы браузер обращается к Nginx, затем Gunicorn передаёт запрос Django; session middleware определяет пользователя, questionnaire читает его данные через repository/ORM. При сохранении формы сначала проверяются, затем обе модели записываются одной транзакцией. При расчёте results блокирует строку пользователя, читает согласованную анкету, вызывает scoring, затем offers, сохраняет Assessment и перенаправляет на страницу результата. Шаблон формирует HTML из сохранённого снимка. При повторном чтении расчёт не запускается."
    )
    r.h("4 Готовность задач и дефекты")
    r.table(
        "Сводка локального трекера",
        ["Категория", "Всего", "Завершено"],
        [
            ("Исходные функциональные задачи CR", 24, summary["closed_counts"].get("original", 0)),
            (
                "Дополнительные задачи плана ЛР3",
                6,
                summary["closed_counts"].get("planned_additional", 0),
            ),
            ("Задачи-описания фактических дефектов", summary["defects"], summary["closed_defects"]),
            (
                "Всего",
                30 + summary["defects"],
                sum(summary["closed_counts"].values()) + summary["closed_defects"],
            ),
        ],
        [11, 3, 3],
    )
    r.p(
        "Шесть дополнительных задач PR-01, INF-01, QA-01, RL-01, QA-02 и RL-02 уже присутствовали в ЛР3 и не являются новыми функциональными требованиями этого релиза. После реализации отдельно зарегистрированы четыре инфраструктурных дефекта BUG-01–BUG-04. Карточки PR и намеренно падающая проверка защиты в число задач не включены. Источник отчёта — Gitea API, docs/evidence/forge-export.json и acceptance.json."
    )
    r.figure("docs/images/infrastructure/tasks.png", "Закрытые карточки в локальном трекере Gitea")
    r.table(
        "Выполнение задач и исходные оценки",
        ["ID", "Задача", "План, ч", "Состояние"],
        [
            (
                t["id"],
                t["title"],
                t["planned_hours"],
                "Закрыта" if t["state"] == "closed" else "Открыта",
            )
            for t in tasks
        ],
        [2.2, 10.5, 2, 2.3],
    )
    r.h("5 Фактическое время и отклонения")
    r.p(
        "В исходном плане 30 задач оценены в 140 часов: 122 часа функциональных работ и 18 часов дополнительных. Наблюдаемый интервал фиксируется tools/tasklog.py по началу и окончанию этапа, с UTC-метками. Он включает автоматизированную помощь, ожидание инструментов, CI и паузы между продолжениями сеанса. Активное рабочее время отдельно не измерялось; интервал не является индивидуальными человеко-часами. Анализ документов до начала журнала не измерялся. Отдельные задачи внутри этапа не хронометрировались; их индивидуальный факт неизвестен."
    )
    plan = {
        "infrastructure": 6,
        "prototype": sum(
            t["planned_hours"]
            for t in tasks
            if t["id"] == "PR-01" or t["id"].startswith(tuple(f"CR-0{n}" for n in range(1, 5)))
        ),
        "assessment": sum(
            t["planned_hours"]
            for t in tasks
            if t["id"].startswith(tuple(f"CR-0{n}" for n in range(5, 9)))
        ),
        "validation": 6,
        "release": 2,
    }
    labels = {
        "infrastructure": "Окружение, INF-01 / RL-01",
        "prototype": "Прототип, PR-01 и CR-01–04",
        "assessment": "Основной функционал, CR-05–08",
        "validation": "Проверки, QA-01 / QA-02",
        "release": "Документация и выпуск, RL-02",
    }
    rows = [
        (
            labels[p["phase"]],
            plan[p["phase"]],
            f"{p['elapsed_seconds'] / 60:.2f}",
            "Идёт на момент снимка" if p.get("snapshot_in_progress") else "Завершён",
        )
        for p in summary["worklog"]
    ]
    r.table(
        "Измеренное время по этапам",
        ["Этап и задачи", "План, ч", "Интервал, мин", "Учёт"],
        rows,
        [8.2, 2, 3, 3.8],
    )
    r.p(
        f"Сумма зарегистрированных интервалов на момент снимка — {sum(p['elapsed_seconds'] for p in summary['worklog']) / 60:.2f} мин. Плановые часы группируются без повторного учёта: INF-01/RL-01 отнесены к инфраструктуре, хотя их повторная проверка выполнялась и на этапе validation. Разница объясняется помощью генерации кода, готовыми средствами Django, автоматическим прогоном и отсутствием банковских интеграций. Временные затраты на настройку CI и оформление отчётов измерены отдельно. Пересчёт этих минут в «сэкономленные человеко-часы» некорректен."
    )
    r.table(
        "Причины отличий интервалов от плановых оценок",
        ["Этап", "Причина"],
        [
            (
                "Инфраструктура",
                "Готовые Docker-образы и автоматизированная настройка; интервал включает ожидание загрузки и CI.",
            ),
            (
                "Прототип",
                "Готовые Django Auth/ORM/формы и Bootstrap; код и тесты создавались с автоматизированной помощью.",
            ),
            (
                "Основной функционал",
                "Учебные детерминированные правила и локальный каталог; нет внешних банковских интеграций.",
            ),
            (
                "Проверки",
                "Параметризация и автоматические прогоны; входит ожидание CI и исправление инфраструктуры.",
            ),
            (
                "Выпуск",
                "Интервал включает длительную паузу между продолжениями сеанса и зависание экспорта Word. PDF получены через LibreOffice. Активное время внутри интервала отдельно не выделено.",
            ),
        ],
        [4.3, 12.7],
    )
    r.h("6 Закрытие задач, активность и объём проекта")
    r.figure(
        "docs/images/statistics/burndown.png",
        "Плановое и фактическое сгорание оценок задач по неделям",
    )
    r.p(
        "Плановая линия построена по восьми двухнедельным спринтам ЛР3 от 07.09.2026 до 27.12.2026; закрытие внутри спринта принято на его конец. Фактическая линия вычитает исходную оценку задачи в дату closed_at локальной карточки. Это оставшиеся плановые часы, а не фактические трудозатраты. Дефекты без исходной оценки в эту линию не включаются. Будущие фактические точки отсутствуют."
    )
    r.figure(
        "docs/images/statistics/weekly-activity.png",
        "Закрытые карточки, коммиты и изменения строк по неделям",
    )
    measured = [w for w in summary["weeks"] if w["commits"] is not None]
    r.table(
        "Наблюдаемая недельная статистика",
        ["Начало недели", "Закрыто карточек", "Коммитов без merge", "+ строк", "− строк"],
        [
            (w["week"], w["closed_issues"], w["commits"], w["added_lines"], w["removed_lines"])
            for w in measured
        ],
        [3.5, 3.7, 4, 2.9, 2.9],
    )
    r.p(
        "Данные выполнения сосредоточены в одной текущей неделе: работы выполнены в одной сессии, карточки перенесены сейчас. До создания локального репозитория и Gitea событий в этих источниках нет; это не доказательство отсутствия предшествующей работы над отчётами. История YouGile недоступна без авторизации и не подменялась вымышленными датами. По одной активной неделе нельзя оценить устойчивую скорость команды. Статистика Git охватывает достижимые из снимка HEAD коммиты без merge; намеренная ветка проверки защиты исключена."
    )
    v = summary["volume"]
    r.table(
        "Объём репозитория на момент снимка",
        ["Показатель", "Значение"],
        [
            ("Файлы под управлением Git", v["tracked_files"]),
            ("Собственные файлы исходников, тестов и конфигураций", v["authored_source_files"]),
            ("Физические строки этих файлов", v["authored_physical_lines"]),
            ("HEAD статистики", summary["head"]),
            ("Момент выгрузки UTC", summary["recorded_at"]),
        ],
        [10.2, 6.8],
    )
    r.p(
        "В собственный объём входят .py, .html, .css, .js, .yaml/.yml, включая tests/tools; исключены сторонний Bootstrap и сгенерированные миграции. Физические строки включают пустые строки и комментарии. Метрика SLOC в ЛР5 имеет более узкую область — только Python приложения. Недельное изменение строк Git включает документацию и сторонние текстовые файлы, если они были зафиксированы; для бинарных файлов строки не считаются. Точный состав по расширениям сохранён в summary.json."
    )
    r.h("7 Проверка выпуска и эксплуатация")
    r.p(
        "Перед выпуском выполнены 91 тест на SQLite и PostgreSQL, два сценария Chromium, проверка Docker-стенда через Nginx/Gunicorn и повторный вход после перезапуска. Smoke получил рейтинг 900, четыре предложения и отсутствие ошибок JavaScript. pg_dump создал резервную копию; оглавление проверено pg_restore --list. Восстановление рабочей БД не выполнялось. Отчёты, пакеты сборки и контрольные суммы опубликованы в локальном релизе v1.0.0."
    )
    r.p(
        "Запуск: python tools/bootstrap.py; docker compose up -d --build. Контроль: /health/ и python tools/smoke.py. Проверки: python tools/check.py --stage local --e2e. PostgreSQL хранит данные в именованном томе; секреты лежат в .local и не включены в Git. Ограничения: одиночный локальный стенд HTTP, учебная формула и каталог, отсутствие банковских/БКИ интеграций, нагрузочного испытания и внешнего аудита. Проверка преподавателем не заявляется."
    )
    r.finish()


def main():
    summary = read("summary.json")
    tasks = read("acceptance.json")
    for builder in [lab5, lab6, lab7, lab8]:
        builder(summary, tasks)


if __name__ == "__main__":
    main()
