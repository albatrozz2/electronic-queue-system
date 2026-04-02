# Система электронной очереди

> **Задание 4 — Ядро системы**  
> Автор: Жамбалов Вандан Ринчинович · Группа Б-752 · ВСГУТУ · 2026

---

## Описание

Веб-приложение для автоматизации обслуживания очереди в организациях.  
Стек: **Python / Flask** · **SQLite** · **HTML5 / CSS3 / JavaScript**

---

## Структура проекта

```
electronic-queue-system/
├── run.py                  # точка входа
├── requirements.txt
├── queue.db                # создаётся автоматически
└── app/
    ├── __init__.py         # фабрика приложения
    ├── database.py         # инициализация и подключение к SQLite
    ├── routes.py           # все маршруты (main, admin, operator)
    └── templates/
        ├── kiosk.html      # интерфейс клиента (киоск)
        ├── operator.html   # интерфейс оператора
        ├── admin.html      # панель администратора
        └── display.html    # дисплей очереди (TV)
```

---

## Быстрый старт

```bash
# 1. клонировать репозиторий
git clone https://github.com/albatrozz2/electronic-queue-system.git
cd electronic-queue-system

# 2. установить зависимости
pip install -r requirements.txt

# 3. запустить
python run.py
```

Приложение запустится на `http://localhost:5000`

| Страница | URL |
|----------|-----|
| Киоск (клиент) | http://localhost:5000/ |
| Оператор | http://localhost:5000/operator/ |
| Администратор | http://localhost:5000/admin/ |
| Дисплей (TV) | http://localhost:5000/display |

---

## База данных

### Схема (SQLite)

**services — Услуги**

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PK | Идентификатор |
| name | TEXT | Название услуги |
| code | TEXT UNIQUE | Код (A, B, C…) |
| priority | INTEGER | Приоритет (1 = высший) |
| active | INTEGER | 1 = активна |

**operators — Операторы**

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PK | Идентификатор |
| full_name | TEXT | ФИО оператора |
| window_number | INTEGER | Номер окна |
| status | TEXT | available / busy / break |
| current_ticket_id | INTEGER | ID текущего талона |

**tickets — Талоны**

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PK | Идентификатор |
| ticket_number | TEXT | Номер (A001, B012…) |
| service_id | INTEGER FK | Ссылка на услугу |
| operator_id | INTEGER FK | Ссылка на оператора |
| status | TEXT | waiting / called / completed / missed / cancelled |
| created_at | TIMESTAMP | Время создания |
| called_at | TIMESTAMP | Время вызова |
| completed_at | TIMESTAMP | Время завершения |

---

## REST API

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/services` | Список услуг |
| POST | `/api/tickets` | Создать талон |
| GET | `/api/tickets/queue` | Текущая очередь |
| GET | `/api/display/data` | Данные для дисплея |
| POST | `/operator/api/next` | Вызвать следующего |
| POST | `/operator/api/complete` | Завершить обслуживание |
| POST | `/operator/api/repeat` | Повторный вызов |
| POST | `/operator/api/break` | Статус: перерыв |
| POST | `/operator/api/missed` | Клиент не явился |
| GET | `/admin/api/services` | Список услуг (CRUD) |
| POST | `/admin/api/services` | Добавить услугу |
| PUT | `/admin/api/services/<id>` | Изменить услугу |
| DELETE | `/admin/api/services/<id>` | Удалить услугу |
| GET | `/admin/api/operators` | Список операторов |
| POST | `/admin/api/operators` | Добавить оператора |
| PUT | `/admin/api/operators/<id>` | Изменить оператора |
| DELETE | `/admin/api/operators/<id>` | Удалить оператора |
| GET | `/admin/api/stats` | Статистика |

### Пример: создать талон

```http
POST /api/tickets
Content-Type: application/json

{ "service_id": 1 }
```

Ответ:
```json
{
  "ticket_number": "A005",
  "service": "Консультация по вопросам",
  "waiting_ahead": 4,
  "est_minutes": 20
}
```

### Пример: вызвать следующего (оператор)

```http
POST /operator/api/next
Content-Type: application/json

{ "operator_id": 1 }
```

Ответ:
```json
{
  "ticket_number": "A005",
  "ticket_id": 12
}
```

---

## Модули системы (ядро)

### Модуль администратора
- CRUD услуг: добавление, редактирование, удаление, приоритеты
- CRUD операторов: назначение на окна
- Статистика: обслужено за день, в очереди, вызваны, среднее время

### Модуль оператора
- Вызов следующего клиента по приоритету и времени прихода
- Управление статусом: доступен / занят / перерыв
- Повторный вызов, отметка неявки, завершение обслуживания
- История обслуживания за смену

### База данных
- Инициализируется автоматически при первом запуске
- Наполняется тестовыми данными (4 услуги, 1 оператор)
- Все операции через параметризованные запросы (защита от SQL-инъекций)

---

## Логика очереди

1. Клиент выбирает услугу → создаётся талон со статусом `waiting`
2. Оператор нажимает **«Следующий»** → выбирается талон с наименьшим приоритетом услуги и наиболее ранним временем создания → статус `called`
3. Оператор нажимает **«Завершить»** → статус `completed`, фиксируется время
4. Если клиент не подошёл — **«Отсутствует»** → статус `missed`
5. Дисплей обновляется каждые 5 секунд через `/api/display/data`
