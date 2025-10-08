# namespace:financial
from typing import Any, Dict, List
import time
from core.tools.base_tool import ToolManifest, ToolInterface, ToolParam, ToolParamType

coordinator_interface = ToolInterface(
    purpose='Профессиональный расчет бюджета строительного проекта с учетом всех факторов: материалов, работ, накладных расходов, прибыли, налогов и рисков',
    input_requirements={
        'project_name': ToolParam(
            name='project_name',
            type=ToolParamType.STRING,
            required=True,
            description='Название проекта'
        ),
        'base_cost': ToolParam(
            name='base_cost',
            type=ToolParamType.NUMBER,
            required=True,
            description='Базовая стоимость материалов и работ'
        )
    },
    execution_flow=[
        'Валидация входных параметров',
        'Расчет базовых компонентов',
        'Учет факторов риска и инфляции',
        'Расчет налогов',
        'Формирование итоговой суммы',
        'Создание детализации по статьям',
        'Генерация рекомендаций',
        'Возврат финансового отчета'
    ],
    output_format={
        'status': 'success|error',
        'data': {
            'total_budget': 'float',
            'breakdown': 'object',
            'recommendations': 'array',
            'metadata': 'object'
        }
    },
    usage_guidelines={
        'for_coordinator': [
            'Используйте для расчета бюджетов строительных проектов',
            'Передавайте точные данные о базовой стоимости',
            'Указывайте тип проекта для применения правильных коэффициентов'
        ],
        'for_models': [
            'Инструмент возвращает полный финансовый отчет',
            'Используйте breakdown для детального анализа затрат',
            'Следуйте рекомендациям для оптимизации бюджета'
        ]
    }
)

