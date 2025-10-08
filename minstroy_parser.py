#!/usr/bin/env python3
"""
Парсер для скачивания PDF-файлов с сайта Минстроя России
Улучшенная версия с обработкой ошибок, логированием и конфигурацией
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import logging
from urllib.parse import urljoin, urlparse
from datetime import datetime
import json
from pathlib import Path
import argparse
from typing import List, Dict, Optional
import sys

class InteractiveLogger:
    """Класс для интерактивного логирования с самозаменяющимися строками"""
    
    def __init__(self):
        self.current_line = ""
        self.last_update = 0
        
    def update(self, message: str, force: bool = False):
        """Обновляет текущую строку прогресса"""
        current_time = time.time()
        
        # Обновляем только если прошло достаточно времени или принудительно
        if force or current_time - self.last_update > 0.5:
            # Очищаем текущую строку
            if self.current_line:
                sys.stdout.write('\r' + ' ' * len(self.current_line) + '\r')
            
            # Выводим новую строку
            sys.stdout.write(f'\r{message}')
            sys.stdout.flush()
            
            self.current_line = message
            self.last_update = current_time
    
    def finish(self, message: str = ""):
        """Завершает текущую строку и переходит на новую"""
        if self.current_line:
            sys.stdout.write('\r' + ' ' * len(self.current_line) + '\r')
        if message:
            print(message)
        self.current_line = ""

class MinstroyParser:
    def __init__(self, config_file: str = "minstroy_config.json"):
        """Инициализация парсера с загрузкой конфигурации"""
        self.config = self._load_config(config_file)
        self.session = requests.Session()
        self._setup_session()
        self._setup_logging()
        self.interactive_logger = InteractiveLogger()
        
    def _load_config(self, config_file: str) -> Dict:
        """Загрузка конфигурации из файла или создание по умолчанию"""
        default_config = {
            "urls": [
                "https://minstroyrf.gov.ru/docs/?date_from=&t%5B%5D=76&d%5B%5D=&q=&active%5B%5D=65"
            ],
            "download_dir": "minstroy_pdfs",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            },
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 2,
            "chunk_size": 8192,
            "max_file_size": 100 * 1024 * 1024,  # 100MB
            "skip_existing": True,
            "log_level": "INFO",
            "max_pages_to_scan": 2000,  # Максимальное количество страниц для сканирования
            "max_empty_pages": 10,  # Максимальное количество пустых страниц подряд
            "page_delay": 2  # Задержка между страницами в секундах
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}. Используются настройки по умолчанию.")
        
        return default_config
    
    def _setup_session(self):
        """Настройка HTTP-сессии"""
        self.session.headers.update(self.config["headers"])
        self.session.timeout = self.config["timeout"]
        
    def _setup_logging(self):
        """Настройка логирования"""
        log_level = getattr(logging, self.config["log_level"].upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('minstroy_parser.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _create_download_dir(self):
        """Создание директории для загрузок"""
        download_dir = Path(self.config["download_dir"])
        download_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Директория для загрузок: {download_dir.absolute()}")
        return download_dir
    
    def _is_valid_pdf_url(self, url: str) -> bool:
        """Проверка, является ли URL ссылкой на PDF"""
        parsed_url = urlparse(url)
        return (
            url.lower().endswith('.pdf') or 
            'pdf' in parsed_url.path.lower() or
            'application/pdf' in url.lower()
        )
    
    def _get_filename_from_url(self, url: str) -> str:
        """Извлечение имени файла из URL"""
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # Очистка имени файла от параметров
        if '?' in filename:
            filename = filename.split('?')[0]
        
        # Если имя файла пустое или не содержит расширение
        if not filename or not filename.endswith('.pdf'):
            filename = f"document_{int(time.time())}.pdf"
        
        # Замена недопустимых символов
        filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        
        return filename
    
    def _download_pdf(self, url: str, filepath: Path) -> bool:
        """Скачивание PDF-файла с повторными попытками"""
        for attempt in range(self.config["retry_attempts"]):
            try:
                self.logger.info(f"Попытка {attempt + 1}/{self.config['retry_attempts']}: {url}")
                
                response = self.session.get(url, stream=True, timeout=self.config["timeout"])
                response.raise_for_status()
                
                # Проверка размера файла
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > self.config["max_file_size"]:
                    self.logger.warning(f"Файл слишком большой: {content_length} байт")
                    return False
                
                # Проверка типа контента
                content_type = response.headers.get('content-type', '').lower()
                if 'pdf' not in content_type and not url.lower().endswith('.pdf'):
                    self.logger.warning(f"Не PDF файл: {content_type}")
                    return False
                
                # Скачивание файла
                total_size = 0
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=self.config["chunk_size"]):
                        if chunk:
                            f.write(chunk)
                            total_size += len(chunk)
                            
                            # Проверка размера во время скачивания
                            if total_size > self.config["max_file_size"]:
                                self.logger.warning("Файл превышает максимальный размер, прерывание загрузки")
                                f.close()
                                filepath.unlink(missing_ok=True)
                                return False
                
                self.logger.info(f"Успешно скачан: {filepath.name} ({total_size} байт)")
                return True
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Ошибка при скачивании (попытка {attempt + 1}): {e}")
                if attempt < self.config["retry_attempts"] - 1:
                    time.sleep(self.config["retry_delay"])
                else:
                    self.logger.error(f"Не удалось скачать после {self.config['retry_attempts']} попыток: {url}")
                    return False
            except Exception as e:
                self.logger.error(f"Неожиданная ошибка при скачивании {url}: {e}")
                return False
        
        return False
    
    def _save_download_log(self, downloaded_files: List[Dict], download_dir: Path):
        """Сохранение лога загруженных файлов"""
        log_file = download_dir / "download_log.json"
        log_data = {
            "download_date": datetime.now().isoformat(),
            "total_files": len(downloaded_files),
            "files": downloaded_files
        }
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Лог загрузки сохранен: {log_file}")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения лога: {e}")
    
    
    def _extract_pdf_links_from_page(self, url: str) -> tuple[List[str], bool]:
        """Извлечение PDF-ссылок с одной страницы и проверка на пустоту"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a', href=True)
            
            pdf_links = []
            for link in links:
                href = link.get('href', '')
                if self._is_valid_pdf_url(href):
                    full_url = urljoin(url, href)
                    pdf_links.append(full_url)
            
            # Проверяем, есть ли на странице контент (не пустая страница)
            # Ищем элементы, которые указывают на наличие документов
            content_indicators = soup.find_all(['div', 'span', 'p'], string=lambda text: text and any(
                keyword in text.lower() for keyword in ['документ', 'файл', 'pdf', 'скачать', 'загрузить']
            ))
            
            # Если нет PDF-ссылок и нет индикаторов контента, страница может быть пустой
            is_empty = len(pdf_links) == 0 and len(content_indicators) == 0
            
            return pdf_links, is_empty
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ошибка загрузки страницы {url}: {e}")
            return [], True
    
    def _process_single_page(self, page_url: str, download_dir: Path, page_num: int) -> Dict:
        """Обработка одной страницы с немедленным скачиванием PDF-файлов"""
        # Извлекаем PDF-ссылки со страницы
        pdf_links, is_empty = self._extract_pdf_links_from_page(page_url)
        
        if is_empty:
            return {
                "page_url": page_url,
                "page_num": page_num,
                "pdf_links_found": 0,
                "downloaded": 0,
                "skipped": 0,
                "failed": 0,
                "is_empty": True
            }
        
        # Скачиваем файлы сразу
        downloaded_files = []
        skipped_files = []
        failed_files = []
        
        for i, pdf_url in enumerate(pdf_links, 1):
            filename = self._get_filename_from_url(pdf_url)
            filepath = download_dir / filename
            
            # Пропуск существующих файлов
            if self.config["skip_existing"] and filepath.exists():
                skipped_files.append({"url": pdf_url, "filename": filename, "reason": "already_exists"})
                continue
            
            # Скачивание файла
            if self._download_pdf(pdf_url, filepath):
                file_info = {
                    "url": pdf_url,
                    "filename": filename,
                    "filepath": str(filepath),
                    "size": filepath.stat().st_size if filepath.exists() else 0,
                    "download_time": datetime.now().isoformat(),
                    "page_num": page_num
                }
                downloaded_files.append(file_info)
            else:
                failed_files.append({"url": pdf_url, "filename": filename, "reason": "download_failed"})
        
        return {
            "page_url": page_url,
            "page_num": page_num,
            "pdf_links_found": len(pdf_links),
            "downloaded": len(downloaded_files),
            "skipped": len(skipped_files),
            "failed": len(failed_files),
            "downloaded_files": downloaded_files,
            "skipped_files": skipped_files,
            "failed_files": failed_files,
            "is_empty": False
        }

    def _find_pagination_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Поиск ссылок на другие страницы пагинации"""
        pagination_links = []
        
        # Поиск ссылок пагинации в HTML
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if any(param in href for param in ['PAGEN_1=', 'page=', 'p=']):
                full_url = urljoin(base_url, href)
                if full_url not in pagination_links:
                    pagination_links.append(full_url)
        
        # Поиск максимального номера страницы в пагинации
        max_page = 1
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if 'PAGEN_1=' in href:
                try:
                    # Извлекаем номер страницы из URL
                    page_part = href.split('PAGEN_1=')[1].split('&')[0]
                    page_num = int(page_part)
                    max_page = max(max_page, page_num)
                except (ValueError, IndexError):
                    continue
        
        # Если не нашли пагинацию в HTML, используем расширенный поиск
        if max_page == 1:
            max_page = self.config.get("max_pages_to_scan", 2000)  # Используем настройку из конфигурации
        
        self.logger.info(f"Найдена пагинация до страницы {max_page}")
        
        # Генерируем URL для всех страниц с разными вариантами параметров
        for page_num in range(2, max_page + 1):
            # Основной вариант с PAGEN_1
            page_url = f"{base_url}?date_from=&t%5B0%5D=60&d%5B0%5D=&q=&active%5B0%5D=65&PAGEN_1={page_num}"
            pagination_links.append(page_url)
            
            # Альтернативные варианты URL
            alt_url1 = f"{base_url}?date_from=&t%5B%5D=60&d%5B%5D=&q=&active%5B%5D=65&PAGEN_1={page_num}"
            if alt_url1 not in pagination_links:
                pagination_links.append(alt_url1)
            
            alt_url2 = f"{base_url}?page={page_num}"
            if alt_url2 not in pagination_links:
                pagination_links.append(alt_url2)
        
        return pagination_links

    def parse_and_download(self) -> Dict:
        """Основной метод парсинга и скачивания с последовательной обработкой страниц"""
        start_time = time.time()
        download_dir = self._create_download_dir()
        
        # Получаем список URL для обработки
        urls_to_process = self.config.get("urls", [self.config.get("url", "")])
        if not urls_to_process or not urls_to_process[0]:
            return {"success": False, "error": "Не указаны URL для обработки"}
        
        print(f"🚀 Начинаем парсинг {len(urls_to_process)} разделов сайта Минстроя")
        print("=" * 60)
        
        # Инициализация общей статистики
        total_stats = {
            "all_downloaded_files": [],
            "all_skipped_files": [],
            "all_failed_files": [],
            "total_pages": 0,
            "total_urls_processed": 0
        }
        
        # Обрабатываем каждый URL
        for url_index, base_url in enumerate(urls_to_process, 1):
            print(f"\n📂 Обработка раздела {url_index}/{len(urls_to_process)}")
            print(f"🔗 URL: {base_url}")
            
            # Загружаем главную страницу для определения количества страниц
            try:
                self.interactive_logger.update(f"⏳ Загружаем главную страницу раздела {url_index}...")
                response = self.session.get(base_url)
                response.raise_for_status()
                self.interactive_logger.finish(f"✅ Главная страница загружена (HTTP {response.status_code})")
            except requests.exceptions.RequestException as e:
                self.interactive_logger.finish(f"❌ Ошибка загрузки главной страницы: {e}")
                continue
            
            # Парсинг главной страницы для поиска ссылок пагинации
            soup = BeautifulSoup(response.content, 'html.parser')
            pagination_links = self._find_pagination_links(soup, base_url)
            
            # Добавляем главную страницу в список для обработки
            all_pages = [base_url] + pagination_links
            
            self.interactive_logger.finish(f"📄 Найдено {len(all_pages)} страниц в разделе {url_index}")
            
            # Инициализация статистики для текущего раздела
            section_stats = {
                "downloaded_files": [],
                "skipped_files": [],
                "failed_files": [],
                "processed_pages": 0,
                "empty_pages_count": 0
            }
            
            max_empty_pages = self.config.get("max_empty_pages", 10)
            
            # Обрабатываем страницы последовательно
            for page_num, page_url in enumerate(all_pages, 1):
                # Обновляем прогресс
                progress_msg = (f"📊 Раздел {url_index}/{len(urls_to_process)} | "
                              f"Страница {page_num}/{len(all_pages)} | "
                              f"Скачано: {len(section_stats['downloaded_files'])} | "
                              f"Пропущено: {len(section_stats['skipped_files'])} | "
                              f"Ошибок: {len(section_stats['failed_files'])}")
                
                self.interactive_logger.update(progress_msg)
                
                # Обрабатываем страницу
                page_result = self._process_single_page(page_url, download_dir, page_num)
                
                section_stats["processed_pages"] += 1
                
                # Обновляем статистику раздела
                if not page_result["is_empty"]:
                    section_stats["empty_pages_count"] = 0  # Сбрасываем счетчик при найденном контенте
                    section_stats["downloaded_files"].extend(page_result["downloaded_files"])
                    section_stats["skipped_files"].extend(page_result["skipped_files"])
                    section_stats["failed_files"].extend(page_result["failed_files"])
                else:
                    section_stats["empty_pages_count"] += 1
                    
                    # Останавливаемся при слишком большом количестве пустых страниц подряд
                    if section_stats["empty_pages_count"] >= max_empty_pages:
                        self.interactive_logger.finish(f"⏹️  Найдено {max_empty_pages} пустых страниц подряд. Остановка сканирования раздела {url_index}.")
                        break
                
                # Пауза между страницами
                time.sleep(self.config.get("page_delay", 2))
            
            # Обновляем общую статистику
            total_stats["all_downloaded_files"].extend(section_stats["downloaded_files"])
            total_stats["all_skipped_files"].extend(section_stats["skipped_files"])
            total_stats["all_failed_files"].extend(section_stats["failed_files"])
            total_stats["total_pages"] += section_stats["processed_pages"]
            total_stats["total_urls_processed"] += 1
            
            # Выводим статистику по разделу
            self.interactive_logger.finish(f"✅ Раздел {url_index} завершен: "
                                         f"страниц {section_stats['processed_pages']}, "
                                         f"скачано {len(section_stats['downloaded_files'])}, "
                                         f"пропущено {len(section_stats['skipped_files'])}, "
                                         f"ошибок {len(section_stats['failed_files'])}")
        
        # Завершаем интерактивное логирование
        self.interactive_logger.finish()
        
        # Сохранение лога
        self._save_download_log(total_stats["all_downloaded_files"], download_dir)
        
        # Статистика
        end_time = time.time()
        duration = end_time - start_time
        
        stats = {
            "success": True,
            "total_pages": total_stats["total_pages"],
            "total_links": len(total_stats["all_downloaded_files"]) + len(total_stats["all_skipped_files"]) + len(total_stats["all_failed_files"]),
            "downloaded": len(total_stats["all_downloaded_files"]),
            "skipped": len(total_stats["all_skipped_files"]),
            "failed": len(total_stats["all_failed_files"]),
            "duration_seconds": round(duration, 2),
            "download_dir": str(download_dir),
            "downloaded_files": total_stats["all_downloaded_files"],
            "skipped_files": total_stats["all_skipped_files"],
            "failed_files": total_stats["all_failed_files"],
            "urls_processed": total_stats["total_urls_processed"]
        }
        
        # Вывод результатов
        print("\n" + "="*60)
        print("🎉 РЕЗУЛЬТАТЫ ПОЛНОГО ПАРСИНГА МИНСТРОЯ")
        print("="*60)
        print(f"📊 Обработано разделов: {stats['urls_processed']}")
        print(f"📄 Обработано страниц: {stats['total_pages']}")
        print(f"🔗 Всего PDF-ссылок найдено: {stats['total_links']}")
        print(f"✅ Успешно скачано: {stats['downloaded']}")
        print(f"⏭️  Пропущено (уже существуют): {stats['skipped']}")
        print(f"❌ Ошибки загрузки: {stats['failed']}")
        print(f"⏱️  Время выполнения: {stats['duration_seconds']} сек")
        print(f"📁 Папка с файлами: {stats['download_dir']}")
        print("="*60)
        
        if total_stats["all_downloaded_files"]:
            print(f"\n📥 Скачано {len(total_stats['all_downloaded_files'])} файлов")
            # Показываем только первые 10 файлов для краткости
            for file_info in total_stats["all_downloaded_files"][:10]:
                size_mb = file_info['size'] / (1024 * 1024)
                print(f"  📄 {file_info['filename']} ({size_mb:.2f} MB) - страница {file_info.get('page_num', '?')}")
            if len(total_stats["all_downloaded_files"]) > 10:
                print(f"  ... и еще {len(total_stats['all_downloaded_files']) - 10} файлов")
        
        if total_stats["all_failed_files"]:
            print(f"\n❌ Ошибки загрузки ({len(total_stats['all_failed_files'])} файлов):")
            for file_info in total_stats["all_failed_files"][:5]:  # Показываем только первые 5 ошибок
                print(f"  🔗 {file_info['filename']}: {file_info['reason']}")
            if len(total_stats["all_failed_files"]) > 5:
                print(f"  ... и еще {len(total_stats['all_failed_files']) - 5} ошибок")
        
        return stats

def main():
    """Главная функция с поддержкой аргументов командной строки"""
    parser = argparse.ArgumentParser(description="Парсер PDF-файлов с сайта Минстроя России")
    parser.add_argument("--config", "-c", default="minstroy_config.json", 
                       help="Путь к файлу конфигурации")
    parser.add_argument("--url", "-u", help="URL для парсинга (переопределяет конфигурацию)")
    parser.add_argument("--output", "-o", help="Папка для сохранения файлов")
    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")
    
    args = parser.parse_args()
    
    # Создание парсера
    minstroy_parser = MinstroyParser(args.config)
    
    # Переопределение настроек из аргументов
    if args.url:
        minstroy_parser.config["urls"] = [args.url]
    if args.output:
        minstroy_parser.config["download_dir"] = args.output
    if args.verbose:
        minstroy_parser.config["log_level"] = "DEBUG"
        minstroy_parser._setup_logging()
    
    # Запуск парсинга
    try:
        results = minstroy_parser.parse_and_download()
        if results["success"]:
            print(f"\n🎉 Парсинг завершен успешно!")
            return 0
        else:
            print(f"\n💥 Ошибка парсинга: {results.get('error', 'Неизвестная ошибка')}")
            return 1
    except KeyboardInterrupt:
        print("\n⏹️  Парсинг прерван пользователем")
        return 1
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
