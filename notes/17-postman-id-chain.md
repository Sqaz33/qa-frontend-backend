# Postman: сохранить id и передать в GET

**На повторение: 4 минуты.** Упражнение выполняется вручную в собственной коллекции.

## Перед началом
Вернуть второй тест POST к ожиданию 1000 и исходному названию. В теле оставить amount=1000.
Сохранить правильную функцию третьего теста: pm.test("...", () => { ... }).

## POST — очистить старое значение
Scripts → Before request:
```javascript
pm.collectionVariables.unset("createdApplicationId");
```

Так не останется id предыдущего успешного создания, если новая попытка завершится ошибкой.

## POST — сохранить новый id
В конец Scripts → After response, где data уже разобран через pm.response.json(), добавить:
```javascript
if (
  pm.response.code === 201 &&
  Number.isInteger(data.id) &&
  data.id > 0
) {
  pm.collectionVariables.set("createdApplicationId", String(data.id));
}
```

Сохранить и отправить POST. Ожидается 201 и прежние три passed.
Открыть коллекцию → Variables: createdApplicationId должен совпасть с id в ответе POST.

## Зависимый GET
В той же коллекции создать «03 — Получить созданную заявку».
```text
GET {{baseUrl}}/api/applications/{{createdApplicationId}}
```
Body none, Authorization No Auth, активное окружение QA Local.

Scripts → After response:
```javascript
const data = pm.response.json();

pm.test("Заявка найдена: 200", () => {
  pm.response.to.have.status(200);
});

pm.test("Вернулась созданная заявка", () => {
  const expectedId = Number(
    pm.collectionVariables.get("createdApplicationId")
  );
  pm.expect(data.id).to.eql(expectedId);
});

pm.test("Сумма сохранилась: 1000", () => {
  pm.expect(data.amount).to.eql(1000);
});
```

Сохранить и отправить GET. Ожидается 200, id последнего POST, amount=1000, три passed.

## Два вида переменных
data — JavaScript-значение в конкретном скрипте.
createdApplicationId — переменная коллекции, доступная другим запросам и подстановке {{createdApplicationId}}.
String при сохранении превращает id в строку. Number в GET-проверке возвращает число для сравнения с числовым полем JSON.

Не создавать одноимённый createdApplicationId в Environment: переменная окружения может перекрыть подстановку из коллекции.
Если красная переменная в URL не разрешается, проверить, сохранены ли POST и GET в одной коллекции, выполнен ли POST и появилось ли значение в Variables.

## Что устанавливает упражнение
Новый id передаётся между запросами без ручного копирования. GET подтверждает доступность созданного ресурса с ожидаемой суммой.
Пока не проверяются все поля ответа и авторизация; это следующие расширения, а не уже выполненные гарантии.

Результат ученика этой цепочки ещё не получен.