manifest = ToolManifest(
    name='auto_budget',
    version='1.0.0',
    title='💰 Автоматический расчет бюджета',
    description='Профессиональный расчет бюджета строительного проекта с учетом всех факторов: материалов, работ, накладных расходов, прибыли, налогов и рисков.',
    category='financial',
    ui_placement='dashboard',
    enabled=True,
    system=False,
    entrypoint='tools.custom.auto_budget_full:execute',
    params=[
        ToolParam(
            name='project_name',
            type=ToolParamType.STRING,
            required=True,
            description='Название проекта',
            ui={
                'placeholder': 'Введите название проекта...',
                'maxLength': 200
            }
        ),
        ToolParam(
            name='base_cost',
            type=ToolParamType.NUMBER,
            required=True,
            description='Базовая стоимость (материалы + работы)',
            ui={
                'min': 1000,
                'max': 100000000,
                'step': 1000,
                'currency': 'RUB'
            }
        ),
        ToolParam(
            name='project_type',
            type=ToolParamType.ENUM,
            required=False,
            default='residential',
            description='Тип проекта',
            enum=[
                {'value': 'residential', 'label': 'Жилой дом'},
                {'value': 'commercial', 'label': 'Коммерческое здание'},
                {'value': 'industrial', 'label': 'Промышленный объект'},
                {'value': 'infrastructure', 'label': 'Инфраструктура'},
                {'value': 'renovation', 'label': 'Реконструкция'},
                {'value': 'repair', 'label': 'Ремонт'}
            ]
        ),
        ToolParam(
            name='worker_daily_wage',
            type=ToolParamType.NUMBER,
            required=False,
            default=6700,
            description='Зарплата рабочего, руб/сут',
            ui={
                'min': 100,
                'max': 50000,
                'step': 100,
                'currency': 'RUB'
            }
        ),
        ToolParam(
            name='total_labor_hours',
            type=ToolParamType.NUMBER,
            required=False,
            default=40000,
            description='Общая трудоёмкость, чел.-часы',
            ui={
                'min': 100,
                'max': 1000000,
                'step': 100
            }
        ),
        ToolParam(
            name='project_duration_months',
            type=ToolParamType.NUMBER,
            required=False,
            default=12,
            description='Продолжительность проекта, мес',
            ui={
                'min': 1,
                'max': 60,
                'step': 1
            }
        ),
        ToolParam(
            name='shifts_per_day',
            type=ToolParamType.NUMBER,
            required=False,
            default=1,
            description='Количество смен в день',
            ui={
                'min': 1,
                'max': 3,
                'step': 1
            }
        ),
        ToolParam(
            name='hours_per_shift',
            type=ToolParamType.NUMBER,
            required=False,
            default=10,
            description='Часов в смене',
            ui={
                'min': 1,
                'max': 24,
                'step': 1
            }
        ),
        ToolParam(
            name='shifts_per_month',
            type=ToolParamType.NUMBER,
            required=False,
            default=30,
            description='Смен в месяце',
            ui={
                'min': 1,
                'max': 31,
                'step': 1
            }
        ),
        ToolParam(
            name='shift_mode_days',
            type=ToolParamType.NUMBER,
            required=False,
            default=45,
            description='Режим вахты, дней',
            ui={
                'min': 1,
                'max': 90,
                'step': 1
            }
        ),
        ToolParam(
            name='efficiency_coefficient',
            type=ToolParamType.NUMBER,
            required=False,
            default=0.8,
            description='Коэффициент выработки',
            ui={
                'min': 0.1,
                'max': 1.0,
                'step': 0.01
            }
        ),
        ToolParam(
            name='siz_cost',
            type=ToolParamType.NUMBER,
            required=False,
            default=30000,
            description='Стоимость комплекта СИЗ, руб',
            ui={
                'min': 1000,
                'max': 100000,
                'step': 1000,
                'currency': 'RUB'
            }
        ),
        ToolParam(
            name='ticket_cost',
            type=ToolParamType.NUMBER,
            required=False,
            default=15000,
            description='Стоимость билета, руб',
            ui={
                'min': 1000,
                'max': 50000,
                'step': 1000,
                'currency': 'RUB'
            }
        ),
        ToolParam(
            name='meal_cost',
            type=ToolParamType.NUMBER,
            required=False,
            default=800,
            description='Стоимость питания, руб/сут/чел',
            ui={
                'min': 100,
                'max': 5000,
                'step': 100,
                'currency': 'RUB'
            }
        ),
        ToolParam(
            name='accommodation_cost',
            type=ToolParamType.NUMBER,
            required=False,
            default=1200,
            description='Стоимость проживания, руб/сут/чел',
            ui={
                'min': 100,
                'max': 5000,
                'step': 100,
                'currency': 'RUB'
            }
        ),
        ToolParam(
            name='engineer_daily_wage',
            type=ToolParamType.NUMBER,
            required=False,
            default=8335,
            description='Зарплата ИТР, руб/сут',
            ui={
                'min': 1000,
                'max': 50000,
                'step': 100,
                'currency': 'RUB'
            }
        ),
        ToolParam(
            name='engineer_ratio',
            type=ToolParamType.NUMBER,
            required=False,
            default=0.14,
            description='Доля линейного ИТР от рабочих',
            ui={
                'min': 0.01,
                'max': 1.0,
                'step': 0.01
            }
        ),
        ToolParam(
            name='mandatory_engineers',
            type=ToolParamType.NUMBER,
            required=False,
            default=8,
            description='Обязательный ИТР (шт.)',
            ui={
                'min': 1,
                'max': 50,
                'step': 1
            }
        ),
        ToolParam(
            name='insurance_rate',
            type=ToolParamType.NUMBER,
            required=False,
            default=0.32,
            description='Страховые взносы (0.0-1.0)',
            ui={
                'min': 0.0,
                'max': 1.0,
                'step': 0.01,
                'slider': True
            }
        ),
        ToolParam(
            name='currency',
            type=ToolParamType.ENUM,
            required=False,
            default='RUB',
            description='Валюта расчета',
            enum=[
                {'value': 'RUB', 'label': 'Рубли (₽)'},
                {'value': 'USD', 'label': 'Доллары ($)'},
                {'value': 'EUR', 'label': 'Евро (€)'}
            ]
        )
    ],
    outputs=['budget', 'total_cost', 'breakdown', 'recommendations'],
    result_display={
        'type': 'financial_report',
        'title': 'Финансовый отчет проекта',
        'description': 'Детальный расчет бюджета с анализом и рекомендациями',
        'features': {
            'exportable': True,
            'printable': True,
            'interactive': True,
            'charts': True
        }
    },
    permissions=['filesystem:write', 'network:out'],
    tags=['budget', 'finance', 'construction', 'planning', 'enterprise'],
    documentation={
        'examples': [
            {
                'title': 'Жилой дом',
                'project_name': 'Строительство коттеджа',
                'base_cost': 5000000,
                'project_type': 'residential'
            },
            {
                'title': 'Коммерческое здание',
                'project_name': 'Офисный центр',
                'base_cost': 15000000,
                'project_type': 'commercial'
            }
        ],
        'tips': [
            'Учитывайте региональные особенности при расчете',
            'Закладывайте резерв на непредвиденные расходы',
            'Регулярно пересматривайте бюджет в процессе строительства'
        ]
    },
    coordinator_interface=coordinator_interface
)

