"""
Тесты для рекурсивного ГОСТ-чанкинга в RAG системе
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from enterprise_rag_trainer_full import EnterpriseRAGTrainer


class TestRecursiveGOSTChunking:
    """Тесты для рекурсивного ГОСТ-чанкинга"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.trainer = EnterpriseRAGTrainer()
    
    def test_recursive_gost_chunking_basic(self):
        """Тест базового рекурсивного ГОСТ-чанкинга"""
        # Тестовый контент с ГОСТ-структурой
        test_content = """
6. Общие требования
6.1 Требования к материалам
6.1.1 Бетон должен соответствовать ГОСТ 26633
6.1.2 Арматура должна соответствовать ГОСТ 10884
6.2 Требования к конструкции
6.2.1 Несущие конструкции должны быть рассчитаны на нагрузки
6.2.2 Фундаменты должны обеспечивать устойчивость
6.2.3 Соединения должны быть надежными
7. Контроль качества
7.1 Приемочный контроль
7.1.1 Контроль должен проводиться в соответствии с требованиями
        """.strip()
        
        metadata = {
            "title": "Тестовый ГОСТ",
            "doc_type": "gost",
            "file_path": "test_gost.pdf"
        }
        
        # Вызываем рекурсивный чанкинг
        chunks = self.trainer._recursive_gost_chunking(test_content, metadata)
        
        # Проверяем, что созданы чанки
        assert len(chunks) > 0, "Должны быть созданы чанки"
        
        # Проверяем, что есть чанки с path длиной >= 2
        chunks_with_path = [chunk for chunk in chunks if len(chunk.metadata.get("path", [])) >= 2]
        assert len(chunks_with_path) > 0, "Должен быть хотя бы один чанк с path длиной >= 2"
        
        # Проверяем структуру метаданных
        for chunk in chunks:
            assert "path" in chunk.metadata, "В метаданных должен быть path"
            assert "title" in chunk.metadata, "В метаданных должен быть title"
            assert "hierarchy_level" in chunk.metadata, "В метаданных должен быть hierarchy_level"
            assert isinstance(chunk.metadata["path"], list), "Path должен быть списком"
            assert chunk.metadata["hierarchy_level"] in [1, 2, 3], "hierarchy_level должен быть 1, 2 или 3"
    
    def test_recursive_gost_chunking_levels(self):
        """Тест чанкинга разных уровней иерархии"""
        test_content = """
1. Общие положения
1.1 Назначение документа
1.1.1 Документ устанавливает требования
1.1.2 Документ применяется для строительства
1.2 Область применения
2. Термины и определения
2.1 Основные термины
2.1.1 Строительство - процесс возведения зданий
2.1.2 Конструкция - несущий элемент здания
        """.strip()
        
        metadata = {"title": "Тестовый СП", "doc_type": "sp"}
        
        chunks = self.trainer._recursive_gost_chunking(test_content, metadata)
        
        # Проверяем наличие чанков разных уровней
        level1_chunks = [chunk for chunk in chunks if chunk.metadata["hierarchy_level"] == 1]
        level2_chunks = [chunk for chunk in chunks if chunk.metadata["hierarchy_level"] == 2]
        level3_chunks = [chunk for chunk in chunks if chunk.metadata["hierarchy_level"] == 3]
        
        assert len(level1_chunks) > 0, "Должны быть чанки 1 уровня"
        assert len(level2_chunks) > 0, "Должны быть чанки 2 уровня"
        assert len(level3_chunks) > 0, "Должны быть чанки 3 уровня"
        
        # Проверяем правильность path для разных уровней
        for chunk in level1_chunks:
            assert len(chunk.metadata["path"]) == 1, "Чанки 1 уровня должны иметь path длиной 1"
        
        for chunk in level2_chunks:
            assert len(chunk.metadata["path"]) == 2, "Чанки 2 уровня должны иметь path длиной 2"
        
        for chunk in level3_chunks:
            assert len(chunk.metadata["path"]) == 3, "Чанки 3 уровня должны иметь path длиной 3"
    
    def test_recursive_gost_chunking_fallback(self):
        """Тест fallback чанкинга когда нет ГОСТ-структуры"""
        test_content = """
Это обычный текст без ГОСТ-структуры.
Он должен быть разбит на fallback чанки.
Каждый абзац может стать отдельным чанком.
        """.strip()
        
        metadata = {"title": "Обычный документ", "doc_type": "other"}
        
        chunks = self.trainer._recursive_gost_chunking(test_content, metadata)
        
        # Если нет ГОСТ-структуры, должен вернуться пустой список
        # (fallback обрабатывается в _create_ntd_chunks)
        assert isinstance(chunks, list), "Должен возвращаться список"
    
    def test_create_ntd_chunks_integration(self):
        """Тест интеграции рекурсивного чанкинга в _create_ntd_chunks"""
        test_content = """
6. Требования к строительству
6.1 Материалы
6.1.1 Бетон должен быть класса В25
6.1.2 Арматура класса А500С
6.2 Конструкции
6.2.1 Несущие стены толщиной не менее 200мм
6.2.2 Перекрытия из железобетона
        """.strip()
        
        structural_data = {"sections": [], "paragraphs": []}
        metadata = {
            "title": "СП 20.13330.2016",
            "doc_type": "sp",
            "file_path": "test_sp.pdf"
        }
        doc_type_info = {"doc_type": "sp"}
        
        # Вызываем _create_ntd_chunks
        chunks = self.trainer._create_ntd_chunks(test_content, structural_data, metadata, doc_type_info)
        
        # Проверяем, что созданы чанки
        assert len(chunks) > 0, "Должны быть созданы чанки"
        
        # Проверяем наличие title чанка
        title_chunks = [chunk for chunk in chunks if chunk.chunk_type == "title"]
        assert len(title_chunks) > 0, "Должен быть чанк заголовка"
        
        # Проверяем наличие ГОСТ чанков
        gost_chunks = [chunk for chunk in chunks if chunk.chunk_type == "gost_section"]
        assert len(gost_chunks) > 0, "Должны быть ГОСТ чанки"
        
        # Проверяем, что есть чанки с path длиной >= 2
        chunks_with_path = [chunk for chunk in chunks if len(chunk.metadata.get("path", [])) >= 2]
        assert len(chunks_with_path) > 0, "Должен быть хотя бы один чанк с path длиной >= 2"
    
    def test_path_structure_correctness(self):
        """Тест правильности структуры path в метаданных"""
        test_content = """
1. Общие положения
1.1 Назначение
1.1.1 Цель документа
1.1.2 Область применения
1.2 Нормативные ссылки
2. Термины
2.1 Определения
2.1.1 Строительство
2.1.2 Конструкция
        """.strip()
        
        metadata = {"title": "Тест структуры", "doc_type": "gost"}
        
        chunks = self.trainer._recursive_gost_chunking(test_content, metadata)
        
        # Проверяем правильность path для каждого уровня
        for chunk in chunks:
            path = chunk.metadata["path"]
            hierarchy_level = chunk.metadata["hierarchy_level"]
            
            if hierarchy_level == 1:
                assert len(path) == 1, f"Уровень 1 должен иметь path длиной 1, получен: {path}"
                assert path[0].isdigit(), f"Первый элемент path должен быть числом: {path}"
            
            elif hierarchy_level == 2:
                assert len(path) == 2, f"Уровень 2 должен иметь path длиной 2, получен: {path}"
                assert path[0].isdigit(), f"Первый элемент path должен быть числом: {path}"
                assert "." in path[1], f"Второй элемент path должен содержать точку: {path}"
            
            elif hierarchy_level == 3:
                assert len(path) == 3, f"Уровень 3 должен иметь path длиной 3, получен: {path}"
                assert path[0].isdigit(), f"Первый элемент path должен быть числом: {path}"
                assert "." in path[1], f"Второй элемент path должен содержать точку: {path}"
                assert path[1].count(".") == 1, f"Второй элемент должен содержать одну точку: {path}"
                assert path[2].count(".") == 2, f"Третий элемент должен содержать две точки: {path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])