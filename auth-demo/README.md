# Учебный API: вход и права доступа

Версия auth-demo-1.0. Отдельный исправный учебный API на http://127.0.0.1:8766; основной demo-1.0 на 8765 не меняется. Это не итоговое задание с неизвестным дефектом.

## Контракт до реализации

Транспорт локальный, JSON UTF-8. Ответы: Content-Type application/json, Cache-Control no-store, X-Build-Version, X-Request-Id. Ответ 204 не содержит тела. Все пароли ниже вымышленные и относятся только к этому учебному API.

| Пользователь | Пароль | Роль |
|---|---|---|
| qa_user | Study123! | user |
| qa_admin | Study123! | admin |

| Запрос | Условия и результат |
|---|---|
| GET /health | Без входа: 200, status=ok и build=auth-demo-1.0 |
| POST /auth/login | JSON с username/password, No Auth. Правильные данные: 200, access_token — непустая строка, token_type=Bearer, expires_in=900, user={id,username,role}. При другой настройке TTL expires_in соответствует ей |
| POST /auth/login | Неизвестный логин либо неверный пароль: 401, error=invalid_credentials. Сообщение одинаковое, токен не выдаётся |
| POST /auth/login | Не JSON Content-Type: 415 unsupported_media_type; сломанный JSON/не объект: 400 invalid_json; username/password отсутствуют, пустые или не строки: 422 validation_error |
| GET /api/me | Bearer access_token: 200 и объект пользователя id/username/role; пароля и хеша в ответе нет |
| GET /api/admin/report | С действующим токеном admin: 200 {report: "Учебный отчёт", total: 2}; с действующим токеном user: 403 forbidden |
| POST /auth/logout | С действующим токеном: 204, отзывает только этот токен; тело запроса не требуется |

На защищённых маршрутах: нет Authorization → 401 unauthorized. Неверный формат заголовка, неизвестный, отозванный либо истёкший токен → 401 invalid_token. Ответы 401 содержат WWW-Authenticate: Bearer realm="qa-auth".

Вход выдаёт новый непрозрачный случайный токен; это не JWT. Обычный срок жизни 900 секунд (15 минут), повторный вход не продлевает старый токен и не отзывает другие. Время жизни не обновляется от чтения /api/me. После перезапуска все токены становятся недействительны. Нет refresh-токенов, cookies, OAuth и регистрации. Поля role/id из запроса входа не влияют на серверные права.

Неизвестный маршрут возвращает 404 not_found. В поддерживаемых маршрутах методы GET/POST проверяются по таблице; иной путь/комбинация этих методов возвращает 404. Другие методы не входят в упражнение.

## Запуск

Из корня проекта:

```powershell
python auth-demo/server.py --port 8766
```

Сервер слушает только 127.0.0.1. Зависимости — стандартная библиотека Python. Для короткой проверки истечения можно запустить отдельный экземпляр на другом свободном порту с --token-ttl 2. Не менять TTL действующего экземпляра во время ручной практики.

## Ручной маршрут

Создать в своей коллекции папку «Авторизация» и добавить в QA Local переменную authBaseUrl=http://127.0.0.1:8766. baseUrl остаётся адресом 8765. authAccessToken — временная переменная коллекции только для токена этого демо; не помещать полученные токены в Git/экспорт или логи. Настоящие секреты хранить через Vault.

1. GET {{authBaseUrl}}/api/me с No Auth → 401.
2. POST {{authBaseUrl}}/auth/login с qa_user/Study123! → 200; сохранить access_token.
3. GET {{authBaseUrl}}/api/me, Authorization → Bearer Token, Token={{authAccessToken}} → 200, username=qa_user, role=user.
4. GET {{authBaseUrl}}/api/admin/report с тем же токеном → 403.
5. Войти как qa_admin и повторить отчёт с новым токеном → 200, role определяется сервером.
6. POST {{authBaseUrl}}/auth/logout с токеном → 204; повторить /api/me с тем же токеном → 401.

Полная ручная инструкция — notes/23-postman-auth-hands-on.md. Прогон готовой коллекции помощника не заменяет эти действия.