def execute(**kwargs) -> Dict[str, Any]:
    """Execute enterprise-level budget calculation with advanced financial analysis."""
    start_time = time.time()
    
    try:
        # Validate and parse parameters
        project_name = kwargs.get('project_name', '').strip()
        if not project_name:
            return {
                'status': 'error',
                'error': 'Название проекта не может быть пустым',
                'execution_time': time.time() - start_time
            }
        
        base_cost = kwargs.get('base_cost', 0)
        if base_cost <= 0:
            return {
                'status': 'error',
                'error': 'Базовая стоимость должна быть больше 0',
                'execution_time': time.time() - start_time
            }
        
        # Parse parameters with defaults
        project_type = kwargs.get('project_type', 'residential')
        worker_daily_wage = kwargs.get('worker_daily_wage', 6700)
        total_labor_hours = kwargs.get('total_labor_hours', 40000)
        project_duration_months = kwargs.get('project_duration_months', 12)
        shifts_per_day = kwargs.get('shifts_per_day', 1)
        hours_per_shift = kwargs.get('hours_per_shift', 10)
        shifts_per_month = kwargs.get('shifts_per_month', 30)
        shift_mode_days = kwargs.get('shift_mode_days', 45)
        efficiency_coefficient = kwargs.get('efficiency_coefficient', 0.8)
        siz_cost = kwargs.get('siz_cost', 30000)
        ticket_cost = kwargs.get('ticket_cost', 15000)
        meal_cost = kwargs.get('meal_cost', 800)
        accommodation_cost = kwargs.get('accommodation_cost', 1200)
        engineer_daily_wage = kwargs.get('engineer_daily_wage', 8335)
        engineer_ratio = kwargs.get('engineer_ratio', 0.14)
        mandatory_engineers = kwargs.get('mandatory_engineers', 8)
        insurance_rate = kwargs.get('insurance_rate', 0.32)
        currency = kwargs.get('currency', 'RUB')
        
        # Calculate comprehensive budget using full budget_final logic
        budget_calculation = _calculate_comprehensive_budget(
            base_cost=base_cost,
            project_type=project_type,
            worker_daily_wage=worker_daily_wage,
            total_labor_hours=total_labor_hours,
            project_duration_months=project_duration_months,
            shifts_per_day=shifts_per_day,
            hours_per_shift=hours_per_shift,
            shifts_per_month=shifts_per_month,
            shift_mode_days=shift_mode_days,
            efficiency_coefficient=efficiency_coefficient,
            siz_cost=siz_cost,
            ticket_cost=ticket_cost,
            meal_cost=meal_cost,
            accommodation_cost=accommodation_cost,
            engineer_daily_wage=engineer_daily_wage,
            engineer_ratio=engineer_ratio,
            mandatory_engineers=mandatory_engineers,
            insurance_rate=insurance_rate,
            currency=currency
        )
        
        # Generate recommendations
        recommendations = _generate_budget_recommendations(
            budget_calculation, project_type, project_duration_months
        )
        
        # Create detailed breakdown table
        table_data = _create_budget_breakdown_table(budget_calculation, currency)
        
        # Generate metadata
        metadata = {
            'project_name': project_name,
            'project_type': project_type,
            'base_cost': base_cost,
            'total_cost': budget_calculation['total_cost'],
            'calculated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'recommendations': recommendations
        }
        
        execution_time = time.time() - start_time
        
        return {
            'status': 'success',
            'data': {
                'budget': budget_calculation,
                'total_cost': budget_calculation['total_cost'],
                'breakdown': table_data,
                'recommendations': recommendations,
                'metadata': metadata
            },
            'execution_time': execution_time,
            'result_type': 'financial_report',
            'result_title': f'💰 Бюджет проекта: {project_name}',
            'result_table': table_data,
            'metadata': metadata
        }
        
    except Exception as e:
        return { 
            'status': 'error', 
            'error': str(e),
            'execution_time': time.time() - start_time
        }

