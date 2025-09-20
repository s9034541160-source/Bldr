#!/usr/bin/env python3
"""
Enhanced Internet Template Search System
Расширенная система поиска шаблонов документов в интернете
"""

import os
import requests
import json
import re
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import quote_plus, urljoin, urlparse
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import mimetypes
import logging

logger = logging.getLogger(__name__)

class SearchEngineType(Enum):
    GOOGLE = "google"
    YANDEX = "yandex"
    BING = "bing"
    DUCKDUCKGO = "duckduckgo"

class DocumentType(Enum):
    CONTRACT = "contract"
    REPORT = "report"
    APPLICATION = "application"
    LETTER = "letter"
    ACT = "act"
    ESTIMATE = "estimate"
    FORM = "form"
    TEMPLATE = "template"

@dataclass
class SearchResult:
    title: str
    url: str
    source: str
    relevance_score: float
    document_type: Optional[str] = None
    file_size: Optional[int] = None
    format: Optional[str] = None
    preview: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    cached_path: Optional[str] = None
@
dataclass
class SearchQuery:
    query: str
    document_type: Optional[DocumentType] = None
    company_type: Optional[str] = None
    language: str = "ru"
    file_formats: List[str] = field(default_factory=lambda: ["pdf", "docx", "doc"])
    max_results: int = 50
    include_cached: bool = True

