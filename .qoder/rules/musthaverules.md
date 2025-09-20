---
trigger: always_on
alwaysApply: true
---
Дата правил: 2025-09-13 (Обязательны для всех заданий — Coordinator/Agents/Tools/E2E/Интеграции).
Автор: Пользователь (владелец Bldr Empire).
Цель: Обеспечить чистый, рабочий код без мусора/моков/лишнего. Фокус на real impl (local LM/Redis/Celery/Neo4j), minimal overhead (no endless loops/retries/tests/docs). После каждого задания: Code clean (git diff clean, no temp files), docs only essential (README + checklist if E2E). Нарушение — переделай задание с нуля. Это правила проекта — embed в start каждого промта (e.g., "Follow these rules strictly").

Вы ОБЯЗАНЫ следовать этим правилам в КАЖДОМ задании/коммите без исключений. Перед кодом: Check "No mocks? Clean? Minimal?". Финальный контроль: "Code real, no junk, docs lean — OK?".

1. РЕАЛЬНАЯ ИМПЛЕМЕНТАЦИЯ (NO MOKS — 100% REAL)
Запрещено: Любые mocks/fakes/simulations (e.g., no "mock Celery" / "simulate LM response" / "fake JSON" / "since not implemented, return mock"). Нет "fallback mock" — если down (LM/Redis), log error + real fallback (e.g., simple RAG без LM, or raise Exception с traceback).
Обязательно: Real calls everywhere (LM Studio localhost:1234/v1 — test connect first; Celery real worker/beat с Redis; Neo4j real queries; TG bot real polling/webhook; tools real (gen_docx lib, vl_analyze real Qwen-VL)). Для E2E: Run full system (run_system.sh), test on real data (sample norms/photo/smeta в I:\docs\clean_base).
Проверка: Перед commit: Run real test (e.g., POST /submit_query → real JSON/files, no "mock_success"). Если error — fix real (e.g., add try/except + log), не mock.
Пример: Celery task: .send_task real → worker log "Executed", result in Redis. Нет "mock task.delay()".
2. МИНИМАЛЬНЫЕ РЕТРИИ (Retries Только При Необходимости — Max 3x)
Запрещено: Бесконечные/авто-ретрии (no while True, no retry=inf). Нет retry для stable (e.g., Neo4j query, parse SBERT — one-shot).
Обязательно: Retries only для flaky (e.g., LM call timeout: retry 3x с backoff 1-3s; requests to sources like minstroyrf: 2x on 5xx). Use tenacity lib if need (pip, but minimal — @retry(stop=tenacity.stop_after_attempt(3), wait=tenacity.wait_exponential(multiplier=1))).
Проверка: В коде: Explicit retry only (e.g., in models_manager.py: for LM, if ConnectionError — retry 3x, else raise). Log each retry ("Retry 1/3: LM timeout"). Для E2E: Simulate error (kill LM) → 3 retries → fallback, no loop.
Пример: vl_analyze_photo: requests.post(LM) with retry(3) on timeout, else "VL error, no analysis".
3. ТЕСТИРОВАНИЕ МИНИМАЛЬНОЕ (Essential Only — No Endless/Overkill)
Запрещено: Бесконечные тесты (no pytest loops, no "test all edge cases 100x"). Нет debug tests (e.g., no test_debug_lm_fail.py — delete after fix). Нет over-cov (max 90%, focus key paths).
Обязательно:
Unit: Pytest only essential (test_tools.py: 10 tools, assert output/files; test_parse_sbert.py: 5-10 queries, conf>0.8). Cov >80% for core (parse/agents/tools), no for utils.
E2E: Only 3-5 flows (Frontend/TG/shell, 1 query each) in cypress/e2e/query.cy.js + pytest test_e2e.py (real POST, assert Neo4j/files). Run time <5min total.
No temp tests: Create test_.py only if needed, delete after (or integrate in main test_.py). Нет "test-fix-branch.py" — fix in-place.
Проверка: Перед commit: pytest -v (pass all, no fails), cypress run (pass). Delete any debug_.py/temp_.log. Cov report: Only html in /tests, no per-file.
Пример: test_agent_role: 1 input per role (8 total), assert JSON keys/sources. Нет 100 variants — sample only.
4. ЧИСТЫЙ КОД (No Junk Files/Branches — Clean After Each Task)
Запрещено: Создание/оставление temp files (no debug.py, fix_*.py, temp_data.csv — delete after use). Нет миллиардов branches (no "feat-debug-lm", "test-fix-parse" — use main branch, atomic commits).
Обязательно:
Files: Only add/edit core (main.py, config.py, parse_utils.py etc.). Temp (e.g., test_photo.jpg) — in /tests/data, gitignore if sample.
Branches: One per task (e.g., "feat:sbert-integration"), merge to main after test, no sub-branches. Git clean -fd after.
Cleanup: End of task: rm -rf temp_/debug_/pycache; git status clean.
Проверка: Перед PR/merge: git diff --stat (only changed files), no new .py/md in root if unused. Run "find . -name 'debug' -delete; find . -name 'temp' -delete".
Пример: Fix LM error — edit models_manager.py, test in E2E, delete any test_lm_fail.py.
5. ДОКУМЕНТАЦИЯ МИНИМАЛЬНАЯ (Essential Only — No Unused MD)
Запрещено: Создание лишних MD (no per-feature "feat-letters.md", no "debug-setup.md", no commit-log.md). Нет "никто не открывал" файлов — delete if not referenced.
Обязательно:
Core: README.md (setup/run/use, update per task: +1 section if new, e.g., "SBERT Parse").
E2E: Only test_report.md (чек-лист table, 50+ rows, update after tests — no new per-test).
No more: Embed notes in README (e.g., "Tools: See common.py"), no separate "rules.md" (use this once).
Проверка: End of task: ls *.md — only README.md + test_report.md (if E2E). Update README: "Changes: Added SBERT, see parse_utils.py". Delete any unused (e.g., old "mock-celery.md").
Пример: New feature — +1 bullet in README "SBERT: pip sentence-transformers, use in parse". No "sbert-guide.md".
6. ОБЩИЕ ПРАВИЛА (Efficiency/Atomicity)
Коммиты: Atomic (1 feature per commit, e.g., "feat: sbert-parse-integration" — code + test + README update). No "wip-debug", no 100 small commits.
Overhead: Minimal deps (no new pip unless essential, e.g., sentence-transformers yes for SBERT). Real data only (no fake samples — use I:\docs\clean_base).
Errors/Logs: Always log (print/loguru: "Error: {e}, fallback {action}"), no silent fail. В E2E: Document errors in checklist, fix before merge.
Финальный Контроль Перед Submit:
Real? (Run system → query → output/files/Neo4j — works?).
Clean? (No mocks/retries junk/temp files/MD? Git clean?).
Minimal? (Tests <20, docs lean, cov ok?).
Если нет — переделай. Log "Task complete: Rules followed".
Применение: В каждом задании — start with "Follow ПРАВИЛА ДЛЯ РАЗРАБОТКИ Bldr Empire v2 strictly". Это обеспечит чистый empire — real, lean, no bloat. Если нарушение (e.g., mock snuck in) — "Redo without mocks". 🚀