def _calculate_comprehensive_budget(
    base_cost: float,
    project_type: str,
    worker_daily_wage: float,
    total_labor_hours: float,
    project_duration_months: int,
    shifts_per_day: int,
    hours_per_shift: int,
    shifts_per_month: int,
    shift_mode_days: int,
    efficiency_coefficient: float,
    siz_cost: float,
    ticket_cost: float,
    meal_cost: float,
    accommodation_cost: float,
    engineer_daily_wage: float,
    engineer_ratio: float,
    mandatory_engineers: int,
    insurance_rate: float,
    currency: str
) -> Dict[str, Any]:
    """Calculate comprehensive budget using full budget_final logic."""
    
    # Validate inputs
    if base_cost <= 0:
        raise ValueError("Базовая стоимость должна быть больше 0")
    
    if total_labor_hours <= 0:
        raise ValueError("Трудоемкость должна быть больше 0")
        
    if project_duration_months <= 0:
        raise ValueError("Продолжительность проекта должна быть больше 0")
        
    if efficiency_coefficient <= 0 or efficiency_coefficient > 1:
        raise ValueError("Коэффициент выработки должен быть в диапазоне (0, 1]")
    
    # --- Исходные данные ---
    input_data = {
        "СТОИМОСТЬ_СТРОИТЕЛЬСТВА": base_cost,
        "ЗП_РАБОЧЕГО_В_СУТКИ": worker_daily_wage,
        "ТРУДОЕМКОСТЬ": total_labor_hours,
        "ПРОДОЛЖИТЕЛЬНОСТЬ_МЕС": project_duration_months,
        "СМЕН": shifts_per_day,
        "ЧАСОВ_В_СМЕНЕ": hours_per_shift,
        "СМЕН_В_МЕС": shifts_per_month,
        "РЕЖИМ_ВАХТЫ_ДНЕЙ": shift_mode_days,
        "КЭФ_ВЫРАБОТКИ": efficiency_coefficient,
        "СТОИМОСТЬ_СИЗ": siz_cost,
        "СТОИМОСТЬ_БИЛЕТА": ticket_cost,
        "СТОИМОСТЬ_ПИТАНИЯ": meal_cost,
        "СТОИМОСТЬ_ПРОЖИВАНИЯ": accommodation_cost,
        "ЗП_ИТР_В_СУТКИ": engineer_daily_wage,
        "ДОЛЯ_ИТР": engineer_ratio,
        "ОБЯЗАТЕЛЬНЫЙ_ИТР": mandatory_engineers,
    }
    
    # --- Промежуточные расчёты ---
    # Количество рабочих
    workers_count = round(
        input_data["ТРУДОЕМКОСТЬ"] / 
        input_data["КЭФ_ВЫРАБОТКИ"] / 
        (input_data["ЧАСОВ_В_СМЕНЕ"] * input_data["СМЕН"] * input_data["СМЕН_В_МЕС"] * input_data["ПРОДОЛЖИТЕЛЬНОСТЬ_МЕС"])
    )
    
    # Количество ИТР
    engineers_count = input_data["ОБЯЗАТЕЛЬНЫЙ_ИТР"] + round(input_data["ДОЛЯ_ИТР"] * workers_count)
    
    # ФОТ рабочих
    worker_fot = (
        workers_count * 
        input_data["ЗП_РАБОЧЕГО_В_СУТКИ"] * 
        input_data["СМЕН"] * 
        input_data["СМЕН_В_МЕС"] * 
        input_data["ПРОДОЛЖИТЕЛЬНОСТЬ_МЕС"]
    )
    
    # ФОТ ИТР
    shifts_engineers = round(
        input_data["СМЕН_В_МЕС"] / 
        input_data["РЕЖИМ_ВАХТЫ_ДНЕЙ"] * 
        input_data["ПРОДОЛЖИТЕЛЬНОСТЬ_МЕС"]
    )
    
    engineer_fot = (
        engineers_count * 
        input_data["ЗП_ИТР_В_СУТКИ"] * 
        shifts_engineers * 
        input_data["РЕЖИМ_ВАХТЫ_ДНЕЙ"]
    )
    
    # ФОТ всего
    total_fot = worker_fot + engineer_fot
    
    # Страховые взносы
    insurance_contributions = total_fot * insurance_rate
    
    # Кол-во вахт рабочих
    shifts_workers = round(
        input_data["СМЕН_В_МЕС"] / 
        input_data["РЕЖИМ_ВАХТЫ_ДНЕЙ"] * 
        input_data["ПРОДОЛЖИТЕЛЬНОСТЬ_МЕС"]
    )
    
    # Билеты
    tickets_cost = (
        (workers_count * 2 * shifts_workers + engineers_count * 2 * shifts_engineers) * 
        input_data["СТОИМОСТЬ_БИЛЕТА"]
    )
    
    # Проживание
    accommodation_total_cost = (
        (workers_count * shifts_workers * input_data["РЕЖИМ_ВАХТЫ_ДНЕЙ"] + 
         engineers_count * shifts_engineers * input_data["РЕЖИМ_ВАХТЫ_ДНЕЙ"]) * 
        input_data["СТОИМОСТЬ_ПРОЖИВАНИЯ"]
    )
    
    # Питание
    meals_cost = (
        (workers_count * shifts_workers * input_data["РЕЖИМ_ВАХТЫ_ДНЕЙ"] + 
         engineers_count * shifts_engineers * input_data["РЕЖИМ_ВАХТЫ_ДНЕЙ"]) * 
        input_data["СТОИМОСТЬ_ПИТАНИЯ"]
    )
    
    # СИЗ
    siz_total_cost = (
        (workers_count + engineers_count) * 2 * 
        input_data["СТОИМОСТЬ_СИЗ"] * 
        round(input_data["ПРОДОЛЖИТЕЛЬНОСТЬ_МЕС"] / 12)
    )
    
    # Выручка всего (равна стоимости строительства)
    total_revenue = input_data["СТОИМОСТЬ_СТРОИТЕЛЬСТВА"]
    
    # Calculate monthly breakdown
    monthly_breakdown = []
    for month in range(1, 13):
        if month <= input_data["ПРОДОЛЖИТЕЛЬНОСТЬ_МЕС"]:
            # Распределение затрат по месяцам
            monthly_worker_fot = worker_fot / input_data["ПРОДОЛЖИТЕЛЬНОСТЬ_МЕС"]
            monthly_engineer_fot = engineer_fot / input_data["ПРОДОЛЖИТЕЛЬНОСТЬ_МЕС"]
            monthly_insurance = insurance_contributions / input_data["ПРОДОЛЖИТЕЛЬНОСТЬ_МЕС"]
            monthly_tickets = tickets_cost / input_data["ПРОДОЛЖИТЕЛЬНОСТЬ_МЕС"]
            monthly_accommodation = accommodation_total_cost / input_data["ПРОДОЛЖИТЕЛЬНОСТЬ_МЕС"]
            monthly_meals = meals_cost / input_data["ПРОДОЛЖИТЕЛЬНОСТЬ_МЕС"]
            monthly_siz = siz_total_cost / input_data["ПРОДОЛЖИТЕЛЬНОСТЬ_МЕС"]
            monthly_revenue = total_revenue / input_data["ПРОДОЛЖИТЕЛЬНОСТЬ_МЕС"]
            
            monthly_breakdown.append({
                'month': month,
                'revenue': monthly_revenue,
                'worker_fot': monthly_worker_fot,
                'engineer_fot': monthly_engineer_fot,
                'insurance': monthly_insurance,
                'tickets': monthly_tickets,
                'accommodation': monthly_accommodation,
                'meals': monthly_meals,
                'siz': monthly_siz,
                'total_expenses': (
                    monthly_worker_fot + monthly_engineer_fot + monthly_insurance +
                    monthly_tickets + monthly_accommodation + monthly_meals + monthly_siz
                )
            })
        else:
            monthly_breakdown.append({
                'month': month,
                'revenue': 0,
                'worker_fot': 0,
                'engineer_fot': 0,
                'insurance': 0,
                'tickets': 0,
                'accommodation': 0,
                'meals': 0,
                'siz': 0,
                'total_expenses': 0
            })
    
    # Calculate total expenses
    total_expenses = (
        worker_fot + engineer_fot + insurance_contributions +
        tickets_cost + accommodation_total_cost + meals_cost + siz_total_cost
    )
    
    # Calculate net profit
    net_profit = total_revenue - total_expenses
    
    # Calculate profit margin
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Currency formatting
    currency_symbol = {'RUB': '₽', 'USD': '$', 'EUR': '€'}.get(currency, '₽')
    
    return {
        'base_cost': base_cost,
        'workers_count': workers_count,
        'engineers_count': engineers_count,
        'worker_fot': worker_fot,
        'engineer_fot': engineer_fot,
        'total_fot': total_fot,
        'insurance_contributions': insurance_contributions,
        'tickets_cost': tickets_cost,
        'accommodation_cost': accommodation_total_cost,
        'meals_cost': meals_cost,
        'siz_cost': siz_total_cost,
        'total_expenses': total_expenses,
        'total_revenue': total_revenue,
        'net_profit': net_profit,
        'profit_margin': profit_margin,
        'total_cost': total_revenue,  # Total cost is the base cost/revenue in construction budgeting
        'currency_symbol': currency_symbol,
        'monthly_breakdown': monthly_breakdown,
        'input_data': input_data,
        'breakdown_percentages': {
            'base': 100.0,
            'worker_fot': (worker_fot / base_cost) * 100,
            'engineer_fot': (engineer_fot / base_cost) * 100,
            'insurance': (insurance_contributions / base_cost) * 100,
            'tickets': (tickets_cost / base_cost) * 100,
            'accommodation': (accommodation_total_cost / base_cost) * 100,
            'meals': (meals_cost / base_cost) * 100,
            'siz': (siz_total_cost / base_cost) * 100,
            'expenses': (total_expenses / base_cost) * 100,
            'profit': (net_profit / base_cost) * 100
        }
    }

