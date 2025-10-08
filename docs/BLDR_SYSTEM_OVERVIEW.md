# Bldr System Overview - Context Reminder

## Core Vision
Bldr is an AI-powered system designed to replace the head office of a large construction company in Russia, initially focusing on industrial construction with future expansion to civil construction.

## Key Objectives
1. **Complete Construction Office Replacement** - Online application with unified access to all documentation
2. **Smart Construction Chatbot** - NTD-based Q&A with document processing capabilities
3. **Automation Toolkit** - Set of tools for routine automation

## System Components
- Online application with authentication and role-based access
- Telegram bot interface
- Future mobile app support
- Document management (projects, contracts, estimates, letters, etc.)
- NTD (Нормативно-Техническая Документация) processing module
- RAG system with Qdrant and Neo4j storage via Docker

## Target Users
- Head office employees from accountant to CEO
- All intermediate positions

## Current Architecture
- Python backend with FastAPI
- React frontend
- Docker containers for databases
- LM Studio for local LLM hosting
- Tools system with Pydantic manifests
- RAG trainer for NTD processing

## Roles
- Admin (full access)
- User (standard access)
- Future role expansion planned

## Current Status
- MVP architecture exists
- Bot functional but LLM responses need improvement
- Hosted locally with future self-hosting planned

## Key Technologies
- Python, FastAPI, React
- Qdrant, Neo4j, Docker
- LM Studio, SBERT
- OpenPyXL, PyPDF2, docx

This file serves as context reminder for future conversations about the Bldr system.