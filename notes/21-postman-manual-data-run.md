# Runner: один запрос с восемью наборами данных

Первый запуск цепочки 02 → 03 завершён по сообщению ученика «готово». Отдельные статусы и счётчики не предоставлены.

## Задача
Одним запросом проверить восемь недопустимых сумм. В postman/negative-amounts.json уже есть 999, 100001, -1, 0, 1000.5, "1000", null и true. Все запрещены контрактом demo-1.0.

## Настройка запроса 04
Можно переименовать его в «04 — Недопустимые суммы».
POST {{baseUrl}}/api/applications, No Auth.

Scripts → Before request:

```javascript
if (!pm.iterationData.has("amount")) {
    throw new Error("В Runner не подключены данные с полем amount");
}

const amount = pm.iterationData.get("amount");
pm.variables.set("negativeBody", JSON.stringify({
    name: "test",
    amount: amount,
    consent: true
}));
```

Body → raw → JSON:

```text
{{negativeBody}}
```

Проверить Content-Type: application/json. Кавычки вокруг подстановки не нужны.
JSON.stringify сохраняет отличие числа 1000 от строки "1000", а также null и boolean.

В After response оставить три проверки 422, validation_error, fields.amount. Первое название лучше заменить на «Недопустимая сумма отклонена: 422». Before request запроса 04 не должен очищать createdApplicationId; After response не должен сохранять id из ошибки.
Сохранить запрос.

## Подключение данных
1. Collection → Run → Functional → Local, если выбор режима показан.
2. Окружение QA Local.
3. Оставить галочку только у запроса 04.
4. Iteration data → Datafiles → Select from computer.
5. Выбрать D:\Projects\qa-interview-axiomatika\postman\negative-amounts.json.
6. В предпросмотре проверить восемь строк, поля caseName и amount.
7. Iterations = 8. Start run (либо Run Collection).

При полном выполнении ожидаются 8 HTTP-запросов с 422 и 24 именованные проверки, если оставлены ровно три pm.test. Это ожидание, фактический результат ещё не получен. Такой прогон пока не проверяет отсутствие созданных записей.

## Если подключение файла требует платного тарифа
Текущая официальная документация относит custom data files к платным возможностям. Покупка для обучения не требуется. В той же конфигурации с Iterations=8 можно оставить файл неподключённым, а Before request заменить на:

```javascript
const amounts = [999, 100001, -1, 0, 1000.5, "1000", null, true];
const index = pm.info.iteration;
if (index >= amounts.length) {
    throw new Error("Для этой итерации не задана сумма");
}
pm.variables.set("negativeBody", JSON.stringify({
    name: "test",
    amount: amounts[index],
    consent: true
}));
```

pm.info.iteration начинается с 0. Это альтернативный учебный способ получить разные данные на каждой итерации; он не использует файл и не подтверждает освоение pm.iterationData.

## Читать результат
Раскрыть итерации и убедиться, что в отправленном теле менялась сумма, а не восемь раз уходило одно значение. При FAILED открыть конкретный запрос и сообщение проверки.

[Файлы данных — документация Postman](https://learning.postman.com/latest-v-12/docs/tests-and-scripts/running-collections/test-data/working-with-data-files).