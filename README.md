# moonraker-telegram-bot (RU Fork)

![image](https://i.ibb.co/p6dLh0n2/2.png)

> **Это форк проекта [nlef/moonraker-telegram-bot](https://github.com/nlef/moonraker-telegram-bot).**
> Отличия от оригинала:
> - Интерфейс бота полностью переведён на **русский язык** (сообщения, кнопки, команды)
> - Добавлен встроенный **HTTP API** для получения статуса печати (см. раздел ниже)

---

Общая идея проекта — дать возможность управлять принтером и следить за ним без необходимости настраивать VPN, открывать домашнюю сеть или делать что-либо подобное. Вдобавок вы получаете push-уведомления прямо в телефон и экономичный способ проверять прогресс печати, находясь вдали от принтера.

Как всегда с подобными решениями, напоминаем: не оставляйте принтер без присмотра и соблюдайте все меры противопожарной безопасности.

---

## Возможности и установка

Подробная информация об установке и описание функций — в [вики оригинального проекта](https://github.com/nlef/moonraker-telegram-bot/wiki).

---

## HTTP API статуса печати

Бот запускает лёгкий HTTP-сервер на порту **7177**, через который можно получить текущий статус принтера в формате JSON. Это удобно для интеграции с домашней автоматизацией, дашбордами и сторонними скриптами.

### Endpoint

```
GET http://<адрес_хоста>:7177/printingstatus
```

Поддерживается CORS — запросы с браузера работают без ограничений.

---

### Пример ответа

```json
{
  "connected": true,
  "state": "ready",
  "state_message": "",

  "printing": true,
  "paused": false,
  "heating": false,

  "filename": "my_model.gcode",
  "filename_with_time": "my_model.gcode_2024-03-15_10-30",

  "progress_percent": 42.5,
  "vsd_progress_percent": 41.8,
  "height_mm": 12.4,

  "print_duration_seconds": 3600,
  "print_duration_formatted": "1:00:00",
  "file_estimated_time_seconds": 7200,
  "file_estimated_time_formatted": "2:00:00",
  "eta_seconds": 3600,
  "eta_formatted": "1:00:00",
  "finish_time": "2024-03-15 11:30",

  "filament_used_mm": 2540.5,
  "filament_used_m": 2.541,
  "filament_total_mm": 6000.0,
  "filament_total_m": 6.0,
  "filament_weight_total_g": 18.5,
  "filament_weight_used_g": 7.83,

  "sensors": {
    "extruder": {
      "temperature": 215.0,
      "target": 215.0,
      "power": 0.3
    },
    "heater_bed": {
      "temperature": 60.0,
      "target": 60.0,
      "power": 0.1
    },
    "fan": {
      "speed": 1.0,
      "rpm": 4200.0
    }
  },

  "power_devices": {
    "printer": {
      "device": "printer",
      "status": "on",
      "locked_while_printing": "True",
      "type": "gpio",
      "is_shutdown": false
    }
  }
}
```

---

### Описание полей

#### Состояние подключения

| Поле | Тип | Описание |
|---|---|---|
| `connected` | bool | Klippy подключён к Moonraker |
| `state` | string | Состояние Klippy: `ready`, `error`, `shutdown`, `startup` |
| `state_message` | string | Сообщение об ошибке состояния (если есть) |

#### Флаги печати

| Поле | Тип | Описание |
|---|---|---|
| `printing` | bool | Идёт печать |
| `paused` | bool | Печать на паузе |
| `heating` | bool | Принтер прогревается (цели нагрева заданы, печать ещё не начата) |

#### Файл

| Поле | Тип | Описание |
|---|---|---|
| `filename` | string | Имя печатаемого файла |
| `filename_with_time` | string | Имя файла с датой и временем начала печати |

#### Прогресс

| Поле | Тип | Описание |
|---|---|---|
| `progress_percent` | float | Прогресс по данным слайсера, % |
| `vsd_progress_percent` | float | Прогресс по виртуальной SD-карте, % |
| `height_mm` | float | Текущая высота печати, мм |

#### Время

| Поле | Тип | Описание |
|---|---|---|
| `print_duration_seconds` | int | Время печати с начала, секунды |
| `print_duration_formatted` | string | То же в формате `H:MM:SS` |
| `file_estimated_time_seconds` | int | Оценочное время из слайсера, секунды |
| `file_estimated_time_formatted` | string | То же в формате `H:MM:SS` |
| `eta_seconds` | int | Осталось до конца, секунды |
| `eta_formatted` | string | То же в формате `H:MM:SS` |
| `finish_time` | string | Предполагаемое время завершения, `YYYY-MM-DD HH:MM` |

#### Пластик

| Поле | Тип | Описание |
|---|---|---|
| `filament_used_mm` | float | Использовано пластика, мм |
| `filament_used_m` | float | Использовано пластика, м |
| `filament_total_mm` | float | Всего пластика в файле, мм |
| `filament_total_m` | float | Всего пластика в файле, м |
| `filament_weight_total_g` | float | Общий вес пластика, г |
| `filament_weight_used_g` | float | Использованный вес пластика, г |

#### Датчики (`sensors`)

Словарь, где ключ — имя датчика, значение — объект с полями:

| Поле | Тип | Описание |
|---|---|---|
| `temperature` | float | Текущая температура, °C |
| `target` | float | Целевая температура, °C |
| `power` | float | Мощность нагрева, 0.0–1.0 |
| `speed` | float | Скорость вентилятора, 0.0–1.0 |
| `rpm` | float | Обороты вентилятора, RPM |

Набор полей зависит от типа датчика. Отсутствующие поля не включаются в ответ.

#### Устройства питания (`power_devices`)

Словарь с устройствами Moonraker Device Power. Каждый объект содержит поля:

| Поле | Тип | Описание |
|---|---|---|
| `device` | string | Имя устройства |
| `status` | string | `on` или `off` |
| `locked_while_printing` | string | Заблокировано во время печати |
| `type` | string | Тип устройства (например, `gpio`, `tplink_smartplug`) |
| `is_shutdown` | bool | Устройство выключено через аварийную остановку |

---

### Коды ответа

| Код | Описание |
|---|---|
| `200` | Успешно, тело — JSON с данными |
| `404` | Неизвестный путь |

---

### Пример использования

**curl:**
```bash
curl http://192.168.1.56:7177/printingstatus
```

**Python:**
```python
import requests

resp = requests.get("http://192.168.1.56:7177/printingstatus")
data = resp.json()
print(f"Прогресс: {data['progress_percent']}%")
print(f"Осталось: {data['eta_formatted']}")
```

**JavaScript / браузер:**
```javascript
const res = await fetch("http://192.168.1.56:7177/printingstatus");
const data = await res.json();
console.log(`Прогресс: ${data.progress_percent}%`);
```

---

## Проблемы и баг-репорты

Подробнее об отладке и сборе логов — в [вики оригинального проекта](https://github.com/nlef/moonraker-telegram-bot/wiki).

При обращении за помощью прикладывайте файл `telegram.log` и вывод команды:
```bash
sudo journalctl -r -u moonraker-telegram-bot
```

---

### Удачной печати!
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/donate/?hosted_button_id=KCKKK5WLXNEFE)

---

**Оригинальный проект** [nlef/moonraker-telegram-bot](https://github.com/nlef/moonraker-telegram-bot)

---

**Klipper** by [KevinOConnor](https://github.com/KevinOConnor):
https://github.com/KevinOConnor/klipper

**Moonraker** by [Arksine](https://github.com/Arksine):
https://github.com/Arksine/moonraker

**KIAUH** by [th33xitus](https://github.com/th33xitus):
https://github.com/th33xitus/KIAUH

**Mainsail** by [meteyou](https://github.com/meteyou):
https://github.com/meteyou/mainsail

**Fluidd** by [cadriel](https://github.com/cadriel):
https://github.com/cadriel/fluidd
