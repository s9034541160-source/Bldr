# Russian Normative Technical Documentation (NTD) System Implementation

## Overview

This document describes the implementation of a comprehensive system for managing normative technical documentation (NTD) in the Russian construction industry and related fields. The system integrates with the existing 14-stage RAG training pipeline to provide automated validation, organization, and processing of normative documents.

## System Components

### 1. Normative Database (`ntd_full_db.json`)

A comprehensive database of Russian normative documents covering:
- **Construction** (СП, СНиП, ГОСТ)
- **Finance and Budget** (ФЗ, Postanovleniya)
- **Safety and Occupational Health** (ПБ, ОТ)
- **Environment** (Environmental regulations)
- **HR and Personnel** (ТК РФ, Минтруд приказы)
- **Procurement** (44-ФЗ, 223-ФЗ)
- **Contracts** (Договора)
- **Executive Documentation** (Исполнительная документация)
- **Materials Supply** (Материальное снабжение)
- **Accounting** (Бухгалтерский учет)

Each document entry includes:
- Digital code + full text name
- Year of introduction
- Status (mandatory/recommendatory/outdated (replaced, annulled))
- PDF link or source where documents can be downloaded for free

### 2. NTD Preprocessor (`ntd_preprocessor.py`)

The core component that integrates as Stage 0 in the RAG pipeline:

#### Key Functions:
1. **Document Actuality Checking** - Verify documents against the database
2. **Automatic Download** - Download actual versions if documents are outdated
3. **Intelligent File Renaming** - Rename files from generic names to descriptive names
4. **Folder Organization** - Automatically move files to appropriate category folders
5. **Duplicate Detection** - Prevent processing of duplicate documents
6. **Database Integration** - Mark processed documents in local database

### 3. RAG Pipeline Integration

The NTD system integrates as Stage 0 in the 14-stage RAG training pipeline:

```
Stage 0:  NTD Preprocessing (NEW) 🔧
Stage 1:  Initial validation
Stage 2:  Duplicate checking
Stage 3:  Text extraction
Stage 4:  Document type detection
Stage 5:  Structural analysis
Stage 6:  Extract work candidates
Stage 7:  Generate Rubern markup
Stage 8:  Metadata extraction
Stage 9:  Quality control
Stage 10: Type-specific processing
Stage 11: Work sequence extraction
Stage 12: Save work sequences
Stage 13: Smart chunking
Stage 14: Save to Qdrant/FAISS
```

## Implementation Details

### Database Structure

The system uses a JSON database (`ntd_full_db.json`) with the following structure:

```json
{
  "id": 1,
  "category": "construction",
  "code": "СП 20.13330.2016",
  "title": "Нагрузки и воздействия (обновлён СНиП 2.01.07-85)",
  "year": 2016,
  "status": "Обязательный",
  "pdf_url": "https://meganorm.ru/Data2/1/4293747/4293747667.pdf",
  "source_site": "meganorm.ru",
  "description": "Нагрузки, воздействия, сейсмика (актуал. СНиП 2.01.07-85)"
}
```

### Folder Structure

The system automatically creates an organized folder structure:

```
01. НТД/
├── 01. Строительство
├── 02. Финансы и бюджет
├── 03. Техника безопасности
├── 04. Экология
├── 05. HR и кадры
├── 06. Тендеры и закупки
├── 07. Договора
├── 08. Исполнительная документация
├── 09. Материальное снабжение
└── 10. Бухгалтерский учет
```

### File Processing Workflow

1. **Detection**: System identifies normative documents by file names or content patterns
2. **Validation**: Checks document actuality against the database
3. **Download**: Automatically downloads actual versions if needed
4. **Renaming**: Renames files with proper naming convention (e.g., "sp2309257.pdf" → "СП 45.13330.2017 Земляные работы.pdf")
5. **Organization**: Moves files to appropriate category folders
6. **Processing**: Continues with the standard 14-stage RAG pipeline

## Key Features

### Automated Document Processing
- **Actuality Checking**: Verify documents are current and not outdated
- **Smart Renaming**: Automatically rename files with proper codes and titles
- **Category Organization**: Sort documents into appropriate folders
- **Duplicate Prevention**: Avoid processing duplicate documents

### Integration Benefits
- **Seamless Pipeline Integration**: Works as Stage 0 in existing RAG pipeline
- **No Manual Intervention**: Fully automated processing
- **Industrial Grade**: No stubs, mocks, or TODO comments
- **Scalable**: Handles large volumes of normative documents

### Database Management
- **Comprehensive Coverage**: 40+ key normative documents across 10 categories
- **Regular Updates**: Database can be updated with new documents
- **Status Tracking**: Monitor document status (mandatory/recommendatory/outdated)
- **Source Tracking**: Keep track of PDF sources for downloads

## Usage Examples

### Example 1: Processing an Outdated Document
```
Input:  "sp24133302011.pdf" (outdated version)
Check:  Document is outdated, replaced by СП 24.13330.2021
Action: Download actual version from database URL
Rename: "СП 24.13330.2021 Промышленные сооружения.pdf"
Move:   To "01. НТД/01. Строительство/"
Process: Continue with RAG pipeline
```

### Example 2: Processing a Current Document
```
Input:  "sp20133302016.pdf" 
Check:  Document is current and mandatory
Rename: "СП 20.13330.2016 Нагрузки и воздействия.pdf"
Move:   To "01. НТД/01. Строительство/"
Process: Continue with RAG pipeline
```

## Technical Implementation

### Core Classes

#### `NormativeDatabase`
Manages the normative document database:
- Load documents from JSON
- Retrieve documents by code
- Search documents by query/category
- Check document actuality
- Track processed documents

#### `NormativeChecker`
Handles document validation and processing:
- Extract document information from files
- Check document actuality
- Download documents from URLs
- Process document files

#### `ntd_preprocess()`
Main processing function that integrates with RAG pipeline:
- Validate file existence and readability
- Extract content for analysis
- Check document actuality
- Download actual versions if needed
- Rename files with proper naming
- Move files to category folders
- Mark documents as processed

## Integration with RAG Pipeline

The NTD system integrates seamlessly with the existing BldrRAGTrainer:

1. **Stage 0 Addition**: New preprocessing stage added before existing pipeline
2. **Callback Updates**: All stage callbacks updated to reflect 15-stage pipeline
3. **File Path Management**: Processed file paths passed to subsequent stages
4. **Error Handling**: Robust error handling for all NTD operations

## Testing and Verification

The implementation includes comprehensive testing:
- Document loading and retrieval
- Database search functionality
- Actuality checking
- File processing workflow
- RAG pipeline integration

## Future Enhancements

1. **Database Expansion**: Add more normative documents to database
2. **Web Scraping**: Implement automated scraping of official sources
3. **Advanced Validation**: Enhanced document validation algorithms
4. **Performance Optimization**: Optimize processing for large document sets
5. **Monitoring**: Add monitoring and reporting capabilities

## Conclusion

This implementation provides a comprehensive solution for managing Russian normative technical documentation in construction and related fields. The system automates the entire process of document validation, organization, and preparation for RAG training, enabling efficient processing of normative documents without manual intervention.