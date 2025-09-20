#!/usr/bin/env python3
"""
Internet Template Search Tool
Поиск шаблонов документов в интернете и их адаптация под проекты
"""

import os
import requests
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
import time
from datetime import datetime

class InternetTemplateSearcher:
    """Поиск и адаптация шаблонов документов из интернета"""
    
    def __init__(self):
        self.templates_dir = Path("I:/docs/templates")
        self.generated_dir = Path("I:/docs_generated/templates")
        self.cache_dir = Path("I:/docs/cache/templates")
        
        # Создаем директории
        for dir_path in [self.templates_dir, self.generated_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Поисковые движки и источники
        self.search_engines = {
            'google': 'https://www.google.com/search?q={}',
            'yandex': 'https://yandex.ru/search/?text={}',
            'bing': 'https://www.bing.com/search?q={}'
        }
        
        # Специализированные источники шаблонов
        self.template_sources = {
            'government': [
                'https://www.consultant.ru',
                'https://www.garant.ru',
                'https://www.gov.ru'
            ],
            'construction': [
                'https://www.minstroyrf.gov.ru',
                'https://www.nostroy.ru',
                'https://www.nopriz.ru'
            ],
            'business': [
                'https://www.nalog.gov.ru',
                'https://www.cbr.ru'
            ]
        }
        
        # Типы документов для поиска
        self.document_types = {
            'contracts': ['договор', 'контракт', 'соглашение'],
            'reports': ['отчет', 'справка', 'заключение'],
            'applications': ['заявление', 'заявка', 'ходатайство'],
            'letters': ['письмо', 'уведомление', 'извещение'],
            'acts': ['акт', 'протокол', 'заключение'],
            'estimates': ['смета', 'калькуляция', 'расчет']
        }

    def search_templates(self, query: str, doc_type: str = None, 
                        company_type: str = None, **kwargs) -> Dict[str, Any]:
        """
        Поиск шаблонов документов в интернете
        
        Args:
            query: Поисковый запрос
            doc_type: Тип документа (contracts, reports, etc.)
            company_type: Тип компании (construction, government, etc.)
            **kwargs: Дополнительные параметры
        """
        try:
            print(f"🔍 Поиск шаблонов: {query}")
            
            # Формируем расширенный поисковый запрос
            search_query = self._build_search_query(query, doc_type, company_type)
            
            # Поиск в разных источниках
            results = []
            
            # Поиск через поисковые системы
            for engine, url_template in self.search_engines.items():
                try:
                    engine_results = self._search_in_engine(engine, search_query, url_template)
                    results.extend(engine_results)
                except Exception as e:
                    print(f"⚠️ Ошибка поиска в {engine}: {e}")
            
            # Поиск в специализированных источниках
            if company_type and company_type in self.template_sources:
                for source in self.template_sources[company_type]:
                    try:
                        source_results = self._search_in_source(source, search_query)
                        results.extend(source_results)
                    except Exception as e:
                        print(f"⚠️ Ошибка поиска в {source}: {e}")
            
            # Фильтрация и ранжирование результатов
            filtered_results = self._filter_and_rank_results(results, query, doc_type)
            
            # Сохранение результатов в кэш
            self._cache_search_results(query, filtered_results)
            
            return {
                'status': 'success',
                'query': query,
                'total_found': len(filtered_results),
                'results': filtered_results[:20],  # Топ 20 результатов
                'search_time': time.time(),
                'metadata': {
                    'doc_type': doc_type,
                    'company_type': company_type,
                    'sources_searched': len(self.search_engines) + 
                                      (len(self.template_sources.get(company_type, [])) if company_type else 0)
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'query': query
            }

    def download_template(self, template_url: str, template_name: str, 
                         project_info: Dict = None, **kwargs) -> Dict[str, Any]:
        """
        Скачивание и адаптация шаблона под проект
        
        Args:
            template_url: URL шаблона
            template_name: Название шаблона
            project_info: Информация о проекте для адаптации
        """
        try:
            print(f"📥 Скачивание шаблона: {template_name}")
            
            # Скачивание файла
            response = requests.get(template_url, timeout=30)
            response.raise_for_status()
            
            # Определение типа файла
            content_type = response.headers.get('content-type', '')
            file_extension = self._get_file_extension(content_type, template_url)
            
            # Сохранение оригинального файла
            original_file = self.templates_dir / f"{template_name}_original{file_extension}"
            with open(original_file, 'wb') as f:
                f.write(response.content)
            
            # Адаптация под проект (если указана информация о проекте)
            adapted_file = None
            if project_info:
                adapted_file = self._adapt_template_to_project(
                    original_file, template_name, project_info
                )
            
            # Анализ содержимого шаблона
            analysis = self._analyze_template_content(original_file)
            
            return {
                'status': 'success',
                'original_file': str(original_file),
                'adapted_file': str(adapted_file) if adapted_file else None,
                'file_size': len(response.content),
                'content_type': content_type,
                'analysis': analysis,
                'download_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'template_url': template_url
            }

    def adapt_template_to_company(self, template_path: str, company_info: Dict, 
                                 **kwargs) -> Dict[str, Any]:
        """
        Адаптация шаблона под конкретную компанию
        
        Args:
            template_path: Путь к шаблону
            company_info: Информация о компании
        """
        try:
            template_file = Path(template_path)
            if not template_file.exists():
                raise FileNotFoundError(f"Шаблон не найден: {template_path}")
            
            print(f"🏢 Адаптация шаблона под компанию: {company_info.get('name', 'Unknown')}")
            
            # Чтение содержимого шаблона
            content = self._read_template_content(template_file)
            
            # Замена плейсхолдеров на данные компании
            adapted_content = self._replace_company_placeholders(content, company_info)
            
            # Сохранение адаптированного шаблона
            adapted_filename = f"{template_file.stem}_adapted_{company_info.get('name', 'company')}{template_file.suffix}"
            adapted_file = self.generated_dir / adapted_filename
            
            self._save_adapted_content(adapted_file, adapted_content, template_file.suffix)
            
            # Создание метаданных
            metadata = {
                'original_template': str(template_file),
                'company_info': company_info,
                'adaptation_date': datetime.now().isoformat(),
                'placeholders_replaced': self._count_replacements(content, adapted_content)
            }
            
            # Сохранение метаданных
            metadata_file = adapted_file.with_suffix('.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            return {
                'status': 'success',
                'adapted_file': str(adapted_file),
                'metadata_file': str(metadata_file),
                'replacements_made': metadata['placeholders_replaced'],
                'company_name': company_info.get('name')
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'template_path': template_path
            }

    def get_template_suggestions(self, project_type: str, work_type: str = None, 
                               **kwargs) -> Dict[str, Any]:
        """
        Получение предложений шаблонов для типа проекта
        
        Args:
            project_type: Тип проекта (строительство, ремонт, etc.)
            work_type: Тип работ (конкретизация)
        """
        try:
            suggestions = []
            
            # Базовые шаблоны для строительных проектов
            if 'строительство' in project_type.lower():
                suggestions.extend([
                    {
                        'name': 'Договор строительного подряда',
                        'type': 'contract',
                        'priority': 'high',
                        'description': 'Основной договор на выполнение строительных работ'
                    },
                    {
                        'name': 'Акт выполненных работ',
                        'type': 'act',
                        'priority': 'high',
                        'description': 'Документ подтверждения выполнения этапов работ'
                    },
                    {
                        'name': 'Смета на строительные работы',
                        'type': 'estimate',
                        'priority': 'high',
                        'description': 'Детальный расчет стоимости работ и материалов'
                    }
                ])
            
            # Дополнительные шаблоны в зависимости от типа работ
            if work_type:
                work_specific = self._get_work_specific_templates(work_type)
                suggestions.extend(work_specific)
            
            # Поиск дополнительных шаблонов в интернете
            search_query = f"{project_type} {work_type or ''} шаблон документ"
            online_suggestions = self.search_templates(search_query, doc_type='all')
            
            if online_suggestions['status'] == 'success':
                for result in online_suggestions['results'][:5]:
                    suggestions.append({
                        'name': result['title'],
                        'type': 'online',
                        'priority': 'medium',
                        'url': result['url'],
                        'description': result.get('description', '')
                    })
            
            return {
                'status': 'success',
                'project_type': project_type,
                'work_type': work_type,
                'suggestions': suggestions,
                'total_suggestions': len(suggestions)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'project_type': project_type
            }

    def _build_search_query(self, query: str, doc_type: str, company_type: str) -> str:
        """Построение расширенного поискового запроса"""
        search_terms = [query]
        
        if doc_type and doc_type in self.document_types:
            search_terms.extend(self.document_types[doc_type])
        
        search_terms.extend(['шаблон', 'образец', 'форма'])
        
        if company_type:
            if company_type == 'construction':
                search_terms.extend(['строительство', 'подряд'])
            elif company_type == 'government':
                search_terms.extend(['государственный', 'муниципальный'])
        
        return ' '.join(search_terms)

    def _search_in_engine(self, engine: str, query: str, url_template: str) -> List[Dict]:
        """Поиск в поисковой системе"""
        results = []
        
        try:
            # Формируем URL для поиска
            search_url = url_template.format(quote_plus(query))
            
            # Выполняем запрос
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Парсим результаты (упрощенная версия)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ищем ссылки на документы
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(ext in href.lower() for ext in ['.doc', '.docx', '.pdf', '.rtf']):
                    results.append({
                        'title': link.get_text(strip=True)[:100],
                        'url': href,
                        'source': engine,
                        'type': 'document'
                    })
                    
                    if len(results) >= 10:  # Ограничиваем количество результатов
                        break
        
        except Exception as e:
            print(f"Ошибка поиска в {engine}: {e}")
        
        return results

    def _search_in_source(self, source_url: str, query: str) -> List[Dict]:
        """Поиск в специализированном источнике"""
        # Упрощенная реализация - в реальности нужно адаптировать под каждый сайт
        return []

    def _filter_and_rank_results(self, results: List[Dict], query: str, doc_type: str) -> List[Dict]:
        """Фильтрация и ранжирование результатов"""
        # Удаляем дубликаты
        unique_results = []
        seen_urls = set()
        
        for result in results:
            if result['url'] not in seen_urls:
                unique_results.append(result)
                seen_urls.add(result['url'])
        
        # Ранжируем по релевантности
        for result in unique_results:
            score = 0
            title_lower = result['title'].lower()
            
            # Бонус за наличие ключевых слов в заголовке
            if query.lower() in title_lower:
                score += 10
            
            if doc_type and any(term in title_lower for term in self.document_types.get(doc_type, [])):
                score += 5
            
            if any(word in title_lower for word in ['шаблон', 'образец', 'форма']):
                score += 3
            
            result['relevance_score'] = score
        
        # Сортируем по релевантности
        return sorted(unique_results, key=lambda x: x['relevance_score'], reverse=True)

    def _cache_search_results(self, query: str, results: List[Dict]):
        """Сохранение результатов поиска в кэш"""
        cache_file = self.cache_dir / f"search_{hash(query)}.json"
        cache_data = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'results': results
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

    def _get_file_extension(self, content_type: str, url: str) -> str:
        """Определение расширения файла"""
        if 'pdf' in content_type:
            return '.pdf'
        elif 'word' in content_type or 'docx' in content_type:
            return '.docx'
        elif 'msword' in content_type or 'doc' in content_type:
            return '.doc'
        elif 'rtf' in content_type:
            return '.rtf'
        else:
            # Пытаемся определить по URL
            if url.endswith('.pdf'):
                return '.pdf'
            elif url.endswith('.docx'):
                return '.docx'
            elif url.endswith('.doc'):
                return '.doc'
            else:
                return '.txt'

    def _adapt_template_to_project(self, template_file: Path, template_name: str, 
                                  project_info: Dict) -> Path:
        """Адаптация шаблона под конкретный проект"""
        # Упрощенная реализация - в реальности нужно более сложная обработка
        adapted_filename = f"{template_name}_project_{project_info.get('name', 'unknown')}.docx"
        adapted_file = self.generated_dir / adapted_filename
        
        # Копируем файл (в реальности здесь должна быть обработка содержимого)
        import shutil
        shutil.copy2(template_file, adapted_file)
        
        return adapted_file

    def _analyze_template_content(self, template_file: Path) -> Dict:
        """Анализ содержимого шаблона"""
        return {
            'file_size': template_file.stat().st_size,
            'file_type': template_file.suffix,
            'has_placeholders': True,  # Упрощенная проверка
            'estimated_fields': 10,    # Упрощенная оценка
            'complexity': 'medium'
        }

    def _read_template_content(self, template_file: Path) -> str:
        """Чтение содержимого шаблона"""
        # Упрощенная реализация - нужно добавить поддержку разных форматов
        try:
            return template_file.read_text(encoding='utf-8')
        except:
            return template_file.read_text(encoding='cp1251')

    def _replace_company_placeholders(self, content: str, company_info: Dict) -> str:
        """Замена плейсхолдеров на данные компании"""
        replacements = {
            '{COMPANY_NAME}': company_info.get('name', ''),
            '{COMPANY_ADDRESS}': company_info.get('address', ''),
            '{COMPANY_PHONE}': company_info.get('phone', ''),
            '{COMPANY_EMAIL}': company_info.get('email', ''),
            '{COMPANY_INN}': company_info.get('inn', ''),
            '{COMPANY_KPP}': company_info.get('kpp', ''),
            '{DIRECTOR_NAME}': company_info.get('director', ''),
        }
        
        adapted_content = content
        for placeholder, value in replacements.items():
            adapted_content = adapted_content.replace(placeholder, value)
        
        return adapted_content

    def _save_adapted_content(self, adapted_file: Path, content: str, file_extension: str):
        """Сохранение адаптированного содержимого"""
        # Упрощенная реализация - нужно добавить поддержку разных форматов
        with open(adapted_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def _count_replacements(self, original: str, adapted: str) -> int:
        """Подсчет количества замен"""
        # Упрощенная реализация
        return len(re.findall(r'\{[A-Z_]+\}', original))

    def _get_work_specific_templates(self, work_type: str) -> List[Dict]:
        """Получение шаблонов для конкретного типа работ"""
        templates = []
        
        if 'фундамент' in work_type.lower():
            templates.extend([
                {
                    'name': 'Акт освидетельствования фундамента',
                    'type': 'act',
                    'priority': 'high',
                    'description': 'Документ приемки фундаментных работ'
                }
            ])
        
        if 'кровля' in work_type.lower():
            templates.extend([
                {
                    'name': 'Акт приемки кровельных работ',
                    'type': 'act', 
                    'priority': 'high',
                    'description': 'Документ приемки кровельных работ'
                }
            ])
        
        return templates


# Функция для интеграции с унифицированной системой инструментов
def search_internet_templates(query: str, doc_type: str = None, 
                            company_type: str = None, **kwargs) -> Dict[str, Any]:
    """
    Поиск шаблонов документов в интернете
    
    Args:
        query: Поисковый запрос
        doc_type: Тип документа
        company_type: Тип компании
        **kwargs: Дополнительные параметры
    """
    searcher = InternetTemplateSearcher()
    return searcher.search_templates(query, doc_type, company_type, **kwargs)


def download_and_adapt_template(template_url: str, template_name: str,
                              project_info: Dict = None, **kwargs) -> Dict[str, Any]:
    """
    Скачивание и адаптация шаблона
    
    Args:
        template_url: URL шаблона
        template_name: Название шаблона
        project_info: Информация о проекте
        **kwargs: Дополнительные параметры
    """
    searcher = InternetTemplateSearcher()
    return searcher.download_template(template_url, template_name, project_info, **kwargs)


def adapt_template_for_company(template_path: str, company_info: Dict, 
                             **kwargs) -> Dict[str, Any]:
    """
    Адаптация шаблона под компанию
    
    Args:
        template_path: Путь к шаблону
        company_info: Информация о компании
        **kwargs: Дополнительные параметры
    """
    searcher = InternetTemplateSearcher()
    return searcher.adapt_template_to_company(template_path, company_info, **kwargs)


def get_project_template_suggestions(project_type: str, work_type: str = None,
                                   **kwargs) -> Dict[str, Any]:
    """
    Получение предложений шаблонов для проекта
    
    Args:
        project_type: Тип проекта
        work_type: Тип работ
        **kwargs: Дополнительные параметры
    """
    searcher = InternetTemplateSearcher()
    return searcher.get_template_suggestions(project_type, work_type, **kwargs)


# Регистрация инструментов в унифицированной системе
UNIFIED_TOOLS = {
    'search_internet_templates': {
        'function': search_internet_templates,
        'description': 'Поиск шаблонов документов в интернете',
        'category': 'document_generation',
        'ui_placement': 'tools',
        'parameters': {
            'query': 'str - Поисковый запрос',
            'doc_type': 'str - Тип документа (contracts, reports, etc.)',
            'company_type': 'str - Тип компании (construction, government, etc.)'
        }
    },
    'download_and_adapt_template': {
        'function': download_and_adapt_template,
        'description': 'Скачивание и адаптация шаблона под проект',
        'category': 'document_generation',
        'ui_placement': 'tools',
        'parameters': {
            'template_url': 'str - URL шаблона',
            'template_name': 'str - Название шаблона',
            'project_info': 'dict - Информация о проекте'
        }
    },
    'adapt_template_for_company': {
        'function': adapt_template_for_company,
        'description': 'Адаптация шаблона под компанию',
        'category': 'document_generation',
        'ui_placement': 'tools',
        'parameters': {
            'template_path': 'str - Путь к шаблону',
            'company_info': 'dict - Информация о компании'
        }
    },
    'get_project_template_suggestions': {
        'function': get_project_template_suggestions,
        'description': 'Получение предложений шаблонов для проекта',
        'category': 'document_generation',
        'ui_placement': 'dashboard',
        'parameters': {
            'project_type': 'str - Тип проекта',
            'work_type': 'str - Тип работ'
        }
    }
}

if __name__ == "__main__":
    # Тестирование
    searcher = InternetTemplateSearcher()
    
    # Тест поиска шаблонов
    result = searcher.search_templates("договор строительного подряда", "contracts", "construction")
    print(json.dumps(result, ensure_ascii=False, indent=2))