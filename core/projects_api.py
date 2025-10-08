from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional, Dict, Any
import os
import shutil
import json
import uuid
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel

# Try to import Neo4j with proper error handling
NEO4J_AVAILABLE = False
GraphDatabase = None
try:
    from neo4j import GraphDatabase  # type: ignore
    NEO4J_AVAILABLE = True
except ImportError as e:
    GraphDatabase = None
    print(f"Warning: Neo4j not available: {e}")

# Import template manager
from core.template_manager import template_manager

router = APIRouter(tags=["projects"])  # Removed the prefix since it's added in main.py

# Project models
class ProjectCreate(BaseModel):
    name: str
    code: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = "planned"

# Template models
class TemplateCreate(BaseModel):
    name: str
    category: str
    preview: str
    full_text: str


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    preview: Optional[str] = None
    full_text: Optional[str] = None


class TemplateResponse(BaseModel):
    id: str
    name: str
    category: str
    preview: str
    full_text: str

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    code: str
    location: Optional[str]
    status: str
    files_count: int
    roi: float
    updated_at: str

class FileResponse(BaseModel):
    id: str
    name: str
    path: str
    size: int
    type: str

class ScanResult(BaseModel):
    files_count: int
    smeta_count: int
    rd_count: int
    graphs_count: int
    smeta_paths: List[str]
    rd_paths: List[str]

class ProjectResult(BaseModel):
    id: str
    type: str
    data: Dict[Any, Any]
    created_at: str

# Add Pydantic model for result data (place this with other models)
class ResultCreate(BaseModel):
    type: str
    data: Dict[Any, Any]

