# Руководство по внесению вклада в BLDR.EMPIRE

Спасибо за интерес к проекту! Это руководство поможет вам внести вклад.

## Процесс разработки

1. **Создайте feature-ветку** от `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/этап-номер-задача
   ```

2. **Внесите изменения** и коммитьте:
   ```bash
   git add .
   git commit -m "feat: описание изменений"
   ```

3. **Пушите изменения**:
   ```bash
   git push origin feature/этап-номер-задача
   ```

4. **Создайте Pull Request** в `develop` через GitHub

## Стандарты кода

### Python
- Используйте `black` для форматирования
- Следуйте PEP 8
- Добавляйте type hints
- Пишите docstrings в формате Google Style

### TypeScript
- Используйте ESLint
- Строгая типизация
- Функциональные компоненты

## Коммиты

Используйте [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - новая функция
- `fix:` - исправление бага
- `docs:` - документация
- `refactor:` - рефакторинг
- `test:` - тесты
- `chore:` - рутинные задачи

## Тестирование

Перед созданием PR убедитесь, что:
- Все тесты проходят
- Код соответствует линтерам
- Добавлены тесты для новой функциональности

