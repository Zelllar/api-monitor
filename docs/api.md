# API Monitor — API Specification

## Общая информация

- Протокол: HTTP
- Формат данных: JSON
- Базовый путь: `/api`
- Именование JSON-полей: camelCase
- Формат даты и времени: ISO 8601 (UTC)

## Эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| GET | /api/monitors | Получить список мониторов |
| POST | /api/monitors | Создать монитор |
| GET | /api/monitors/{id} | Получить монитор |
| PATCH | /api/monitors/{id} | Изменить монитор |
| DELETE | /api/monitors/{id} | Удалить монитор |
| POST | /api/monitors/{id}/check | Запустить проверку |
| GET | /api/monitors/{id}/history | Получить историю проверок |

## Общие правила

- Все ответы API возвращаются в формате JSON, кроме ответов без тела.
- Время возвращается в UTC.
- История проверок содержит не более 50 последних результатов.
- Результаты истории сортируются от новых к старым.
- Удаление монитора приводит к удалению его истории проверок.
- Допустимые протоколы URL: HTTP и HTTPS.

## Статусы монитора

- `UP` — последняя проверка успешна.
- `DOWN` — последняя проверка завершилась ошибкой.
- `UNKNOWN` — проверок ещё не было.

## Статусы HTTP

| Код | Значение |
|---|---|
| 200 | Успешный запрос |
| 201 | Ресурс создан |
| 204 | Успешное удаление |
| 400 | Некорректные данные |
| 404 | Монитор не найден |
| 422 | Ошибка валидации |
| 500 | Внутренняя ошибка сервера |


---

## 1. Получение списка мониторов

`GET /api/monitors`

**Ответ: `200 OK`**

```json
{
  "monitors": [
    {
      "id": 1,
      "name": "JSONPlaceholder",
      "url": "https://jsonplaceholder.typicode.com",
      "intervalSeconds": 60,
      "isActive": true,
      "status": "UP",
      "responseTimeMs": 145,
      "lastCheckedAt": "2026-11-15T10:30:00Z",
      "createdAt": "2026-11-14T12:00:00Z"
    }
  ]
}
```

Если проверок ещё не было, `status` будет `UNKNOWN`, а `responseTimeMs` и `lastCheckedAt` — `null`.

## 2. Создание монитора

`POST /api/monitors`

**Тело запроса:**

```json
{
  "name": "JSONPlaceholder",
  "url": "https://jsonplaceholder.typicode.com",
  "intervalSeconds": 60
}
```

**Ответ: `201 Created`**

Возвращается созданный объект монитора.

## 3. Получение монитора

`GET /api/monitors/{id}`

**Ответ: `200 OK`**

Возвращается объект монитора в том же формате, что и в списке.

## 4. Изменение монитора

`PATCH /api/monitors/{id}`

**Тело запроса:**

```json
{
  "intervalSeconds": 120
}
```

Можно передавать одно или несколько полей:

- `name`
- `url`
- `intervalSeconds`
- `isActive`

**Ответ: `200 OK`**

Возвращается обновлённый объект монитора.

## 5. Удаление монитора

`DELETE /api/monitors/{id}`

**Ответ: `204 No Content`**

Тело ответа отсутствует.

## 6. Ручная проверка

`POST /api/monitors/{id}/check`

Тело запроса не требуется.

**Ответ: `200 OK`**

```json
{
  "status": "UP",
  "statusCode": 200,
  "responseTimeMs": 145,
  "errorMessage": null,
  "checkedAt": "2026-11-15T10:30:00Z"
}
```

При неудачной проверке статус будет `DOWN`. Поля `statusCode`, `responseTimeMs` и `errorMessage` могут содержать `null`, если соответствующее значение недоступно.

## 7. История проверок

`GET /api/monitors/{id}/history`

**Ответ: `200 OK`**

```json
{
  "history": [
    {
      "id": 15,
      "status": "UP",
      "statusCode": 200,
      "responseTimeMs": 145,
      "errorMessage": null,
      "checkedAt": "2026-11-15T10:30:00Z"
    }
  ]
}
```

Возвращаются последние 50 результатов, отсортированные от новых к старым.

## 8. Формат ошибок

При возникновении ошибки возвращается JSON:

```json
{
  "error": {
    "code": "MONITOR_NOT_FOUND",
    "message": "Monitor not found"
  }
}
```

Примеры кодов ошибок:

| Код | Описание |
|---|---|
| MONITOR_NOT_FOUND | Монитор не найден |
| VALIDATION_ERROR | Некорректные данные |
| INTERNAL_ERROR | Внутренняя ошибка сервера |

