# Project Integration Guide

This guide explains how to use the enhanced project management features and their integration with Pro-Tools in the Bldr Empire system.

## New Features

### 1. Enhanced Project Management
The Projects tab now includes full CRUD (Create, Read, Update, Delete) functionality:

- **Create Projects**: Add new projects with name, code, location, and status
- **Edit Projects**: Modify existing project details
- **Delete Projects**: Remove projects and all associated files
- **Project Details View**: Detailed view with tabs for project information and files

### 2. File Management
Each project can now manage files:

- **Attach Files**: Upload files directly to a project
- **File Categorization**: Automatic detection of file types (smeta, rd, graphs)
- **File Scanning**: Scan project files to identify document types
- **File Removal**: Delete individual files from projects

### 3. Pro-Tools Integration
All Pro-Tools now integrate with projects:

- **Project Selection**: Dropdown to select a project in each tool
- **Auto-loading**: Automatically load relevant files from selected projects
- **Result Saving**: Save tool results directly to projects
- **Data Pre-filling**: Pre-fill forms with data from project results

## How to Use

### Creating and Managing Projects

1. Navigate to the "Projects" tab
2. Click "Создать проект" to create a new project
3. Fill in project details (name, code, location, status)
4. Click a project to open its details view
5. Use the edit button to modify project details
6. Use the delete button to remove projects

### Attaching Files to Projects

1. Open a project's details view
2. Go to the "Файлы" tab
3. Click "Выбрать файлы" to select files from your computer
4. Click "Прикрепить файлы" to upload them to the project
5. Use "Сканировать проект" to categorize files

### Using Projects with Pro-Tools

1. Navigate to any Pro-Tool (Batch Estimate, Budget, Tender Analysis, etc.)
2. Select a project from the "Проект" dropdown
3. The tool will automatically load relevant files from the project
4. Run the tool as usual
5. Click "Сохранить в проект" to save results to the project

## File Type Detection

The system automatically detects file types based on:

- **Smeta files**: Excel files (.xlsx, .xls) containing "ГЭСН" 
- **RD files**: PDF files (.pdf) containing "РД"
- **Graph files**: Microsoft Project files (.mpp) or Gantt files

## API Endpoints

The enhanced project system uses the following API endpoints:

- `POST /projects` - Create a new project
- `GET /projects` - List all projects
- `GET /projects/{id}` - Get a specific project
- `PUT /projects/{id}` - Update a project
- `DELETE /projects/{id}` - Delete a project
- `POST /projects/{id}/files` - Add files to a project
- `GET /projects/{id}/files` - Get project files
- `DELETE /projects/{id}/files/{file_id}` - Delete a file from a project
- `GET /projects/{id}/scan` - Scan and categorize project files
- `POST /projects/{id}/results` - Save tool results to a project
- `GET /projects/{id}/results` - Get project results

## Technical Implementation

### Frontend Components

- **Projects.tsx**: Enhanced with edit/delete functionality and file management
- **ProFeatures.tsx**: Integrated with project selection and auto-loading

### Backend Services

- **projects_api.py**: Full CRUD implementation with Neo4j integration
- **API service**: Extended with project file and result management methods

## Testing

Run the integration tests with:

```bash
python tests/project_integration_test.py
```

## Requirements

- Neo4j database (for project data storage)
- File system access (for file storage)