class ProjectManager:
    def __init__(self, neo4j_uri=None, neo4j_user=None, neo4j_password=None):
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "neopassword")
        self.driver = None
        
        # Initialize Neo4j driver if available
        if NEO4J_AVAILABLE:
            try:
                self.driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
                # Test connection
                with self.driver.session() as session:
                    session.run("RETURN 1")
                print("[OK] Neo4j connection established for project management")
            except Exception as e:
                print(f"[WARN] Failed to connect to Neo4j for project management: {e}")
                self.driver = None
    
    def detect_file_type(self, filename: str, content: bytes = b'') -> str:
        """Detect file type based on extension and content"""
        filename_lower = filename.lower()
        
        # Smet files (Excel with GESN)
        if filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls'):
            if content and b'\xd0\xb3\xd1\x8d\xd1\x81\xd0\xbd' in content.lower():  # 'гэсн' in UTF-8 bytes
                return 'smeta'
            return 'smeta'
        
        # RD files (PDF with RD)
        if filename_lower.endswith('.pdf'):
            if content and b'\xd1\x80\xd0\xb4' in content.lower():  # 'рд' in UTF-8 bytes
                return 'rd'
            return 'rd'
        
        # Graph files
        if filename_lower.endswith('.mpp') or filename_lower.endswith('.gantt'):
            return 'graphs'
        
        return 'other'
    
    def create_project(self, project_data: ProjectCreate) -> dict:
        """Create a new project in Neo4j"""
        if not self.driver:
            raise HTTPException(status_code=500, detail="Database not available")
        
        project_id = str(uuid.uuid4())
        
        # Default code if not provided
        if not project_data.code:
            project_data.code = f"PRJ-{project_id[:8].upper()}"
        
        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    CREATE (p:Project {
                        id: $id,
                        name: $name,
                        code: $code,
                        location: $location,
                        status: $status,
                        files_count: 0,
                        roi: 0.0,
                        created_at: datetime(),
                        updated_at: datetime()
                    })
                    RETURN p
                    """,
                    id=project_id,
                    name=project_data.name,
                    code=project_data.code,
                    location=project_data.location,
                    status=project_data.status
                )
                record = result.single()
                if record:
                    project = dict(record["p"])
                    return {
                        "id": project.get("id", ""),
                        "name": project.get("name", ""),
                        "code": project.get("code", ""),
                        "location": project.get("location"),
                        "status": project.get("status", "planned"),
                        "files_count": project.get("files_count", 0),
                        "roi": project.get("roi", 0.0),
                        "updated_at": project.get("updated_at", datetime.now().isoformat()) if isinstance(project.get("updated_at"), str) else project.get("updated_at", datetime.now()).isoformat()
                    }
                else:
                    raise HTTPException(status_code=500, detail="Failed to create project")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    def get_projects(self) -> List[dict]:
        """Get all projects with file counts"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (p:Project)
                    OPTIONAL MATCH (p)-[:HAS_FILE]->(f:File)
                    RETURN p, count(f) as files_count
                    ORDER BY p.updated_at DESC
                    """
                )
                projects = []
                for record in result:
                    project = dict(record["p"])
                    project["files_count"] = record["files_count"]
                    projects.append({
                        "id": project.get("id", ""),
                        "name": project.get("name", ""),
                        "code": project.get("code", ""),
                        "location": project.get("location"),
                        "status": project.get("status", "planned"),
                        "files_count": project.get("files_count", 0),
                        "roi": project.get("roi", 0.0),
                        "updated_at": project.get("updated_at", datetime.now().isoformat()) if isinstance(project.get("updated_at"), str) else project.get("updated_at", datetime.now()).isoformat()
                    })
                return projects
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    def get_project(self, project_id: str) -> dict:
        """Get a specific project"""
        if not self.driver:
            raise HTTPException(status_code=404, detail="Project not found")
        
        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (p:Project {id: $id})
                    OPTIONAL MATCH (p)-[:HAS_FILE]->(f:File)
                    RETURN p, count(f) as files_count
                    """,
                    id=project_id
                )
                record = result.single()
                if record:
                    project = dict(record["p"])
                    project["files_count"] = record["files_count"]
                    return {
                        "id": project.get("id", ""),
                        "name": project.get("name", ""),
                        "code": project.get("code", ""),
                        "location": project.get("location"),
                        "status": project.get("status", "planned"),
                        "files_count": project.get("files_count", 0),
                        "roi": project.get("roi", 0.0),
                        "updated_at": project.get("updated_at", datetime.now().isoformat()) if isinstance(project.get("updated_at"), str) else project.get("updated_at", datetime.now()).isoformat()
                    }
                else:
                    raise HTTPException(status_code=404, detail="Project not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    def update_project(self, project_id: str, project_data: ProjectUpdate) -> dict:
        """Update a project"""
        if not self.driver:
            raise HTTPException(status_code=404, detail="Project not found")
        
        try:
            with self.driver.session() as session:
                # Build dynamic SET clause
                set_parts = []
                params = {"id": project_id}
                
                if project_data.name is not None:
                    set_parts.append("p.name = $name")
                    params["name"] = project_data.name
                    
                if project_data.code is not None:
                    set_parts.append("p.code = $code")
                    params["code"] = project_data.code
                    
                if project_data.location is not None:
                    set_parts.append("p.location = $location")
                    params["location"] = project_data.location
                    
                if project_data.status is not None:
                    set_parts.append("p.status = $status")
                    params["status"] = project_data.status
                
                set_parts.append("p.updated_at = datetime()")
                
                query = f"""
                    MATCH (p:Project {{id: $id}})
                    SET {", ".join(set_parts)}
                    RETURN p
                """
                
                result = session.run(query, **params)
                record = result.single()
                if record:
                    project = dict(record["p"])
                    return {
                        "id": project.get("id", ""),
                        "name": project.get("name", ""),
                        "code": project.get("code", ""),
                        "location": project.get("location"),
                        "status": project.get("status", "planned"),
                        "files_count": project.get("files_count", 0),
                        "roi": project.get("roi", 0.0),
                        "updated_at": project.get("updated_at", datetime.now().isoformat()) if isinstance(project.get("updated_at"), str) else project.get("updated_at", datetime.now()).isoformat()
                    }
                else:
                    raise HTTPException(status_code=404, detail="Project not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    def delete_project(self, project_id: str) -> dict:
        """Delete a project and all related files"""
        if not self.driver:
            raise HTTPException(status_code=404, detail="Project not found")
        
        try:
            with self.driver.session() as session:
                # Get file paths to delete from filesystem
                result = session.run(
                    """
                    MATCH (p:Project {id: $id})-[:HAS_FILE]->(f:File)
                    RETURN f.path as path
                    """,
                    id=project_id
                )
                file_paths = [record["path"] for record in result]
                
                # Delete files from filesystem
                for file_path in file_paths:
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        print(f"Warning: Failed to delete file {file_path}: {e}")
                
                # Delete project and related files from database
                session.run(
                    """
                    MATCH (p:Project {id: $id})
                    DETACH DELETE p
                    """,
                    id=project_id
                )
                
                return {"message": "Project deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    def add_files_to_project(self, project_id: str, files: List[UploadFile]) -> dict:
        """Add files to a project"""
        if not self.driver:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Check if project exists
        project = self.get_project(project_id)
        
        # Create project directory if it doesn't exist
        project_dir = Path(f"data/projects/{project_id}")
        project_dir.mkdir(parents=True, exist_ok=True)
        
        added_files = []
        added_count = 0
        
        try:
            for file in files:
                # Save file to disk
                file_id = str(uuid.uuid4())
                file_extension = Path(file.filename).suffix
                file_path = project_dir / f"{file_id}{file_extension}"
                
                # Read file content
                content = file.file.read()
                file.file.seek(0)  # Reset file pointer
                
                # Save file
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # Detect file type
                file_type = self.detect_file_type(file.filename, content)
                
                # Add file to database
                with self.driver.session() as session:
                    session.run(
                        """
                        MATCH (p:Project {id: $project_id})
                        CREATE (p)-[:HAS_FILE]->(f:File {
                            id: $id,
                            name: $name,
                            path: $path,
                            size: $size,
                            type: $type,
                            uploaded_at: datetime()
                        })
                        """,
                        project_id=project_id,
                        id=file_id,
                        name=file.filename,
                        path=str(file_path),
                        size=len(content),
                        type=file_type
                    )
                
                added_files.append({
                    "id": file_id,
                    "name": file.filename,
                    "path": str(file_path),
                    "size": len(content),
                    "type": file_type
                })
                added_count += 1
            
            # Update project files count
            with self.driver.session() as session:
                session.run(
                    """
                    MATCH (p:Project {id: $id})
                    SET p.files_count = p.files_count + $count,
                        p.updated_at = datetime()
                    """,
                    id=project_id,
                    count=added_count
                )
            
            return {
                "added": added_count,
                "files": added_files
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add files: {str(e)}")
    
    def get_project_files(self, project_id: str) -> List[dict]:
        """Get all files for a project"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (p:Project {id: $id})-[:HAS_FILE]->(f:File)
                    RETURN f
                    ORDER BY f.uploaded_at DESC
                    """,
                    id=project_id
                )
                files = []
                for record in result:
                    file = dict(record["f"])
                    files.append({
                        "id": file["id"],
                        "name": file["name"],
                        "path": file["path"],
                        "size": file["size"],
                        "type": file["type"],
                        "uploaded_at": file["uploaded_at"].isoformat() if "uploaded_at" in file else ""
                    })
                return files
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    def scan_project_files(self, project_id: str) -> dict:
        """Scan project files and categorize them"""
        files = self.get_project_files(project_id)
        
        smeta_paths = []
        rd_paths = []
        graphs_paths = []
        
        for file in files:
            if file["type"] == "smeta":
                smeta_paths.append(file["path"])
            elif file["type"] == "rd":
                rd_paths.append(file["path"])
            elif file["type"] == "graphs":
                graphs_paths.append(file["path"])
        
        return {
            "files_count": len(files),
            "smeta_count": len(smeta_paths),
            "rd_count": len(rd_paths),
            "graphs_count": len(graphs_paths),
            "smeta_paths": smeta_paths,
            "rd_paths": rd_paths
        }
    
    def scan_directory_for_project(self, project_id: str, directory_path: str) -> dict:
        """Scan a directory and add relevant files to project"""
        if not os.path.exists(directory_path):
            raise HTTPException(status_code=404, detail="Directory not found")
        
        # Supported file extensions
        smeta_extensions = ['.xlsx', '.xls']
        rd_extensions = ['.pdf']
        graphs_extensions = ['.mpp', '.gantt']
        
        # Scan directory for files
        found_files = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory_path)
                
                # Determine file type based on extension and content
                file_type = "other"
                file_extension = Path(file).suffix.lower()
                
                if file_extension in smeta_extensions:
                    # Check if it's actually a smeta file by looking at content
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read(1024)  # Read first 1KB
                            if b'\xd0\xb3\xd1\x8d\xd1\x81\xd0\xbd' in content.lower():  # 'гэсн' in UTF-8 bytes
                                file_type = "smeta"
                            else:
                                file_type = "smeta"  # Default to smeta for Excel files
                    except:
                        file_type = "smeta"  # Default to smeta for Excel files
                        
                elif file_extension in rd_extensions:
                    # Check if it's actually an RD file by looking at content
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read(1024)  # Read first 1KB
                            if b'\xd1\x80\xd0\xb4' in content.lower():  # 'рд' in UTF-8 bytes
                                file_type = "rd"
                            else:
                                file_type = "rd"  # Default to rd for PDF files
                    except:
                        file_type = "rd"  # Default to rd for PDF files
                        
                elif file_extension in graphs_extensions:
                    file_type = "graphs"
                
                found_files.append({
                    "name": file,
                    "path": file_path,
                    "relative_path": relative_path,
                    "type": file_type,
                    "size": os.path.getsize(file_path)
                })
        
        # Add found files to project
        added_count = 0
        added_files = []
        
        # Create project directory if it doesn't exist
        project_dir = Path(f"data/projects/{project_id}")
        project_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            for file_info in found_files:
                # Copy file to project directory
                file_id = str(uuid.uuid4())
                file_extension = Path(file_info["name"]).suffix
                destination_path = project_dir / f"{file_id}{file_extension}"
                
                shutil.copy2(file_info["path"], destination_path)
                
                # Add file to database
                with self.driver.session() as session:
                    session.run(
                        """
                        MATCH (p:Project {id: $project_id})
                        CREATE (p)-[:HAS_FILE]->(f:File {
                            id: $id,
                            name: $name,
                            path: $path,
                            size: $size,
                            type: $type,
                            uploaded_at: datetime()
                        })
                        """,
                        project_id=project_id,
                        id=file_id,
                        name=file_info["name"],
                        path=str(destination_path),
                        size=file_info["size"],
                        type=file_info["type"]
                    )
                
                added_files.append({
                    "id": file_id,
                    "name": file_info["name"],
                    "path": str(destination_path),
                    "size": file_info["size"],
                    "type": file_info["type"]
                })
                added_count += 1
            
            # Update project files count
            with self.driver.session() as session:
                session.run(
                    """
                    MATCH (p:Project {id: $id})
                    SET p.files_count = p.files_count + $count,
                        p.updated_at = datetime()
                    """,
                    id=project_id,
                    count=added_count
                )
            
            # Categorize added files
            smeta_paths = [f["path"] for f in added_files if f["type"] == "smeta"]
            rd_paths = [f["path"] for f in added_files if f["type"] == "rd"]
            graphs_paths = [f["path"] for f in added_files if f["type"] == "graphs"]
            
            return {
                "added": added_count,
                "files": added_files,
                "files_count": added_count,
                "smeta_count": len(smeta_paths),
                "rd_count": len(rd_paths),
                "graphs_count": len(graphs_paths),
                "smeta_paths": smeta_paths,
                "rd_paths": rd_paths
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add files from directory: {str(e)}")
    
    def delete_project_file(self, project_id: str, file_id: str) -> dict:
        """Delete a file from a project"""
        if not self.driver:
            raise HTTPException(status_code=404, detail="File not found")
        
        try:
            with self.driver.session() as session:
                # Get file path to delete from filesystem
                result = session.run(
                    """
                    MATCH (p:Project {id: $project_id})-[:HAS_FILE]->(f:File {id: $file_id})
                    RETURN f.path as path
                    """,
                    project_id=project_id,
                    file_id=file_id
                )
                record = result.single()
                if not record:
                    raise HTTPException(status_code=404, detail="File not found")
                
                file_path = record["path"]
                
                # Delete file from filesystem
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Warning: Failed to delete file {file_path}: {e}")
                
                # Delete file from database
                session.run(
                    """
                    MATCH (p:Project {id: $project_id})-[:HAS_FILE]->(f:File {id: $file_id})
                    DELETE f
                    """,
                    project_id=project_id,
                    file_id=file_id
                )
                
                # Update project files count
                session.run(
                    """
                    MATCH (p:Project {id: $project_id})
                    SET p.files_count = p.files_count - 1,
                        p.updated_at = datetime()
                    """,
                    project_id=project_id
                )
                
                return {"message": "File deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    def save_project_result(self, project_id: str, result_type: str, data: Dict[Any, Any]) -> Dict[Any, Any]:
        """Save a result to a project"""
        if not self.driver:
            raise HTTPException(status_code=500, detail="Database not available")
        
        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (p:Project {id: $project_id})
                    CREATE (p)-[:HAS_RESULT]->(r:Result {
                        id: randomUUID(),
                        type: $type,
                        data: $data,
                        created_at: datetime()
                    })
                    RETURN r
                    """,
                    project_id=project_id,
                    type=result_type,
                    data=json.dumps(data, ensure_ascii=False)
                )
                record = result.single()
                if record:
                    result_node = dict(record["r"])
                    return {
                        "id": result_node["id"],
                        "type": result_node["type"],
                        "data": json.loads(result_node["data"]),
                        "created_at": result_node["created_at"].isoformat()
                    }
                else:
                    raise HTTPException(status_code=500, detail="Failed to save result")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    def get_project_results(self, project_id: str) -> List[Dict[Any, Any]]:
        """Get all results for a project"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (p:Project {id: $project_id})-[:HAS_RESULT]->(r:Result)
                    RETURN r
                    ORDER BY r.created_at DESC
                    """,
                    project_id=project_id
                )
                results = []
                for record in result:
                    result_node = dict(record["r"])
                    results.append({
                        "id": result_node["id"],
                        "type": result_node["type"],
                        "data": json.loads(result_node["data"]),
                        "created_at": result_node["created_at"].isoformat()
                    })
                return results
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Initialize project manager
project_manager = ProjectManager()

# Create default templates on startup
template_manager.create_default_templates()

# API routes
@router.post("/", response_model=ProjectResponse)
async def create_project(project_data: ProjectCreate):
    """Create a new project"""
    return project_manager.create_project(project_data)

@router.get("/", response_model=List[ProjectResponse])
async def get_projects():
    """Get all projects"""
    return project_manager.get_projects()

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get a specific project"""
    return project_manager.get_project(project_id)

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, project_data: ProjectUpdate):
    """Update a project"""
    return project_manager.update_project(project_id, project_data)

@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    return project_manager.delete_project(project_id)

@router.post("/{project_id}/files")
async def add_files_to_project(project_id: str, files: List[UploadFile] = File(...)):
    """Add files to a project"""
    return project_manager.add_files_to_project(project_id, files)

@router.get("/{project_id}/files")
async def get_project_files(project_id: str):
    """Get all files for a project"""
    return project_manager.get_project_files(project_id)

@router.get("/{project_id}/scan")
async def scan_project_files(project_id: str):
    """Scan project files and categorize them"""
    return project_manager.scan_project_files(project_id)

@router.delete("/{project_id}/files/{file_id}")
async def delete_project_file(project_id: str, file_id: str):
    """Delete a file from a project"""
    return project_manager.delete_project_file(project_id, file_id)

@router.post("/{project_id}/scan-directory")
async def scan_directory_for_project(project_id: str, directory_path: str = Form(...)):
    """Scan a directory and add relevant files to project"""
    return project_manager.scan_directory_for_project(project_id, directory_path)

@router.post("/{project_id}/results", response_model=ProjectResult)
async def save_project_result(project_id: str, result_data: ResultCreate):
    """Save a result to a project"""
    return project_manager.save_project_result(project_id, result_data.type, result_data.data)

@router.get("/{project_id}/results", response_model=List[ProjectResult])
async def get_project_results(project_id: str):
    """Get all results for a project"""
    return project_manager.get_project_results(project_id)


# Template management endpoints
@router.get("/templates", response_model=List[TemplateResponse])
async def get_templates(category: Optional[str] = None):
    """Get all templates or templates by category"""
    return template_manager.get_templates(category)


@router.post("/templates", response_model=TemplateResponse)
async def create_template(template_data: TemplateCreate):
    """Create a new template"""
    return template_manager.create_template(template_data.dict())


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(template_id: str, template_data: TemplateUpdate):
    """Update an existing template"""
    return template_manager.update_template(template_id, template_data.dict())


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """Delete a template"""
    return template_manager.delete_template(template_id)
