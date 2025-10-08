#!/usr/bin/env python3
"""
Улучшенный менеджер реестра НТД с обходом защиты и актуальными источниками
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
import sqlite3
import json
import re
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedNTDRegistryManager:
    """Улучшенный менеджер реестра НТД с обходом защиты"""
    
    def __init__(self, db_path: str = "test_registry/ntd_registry_test.db"):
        self.db_path = db_path
        
        # Обновленные источники с актуальными URL
        self.sources = {
            # Официальные источники
            "minstroyrf.ru": {
                "category": "construction",
                "url_pattern": "https://www.minstroyrf.ru/activities/technical-regulation/",
                "selector": "a[href*='.pdf'], a[href*='document'], .document-link",
                "rate_limit": 2,
                "priority": 1
            },
            "gost.ru": {
                "category": "standards", 
                "url_pattern": "https://www.gost.ru/portal/gost/",
                "selector": "a[href*='gost'], .gost-link, .standard-link",
                "rate_limit": 2,
                "priority": 1
            },
            "consultant.ru": {
                "category": "laws",
                "url_pattern": "https://www.consultant.ru/law/",
                "selector": "a[href*='document'], .law-link",
                "rate_limit": 3,
                "priority": 2
            },
            # Альтернативные источники
            "stroyinf.ru": {
                "category": "construction",
                "url_pattern": "https://files.stroyinf.ru/Index2/1/4293880/4293880.htm",
                "selector": "a[href$='.pdf'], a[href$='.htm']",
                "rate_limit": 2,
                "priority": 3
            },
            "rosstat.gov.ru": {
                "category": "statistics",
                "url_pattern": "https://rosstat.gov.ru/statistics/",
                "selector": "a[href$='.xlsx'], a[href$='.xls']",
                "rate_limit": 2,
                "priority": 3
            }
        }
        
        # User-Agent для обхода защиты
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
    def _get_random_headers(self) -> Dict[str, str]:
        """Генерируем случайные заголовки для обхода защиты"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _extract_canonical_name_improved(self, text: str, url: str, context: str = "") -> Optional[str]:
        """
        Улучшенное извлечение канонического имени
        
        Args:
            text: Текст ссылки
            url: URL ссылки
            context: Контекст (заголовок страницы, родительский элемент)
            
        Returns:
            Каноническое имя или None
        """
        # Расширенные паттерны для поиска НТД
        patterns = [
            # Современные СП
            r'(СП\s+\d+\.\d+\.\d+\.\d+)',  # СП 43.13330.2012
            r'(СП\s+\d+\.\d+\.\d+)',       # СП 43.13330
            r'(СП\s+\d+\.\d+)',            # СП 43
            
            # Старые СНиП
            r'(СНиП\s+\d+\.\d+\.\d+)',     # СНиП 2.09.03
            r'(СНиП\s+\d+\.\d+)',          # СНиП 2.09
            
            # ГОСТы
            r'(ГОСТ\s+\d+\.\d+)',          # ГОСТ 12345
            r'(ГОСТ\s+\d+)',               # ГОСТ 123
            
            # Другие НТД
            r'(СН\s+\d+\.\d+)',            # СН 123
            r'(РД\s+\d+\.\d+)',            # РД 123
            r'(МДС\s+\d+\.\d+)',           # МДС 123
            r'(ТСН\s+\d+\.\d+)',           # ТСН 123
            
            # Изменения
            r'(Изм\.\s*\d+\s*к\s*СП\s+\d+\.\d+\.\d+\.\d+)',  # Изм. 3 к СП 43.13330.2012
            r'(Изм\.\s*\d+\s*к\s*СНиП\s+\d+\.\d+\.\d+)',      # Изм. 3 к СНиП 2.09.03
        ]
        
        # Ищем в тексте ссылки
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Ищем в контексте (заголовок страницы, родительский элемент)
        if context:
            for pattern in patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        
        # Если не нашли по паттернам, попробуем извлечь из URL
        if any(keyword in text.lower() for keyword in ['сп', 'снип', 'гост', 'сн', 'рд', 'мдс']):
            # Очищаем текст от лишних символов
            clean_text = re.sub(r'[^\w\s\.\-]', ' ', text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            if len(clean_text) > 5 and len(clean_text) < 100:
                return clean_text
        
        return None
    
    def _extract_synonyms_improved(self, text: str, canonical_name: str, context: str = "") -> List[str]:
        """
        Улучшенное извлечение синонимов
        
        Args:
            text: Полный текст
            canonical_name: Каноническое имя
            context: Контекст
            
        Returns:
            Список синонимов
        """
        synonyms = []
        
        # Расширенные паттерны для поиска синонимов
        ntd_patterns = [
            r'(СП\s+\d+\.\d+\.\d+\.\d+)',
            r'(СП\s+\d+\.\d+\.\d+)',
            r'(СП\s+\d+\.\d+)',
            r'(СНиП\s+\d+\.\d+\.\d+)',
            r'(СНиП\s+\d+\.\d+)',
            r'(ГОСТ\s+\d+\.\d+)',
            r'(ГОСТ\s+\d+)',
            r'(СН\s+\d+\.\d+)',
            r'(РД\s+\d+\.\d+)',
            r'(МДС\s+\d+\.\d+)',
            r'(ТСН\s+\d+\.\d+)',
        ]
        
        # Ищем в тексте и контексте
        search_text = f"{text} {context}"
        
        for pattern in ntd_patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            for match in matches:
                clean_match = match.strip()
                if clean_match != canonical_name and clean_match not in synonyms:
                    synonyms.append(clean_match)
        
        return synonyms[:15]  # Максимум 15 синонимов
    
    async def _parse_single_source_improved(self, source_name: str, source_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Улучшенный парсинг одного источника с обходом защиты
        
        Args:
            source_name: Имя источника
            source_config: Конфигурация источника
            
        Returns:
            Список найденных документов
        """
        documents = []
        
        try:
            # Создаем HTTP клиент с настройками для обхода защиты
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                verify=False,
                headers=self._get_random_headers()
            ) as client:
                
                logger.info(f"Parsing {source_name} with improved method...")
                
                # Загружаем страницу
                response = await client.get(source_config['url_pattern'])
                response.raise_for_status()
                
                logger.info(f"Successfully loaded {source_name}: {response.status_code}")
                
                # Парсим HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Получаем контекст (заголовок страницы)
                page_title = soup.find('title')
                page_context = page_title.get_text() if page_title else ""
                
                # Ищем ссылки с расширенными селекторами
                links = soup.select(source_config['selector'])
                
                logger.info(f"Found {len(links)} links on {source_name}")
                
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    if not href or not text:
                        continue
                    
                    # Получаем контекст ссылки (родительский элемент)
                    parent_context = ""
                    parent = link.parent
                    if parent:
                        parent_context = parent.get_text(strip=True)[:200]
                    
                    # Извлекаем каноническое имя с улучшенным методом
                    canonical_name = self._extract_canonical_name_improved(
                        text, href, f"{page_context} {parent_context}"
                    )
                    
                    if canonical_name:
                        # Извлекаем синонимы
                        synonyms = self._extract_synonyms_improved(
                            text, canonical_name, f"{page_context} {parent_context}"
                        )
                        
                        doc = {
                            'canonical_id': canonical_name,
                            'ntd_synonyms': synonyms,
                            'source_url': href if href.startswith('http') else f"{source_config['url_pattern']}{href}",
                            'source_name': source_name,
                            'category': source_config['category'],
                            'raw_text': text[:200],
                            'context': parent_context[:100]
                        }
                        
                        documents.append(doc)
                        logger.info(f"Found NTD: {canonical_name} (synonyms: {len(synonyms)})")
                
                # Добавляем задержку для вежливого парсинга
                await asyncio.sleep(random.uniform(1, 3))
                
        except Exception as e:
            logger.error(f"Error parsing {source_name}: {e}")
        
        return documents
    
    def _save_to_database(self, documents: List[Dict[str, Any]]) -> int:
        """Сохраняем документы в базу данных"""
        if not documents:
            return 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            saved_count = 0
            
            for doc in documents:
                try:
                    # Проверяем, есть ли уже такая запись
                    cursor.execute(
                        "SELECT canonical_id FROM ntd_registry_test WHERE canonical_id = ?",
                        (doc['canonical_id'],)
                    )
                    
                    if cursor.fetchone():
                        # Обновляем существующую запись
                        cursor.execute("""
                            UPDATE ntd_registry_test 
                            SET ntd_synonyms = ?, source_url = ?, created_at = CURRENT_TIMESTAMP
                            WHERE canonical_id = ?
                        """, (
                            json.dumps(doc['ntd_synonyms'], ensure_ascii=False),
                            doc['source_url'],
                            doc['canonical_id']
                        ))
                    else:
                        # Создаем новую запись
                        cursor.execute("""
                            INSERT INTO ntd_registry_test 
                            (canonical_id, ntd_synonyms, source_url, status_rag)
                            VALUES (?, ?, ?, 'NOT_ON_DISK')
                        """, (
                            doc['canonical_id'],
                            json.dumps(doc['ntd_synonyms'], ensure_ascii=False),
                            doc['source_url']
                        ))
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving document {doc['canonical_id']}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {saved_count} documents to database")
            return saved_count
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            return 0
    
    async def update_registry_improved(self, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Улучшенное обновление реестра НТД
        
        Args:
            categories: Список категорий для обновления
            
        Returns:
            Результаты обновления
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "sources_processed": [],
            "documents_found": 0,
            "documents_saved": 0,
            "errors": []
        }
        
        # Сортируем источники по приоритету
        sources_to_process = []
        for source_name, config in self.sources.items():
            if not categories or config['category'] in categories:
                sources_to_process.append((source_name, config))
        
        # Сортируем по приоритету (1 = высший)
        sources_to_process.sort(key=lambda x: x[1]['priority'])
        
        logger.info(f"Processing {len(sources_to_process)} sources in priority order")
        
        for source_name, source_config in sources_to_process:
            try:
                logger.info(f"Processing source: {source_name} (priority: {source_config['priority']})")
                
                # Парсим источник с улучшенным методом
                documents = await self._parse_single_source_improved(source_name, source_config)
                
                if documents:
                    # Сохраняем в БД
                    saved_count = self._save_to_database(documents)
                    
                    results["sources_processed"].append({
                        "source": source_name,
                        "priority": source_config['priority'],
                        "documents_found": len(documents),
                        "documents_saved": saved_count
                    })
                    
                    results["documents_found"] += len(documents)
                    results["documents_saved"] += saved_count
                    
                    logger.info(f"Source {source_name}: {len(documents)} found, {saved_count} saved")
                else:
                    logger.warning(f"No documents found on {source_name}")
                    results["sources_processed"].append({
                        "source": source_name,
                        "priority": source_config['priority'],
                        "documents_found": 0,
                        "documents_saved": 0
                    })
                
                # Задержка между источниками
                await asyncio.sleep(random.uniform(2, 5))
                
            except Exception as e:
                error_msg = f"Error processing {source_name}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        return results
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Получаем статистику реестра"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Общее количество
            cursor.execute("SELECT COUNT(*) FROM ntd_registry_test")
            total_count = cursor.fetchone()[0]
            
            # По статусам
            cursor.execute("SELECT status_rag, COUNT(*) FROM ntd_registry_test GROUP BY status_rag")
            status_counts = dict(cursor.fetchall())
            
            # По категориям
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN source_url LIKE '%minstroy%' OR source_url LIKE '%stroyinf%' THEN 'construction'
                        WHEN source_url LIKE '%consultant%' THEN 'laws'
                        WHEN source_url LIKE '%rosstat%' THEN 'statistics'
                        WHEN source_url LIKE '%gost%' THEN 'standards'
                        ELSE 'other'
                    END as category,
                    COUNT(*) as count
                FROM ntd_registry_test 
                GROUP BY category
            """)
            category_counts = dict(cursor.fetchall())
            
            # Топ канонических имен
            cursor.execute("""
                SELECT canonical_id, COUNT(*) as count 
                FROM ntd_registry_test 
                GROUP BY canonical_id 
                ORDER BY count DESC 
                LIMIT 10
            """)
            top_names = cursor.fetchall()
            
            conn.close()
            
            return {
                "total_documents": total_count,
                "status_counts": status_counts,
                "category_counts": category_counts,
                "top_canonical_names": top_names
            }
            
        except Exception as e:
            logger.error(f"Error getting registry stats: {e}")
            return {"error": str(e)}

# Example usage
if __name__ == "__main__":
    async def main():
        manager = ImprovedNTDRegistryManager()
        
        print("Starting improved NTD Registry update...")
        results = await manager.update_registry_improved(categories=['construction', 'standards'])
        
        print(f"Results: {json.dumps(results, indent=2, ensure_ascii=False)}")
        
        # Показываем статистику
        stats = manager.get_registry_stats()
        print(f"Registry stats: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    
    asyncio.run(main())
