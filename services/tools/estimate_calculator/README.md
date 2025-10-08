# Сметный калькулятор

Инструмент для расчета смет с маржой % на основе объемов работ и ГЭСН-цен.

## Возможности

- ✅ Расчет прямых затрат по ГЭСН
- ✅ Расчет зарплаты и вахтовых надбавок
- ✅ Учет северных коэффициентов
- ✅ Расчет командировочных расходов
- ✅ Расчет стоимости СИЗ
- ✅ Расчет накладных расходов (18%)
- ✅ Расчет маржи в процентах
- ✅ Экспорт в Excel с цветным форматированием

## API Endpoints

### POST `/tools/estimate_calculator/calculate`
Расчет сметы с маржой %

**Параметры:**
```json
{
  "volumes": [
    {
      "code": "01-01-001-01",
      "name": "Бетон тяжелый",
      "unit": "м³",
      "qty": 10.0
    }
  ],
  "region": "Москва",
  "shift_pattern": "30/15",
  "north_coeff": 1.0,
  "travel_days": 0,
  "contract_price": 100000.0
}
```

**Ответ:**
```json
{
  "file_path": "/tmp/estimate_abc123.xlsx",
  "total_cost": 75000.0,
  "margin_pct": 25.0,
  "cost_breakdown": {
    "direct_costs": 65000.0,
    "payroll": 12000.0,
    "shift_bonus": 2400.0,
    "northern_coeff": 0.0,
    "travel_costs": 0.0,
    "siz_costs": 1300.0,
    "overhead": 2160.0,
    "total_cost": 75000.0
  }
}
```

### GET `/tools/estimate_calculator/regions`
Получение списка регионов с коэффициентами

### GET `/tools/estimate_calculator/gesn/{code}`
Получение цены по коду ГЭСН

### GET `/tools/estimate_calculator/download/{file_id}`
Скачивание Excel файла сметы

## Структура затрат

1. **Прямые затраты** = qty × (price_material + price_labour + price_machine)
2. **Зарплата** = qty × price_labour
3. **Вахтовая надбавка** = зарплата × (дни_работы/30) × 0.2
4. **Северный коэффициент** = зарплата × (north_coeff - 1.0)
5. **Командировочные** = travel_days × daily_allowance
6. **СИЗ** = 2% от прямых затрат
7. **Накладные расходы** = зарплата × 0.18
8. **Общая стоимость** = сумма всех затрат
9. **Маржа %** = (contract_price - total_cost) / contract_price × 100

## Тестирование

```bash
pytest services/tools/estimate_calculator/tests/test_calculator.py -v
```

## Требования

- Python 3.8+
- FastAPI
- pandas
- openpyxl
- pydantic

## Установка

```bash
pip install fastapi pandas openpyxl pydantic
```

## Использование

```python
from services.tools.estimate_calculator.calculator import EstimateCalculator
from services.tools.estimate_calculator.models import EstimateRequest, VolumeItem

# Создание калькулятора
calculator = EstimateCalculator()

# Создание запроса
request = EstimateRequest(
    volumes=[
        VolumeItem(code="01-01-001-01", name="Бетон", unit="м³", qty=10.0)
    ],
    region="Москва",
    shift_pattern="30/15",
    north_coeff=1.0
)

# Расчет сметы
result = calculator.calculate_estimate(request)
print(f"Общая стоимость: {result.total_cost:,.2f} ₽")
print(f"Маржа: {result.margin_pct:.1f}%")
```
