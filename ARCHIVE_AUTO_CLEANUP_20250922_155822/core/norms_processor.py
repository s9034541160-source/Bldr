import os
import shutil
import pandas as pd
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
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

class NormsProcessor:
    """Process and restructure the NTD base: dedup, organize, update metadata"""
    
    def __init__(self, base_dir: str = "I:/docs/база", clean_base_dir: str = "I:/docs/clean_base", 
                 neo4j_uri=None, neo4j_user=None, neo4j_password=None):
        self.base_dir = Path(base_dir)
        self.clean_base_dir = Path(clean_base_dir)
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
                print("✅ Neo4j connection established for norms processing")
            except Exception as e:
                print(f"⚠️ Failed to connect to Neo4j for norms processing: {e}")
                self.driver = None
        
        # Document types
        self.doc_types = {
            'mandatory': ['сп', 'гост', 'фз', 'снип', 'обязатель'],  # Обязательная НТД
            'recommended': ['рекомендуемая', 'рекомендации', 'рекоменд'],  # Рекомендуемая НТД
            'methodical': ['методичка', 'методика', 'инструкция', 'руковод'],  # Методическая литература
            'textbook': ['учебник', 'учебное', 'пособие']  # Учебники
        }
        
        # Document statuses
        self.statuses = ['actual', 'outdated', 'pending']
    
    def dedup_and_restructure(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Deduplicate documents and restructure them in clean base
        
        Args:
            df: DataFrame with document information
            
        Returns:
            DataFrame with cleaned document information
        """
        logger.info("Starting deduplication and restructuring...")
        
        # Create clean base directory
        self.clean_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Group by hash to find duplicates
        dup_groups = df.groupby('hash')
        cleaned = []
        
        for h, group in dup_groups:
            if len(group) == 1:
                # No duplicates, keep as is
                cleaned.append(group.iloc[0])
                continue
            
            # Multiple versions: keep the newest
            group_sorted = group.copy()
            group_sorted['sort_date'] = pd.to_datetime(group_sorted['issue_date'], errors='coerce').fillna(pd.Timestamp('1900-01-01'))
            group_sorted = group_sorted.sort_values('sort_date', ascending=False)
            
            # Keep the newest version
            newest = group_sorted.iloc[0]
            old_versions = group_sorted.iloc[1:]
            
            # Log what we're keeping and deleting
            log_msg = f"Dedup {h}: Kept {newest['path']}, deleted {len(old_versions)} old versions"
            logger.info(log_msg)
            self._log_to_neo4j({"action": "dedup", "hash": h, "kept": newest['path'], 
                              "deleted": old_versions['path'].tolist()})
            
            # Delete old versions
            for _, old_row in old_versions.iterrows():
                try:
                    Path(old_row['path']).unlink()
                    logger.info(f"Deleted old version: {old_row['path']}")
                except Exception as e:
                    logger.warning(f"Error deleting {old_row['path']}: {e}")
            
            cleaned.append(newest)
        
        clean_df = pd.DataFrame(cleaned)
        logger.info(f"Kept {len(clean_df)} unique documents after deduplication")
        
        # Restructure: Create organized folder structure
        logger.info("Restructuring documents...")
        restructured = []
        
        for _, row in clean_df.iterrows():
            try:
                # Create category directory
                cat_dir = self.clean_base_dir / row['category']
                cat_dir.mkdir(exist_ok=True)
                
                # Extract document ID from filename
                doc_id = self._extract_doc_id(row['name'])
                if not doc_id:
                    doc_id = f"DOC_{hashlib.md5(row['name'].encode()).hexdigest()[:8]}"
                
                # Create new filename with proper structure
                version = row['version'] if row['version'] != 'unknown' else 'v1'
                date_str = row['issue_date'] if row['issue_date'] != 'unknown' else datetime.now().strftime('%Y-%m-%d')
                
                # Sanitize filename
                safe_doc_id = re.sub(r'[<>:"/\\|?*]', '_', doc_id)
                new_name = f"{safe_doc_id}_{version}_{date_str}{Path(row['path']).suffix}"
                new_path = cat_dir / new_name
                
                # Move file to new location
                old_path = Path(row['path'])
                if old_path.exists() and not new_path.exists():
                    shutil.move(str(old_path), str(new_path))
                    logger.info(f"Moved {old_path} to {new_path}")
                elif new_path.exists():
                    logger.warning(f"File already exists at {new_path}, skipping")
                    new_path = old_path  # Keep original path
                else:
                    logger.warning(f"Source file {old_path} not found, keeping path")
                    new_path = old_path
                
                # Update row with new path
                row_copy = row.copy()
                row_copy['new_path'] = str(new_path)
                row_copy['doc_id'] = doc_id
                restructured.append(row_copy)
                
            except Exception as e:
                logger.error(f"Error restructuring {row['path']}: {e}")
                # Keep original row if restructuring fails
                restructured.append(row)
        
        restructured_df = pd.DataFrame(restructured)
        logger.info(f"Restructured {len(restructured_df)} documents")
        
        # Import to Neo4j
        self._import_to_neo4j(restructured_df)
        
        return restructured_df
    
    def _extract_doc_id(self, filename: str) -> Optional[str]:
        """
        Extract document ID from filename
        
        Args:
            filename: Name of the file
            
        Returns:
            Document ID or None
        """
        filename_lower = filename.lower()
        
        # Patterns for common document types
        patterns = [
            r'(?:сп|гост|снип|фз|тк|санпин|рд|гэсн|фер)-?(\d+[.\d]*)',  # СП31, ГОСТ 123, ФЗ-44
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename_lower, re.IGNORECASE)
            if match:
                # Extract the base part and number
                base_match = re.search(r'(?:сп|гост|снип|фз|тк|санпин|рд|гэсн|фер)', filename_lower, re.IGNORECASE)
                if base_match:
                    base = base_match.group(0).upper()
                    number = match.group(1)
                    return f"{base}{number}"
        
        return None
    
    def _determine_doc_type(self, filename: str, content: str = "") -> str:
        """
        Determine document type based on filename and content
        
        Args:
            filename: Name of the file
            content: Content of the file (optional)
            
        Returns:
            Document type
        """
        text = (filename + " " + content).lower()
        
        # Check each type
        for doc_type, keywords in self.doc_types.items():
            if any(keyword in text for keyword in keywords):
                return doc_type
        
        # Default to mandatory for common document types
        if any(keyword in filename.lower() for keyword in ['сп', 'гост', 'фз', 'снип']):
            return 'mandatory'
        
        return 'other'  # Default type
    
    def _import_to_neo4j(self, df: pd.DataFrame):
        """
        Import processed documents to Neo4j
        
        Args:
            df: DataFrame with processed document information
        """
        if not self.driver:
            logger.warning("Neo4j not available, skipping import")
            return
        
        try:
            with self.driver.session() as session:
                for _, row in df.iterrows():
                    # Determine document type
                    doc_type = self._determine_doc_type(row['name'])
                    
                    # Import document node
                    session.run(
                        """
                        MERGE (d:NormDoc {id: $doc_id})
                        ON MATCH SET 
                            d.name = $name,
                            d.category = $category,
                            d.path = $path,
                            d.hash = $hash,
                            d.size = $size,
                            d.issue_date = $issue_date,
                            d.status = 'actual',
                            d.source = 'local',
                            d.description = $title,
                            d.type = $type,
                            d.updated_at = datetime()
                        ON CREATE SET 
                            d.created_at = datetime(),
                            d.name = $name,
                            d.category = $category,
                            d.path = $path,
                            d.hash = $hash,
                            d.size = $size,
                            d.issue_date = $issue_date,
                            d.status = 'actual',
                            d.source = 'local',
                            d.description = $title,
                            d.type = $type
                        """,
                        doc_id=row.get('doc_id', f"DOC_{hashlib.md5(row['name'].encode()).hexdigest()[:8]}"),
                        name=row['name'],
                        category=row['category'],
                        path=row.get('new_path', row['path']),
                        hash=row['hash'],
                        size=row['size'],
                        issue_date=row['issue_date'],
                        title=row['title'],
                        type=doc_type
                    )
                
                logger.info(f"Imported {len(df)} documents to Neo4j")
        except Exception as e:
            logger.error(f"Error importing to Neo4j: {e}")
    
    def _log_to_neo4j(self, data: Dict[str, Any]):
        """
        Log processing actions to Neo4j
        
        Args:
            data: Log data
        """
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                session.run(
                    """
                    CREATE (l:UpdateLog {
                        timestamp: datetime(),
                        action: $action,
                        data: $data
                    })
                    """,
                    action=data.get('action', 'unknown'),
                    data=json.dumps(data, ensure_ascii=False)
                )
        except Exception as e:
            logger.error(f"Error logging to Neo4j: {e}")
    
    def merge_bases(self, local_df: pd.DataFrame, downloaded_docs: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Merge local and downloaded documents
        
        Args:
            local_df: DataFrame with local documents
            downloaded_docs: List of downloaded documents
            
        Returns:
            Merged DataFrame
        """
        logger.info("Merging local and downloaded documents...")
        
        # Convert downloaded docs to DataFrame
        if downloaded_docs:
            downloaded_df = pd.DataFrame(downloaded_docs)
            # Deduplicate by ID and version
            downloaded_df.drop_duplicates(subset=['id', 'version'], keep='last', inplace=True)
            
            # Merge with local documents
            merged_df = pd.concat([local_df, downloaded_df], ignore_index=True)
            
            # Final deduplication
            if 'doc_id' in merged_df.columns:
                merged_df.drop_duplicates(subset=['doc_id'], keep='last', inplace=True)
        else:
            merged_df = local_df.copy()
        
        logger.info(f"Merged to {len(merged_df)} documents")
        return merged_df

# Example usage
if __name__ == "__main__":
    # This would be called from the main processing script
    processor = NormsProcessor()
    
    # For testing, you would load the scan results
    # df = pd.read_csv("norms_scan_results.csv")  # Or load from Neo4j
    # cleaned = processor.dedup_and_restructure(df)
    # print(f"Processed {len(cleaned)} documents")
    
    print("NormsProcessor ready for use")