def _create_budget_breakdown_table(budget_calculation: Dict[str, Any], currency: str) -> List[Dict[str, Any]]:
    """Create detailed budget breakdown table."""
    symbol = budget_calculation['currency_symbol']
    
    table_data = [
        {
            'item': 'Стоимость строительства',
            'amount': f"{budget_calculation['base_cost']:,.2f} {symbol}",
            'percentage': f"{budget_calculation['breakdown_percentages']['base']:.1f}%",
            'category': 'Выручка'
        },
        {
            'item': 'ФОТ рабочих',
            'amount': f"{budget_calculation['worker_fot']:,.2f} {symbol}",
            'percentage': f"{budget_calculation['breakdown_percentages']['worker_fot']:.1f}%",
            'category': 'Заработная плата'
        },
        {
            'item': 'ФОТ ИТР',
            'amount': f"{budget_calculation['engineer_fot']:,.2f} {symbol}",
            'percentage': f"{budget_calculation['breakdown_percentages']['engineer_fot']:.1f}%",
            'category': 'Заработная плата'
        },
        {
            'item': 'Страховые взносы',
            'amount': f"{budget_calculation['insurance_contributions']:,.2f} {symbol}",
            'percentage': f"{budget_calculation['breakdown_percentages']['insurance']:.1f}%",
            'category': 'Страхование'
        },
        {
            'item': 'Билеты',
            'amount': f"{budget_calculation['tickets_cost']:,.2f} {symbol}",
            'percentage': f"{budget_calculation['breakdown_percentages']['tickets']:.1f}%",
            'category': 'Командировки'
        },
        {
            'item': 'Проживание',
            'amount': f"{budget_calculation['accommodation_cost']:,.2f} {symbol}",
            'percentage': f"{budget_calculation['breakdown_percentages']['accommodation']:.1f}%",
            'category': 'Командировки'
        },
        {
            'item': 'Питание',
            'amount': f"{budget_calculation['meals_cost']:,.2f} {symbol}",
            'percentage': f"{budget_calculation['breakdown_percentages']['meals']:.1f}%",
            'category': 'Командировки'
        },
        {
            'item': 'СИЗ',
            'amount': f"{budget_calculation['siz_cost']:,.2f} {symbol}",
            'percentage': f"{budget_calculation['breakdown_percentages']['siz']:.1f}%",
            'category': 'Средства индивидуальной защиты'
        },
        {
            'item': 'ИТОГО РАСХОДЫ',
            'amount': f"{budget_calculation['total_expenses']:,.2f} {symbol}",
            'percentage': f"{budget_calculation['breakdown_percentages']['expenses']:.1f}%",
            'category': 'Общие расходы'
        },
        {
            'item': 'ЧИСТАЯ ПРИБЫЛЬ',
            'amount': f"{budget_calculation['net_profit']:,.2f} {symbol}",
            'percentage': f"{budget_calculation['breakdown_percentages']['profit']:.1f}%",
            'category': 'Прибыль'
        }
    ]
    
    return table_data

