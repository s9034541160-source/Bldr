import asyncio
import httpx
from bs4 import BeautifulSoup
from pathlib import Path
import json
import hashlib
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import re
import ssl
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NormsUpdater:
    """Auto-search functionality for downloading NTD from official Russian sources"""
    
    def __init__(self, base_dir: Optional[str] = None):
        # Use BASE_DIR environment variable or default to I:/docs/new_ntd
        base_dir_env = os.getenv("BASE_DIR", "I:/docs")
        self.base_dir = Path(base_dir or os.path.join(base_dir_env, "new_ntd"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.sources = {
            "minstroyrf.ru": {
                "category": "construction",
                "url_pattern": "https://minstroyrf.ru/normative/",
                "selector": "a[href$='.pdf']",
                "rate_limit": 1
            },
            "stroyinf.ru": {
                "category": "construction",
                "url_pattern": "https://files.stroyinf.ru/Index2/1/4293880/4293880.htm",  # Updated to correct URL
                "selector": "a[href$='.pdf'], a[href$='.htm']",  # PDFs and HTML pages with document info
                "rate_limit": 2  # Более осторожно, сайт может иметь защиту
            },
            "consultant.ru": {
                "category": "laws",
                "url_pattern": "https://www.consultant.ru/document-collection/laws/",
                "selector": "a[href^='/document/']",
                "rate_limit": 1
            },
            "rosstat.gov.ru": {
                "category": "statistics",
                "url_pattern": "https://rosstat.gov.ru/statistics/",
                "selector": "a[href$='.xlsx'], a[href$='.xls']",
                "rate_limit": 1
            },
            "mintrud.gov.ru": {
                "category": "hr",
                "url_pattern": "https://mintrud.gov.ru/documents/",
                "selector": "a[href$='.pdf']",
                "rate_limit": 1
            },
            "rospotrebnadzor.ru": {
                "category": "safety",
                "url_pattern": "https://rospotrebnadzor.ru/normative/",
                "selector": "a[href$='.pdf']",
                "rate_limit": 1
            },
            "nalog.gov.ru": {
                "category": "tax",
                "url_pattern": "https://nalog.gov.ru/docs/nk_rf/",
                "selector": "a[href$='.pdf']",
                "rate_limit": 1
            },
            "minfin.ru": {
                "category": "finance",
                "url_pattern": "https://minfin.ru/ru/documents/",
                "selector": "a[href$='.pdf']",
                "rate_limit": 1
            },
            "minprirody.ru": {
                "category": "ecology",
                "url_pattern": "https://minprirody.ru/activities/normative/",
                "selector": "a[href$='.pdf']",
                "rate_limit": 1
            }
        }
        
    async def update_norms_daily(self, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Daily update of norms from official sources
        
        Args:
            categories: List of categories to update (None for all)
            
        Returns:
            Dictionary with update results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "sources_updated": [],
            "documents_downloaded": 0,
            "errors": []
        }
        
        # Create HTTP client that follows redirects
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=False) as client:
            for source_name, source_config in self.sources.items():
                # Skip if category filter is applied and doesn't match
                if categories and source_config["category"] not in categories:
                    continue
                    
                try:
                    logger.info(f"Updating norms from {source_name}")
                    docs = await self._scrape_source(client, source_name, source_config)
                    results["sources_updated"].append(source_name)
                    results["documents_downloaded"] += len(docs)
                    
                    # Rate limiting
                    await asyncio.sleep(source_config.get("rate_limit", 1))
                except Exception as e:
                    error_msg = f"Error updating {source_name}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    
        return results
    
    async def _scrape_source(self, client: httpx.AsyncClient, source_name: str, source_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scrape documents from a specific source
        
        Args:
            client: HTTP client
            source_name: Name of the source
            source_config: Configuration for the source
            
        Returns:
            List of downloaded documents
        """
        docs = []
        try:
            # Get the main page
            response = await client.get(
                source_config["url_pattern"],
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                }
            )
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find document links
            links = soup.select(source_config["selector"])
            
            # Limit to 20 docs per source per day (to avoid overload)
            links = links[:20]
            
            # Download each document
            for link in links:
                try:
                    href = link.get('href')
                    if not href:
                        continue
                        
                    # Make sure href is a string
                    href = str(href)
                        
                    # Make absolute URL if needed
                    if href.startswith('/'):
                        url_parts = source_config["url_pattern"].split("/")
                        base_url = url_parts[0] + "//" + url_parts[2]
                        href = base_url + href
                    elif not href.startswith('http'):
                        # Relative URL
                        href = source_config["url_pattern"] + href
                    
                    # Download document
                    doc = await self._download_document(client, href, source_config["category"], source_name)
                    if doc:
                        docs.append(doc)
                        
                except Exception as e:
                    logger.warning(f"Error downloading document from link: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping {source_name}: {str(e)}")
            raise
            
        return docs
    
    async def _download_document(self, client: httpx.AsyncClient, url: str, category: str, source: str) -> Optional[Dict[str, Any]]:
        """
        Download a document from URL
        
        Args:
            client: HTTP client
            url: Document URL
            category: Document category
            source: Source name
            
        Returns:
            Document info dictionary or None if failed
        """
        try:
            # Get document
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                }
            )
            response.raise_for_status()
            
            # Determine file extension
            content_type = response.headers.get('content-type', '')
            if 'pdf' in content_type:
                ext = '.pdf'
            elif 'excel' in content_type or 'spreadsheet' in content_type:
                ext = '.xlsx'
            elif 'word' in content_type:
                ext = '.docx'
            else:
                # Try to determine from URL
                if url.endswith('.pdf'):
                    ext = '.pdf'
                elif url.endswith('.xlsx') or url.endswith('.xls'):
                    ext = '.xlsx'
                elif url.endswith('.docx') or url.endswith('.doc'):
                    ext = '.docx'
                else:
                    ext = '.pdf'  # Default
            
            # Generate filename from URL or title
            filename = self._generate_filename(url, response, ext)
            
            # Save to category directory
            category_dir = self.base_dir / category
            category_dir.mkdir(exist_ok=True)
            
            file_path = category_dir / filename
            with open(file_path, 'wb') as f:
                f.write(response.content)
                
            # Get document info
            doc_info = {
                "url": url,
                "file_path": str(file_path),
                "category": category,
                "source": source,
                "downloaded_at": datetime.now().isoformat(),
                "size": len(response.content)
            }
            
            logger.info(f"Downloaded document: {filename} ({len(response.content)} bytes)")
            return doc_info
            
        except Exception as e:
            logger.error(f"Error downloading document from {url}: {str(e)}")
            return None
    
    def _generate_filename(self, url: str, response: httpx.Response, ext: str) -> str:
        """
        Generate filename for downloaded document
        
        Args:
            url: Document URL
            response: HTTP response
            ext: File extension
            
        Returns:
            Generated filename
        """
        # Try to get filename from Content-Disposition header
        content_disposition = response.headers.get('content-disposition', '')
        if 'filename=' in content_disposition:
            # Extract filename from header
            filename_match = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', content_disposition)
            if filename_match:
                filename = filename_match.group(1).strip('"\'')
                # Sanitize filename
                filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                return filename
        
        # Try to generate filename from URL
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')
        if path_parts and path_parts[-1]:
            filename_base = path_parts[-1]
            # Remove query parameters
            filename_base = filename_base.split('?')[0]
            # Sanitize filename
            filename_base = re.sub(r'[<>:"/\\|?*]', '_', filename_base)
            if not filename_base.endswith(ext):
                filename_base += ext
            return filename_base
        
        # Fallback to hash-based filename
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"document_{url_hash}{ext}"
    
    def get_source_status(self) -> Dict[str, Any]:
        """
        Get status of all sources
        
        Returns:
            Dictionary with source status
        """
        status = {}
        for source_name, source_config in self.sources.items():
            category_dir = self.base_dir / source_config["category"]
            if category_dir.exists():
                doc_count = len(list(category_dir.glob("*")))
                last_update = None
                for file_path in category_dir.glob("*"):
                    mtime = file_path.stat().st_mtime
                    file_date = datetime.fromtimestamp(mtime)
                    if not last_update or file_date > last_update:
                        last_update = file_date
                        
                status[source_name] = {
                    "category": source_config["category"],
                    "documents": doc_count,
                    "last_update": last_update.isoformat() if last_update else None
                }
            else:
                status[source_name] = {
                    "category": source_config["category"],
                    "documents": 0,
                    "last_update": None
                }
                
        return status

# Example usage
if __name__ == "__main__":
    # This would be called from the main application
    updater = NormsUpdater()
    
    # Run update
    async def main():
        results = await updater.update_norms_daily(categories=['construction'])
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
    # asyncio.run(main())