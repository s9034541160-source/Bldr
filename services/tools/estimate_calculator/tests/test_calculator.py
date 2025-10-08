"""
Тесты для сметного калькулятора
"""
import pytest
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from services.tools.estimate_calculator.models import EstimateRequest, VolumeItem
from services.tools.estimate_calculator.calculator import EstimateCalculator


class TestEstimateCalculator:
    """Тесты для сметного калькулятора"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.calculator = EstimateCalculator()
    
    def test_calculator_initialization(self):
        """Тест инициализации калькулятора"""
        assert self.calculator is not None
        assert len(self.calculator.gesn_prices) > 0
        assert len(self.calculator.region_coeffs) > 0
        assert len(self.calculator.siz_norms) > 0
    
    def test_basic_estimate_calculation(self):
        """Тест базового расчета сметы"""
        # Тестовые данные: 10 м³ бетона
        request = EstimateRequest(
            volumes=[
                VolumeItem(
                    code="01-01-001-01",
                    name="Бетон тяжелый",
                    unit="м³",
                    qty=10.0
                )
            ],
            region="Москва",
            shift_pattern="30/15",
            north_coeff=1.0,
            travel_days=0
        )
        
        result = self.calculator.calculate_estimate(request)
        
        # Проверяем основные результаты
        assert result is not None
        assert result.total_cost > 0
        assert result.margin_pct > 0
        assert result.file_path is not None
        assert result.cost_breakdown is not None
        
        # Проверяем детализацию затрат
        breakdown = result.cost_breakdown
        assert breakdown.direct_costs > 0
        assert breakdown.payroll > 0
        assert breakdown.total_cost > 0
        
        print(f"Общая стоимость: {result.total_cost:,.2f} ₽")
        print(f"Маржа: {result.margin_pct:.1f}%")
    
    def test_margin_calculation_range(self):
        """Тест что маржа находится в диапазоне 15-25%"""
        request = EstimateRequest(
            volumes=[
                VolumeItem(
                    code="01-01-001-01",
                    name="Бетон тяжелый",
                    unit="м³",
                    qty=10.0
                )
            ],
            region="Москва",
            shift_pattern="30/15",
            north_coeff=1.0,
            travel_days=0
        )
        
        result = self.calculator.calculate_estimate(request)
        
        # Проверяем что маржа в диапазоне 15-25%
        assert 15.0 <= result.margin_pct <= 25.0, f"Маржа {result.margin_pct:.1f}% не в диапазоне 15-25%"
        
        print(f"✅ Маржа {result.margin_pct:.1f}% в диапазоне 15-25%")
    
    def test_multiple_volumes_calculation(self):
        """Тест расчета с несколькими видами работ"""
        request = EstimateRequest(
            volumes=[
                VolumeItem(
                    code="01-01-001-01",
                    name="Бетон тяжелый",
                    unit="м³",
                    qty=10.0
                ),
                VolumeItem(
                    code="01-01-002-01",
                    name="Арматура",
                    unit="т",
                    qty=2.0
                ),
                VolumeItem(
                    code="01-01-003-01",
                    name="Опалубка",
                    unit="м²",
                    qty=50.0
                )
            ],
            region="Москва",
            shift_pattern="30/15",
            north_coeff=1.0,
            travel_days=5
        )
        
        result = self.calculator.calculate_estimate(request)
        
        # Проверяем результаты
        assert result.total_cost > 0
        assert result.margin_pct > 0
        assert result.cost_breakdown.travel_costs > 0  # Должны быть командировочные
        
        print(f"Множественные работы - Общая стоимость: {result.total_cost:,.2f} ₽")
        print(f"Множественные работы - Маржа: {result.margin_pct:.1f}%")
    
    def test_northern_coefficient_calculation(self):
        """Тест расчета северного коэффициента"""
        # Тест с северным коэффициентом
        request = EstimateRequest(
            volumes=[
                VolumeItem(
                    code="01-01-001-01",
                    name="Бетон тяжелый",
                    unit="м³",
                    qty=10.0
                )
            ],
            region="Мурманск",
            shift_pattern="30/15",
            north_coeff=1.4,
            travel_days=0
        )
        
        result = self.calculator.calculate_estimate(request)
        
        # Проверяем что северный коэффициент учтен
        assert result.cost_breakdown.northern_coeff > 0
        assert result.total_cost > 0
        
        print(f"Северный коэффициент - Общая стоимость: {result.total_cost:,.2f} ₽")
        print(f"Северный коэффициент - Маржа: {result.margin_pct:.1f}%")
    
    def test_shift_bonus_calculation(self):
        """Тест расчета вахтовой надбавки"""
        request = EstimateRequest(
            volumes=[
                VolumeItem(
                    code="01-01-001-01",
                    name="Бетон тяжелый",
                    unit="м³",
                    qty=10.0
                )
            ],
            region="Москва",
            shift_pattern="30/15",  # 30 дней работы
            north_coeff=1.0,
            travel_days=0
        )
        
        result = self.calculator.calculate_estimate(request)
        
        # Проверяем что вахтовая надбавка рассчитана
        assert result.cost_breakdown.shift_bonus > 0
        assert result.cost_breakdown.payroll > 0
        
        # Вахтовая надбавка должна быть 20% от зарплаты за 30 дней
        expected_bonus = result.cost_breakdown.payroll * (30/30) * 0.2
        assert abs(result.cost_breakdown.shift_bonus - expected_bonus) < 0.01
        
        print(f"Вахтовая надбавка: {result.cost_breakdown.shift_bonus:,.2f} ₽")
    
    def test_excel_file_creation(self):
        """Тест создания Excel файла"""
        request = EstimateRequest(
            volumes=[
                VolumeItem(
                    code="01-01-001-01",
                    name="Бетон тяжелый",
                    unit="м³",
                    qty=10.0
                )
            ],
            region="Москва",
            shift_pattern="30/15",
            north_coeff=1.0,
            travel_days=0
        )
        
        result = self.calculator.calculate_estimate(request)
        
        # Проверяем что файл создан
        assert result.file_path is not None
        assert result.file_path.endswith('.xlsx')
        
        # Проверяем что файл существует (если путь абсолютный)
        if os.path.isabs(result.file_path):
            assert os.path.exists(result.file_path), f"Файл {result.file_path} не найден"
        
        print(f"Excel файл создан: {result.file_path}")
    
    def test_cost_breakdown_structure(self):
        """Тест структуры детализации затрат"""
        request = EstimateRequest(
            volumes=[
                VolumeItem(
                    code="01-01-001-01",
                    name="Бетон тяжелый",
                    unit="м³",
                    qty=10.0
                )
            ],
            region="Москва",
            shift_pattern="30/15",
            north_coeff=1.0,
            travel_days=3
        )
        
        result = self.calculator.calculate_estimate(request)
        breakdown = result.cost_breakdown
        
        # Проверяем все поля детализации
        assert breakdown.direct_costs > 0
        assert breakdown.payroll > 0
        assert breakdown.shift_bonus >= 0
        assert breakdown.northern_coeff >= 0
        assert breakdown.travel_costs > 0  # Должны быть командировочные
        assert breakdown.siz_costs >= 0
        assert breakdown.overhead > 0
        assert breakdown.total_cost > 0
        
        # Проверяем что общая стоимость равна сумме всех затрат
        # Прямые затраты уже включают зарплату, поэтому не добавляем её отдельно
        calculated_total = (breakdown.direct_costs + breakdown.shift_bonus + 
                          breakdown.northern_coeff + breakdown.travel_costs + 
                          breakdown.siz_costs + breakdown.overhead)
        
        assert abs(breakdown.total_cost - calculated_total) < 0.01
        
        print("✅ Структура детализации затрат корректна")
    
    def test_contract_price_margin_calculation(self):
        """Тест расчета маржи с заданной договорной ценой"""
        request = EstimateRequest(
            volumes=[
                VolumeItem(
                    code="01-01-001-01",
                    name="Бетон тяжелый",
                    unit="м³",
                    qty=10.0
                )
            ],
            region="Москва",
            shift_pattern="30/15",
            north_coeff=1.0,
            travel_days=0,
            contract_price=100000.0  # Заданная договорная цена
        )
        
        result = self.calculator.calculate_estimate(request)
        
        # Проверяем что маржа рассчитана корректно
        expected_margin = ((request.contract_price - result.total_cost) / request.contract_price) * 100
        assert abs(result.margin_pct - expected_margin) < 0.01
        
        print(f"Маржа с договорной ценой: {result.margin_pct:.1f}%")
    
    def test_region_coefficients(self):
        """Тест районных коэффициентов"""
        regions = ["Москва", "СПб", "Мурманск", "Норильск"]
        
        for region in regions:
            request = EstimateRequest(
                volumes=[
                    VolumeItem(
                        code="01-01-001-01",
                        name="Бетон тяжелый",
                        unit="м³",
                        qty=10.0
                    )
                ],
                region=region,
                shift_pattern="30/15",
                north_coeff=1.0,
                travel_days=0
            )
            
            result = self.calculator.calculate_estimate(request)
            
            # Проверяем что расчет прошел успешно
            assert result.total_cost > 0
            assert result.margin_pct > 0
            
            print(f"{region}: {result.total_cost:,.2f} ₽, маржа {result.margin_pct:.1f}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