class EnhancedTemplateSearcher:
    """Расширенная система поиска шаблонов документов"""
    
    def __init__(self):
        self.templates_dir = Path("I:/docs/templates")
        self.generated_dir = Path("I:/docs_generated/templates")
        self.cache_dir = Path("I:/docs/cache/templates")
        
        # Создаем директории
        for dir_path in [self.templates_dir, self.generated_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Расширенные поисковые движки
        self.search_engines = {
            SearchEngineType.GOOGLE: {
                'url': 'https://www.google.com/search?q={}',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                'parser': self._parse_google_results
            },
            SearchEngineType.YANDEX: {
                'url': 'https://yandex.ru/search/?text={}',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                'parser': self._parse_yandex_results
            },
            SearchEngineType.BING: {
                'url': 'https://www.bing.com/search?q={}',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                'parser': self._parse_bing_results
            },
            SearchEngineType.DUCKDUCKGO: {
                'url': 'https://duckduckgo.com/html/?q={}',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                'parser': self._parse_duckduckgo_results
            }
        }
        
        # Специализированные источники
        self.specialized_sources = {
            'government': [
                {
                    'name': 'Consultant.ru',
                    'base_url': 'https://www.consultant.ru',
                    'search_url': 'https://www.consultant.ru/search/?q={}',
                    'parser': self._parse_consultant_results
                },
                {
                    'name': 'Garant.ru', 
                    'base_url': 'https://www.garant.ru',
                    'search_url': 'https://www.garant.ru/search/?q={}',
                    'parser': self._parse_garant_results
                },
                {
                    'name': 'Gov.ru',
                    'base_url': 'https://www.gov.ru',
                    'search_url': 'https://www.gov.ru/search?q={}',
                    'parser': self._parse_gov_results
                }
            ],
            'construction': [
                {
                    'name': 'MinstroyRF',
                    'base_url': 'https://www.minstroyrf.gov.ru',
                    'search_url': 'https://www.minstroyrf.gov.ru/search/?q={}',
                    'parser': self._parse_minstroy_results
                },
                {
                    'name': 'NOSTROY',
                    'base_url': 'https://www.nostroy.ru',
                    'search_url': 'https://www.nostroy.ru/search/?q={}',
                    'parser': self._parse_nostroy_results
                }
            ]
        }        

        # Типы документов с расширенными ключевыми словами
        self.document_keywords = {
            DocumentType.CONTRACT: {
                'ru': ['договор', 'контракт', 'соглашение', 'сделка', 'подряд'],
                'en': ['contract', 'agreement', 'deal', 'arrangement']
            },
            DocumentType.REPORT: {
                'ru': ['отчет', 'справка', 'заключение', 'доклад', 'сводка'],
                'en': ['report', 'summary', 'conclusion', 'statement']
            },
            DocumentType.APPLICATION: {
                'ru': ['заявление', 'заявка', 'ходатайство', 'прошение'],
                'en': ['application', 'request', 'petition', 'submission']
            },
            DocumentType.LETTER: {
                'ru': ['письмо', 'уведомление', 'извещение', 'сообщение'],
                'en': ['letter', 'notification', 'notice', 'message']
            },
            DocumentType.ACT: {
                'ru': ['акт', 'протокол', 'заключение', 'свидетельство'],
                'en': ['act', 'protocol', 'certificate', 'record']
            },
            DocumentType.ESTIMATE: {
                'ru': ['смета', 'калькуляция', 'расчет', 'оценка'],
                'en': ['estimate', 'calculation', 'assessment', 'evaluation']
            }
        }
        
        # Кэш результатов поиска
        self.search_cache = {}
        self.cache_ttl = timedelta(hours=24)  # Время жизни кэша
        
    async def search_templates_async(self, search_query: SearchQuery) -> List[SearchResult]:
        """Асинхронный поиск шаблонов"""
        logger.info(f"Starting async search for: {search_query.query}")
        
        # Проверяем кэш
        cache_key = self._get_cache_key(search_query)
        if search_query.include_cached and cache_key in self.search_cache:
            cached_result = self.search_cache[cache_key]
            if datetime.now() - cached_result['timestamp'] < self.cache_ttl:
                logger.info("Returning cached results")
                return cached_result['results']
        
        # Расширяем поисковый запрос
        expanded_query = self._expand_search_query(search_query)
        
        # Параллельный поиск во всех источниках
        tasks = []
        
        # Поиск в поисковых системах
        for engine_type in SearchEngineType:
            task = self._search_in_engine_async(engine_type, expanded_query, search_query)
            tasks.append(task)
        
        # Поиск в специализированных источниках
        if search_query.company_type and search_query.company_type in self.specialized_sources:
            for source in self.specialized_sources[search_query.company_type]:
                task = self._search_in_specialized_source_async(source, expanded_query, search_query)
                tasks.append(task)
        
        # Выполняем все задачи параллельно
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Объединяем результаты
        all_results = []
        for results in results_lists:
            if isinstance(results, list):
                all_results.extend(results)
            elif isinstance(results, Exception):
                logger.error(f"Search task failed: {results}")
        
        # Фильтруем и ранжируем результаты
        filtered_results = self._filter_and_rank_results(all_results, search_query)
        
        # Сохраняем в кэш
        self.search_cache[cache_key] = {
            'timestamp': datetime.now(),
            'results': filtered_results
        }
        
        logger.info(f"Search completed. Found {len(filtered_results)} results")
        return filtered_results[:search_query.max_results]
    
    def _expand_search_query(self, search_query: SearchQuery) -> str:
        """Расширение поискового запроса"""
        terms = [search_query.query]
        
        # Добавляем ключевые слова типа документа
        if search_query.document_type:
            doc_keywords = self.document_keywords.get(search_query.document_type, {})
            lang_keywords = doc_keywords.get(search_query.language, [])
            terms.extend(lang_keywords[:2])  # Берем первые 2 ключевых слова
        
        # Добавляем общие термины для поиска шаблонов
        template_terms = {
            'ru': ['шаблон', 'образец', 'форма', 'бланк'],
            'en': ['template', 'sample', 'form', 'blank']
        }
        terms.extend(template_terms.get(search_query.language, template_terms['ru'])[:2])
        
        # Добавляем термины типа компании
        if search_query.company_type:
            company_terms = {
                'construction': ['строительство', 'подряд', 'стройка'],
                'government': ['государственный', 'муниципальный', 'бюджетный'],
                'business': ['коммерческий', 'предпринимательский', 'бизнес']
            }
            if search_query.company_type in company_terms:
                terms.extend(company_terms[search_query.company_type][:1])
        
        # Добавляем форматы файлов
        format_terms = [f"filetype:{fmt}" for fmt in search_query.file_formats[:2]]
        terms.extend(format_terms)
        
        return ' '.join(terms)    
 
   async def _search_in_engine_async(self, engine_type: SearchEngineType, 
                                     query: str, search_query: SearchQuery) -> List[SearchResult]:
        """Асинхронный поиск в поисковой системе"""
        engine_config = self.search_engines[engine_type]
        search_url = engine_config['url'].format(quote_plus(query))
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    search_url, 
                    headers=engine_config['headers'],
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        return engine_config['parser'](html_content, engine_type.value)
                    else:
                        logger.warning(f"Search engine {engine_type.value} returned status {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error searching in {engine_type.value}: {e}")
            return []
    
    async def _search_in_specialized_source_async(self, source: Dict, 
                                                 query: str, search_query: SearchQuery) -> List[SearchResult]:
        """Асинхронный поиск в специализированном источнике"""
        search_url = source['search_url'].format(quote_plus(query))
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    search_url,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        return source['parser'](html_content, source['name'])
                    else:
                        logger.warning(f"Specialized source {source['name']} returned status {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error searching in {source['name']}: {e}")
            return []
    
    def _parse_google_results(self, html_content: str, source: str) -> List[SearchResult]:
        """Парсинг результатов Google"""
        results = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Ищем результаты поиска
        search_results = soup.find_all('div', class_='g')
        
        for result in search_results[:10]:  # Берем первые 10 результатов
            try:
                # Извлекаем заголовок и ссылку
                title_elem = result.find('h3')
                link_elem = result.find('a')
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    url = link_elem.get('href', '')
                    
                    # Проверяем, что это ссылка на документ
                    if self._is_document_url(url):
                        # Извлекаем описание
                        desc_elem = result.find('span', class_='st') or result.find('div', class_='s')
                        description = desc_elem.get_text(strip=True) if desc_elem else ""
                        
                        search_result = SearchResult(
                            title=title,
                            url=url,
                            source=source,
                            relevance_score=0.0,  # Будет вычислен позже
                            preview=description[:200] if description else None,
                            metadata={'search_engine': 'google'}
                        )
                        results.append(search_result)
                        
            except Exception as e:
                logger.error(f"Error parsing Google result: {e}")
                continue
        
        return results
    
    def _parse_yandex_results(self, html_content: str, source: str) -> List[SearchResult]:
        """Парсинг результатов Yandex"""
        results = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Ищем результаты поиска Yandex
        search_results = soup.find_all('li', class_='serp-item')
        
        for result in search_results[:10]:
            try:
                title_elem = result.find('h2') or result.find('a')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    
                    # Ищем ссылку
                    link_elem = result.find('a')
                    if link_elem:
                        url = link_elem.get('href', '')
                        
                        if self._is_document_url(url):
                            # Извлекаем описание
                            desc_elem = result.find('div', class_='text-container')
                            description = desc_elem.get_text(strip=True) if desc_elem else ""
                            
                            search_result = SearchResult(
                                title=title,
                                url=url,
                                source=source,
                                relevance_score=0.0,
                                preview=description[:200] if description else None,
                                metadata={'search_engine': 'yandex'}
                            )
                            results.append(search_result)
                            
            except Exception as e:
                logger.error(f"Error parsing Yandex result: {e}")
                continue
        
        return results   
 
    def _parse_bing_results(self, html_content: str, source: str) -> List[SearchResult]:
        """Парсинг результатов Bing"""
        results = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        search_results = soup.find_all('li', class_='b_algo')
        
        for result in search_results[:10]:
            try:
                title_elem = result.find('h2')
                
                if title_elem:
                    link_elem = title_elem.find('a')
                    if link_elem:
                        title = link_elem.get_text(strip=True)
                        url = link_elem.get('href', '')
                        
                        if self._is_document_url(url):
                            desc_elem = result.find('p')
                            description = desc_elem.get_text(strip=True) if desc_elem else ""
                            
                            search_result = SearchResult(
                                title=title,
                                url=url,
                                source=source,
                                relevance_score=0.0,
                                preview=description[:200] if description else None,
                                metadata={'search_engine': 'bing'}
                            )
                            results.append(search_result)
                            
            except Exception as e:
                logger.error(f"Error parsing Bing result: {e}")
                continue
        
        return results
    
    def _parse_duckduckgo_results(self, html_content: str, source: str) -> List[SearchResult]:
        """Парсинг результатов DuckDuckGo"""
        results = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        search_results = soup.find_all('div', class_='result')
        
        for result in search_results[:10]:
            try:
                title_elem = result.find('a', class_='result__a')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    
                    if self._is_document_url(url):
                        desc_elem = result.find('a', class_='result__snippet')
                        description = desc_elem.get_text(strip=True) if desc_elem else ""
                        
                        search_result = SearchResult(
                            title=title,
                            url=url,
                            source=source,
                            relevance_score=0.0,
                            preview=description[:200] if description else None,
                            metadata={'search_engine': 'duckduckgo'}
                        )
                        results.append(search_result)
                        
            except Exception as e:
                logger.error(f"Error parsing DuckDuckGo result: {e}")
                continue
        
        return results
    
    def _parse_consultant_results(self, html_content: str, source: str) -> List[SearchResult]:
        """Парсинг результатов Consultant.ru"""
        results = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Специфичная логика для Consultant.ru
        search_results = soup.find_all('div', class_='search-result')
        
        for result in search_results[:5]:
            try:
                title_elem = result.find('a')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    url = urljoin('https://www.consultant.ru', title_elem.get('href', ''))
                    
                    desc_elem = result.find('div', class_='description')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""
                    
                    search_result = SearchResult(
                        title=title,
                        url=url,
                        source=source,
                        relevance_score=0.8,  # Высокий рейтинг для специализированных источников
                        preview=description[:200] if description else None,
                        metadata={'source_type': 'legal', 'authority': 'high'}
                    )
                    results.append(search_result)
                    
            except Exception as e:
                logger.error(f"Error parsing Consultant result: {e}")
                continue
        
        return results    
    d
ef _parse_garant_results(self, html_content: str, source: str) -> List[SearchResult]:
        """Парсинг результатов Garant.ru"""
        results = []
        # Упрощенная реализация - в реальности нужна адаптация под конкретный сайт
        return results
    
    def _parse_gov_results(self, html_content: str, source: str) -> List[SearchResult]:
        """Парсинг результатов Gov.ru"""
        results = []
        # Упрощенная реализация - в реальности нужна адаптация под конкретный сайт
        return results
    
    def _parse_minstroy_results(self, html_content: str, source: str) -> List[SearchResult]:
        """Парсинг результатов MinstroyRF"""
        results = []
        # Упрощенная реализация - в реальности нужна адаптация под конкретный сайт
        return results
    
    def _parse_nostroy_results(self, html_content: str, source: str) -> List[SearchResult]:
        """Парсинг результатов NOSTROY"""
        results = []
        # Упрощенная реализация - в реальности нужна адаптация под конкретный сайт
        return results
    
    def _is_document_url(self, url: str) -> bool:
        """Проверка, является ли URL ссылкой на документ"""
        if not url:
            return False
            
        # Проверяем расширения файлов
        document_extensions = ['.pdf', '.doc', '.docx', '.rtf', '.odt', '.xls', '.xlsx']
        url_lower = url.lower()
        
        for ext in document_extensions:
            if ext in url_lower:
                return True
        
        # Проверяем ключевые слова в URL
        document_keywords = ['download', 'file', 'document', 'template', 'form', 'blank']
        for keyword in document_keywords:
            if keyword in url_lower:
                return True
        
        return False
    
    def _filter_and_rank_results(self, results: List[SearchResult], 
                                search_query: SearchQuery) -> List[SearchResult]:
        """Фильтрация и ранжирование результатов"""
        if not results:
            return []
        
        # Удаляем дубликаты по URL
        unique_results = {}
        for result in results:
            if result.url not in unique_results:
                unique_results[result.url] = result
        
        filtered_results = list(unique_results.values())
        
        # Вычисляем релевантность для каждого результата
        for result in filtered_results:
            result.relevance_score = self._calculate_relevance_score(result, search_query)
        
        # Сортируем по релевантности
        filtered_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return filtered_results
    
    def _calculate_relevance_score(self, result: SearchResult, search_query: SearchQuery) -> float:
        """Вычисление релевантности результата"""
        score = 0.0
        
        title_lower = result.title.lower()
        query_lower = search_query.query.lower()
        
        # Базовая релевантность по заголовку
        if query_lower in title_lower:
            score += 10.0
        
        # Бонус за ключевые слова типа документа
        if search_query.document_type:
            doc_keywords = self.document_keywords.get(search_query.document_type, {})
            lang_keywords = doc_keywords.get(search_query.language, [])
            
            for keyword in lang_keywords:
                if keyword in title_lower:
                    score += 5.0
        
        # Бонус за слова "шаблон", "образец", "форма"
        template_words = ['шаблон', 'образец', 'форма', 'бланк', 'template', 'sample', 'form']
        for word in template_words:
            if word in title_lower:
                score += 3.0
        
        # Бонус за источник
        source_bonuses = {
            'consultant': 8.0,
            'garant': 8.0,
            'gov': 7.0,
            'minstroy': 6.0,
            'nostroy': 6.0,
            'google': 2.0,
            'yandex': 2.0,
            'bing': 1.5,
            'duckduckgo': 1.0
        }
        
        for source_key, bonus in source_bonuses.items():
            if source_key in result.source.lower():
                score += bonus
                break
        
        # Штраф за подозрительные URL
        suspicious_patterns = ['spam', 'ads', 'advertisement', 'click']
        for pattern in suspicious_patterns:
            if pattern in result.url.lower():
                score -= 5.0
        
        # Бонус за HTTPS
        if result.url.startswith('https://'):
            score += 1.0
        
        return max(0.0, score)  # Не даем отрицательный score
    
    def _get_cache_key(self, search_query: SearchQuery) -> str:
        """Генерация ключа кэша для поискового запроса"""
        key_data = {
            'query': search_query.query,
            'document_type': search_query.document_type.value if search_query.document_type else None,
            'company_type': search_query.company_type,
            'language': search_query.language,
            'file_formats': sorted(search_query.file_formats)
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()# Фу
нкции для интеграции с унифицированной системой инструментов
async def enhanced_search_internet_templates(query: str, doc_type: str = None, 
                                           company_type: str = None, language: str = "ru",
                                           max_results: int = 20, **kwargs) -> Dict[str, Any]:
    """
    Расширенный поиск шаблонов документов в интернете
    
    Args:
        query: Поисковый запрос
        doc_type: Тип документа
        company_type: Тип компании
        language: Язык поиска
        max_results: Максимальное количество результатов
        **kwargs: Дополнительные параметры
    """
    try:
        searcher = EnhancedTemplateSearcher()
        
        # Преобразуем строковый тип документа в enum
        document_type = None
        if doc_type:
            try:
                document_type = DocumentType(doc_type.lower())
            except ValueError:
                logger.warning(f"Unknown document type: {doc_type}")
        
        search_query = SearchQuery(
            query=query,
            document_type=document_type,
            company_type=company_type,
            language=language,
            max_results=max_results
        )
        
        # Выполняем асинхронный поиск
        results = await searcher.search_templates_async(search_query)
        
        # Преобразуем результаты в словари для JSON сериализации
        serialized_results = []
        for result in results:
            serialized_results.append({
                'title': result.title,
                'url': result.url,
                'source': result.source,
                'relevance_score': result.relevance_score,
                'document_type': result.document_type,
                'file_size': result.file_size,
                'format': result.format,
                'preview': result.preview,
                'metadata': result.metadata
            })
        
        return {
            'status': 'success',
            'query': query,
            'total_found': len(serialized_results),
            'results': serialized_results,
            'search_time': datetime.now().isoformat(),
            'metadata': {
                'doc_type': doc_type,
                'company_type': company_type,
                'language': language,
                'sources_searched': len(SearchEngineType) + 
                                  (len(searcher.specialized_sources.get(company_type, [])) if company_type else 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in enhanced template search: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'query': query
        }

def sync_search_internet_templates(query: str, doc_type: str = None, 
                                 company_type: str = None, **kwargs) -> Dict[str, Any]:
    """
    Синхронная обертка для асинхронного поиска шаблонов
    """
    try:
        # Создаем новый event loop если его нет
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Выполняем асинхронную функцию
        return loop.run_until_complete(
            enhanced_search_internet_templates(query, doc_type, company_type, **kwargs)
        )
        
    except Exception as e:
        logger.error(f"Error in sync template search: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'query': query
        }

# Регистрация в унифицированной системе инструментов
ENHANCED_UNIFIED_TOOLS = {
    'enhanced_search_internet_templates': {
        'function': sync_search_internet_templates,
        'description': 'Расширенный поиск шаблонов документов в интернете с поддержкой множественных источников',
        'category': 'document_generation',
        'ui_placement': 'tools',
        'parameters': {
            'query': 'str - Поисковый запрос',
            'doc_type': 'str - Тип документа (contract, report, application, letter, act, estimate)',
            'company_type': 'str - Тип компании (construction, government, business)',
            'language': 'str - Язык поиска (ru, en)',
            'max_results': 'int - Максимальное количество результатов (по умолчанию 20)'
        }
    }
}

if __name__ == "__main__":
    # Тестирование расширенной системы поиска
    import asyncio
    
    async def test_search():
        searcher = EnhancedTemplateSearcher()
        
        search_query = SearchQuery(
            query="договор строительного подряда",
            document_type=DocumentType.CONTRACT,
            company_type="construction",
            language="ru",
            max_results=10
        )
        
        print(f"Searching for: {search_query.query}")
        results = await searcher.search_templates_async(search_query)
        
        print(f"\nFound {len(results)} results:")
        for i, result in enumerate(results[:5], 1):
            print(f"{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Source: {result.source}")
            print(f"   Score: {result.relevance_score:.2f}")
            if result.preview:
                print(f"   Preview: {result.preview[:100]}...")
            print()
    
    # Запускаем тест
    asyncio.run(test_search())