def _generate_budget_recommendations(budget_calculation: Dict[str, Any], 
                                   project_type: str, project_duration_months: int) -> List[str]:
    """Generate budget recommendations based on analysis."""
    recommendations = []
    
    total_cost = budget_calculation['total_cost']
    base_cost = budget_calculation['base_cost']
    profit_rate = budget_calculation['breakdown_percentages']['profit']
    expenses_rate = budget_calculation['breakdown_percentages']['expenses']
    
    # Expenses analysis
    if expenses_rate > 25:
        recommendations.append("⚠️ Высокие расходы (>25% от базовой стоимости). Рассмотрите оптимизацию управления.")
    elif expenses_rate < 15:
        recommendations.append("✅ Расходы в норме. Хорошая эффективность управления.")
    
    # Profit analysis
    if profit_rate > 20:
        recommendations.append("💰 Высокая норма прибыли. Проект может быть привлекательным для инвесторов.")
    elif profit_rate < 10:
        recommendations.append("⚠️ Низкая норма прибыли. Рассмотрите повышение эффективности.")
    elif profit_rate < 0:
        recommendations.append("❌ Отрицательная прибыль. Расходы превышают базовую стоимость.")
    
    # Project type specific recommendations
    if project_type == 'residential':
        recommendations.append("🏠 Для жилых проектов рекомендуется заложить резерв 10-15% на непредвиденные расходы.")
    elif project_type == 'commercial':
        recommendations.append("🏢 Коммерческие проекты требуют тщательного планирования сроков и бюджета.")
    elif project_type == 'industrial':
        recommendations.append("🏭 Промышленные объекты требуют дополнительного учета экологических требований.")
    
    # Duration analysis
    if project_duration_months > 24:
        recommendations.append("⏰ Длительные проекты требуют регулярного пересмотра бюджета с учетом инфляции.")
    
    # Cost analysis
    if total_cost > base_cost * 2:
        recommendations.append("📊 Общая стоимость значительно превышает базовую. Проверьте расчеты.")
    
    return recommendations