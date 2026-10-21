# Postman: проверки ответа и цепочка запросов

**На повторение: 5 минут.** Код уже есть в папке 01 коллекции; читать по частям.

## Когда выполняются скрипты

| Раздел Scripts | Когда | Применение |
|---|---|---|
| Before request / Pre-request | Перед отправкой | Подготовить данные и временные значения |
| After response / Post-response | После ответа | Проверить результат, сохранить id |

В интерфейсе пользователя разделы называются Before request и After response. В документации встречаются Pre-request и Post-response; в старых материалах послеответный раздел также называется Tests.

## Первая проверка

В Scripts → After response у запроса создания:
```javascript
pm.test("Заявка создана: 201", () => {
  pm.response.to.have.status(201);
});
```

pm.test задаёт именованную проверку. Если утверждение не выполнится, эта проверка будет failed.
Успешная HTTP-отправка и успешные проверки — разные результаты.

## Проверить данные
```javascript
const data = pm.response.json();

pm.test("Сумма — число 1000", () => {
  pm.expect(data.amount).to.eql(1000);
});
```

eql проверяет значение с учётом типа: строка "1000" не равна числу 1000.
Ожидание 1000 взято из сценария с допустимой нижней границей, не из случайного ответа сервера.

## Передать id дальше
После успешного создания:
```javascript
pm.collectionVariables.set("createdApplicationId", String(data.id));
```

Следующий GET:
```text
{{baseUrl}}/api/applications/{{createdApplicationId}}
```

Больше не нужно вручную вписывать 4. При каждом создании приходит новый id.

В готовой коллекции сохранение выполняется только при 201 и корректном id. Перед новым созданием старое значение удаляется, чтобы сбой POST не привёл к проверке старой заявки.

## Проверить чтение
Готовая коллекция сохраняет также ответ создания в createdApplication и сравнивает с GET:
id, name, amount, consent, status, created_at.
Создание отдельно проверяется на name=test, amount=1000, consent=true и status=new. Поэтому ошибку, одинаковую в POST и GET, мы не оправдываем одним совпадением ответов.

## Что делать руками
Основной путь — собрать запросы и скрипты в собственной коллекции. Папка 01 готового файла служит образцом для сравнения.
После каждого ответа открыть результаты тестов и посмотреть, какая именно проверка прошла.
Проверки помощника уже прошли, но результат ученика этим не подменяется.

[Объект pm и переменные](https://learning.postman.com/docs/tests-and-scripts/write-scripts/postman-sandbox-reference/pm-variables).
[Пример сохранения ответа для следующего вызова](https://support.postman.com/hc/en-us/articles/115003340869-How-to-save-a-response-as-a-variable-and-reuse-it-for-another-API-call).

## Ручной шаг: первый POST со скриптом

В собственной коллекции создать и сохранить «02 — Создать заявку».
POST {{baseUrl}}/api/applications, Body raw JSON:
```json
{"name":"test","amount":1000,"consent":true}
```
Content-Type application/json; Authorization No Auth.

В Scripts → After response:
```javascript
pm.test("Заявка создана: 201", () => {
  pm.response.to.have.status(201);
});

const data = pm.response.json();

pm.test("Сумма — число 1000", () => {
  pm.expect(data.amount).to.eql(1000);
});

pm.test("Выдан положительный целочисленный id", () => {
  pm.expect(Number.isInteger(data.id) && data.id > 0).to.eql(true);
});
```

Ожидается HTTP 201 и три passed в Test Results. Выполнение пользователем ещё не подтверждено.
pm.response.json() разбирает тело ответа в JavaScript-значение. const data существует внутри скрипта; для передачи id следующему запросу отдельно создадим переменную коллекции.
Перед отправкой убедиться, что выбрано QA Local и запрос сохранён в собственной коллекции.

## Результат и следующий разбор
На скриншоте пользователя показаны 201 и 3/3 PASSED. В третьей проверке нужно восстановить функцию вторым аргументом pm.test. См. [разбор callback и FAILED](16-postman-callback-and-failed.md).
