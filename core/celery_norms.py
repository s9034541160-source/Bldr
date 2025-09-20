import asyncio
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import os
import shutil
from pathlib import Path
import hashlib
import re
import json

# Try to import pandas with proper error handling
PANDAS_AVAILABLE = False
pd = None
try:
    import pandas as pd  # type: ignore
    PANDAS_AVAILABLE = True
except ImportError as e:
    pd = None
    print(f"Warning: pandas not available: {e}")

# Try to import Neo4j with proper error handling
NEO4J_AVAILABLE = False
GraphDatabase = None
try:
    from neo4j import GraphDatabase  # type: ignore
    NEO4J_AVAILABLE = True
except ImportError as e:
    GraphDatabase = None
    print(f"Warning: Neo4j not available: {e}")

# Import norms updater
from core.norms_updater import NormsUpdater

# Import Celery
from core.celery_app import celery_app

# Import WebSocket manager for real-time updates
from core.websocket_manager import manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NormsUpdateTask:
    """Celery task for updating NTD from official sources"""
    
    def __init__(self, neo4j_uri=None, neo4j_user=None, neo4j_password=None):
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "neopassword")
        self.driver = None
        self.norms_updater = NormsUpdater()
        
        # Initialize Neo4j driver if available
        if NEO4J_AVAILABLE and GraphDatabase:
            try:
                self.driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
                # Test connection
                with self.driver.session() as session:
                    session.run("RETURN 1")
                print("✅ Neo4j connection established for norms update tasks")
            except Exception as e:
                print(f"⚠️ Failed to connect to Neo4j for norms update tasks: {e}")
                self.driver = None
    
    def update_norms(self, categories: Optional[List[str]] = None, force: bool = False) -> Dict[str, Any]:
        """
        Update norms from official sources
        
        Args:
            categories: List of categories to update (None for all)
            force: Force update even if local version is newer
            
        Returns:
            Dictionary with update results
        """
        logger.info(f"Starting norms update for categories: {categories or 'all'}, force: {force}")
        
        try:
            # Run async update in a new event loop
            results = asyncio.run(self.norms_updater.update_norms_daily(categories))
            logger.info(f"Norms update completed: {results['documents_downloaded']} documents downloaded")
            
            # Process newly downloaded documents
            if results['documents_downloaded'] > 0:
                logger.info("Processing newly downloaded documents...")
                self._process_new_documents()
                logger.info("New documents processed and indexed")
            
            # Log to Neo4j
            self._log_to_neo4j({
                "action": "update_norms",
                "categories": categories,
                "force": force,
                "results": results,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "updated": results['documents_downloaded'],
                "sources_updated": results['sources_updated'],
                "errors": results['errors']
            }
        except Exception as e:
            logger.error(f"Error updating norms: {e}")
            self._log_to_neo4j({
                "action": "update_norms_error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            raise
    
    def _process_new_documents(self):
        """Process newly downloaded documents and update Neo4j"""
        if not self.driver:
            logger.warning("Neo4j not available, skipping document processing")
            return
        
        try:
            # Get all documents in the norms database
            base_dir_env = os.getenv("BASE_DIR", "I:/docs")
            base_dir = Path(os.path.join(base_dir_env, "ntd"))
            if not base_dir.exists():
                logger.warning("Norms database directory not found")
                return
            
            processed_count = 0
            
            # Process each category directory
            for category_dir in base_dir.iterdir():
                if not category_dir.is_dir():
                    continue
                    
                category = category_dir.name
                logger.info(f"Processing documents in category: {category}")
                
                # Process each document in the category
                for doc_path in category_dir.iterdir():
                    if not doc_path.is_file():
                        continue
                        
                    try:
                        # Extract document information
                        doc_info = self._extract_doc_info(doc_path, category)
                        
                        # Update Neo4j
                        with self.driver.session() as session:
                            # Check if document already exists
                            result = session.run(
                                """
                                MATCH (d:NormDoc {id: $id})
                                RETURN d.issue_date as issue_date
                                """,
                                id=doc_info['id']
                            )
                            existing = result.single()
                            
                            if existing:
                                # Document exists, update if newer or forced
                                existing_date = existing['issue_date']
                                # Use datetime parsing instead of pandas when pandas is not available
                                if PANDAS_AVAILABLE and pd:
                                    is_newer = pd.to_datetime(doc_info['issue_date']) > pd.to_datetime(existing_date)
                                else:
                                    # Simple string comparison as fallback
                                    is_newer = doc_info['issue_date'] > existing_date
                                
                                if is_newer:
                                    # Move old version to archive
                                    self._archive_old_version(doc_info['id'], existing_date, doc_path)
                                    
                                    # Update document
                                    session.run(
                                        """
                                        MATCH (d:NormDoc {id: $id})
                                        SET d.name = $name,
                                            d.category = $category,
                                            d.path = $path,
                                            d.size = $size,
                                            d.issue_date = $issue_date,
                                            d.status = 'actual',
                                            d.source = $source,
                                            d.link = $link,
                                            d.check_date = datetime(),
                                            d.updated_at = datetime()
                                        """,
                                        id=doc_info['id'],
                                        name=doc_info['name'],
                                        category=doc_info['category'],
                                        path=str(doc_path),
                                        size=doc_info['size'],
                                        issue_date=doc_info['issue_date'],
                                        source=doc_info['source'],
                                        link=doc_info['link']
                                    )
                                    logger.info(f"Updated document: {doc_info['id']}")
                            else:
                                # New document, create it
                                session.run(
                                    """
                                    CREATE (d:NormDoc {
                                        id: $id,
                                        name: $name,
                                        category: $category,
                                        path: $path,
                                        size: $size,
                                        issue_date: $issue_date,
                                        status: 'actual',
                                        source: $source,
                                        link: $link,
                                        check_date: datetime(),
                                        created_at: datetime(),
                                        updated_at: datetime()
                                    })
                                    """,
                                    id=doc_info['id'],
                                    name=doc_info['name'],
                                    category=doc_info['category'],
                                    path=str(doc_path),
                                    size=doc_info['size'],
                                    issue_date=doc_info['issue_date'],
                                    source=doc_info['source'],
                                    link=doc_info['link']
                                )
                                logger.info(f"Created new document: {doc_info['id']}")
                        
                        processed_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing document {doc_path}: {e}")
                        continue
            
            logger.info(f"Processed {processed_count} documents")
            
        except Exception as e:
            logger.error(f"Error processing new documents: {e}")
    
    def _extract_doc_info(self, doc_path: Path, category: str) -> Dict[str, Any]:
        """
        Extract document information from file path and content
        
        Args:
            doc_path: Path to the document
            category: Document category
            
        Returns:
            Dictionary with document information
        """
        # Generate document ID from filename
        filename = doc_path.name
        doc_id = self._extract_doc_id(filename)
        if not doc_id:
            doc_id = f"DOC_{hashlib.md5(filename.encode()).hexdigest()[:8]}"
        
        # Extract version and date from filename
        version = self._extract_version(filename)
        issue_date = self._extract_date(filename)
        
        # Get file size
        size = doc_path.stat().st_size
        
        # Determine source from path
        source = "unknown"
        for part in doc_path.parts:
            if "minstroyrf" in part.lower():
                source = "minstroyrf"
            elif "consultant" in part.lower():
                source = "consultant"
            elif "gosstandart" in part.lower():
                source = "gosstandart"
            elif "garant" in part.lower():
                source = "garant"
        
        return {
            "id": doc_id,
            "name": filename,
            "category": category,
            "path": str(doc_path),
            "size": size,
            "issue_date": issue_date,
            "version": version,
            "source": source,
            "link": f"file://{doc_path}"
        }
    
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
    
    def _extract_version(self, filename: str) -> str:
        """
        Extract version from filename
        
        Args:
            filename: Name of the file
            
        Returns:
            Version string
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
    
    def _extract_date(self, filename: str) -> str:
        """
        Extract date from filename
        
        Args:
            filename: Name of the file
            
        Returns:
            Date string
        """
        # Look for date patterns
        date_patterns = [
            r'(\d{4})[._-](\d{2})[._-](\d{2})',  # YYYY-MM-DD or YYYY.MM.DD or YYYY_MM_DD
            r'(\d{2})[._-](\d{2})[._-](\d{4})',  # DD-MM-YYYY or DD.MM.YYYY or DD_MM_YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                groups = match.groups()
                if len(groups[0]) == 4:  # YYYY-MM-DD format
                    return f"{groups[0]}-{groups[1]}-{groups[2]}"
                else:  # DD-MM-YYYY format
                    return f"{groups[2]}-{groups[1]}-{groups[0]}"
        
        # Default to current date
        return datetime.now().strftime('%Y-%m-%d')
    
    def _archive_old_version(self, doc_id: str, old_date: str, doc_path: Path):
        """
        Move old version of document to archive
        
        Args:
            doc_id: Document ID
            old_date: Date of old version
            doc_path: Path to current document
        """
        try:
            base_dir_env = os.getenv("BASE_DIR", "I:/docs")
            archive_dir = Path(os.path.join(base_dir_env, "ntd", "archive"))
            archive_dir.mkdir(exist_ok=True, parents=True)
            
            # Create archive filename
            ext = doc_path.suffix
            archive_filename = f"{doc_id}_old_{old_date}{ext}"
            archive_path = archive_dir / archive_filename
            
            # Move old version to archive
            if doc_path.exists() and not archive_path.exists():
                shutil.move(str(doc_path), str(archive_path))
                logger.info(f"Archived old version: {archive_path}")
                
                # Update Neo4j status to outdated
                if self.driver:
                    with self.driver.session() as session:
                        session.run(
                            """
                            MATCH (d:NormDoc {id: $id})
                            SET d.status = 'outdated'
                            """,
                            id=doc_id
                        )
        except Exception as e:
            logger.error(f"Error archiving old version of {doc_id}: {e}")
    
    def _log_to_neo4j(self, data: Dict[str, Any]):
        """
        Log update actions to Neo4j
        
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

@celery_app.task(bind=True, name='core.celery_norms.update_norms_task')
def update_norms_task(self, categories: Optional[List[str]] = None, force: bool = False):
    """
    Celery task function for updating norms
    
    Args:
        categories: List of categories to update (None for all)
        force: Force update even if local version is newer
    """
    task_id = self.request.id
    logger.info(f"Starting norms update task {task_id}")
    
    # Log task start in Neo4j
    try:
        if NEO4J_AVAILABLE and GraphDatabase:
            neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
            neo4j_password = os.getenv("NEO4J_PASSWORD", "neopassword")
            
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            with driver.session() as session:
                session.run(
                    """
                    CREATE (t:Task {
                        id: $id,
                        type: 'update_norms',
                        status: 'running',
                        progress: 0,
                        started_at: datetime()
                    })
                    """,
                    id=task_id
                )
            driver.close()
            
            # Emit WebSocket update
            try:
                async def emit_start():
                    await manager.broadcast(json.dumps({
                        'id': task_id,
                        'type': 'update_norms',
                        'status': 'running',
                        'progress': 0,
                        'message': 'Task started'
                    }))
                
                # Create a new event loop for the async call
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(emit_start())
                loop.close()
            except Exception as e:
                logger.error(f"Error emitting WebSocket start update: {e}")
    except Exception as e:
        logger.error(f"Error logging task start to Neo4j: {e}")
    
    try:
        updater = NormsUpdateTask()
        results = updater.update_norms(categories, force)
        
        # Update task status in Neo4j
        try:
            if NEO4J_AVAILABLE and GraphDatabase:
                neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
                neo4j_user = os.getenv("NEO4J_USER", "neo4j")
                neo4j_password = os.getenv("NEO4J_PASSWORD", "neopassword")
                
                driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
                with driver.session() as session:
                    session.run(
                        """
                        MATCH (t:Task {id: $id})
                        SET t.status = 'completed',
                            t.progress = 100,
                            t.completed_at = datetime(),
                            t.results = $results
                        """,
                        id=task_id,
                        results=json.dumps(results, ensure_ascii=False)
                    )
                driver.close()
                
                # Emit WebSocket update
                try:
                    async def emit_complete():
                        await manager.broadcast(json.dumps({
                            'id': task_id,
                            'type': 'update_norms',
                            'status': 'completed',
                            'progress': 100,
                            'results': results
                        }))
                    
                    # Create a new event loop for the async call
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(emit_complete())
                    loop.close()
                except Exception as e:
                    logger.error(f"Error emitting WebSocket complete update: {e}")
        except Exception as e:
            logger.error(f"Error updating task status in Neo4j: {e}")
        
        return results
    except Exception as e:
        logger.error(f"Error in norms update task: {e}")
        
        # Update task status in Neo4j
        try:
            if NEO4J_AVAILABLE and GraphDatabase:
                neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
                neo4j_user = os.getenv("NEO4J_USER", "neo4j")
                neo4j_password = os.getenv("NEO4J_PASSWORD", "neopassword")
                
                driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
                with driver.session() as session:
                    session.run(
                        """
                        MATCH (t:Task {id: $id})
                        SET t.status = 'failed',
                            t.error = $error,
                            t.completed_at = datetime()
                        """,
                        id=task_id,
                        error=str(e)
                    )
                driver.close()
                
                # Emit WebSocket update
                try:
                    async def emit_error():
                        await manager.broadcast(json.dumps({
                            'id': task_id,
                            'type': 'update_norms',
                            'status': 'failed',
                            'error': str(e)
                        }))
                    
                    # Create a new event loop for the async call
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(emit_error())
                    loop.close()
                except Exception as we:
                    logger.error(f"Error emitting WebSocket error update: {we}")
        except Exception as ne:
            logger.error(f"Error updating task status in Neo4j: {ne}")
        
        raise

if __name__ == "__main__":
    # Example usage
    updater = NormsUpdateTask()
    results = updater.update_norms(categories=['construction', 'finance'])
    print(json.dumps(results, indent=2, ensure_ascii=False))