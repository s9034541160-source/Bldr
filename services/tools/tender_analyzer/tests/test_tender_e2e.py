"""
E2E тесты для полного пайплайна tender_analyzer
"""
import pytest
import os
import sys
import time
import tempfile
import zipfile
import json
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from services.tools.tender_analyzer.pipeline import TenderAnalyzerPipeline


class TestTenderAnalyzerE2E:
    """E2E тесты для полного пайплайна tender_analyzer"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.pipeline = TenderAnalyzerPipeline()
    
    def test_full_pipeline_e2e(self):
        """E2E тест полного пайплайна анализа тендера"""
        start_time = time.time()
        
        # Создаем тестовый PDF файл
        test_pdf_path = self._create_test_pdf()
        
        try:
            # Запускаем полный анализ
            zip_path = self.pipeline.analyze_tender(
                pdf_path=test_pdf_path,
                user_region="Москва",
                shift_pattern="30/15",
                north_coeff=1.2
            )
            
            # Проверяем что ZIP создан
            assert os.path.exists(zip_path), f"ZIP файл не найден: {zip_path}"
            
            # Проверяем содержимое ZIP
            self._verify_zip_contents(zip_path)
            
            # Проверяем время выполнения
            elapsed_time = time.time() - start_time
            assert elapsed_time <= 180, f"Время выполнения {elapsed_time:.1f}с превышает 180с"
            
            print(f"✅ E2E тест пройден за {elapsed_time:.1f} секунд")
            print(f"📁 ZIP файл: {zip_path}")
            
        finally:
            # Очищаем тестовые файлы
            if os.path.exists(test_pdf_path):
                os.unlink(test_pdf_path)
    
    def test_zip_contains_required_files(self):
        """Тест что ZIP содержит все необходимые файлы"""
        test_pdf_path = self._create_test_pdf()
        
        try:
            zip_path = self.pipeline.analyze_tender(
                pdf_path=test_pdf_path,
                user_region="Москва",
                shift_pattern="30/15",
                north_coeff=1.2
            )
            
            # Проверяем содержимое ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                file_list = zip_file.namelist()
                
                # Проверяем наличие всех необходимых файлов
                required_files = [
                    "tender_report.docx",
                    "estimate.xlsx", 
                    "gantt.xlsx",
                    "finance.json",
                    "README.txt"
                ]
                
                for required_file in required_files:
                    assert required_file in file_list, f"Файл {required_file} не найден в ZIP"
                
                print(f"✅ ZIP содержит все необходимые файлы: {len(file_list)} файлов")
                
        finally:
            if os.path.exists(test_pdf_path):
                os.unlink(test_pdf_path)
    
    def test_finance_json_margin_range(self):
        """Тест что finance.json содержит маржу в диапазоне 15-25%"""
        test_pdf_path = self._create_test_pdf()
        
        try:
            zip_path = self.pipeline.analyze_tender(
                pdf_path=test_pdf_path,
                user_region="Москва",
                shift_pattern="30/15",
                north_coeff=1.2
            )
            
            # Извлекаем и проверяем finance.json
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                finance_data = json.loads(zip_file.read("finance.json"))
                
                # Проверяем структуру finance.json
                assert "total_cost" in finance_data
                assert "margin_pct" in finance_data
                assert "cost_breakdown" in finance_data
                
                # Проверяем диапазон маржи
                margin_pct = finance_data["margin_pct"]
                assert 15.0 <= margin_pct <= 25.0, f"Маржа {margin_pct:.1f}% не в диапазоне 15-25%"
                
                print(f"✅ Маржа {margin_pct:.1f}% в диапазоне 15-25%")
                
                # Проверяем детализацию затрат
                breakdown = finance_data["cost_breakdown"]
                required_fields = [
                    "direct_costs", "payroll", "shift_bonus", 
                    "northern_coeff", "travel_costs", "siz_costs", "overhead"
                ]
                
                for field in required_fields:
                    assert field in breakdown, f"Поле {field} не найдено в cost_breakdown"
                
                print("✅ Структура finance.json корректна")
                
        finally:
            if os.path.exists(test_pdf_path):
                os.unlink(test_pdf_path)
    
    def test_different_regions(self):
        """Тест анализа для разных регионов"""
        regions = ["Москва", "СПб", "Мурманск", "Норильск"]
        
        for region in regions:
            test_pdf_path = self._create_test_pdf()
            
            try:
                zip_path = self.pipeline.analyze_tender(
                    pdf_path=test_pdf_path,
                    user_region=region,
                    shift_pattern="30/15",
                    north_coeff=1.2
                )
                
                # Проверяем что анализ прошел успешно
                assert os.path.exists(zip_path), f"ZIP не создан для региона {region}"
                
                # Проверяем finance.json
                with zipfile.ZipFile(zip_path, 'r') as zip_file:
                    finance_data = json.loads(zip_file.read("finance.json"))
                    assert finance_data["region"] == region
                    assert finance_data["margin_pct"] > 0
                
                print(f"✅ Регион {region}: маржа {finance_data['margin_pct']:.1f}%")
                
            finally:
                if os.path.exists(test_pdf_path):
                    os.unlink(test_pdf_path)
    
    def test_performance_benchmark(self):
        """Тест производительности - время выполнения должно быть ≤ 180 сек"""
        start_time = time.time()
        
        test_pdf_path = self._create_test_pdf()
        
        try:
            zip_path = self.pipeline.analyze_tender(
                pdf_path=test_pdf_path,
                user_region="Москва",
                shift_pattern="30/15",
                north_coeff=1.2
            )
            
            elapsed_time = time.time() - start_time
            
            # Проверяем время выполнения
            assert elapsed_time <= 180, f"Время выполнения {elapsed_time:.1f}с превышает 180с"
            
            print(f"✅ Производительность: {elapsed_time:.1f}с (лимит: 180с)")
            
            # Проверяем что все файлы созданы
            assert os.path.exists(zip_path)
            
        finally:
            if os.path.exists(test_pdf_path):
                os.unlink(test_pdf_path)
    
    def _create_test_pdf(self) -> str:
        """Создание тестового PDF файла"""
        test_content = """
        TENDER DOCUMENTATION
        
        1. GENERAL PROVISIONS
        This tender is conducted for construction work.
        
        2. WORK VOLUMES
        2.1 Concrete works - 100 m3
        2.2 Reinforcement works - 5 tons
        2.3 Formwork works - 200 m2
        
        3. EXECUTION TERMS
        Start of works: 01.01.2024
        End of works: 31.12.2024
        
        4. TECHNICAL REQUIREMENTS
        - Concrete quality not lower than B25
        - Reinforcement class A500C
        - Compliance with GOST 26633
        """
        
        # Создаем временный файл с UTF-8 кодировкой
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pdf', encoding='utf-8') as f:
            f.write(test_content)
            return f.name
    
    def _verify_zip_contents(self, zip_path: str):
        """Проверка содержимого ZIP файла"""
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            file_list = zip_file.namelist()
            
            # Проверяем количество файлов
            assert len(file_list) >= 4, f"Недостаточно файлов в ZIP: {len(file_list)}"
            
            # Проверяем размеры файлов
            for file_name in file_list:
                file_info = zip_file.getinfo(file_name)
                assert file_info.file_size > 0, f"Файл {file_name} пустой"
            
            print(f"✅ ZIP содержит {len(file_list)} файлов")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
