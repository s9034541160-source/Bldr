import os
import hashlib
import pandas as pd
import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import re
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import Neo4j with proper error handling
NEO4J_AVAILABLE = False
GraphDatabase = None
try:
    from neo4j import GraphDatabase  # type: ignore
    NEO4J_AVAILABLE = True
except ImportError as e:
    GraphDatabase = None
    print(f"Warning: Neo4j not available: {e}")

class NormsScanner:
    """Scan and analyze the existing NTD base for duplicates and outdated documents"""
    
    def __init__(self, base_dir: str = "I:/docs/база", neo4j_uri=None, neo4j_user=None, neo4j_password=None):
        self.base_dir = Path(base_dir)
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "neopassword")
        self.driver = None
        
        # Initialize Neo4j driver if available
        if NEO4J_AVAILABLE and GraphDatabase:
            try:
                self.driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
                # Test connection
                with self.driver.session() as session:
                    session.run("RETURN 1")
                print("✅ Neo4j connection established for norms scanning")
            except Exception as e:
                print(f"⚠️ Failed to connect to Neo4j for norms scanning: {e}")
                self.driver = None
        
        # Document categories
        self.categories = {
            'construction': ['сп', 'гост', 'снип', 'rd', 'bim', 'смет', 'проект', 'км', 'кс'],
            'finance': ['фз-44', 'гэсн', 'фер', 'смет', 'бюджет', 'контракт'],
            'safety': ['санпин', 'промбез', 'тб', 'пожар', 'безопасн'],
            'ecology': ['овос', 'фз-7', 'экология', 'эколог', 'природ'],
            'hr': ['тк рф', 'мрот', 'кадры', 'труд', 'персонал'],
            'methodical': ['методичка', 'методика', 'инструкция', 'руковод', 'пособие'],
            'textbook': ['учебник', 'учебное', 'пособие', 'учебн']
        }
    
    def scan_base(self) -> pd.DataFrame:
        """
        Scan the base directory for documents and extract metadata
        
        Returns:
            DataFrame with document information
        """
        logger.info(f"Scanning base directory: {self.base_dir}")
        
        files = []
        supported_extensions = ('.pdf', '.docx', '.xlsx', '.txt', '.doc')
        
        # Walk through all files in the base directory
        for root, dirs, fs in os.walk(self.base_dir):
            for f in fs:
                if f.lower().endswith(supported_extensions):
                    path = Path(root) / f
                    try:
                        # Calculate file hash
                        with open(path, 'rb') as ff:
                            file_content = ff.read()
                            h = hashlib.md5(file_content).hexdigest()
                            size = len(file_content)
                        
                        # Extract metadata from PDF files
                        title = f
                        issue_date = 'unknown'
                        if f.lower().endswith('.pdf'):
                            try:
                                doc = fitz.open(path)
                                meta = doc.metadata
                                title = meta.get('title', f)
                                # Try to extract creation date
                                raw_date = meta.get('creationDate', '')
                                if raw_date:
                                    # Parse PDF date format: D:20230101120000
                                    date_match = re.search(r'D:(\d{4})(\d{2})(\d{2})', raw_date)
                                    if date_match:
                                        issue_date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                                    else:
                                        issue_date = raw_date
                                doc.close()
                            except Exception as e:
                                logger.warning(f"Error extracting PDF metadata from {path}: {e}")
                                title = f
                                issue_date = 'unknown'
                        
                        # Determine category by keywords
                        cat = self._categorize_document(f, path)
                        
                        # Extract version from filename if possible
                        version = self._extract_version(f)
                        
                        files.append({
                            'path': str(path),
                            'name': f,
                            'hash': h,
                            'size': size,
                            'title': title,
                            'issue_date': issue_date,
                            'category': cat,
                            'version': version
                        })
                        
                    except Exception as e:
                        logger.warning(f"Error processing file {path}: {e}")
                        continue
        
        df = pd.DataFrame(files)
        logger.info(f"Found {len(df)} documents")
        return df
    
    def _categorize_document(self, filename: str, filepath: Path) -> str:
        """
        Categorize document based on filename and content
        
        Args:
            filename: Name of the file
            filepath: Path to the file
            
        Returns:
            Category string
        """
        filename_lower = filename.lower()
        
        # Check each category
        for category, keywords in self.categories.items():
            if any(keyword in filename_lower for keyword in keywords):
                return category
        
        # Try to read file content for additional categorization
        try:
            if filename_lower.endswith('.pdf'):
                doc = fitz.open(filepath)
                text = ""
                # Extract text from first few pages
                for page_num in range(min(3, doc.page_count)):
                    page = doc.load_page(page_num)
                    text += page.get_text()
                doc.close()
                
                text_lower = text.lower()
                for category, keywords in self.categories.items():
                    if any(keyword in text_lower for keyword in keywords):
                        return category
        except Exception as e:
            logger.warning(f"Error reading content for categorization: {e}")
        
        return 'other'
    
    def _extract_version(self, filename: str) -> str:
        """
        Extract version from filename
        
        Args:
            filename: Name of the file
            
        Returns:
            Version string or 'unknown'
        """
        # Look for patterns like v2023, 2023, v.2023
        version_patterns = [
            r'[vв]?\.?\s*(\d{4})',  # v2023, 2023, v.2023, в2023
            r'(\d{4})\s*г\.?',      # 2023 г.
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return 'unknown'
    
    def find_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Find duplicate documents by hash
        
        Args:
            df: DataFrame with document information
            
        Returns:
            DataFrame with duplicate documents
        """
        # Group by hash and find duplicates
        dup_groups = df.groupby('hash')
        duplicates = []
        
        for h, group in dup_groups:
            if len(group) > 1:
                # Sort by issue date to identify newest
                group_sorted = group.copy()
                group_sorted['sort_date'] = pd.to_datetime(group_sorted['issue_date'], errors='coerce').fillna(pd.Timestamp('1900-01-01'))
                group_sorted = group_sorted.sort_values('sort_date', ascending=False)
                
                # Keep the newest, mark others as duplicates
                newest = group_sorted.iloc[0]
                for _, row in group_sorted.iloc[1:].iterrows():
                    duplicates.append({
                        'hash': h,
                        'kept_path': newest['path'],
                        'deleted_path': row['path'],
                        'kept_name': newest['name'],
                        'deleted_name': row['name'],
                        'kept_date': newest['issue_date'],
                        'deleted_date': row['issue_date']
                    })
        
        return pd.DataFrame(duplicates)
    
    def find_outdated(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Find outdated documents based on version/year
        
        Args:
            df: DataFrame with document information
            
        Returns:
            DataFrame with outdated documents
        """
        # For now, we'll consider documents with years before 2023 as potentially outdated
        # Check against current versions from official sources
        outdated = []
        
        for _, row in df.iterrows():
            # Check if filename contains old years
            name_lower = row['name'].lower()
            if any(year in name_lower for year in ['2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021']):
                outdated.append(row.to_dict())
        
        return pd.DataFrame(outdated)
    
    def log_to_neo4j(self, data: Dict[str, Any]):
        """
        Log scan results to Neo4j
        
        Args:
            data: Scan results data
        """
        if not self.driver:
            logger.warning("Neo4j not available, skipping log")
            return
        
        try:
            with self.driver.session() as session:
                # Create scan log node
                session.run(
                    """
                    CREATE (l:ScanLog {
                        timestamp: datetime(),
                        data: $data
                    })
                    """,
                    data=json.dumps(data, ensure_ascii=False)
                )
                logger.info("Scan results logged to Neo4j")
        except Exception as e:
            logger.error(f"Error logging to Neo4j: {e}")
    
    def run_scan(self) -> Dict[str, Any]:
        """
        Run complete scan and analysis
        
        Returns:
            Dictionary with scan results
        """
        logger.info("Starting norms base scan...")
        
        # Scan base directory
        df = self.scan_base()
        
        # Find duplicates
        duplicates = self.find_duplicates(df)
        
        # Find outdated documents
        outdated = self.find_outdated(df)
        
        # Category counts
        cat_counts = df['category'].value_counts().to_dict()
        
        # Prepare results
        results = {
            "total": len(df),
            "dupes_count": len(duplicates),
            "outdated_count": len(outdated),
            "categories": cat_counts,
            "dupes_list": duplicates[['deleted_path', 'kept_path']].to_dict('records') if not duplicates.empty else [],
            "outdated_list": outdated['path'].tolist() if not outdated.empty else []
        }
        
        # Log to Neo4j
        self.log_to_neo4j(results)
        
        # Print summary
        print(f"Файлов: {results['total']}")
        print(f"Дублей: {results['dupes_count']}")
        print(f"Устаревших: {results['outdated_count']}")
        print("Категории:")
        for cat, count in cat_counts.items():
            print(f"  {cat}: {count}")
        
        return results

# Example usage
if __name__ == "__main__":
    # Create backup first
    import shutil
    from datetime import datetime
    
    base_dir = Path("I:/docs/база")
    backup_dir = Path(f"I:/docs/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    if base_dir.exists():
        print(f"Creating backup to {backup_dir}")
        shutil.copytree(base_dir, backup_dir)
        print("Backup created successfully")
    
    # Run scan
    scanner = NormsScanner()
    results = scanner.run_scan()
    
    # Save results to JSON
    with open('norms_scan_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("Scan results saved to norms_scan_results.json")