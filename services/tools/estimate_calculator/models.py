"""
Pydantic модели для сметного калькулятора
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class VolumeItem(BaseModel):
    """Элемент объема работ"""
    code: str = Field(..., description="Код ГЭСН")
    name: str = Field(..., description="Наименование работы")
    unit: str = Field(..., description="Единица измерения")
    qty: float = Field(..., gt=0, description="Количество")


class EstimateRequest(BaseModel):
    """Запрос на расчет сметы"""
    volumes: List[VolumeItem] = Field(..., description="Список объемов работ")
    region: str = Field(..., description="Регион выполнения работ")
    shift_pattern: str = Field(default="30/15", description="График вахты (дни работы/дни отдыха)")
    north_coeff: float = Field(default=1.0, gt=0, description="Северный коэффициент")
    contract_price: Optional[float] = Field(default=None, gt=0, description="Договорная цена (если известна)")
    travel_days: int = Field(default=0, ge=0, description="Количество дней командировки")
    daily_allowance: float = Field(default=2000.0, gt=0, description="Суточные (руб/день)")


class CostBreakdown(BaseModel):
    """Детализация затрат"""
    direct_costs: float = Field(..., description="Прямые затраты")
    payroll: float = Field(..., description="Зарплата")
    shift_bonus: float = Field(..., description="Вахтовая надбавка")
    northern_coeff: float = Field(..., description="Северный коэффициент")
    travel_costs: float = Field(..., description="Командировочные")
    siz_costs: float = Field(..., description="СИЗ")
    overhead: float = Field(..., description="Накладные расходы")
    total_cost: float = Field(..., description="Общая стоимость")


class EstimateResponse(BaseModel):
    """Ответ с результатами расчета сметы"""
    file_path: str = Field(..., description="Путь к Excel файлу")
    total_cost: float = Field(..., description="Общая стоимость работ")
    margin_pct: float = Field(..., description="Маржа в процентах")
    cost_breakdown: CostBreakdown = Field(..., description="Детализация затрат")
    created_at: datetime = Field(default_factory=datetime.now, description="Время создания")
    region: str = Field(..., description="Регион")
    shift_pattern: str = Field(..., description="График вахты")


class GESNPrice(BaseModel):
    """Цена по ГЭСН"""
    code: str = Field(..., description="Код ГЭСН")
    name: str = Field(..., description="Наименование")
    unit: str = Field(..., description="Единица измерения")
    price_material: float = Field(default=0.0, description="Цена материалов")
    price_labour: float = Field(default=0.0, description="Цена труда")
    price_machine: float = Field(default=0.0, description="Цена машин")
    total_price: float = Field(default=0.0, description="Общая цена")
    
    def __init__(self, **data):
        # Вычисляем total_price если не задан
        if 'total_price' not in data or data['total_price'] == 0:
            data['total_price'] = data.get('price_material', 0) + data.get('price_labour', 0) + data.get('price_machine', 0)
        super().__init__(**data)


class SIZNorm(BaseModel):
    """Норма СИЗ"""
    profession: str = Field(..., description="Профессия")
    item: str = Field(..., description="Наименование СИЗ")
    unit: str = Field(..., description="Единица измерения")
    norm: float = Field(..., description="Норма на человека")
    price: float = Field(..., description="Цена за единицу")


class RegionCoeff(BaseModel):
    """Районный коэффициент"""
    region: str = Field(..., description="Регион")
    coeff: float = Field(..., description="Коэффициент")
    description: str = Field(..., description="Описание")
