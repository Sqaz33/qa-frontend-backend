# Углублённый Postman

Этот блок добавлен по просьбе пользователя перед продолжением основного плана.
Формат: короткое объяснение → пример → понятные действия. Обязательного опроса нет.

## Порядок
1. [Коллекции и окружения](../notes/10-postman-collections-environments.md).
2. [Запрос и ответ](../notes/11-postman-request-and-response.md).
3. [Скрипты и передача id](../notes/12-postman-scripts-and-chaining.md).
4. [Runner и данные](../notes/13-postman-runner-and-data.md).
5. [Авторизация](../notes/14-postman-authorization.md).

## Файлы
- qa-demo.postman_collection.json — прежние запросы и две новые папки.
- qa-local.environment.json — окружение QA Local, baseUrl=http://127.0.0.1:8765.
- negative-amounts.json — восемь наборов недопустимых сумм.

По уточнению пользователя сначала пройти [ручную практику](PRACTICE_MANUAL.md): самому создать коллекцию, окружение, запросы и скрипты. Готовая коллекция служит образцом; импортировать её для начала не обязательно.
На 2026-10-21 ученик сообщил о выполнении цепочки и прогонов Runner; первый GET и часть assertions подтверждены скриншотами. По его просьбе текущий блок завершён для перехода к дефектам и релизам. Успешная auth-практика после коррекции метода не подтверждена. Отдельный защищённый пример auth-demo-1.0 и инструкция notes/23 сохранены для повторения.

## Проверка помощником
CLI 1.75.0, живой локальный demo-1.0.
Папка 01: 3 запроса, 10 assertions, exit 0; создан id=5, GET совпал.
Папка 02: 8 итераций, 24 запроса, 64 assertions, exit 0; список после отказов не изменился.
Окружение: lint — 0 ошибок, 0 предупреждений.
Это subset контракта; авторизация, нагрузка и другие API-методы не проверялись.

## CLI для повторения
Из корня проекта:
```powershell
postman collection run postman/qa-demo.postman_collection.json -i "01 — Цепочка POST → GET" -e postman/qa-local.environment.json --no-report-events
postman collection run postman/qa-demo.postman_collection.json -i "02 — Негативные данные" -e postman/qa-local.environment.json -d postman/negative-amounts.json -n 8 --no-report-events
```

У установленной версии --output требует входа в Postman; обычные локальные прогоны без этого флага завершились успешно. Облачный отчёт не публиковался.
Подробности: [evidence](../evidence/postman-advanced-verification.md).
