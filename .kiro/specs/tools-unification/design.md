# Design Document - Tools System Unification

## Overview

This design document outlines the unified architecture for Bldr Empire v2's 47+ construction tools. The system will provide a consistent, flexible interface using **kwargs for parameter passing, standardized response formats, and automatic tool discovery while maintaining backward compatibility.

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Bldr Empire v2 Core                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   LM Studio     │  │ Multi-Agent     │  │  Frontend   │ │
│  │   (Models)      │  │   System        │  │  Dashboard  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Unified Tools System                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              UnifiedToolsManager                        │ │
│  │  • execute_tool(name: str, **kwargs)                   │ │
│  │  • discover_tools() -> List[ToolInfo]                  │ │
│  │  • get_tool_docs(name: str) -> ToolDocs               │ │
│  └─────────────────────────────────────────────────────────┘ │
│                              │                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Tool Categories                            │ │
│  │                                                         │ │
│  │  Core RAG & Analysis (8 tools)                        │ │
│  │  ├─ search_rag_database                               │ │
│  │  ├─ analyze_image                                     │ │
│  │  ├─ check_normative                                   │ │
│  │  └─ semantic_parse                                    │ │
│  │                                                         │ │
│  │  Financial & Estimates (12 tools)                     │ │
│  │  ├─ calculate_estimate                                │ │
│  │  ├─ auto_budget                                       │ │
│  │  ├─ calculate_financial_metrics                       │ │
│  │  └─ parse_gesn_estimate                              │ │
│  │                                                         │ │
│  │  Project Management (10 tools)                        │ │
│  │  ├─ generate_construction_schedule                    │ │
│  │  ├─ create_gantt_chart                               │ │
│  │  ├─ calculate_critical_path                           │ │
│  │  └─ monte_carlo_sim                                   │ │
│  │                                                         │ │
│  │  Document Generation (8 tools)                        │ │
│  │  ├─ generate_letter                                   │ │
│  │  ├─ improve_letter                                    │ │
│  │  ├─ generate_ppr                                      │ │
│  │  └─ create_document                                   │ │
│  │                                                         │ │
│  │  Advanced Analysis (9 tools)                          │ │
│  │  ├─ analyze_tender                                    │ │
│  │  ├─ comprehensive_analysis                            │ │
│  │  ├─ analyze_bentley_model                            │ │
│  │  └─ enterprise_rag_trainer (training tool)           │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Tool Classification by UI Placement

**Dashboard Tiles (High-Impact Daily Tools):**
- generate_letter + improve_letter
- analyze_tender + comprehensive_analysis  
- calculate_estimate + auto_budget
- analyze_image
- generate_construction_schedule
- parse_gesn_estimate

**Tools Tab (Professional Tools):**
- search_rag_database + check_normative
- calculate_financial_metrics
- create_gantt_chart + calculate_critical_path
- generate_ppr + create_gpp
- analyze_bentley_model + autocad_export
- monte_carlo_sim

**Service Tools (Hidden from UI):**
- semantic_parse
- extract_text_from_pdf
- extract_works_nlp
- extract_construction_data
- enterprise_rag_trainer (accessible via special interface)

## Components and Interfaces

### 1. UnifiedToolsManager

```python
class UnifiedToolsManager:
    """Central manager for all 47+ construction tools"""
    
    def __init__(self):
        self.tools_registry: Dict[str, ToolInfo] = {}
        self.executor = EnhancedToolExecutor()
        self.response_formatter = ResponseFormatter()
    
    def execute_tool(self, tool_name: str, **kwargs) -> StandardResponse:
        """Execute any tool with flexible kwargs"""
        
    def discover_tools(self) -> List[ToolInfo]:
        """Auto-discover all available tools"""
        
    def get_tool_docs(self, tool_name: str) -> ToolDocs:
        """Get documentation for specific tool"""
        
    def register_tool(self, tool_info: ToolInfo):
        """Register new tool in the system"""
```

### 2. StandardResponse Format

```python
class StandardResponse(BaseModel):
    """Unified response format for all tools"""
    status: Literal["success", "error", "warning"]
    data: Optional[Dict[str, Any]] = None
    files: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    tool_name: str
    timestamp: datetime
```

### 3. ToolInfo Schema

```python
class ToolInfo(BaseModel):
    """Tool registration information"""
    name: str
    category: str
    description: str
    parameters: Dict[str, ParameterInfo]
    ui_placement: Literal["dashboard", "tools", "service"]
    priority: int
    dependencies: List[str]
    examples: List[Dict[str, Any]]
```

### 4. Parameter Handling

```python
class FlexibleParameterHandler:
    """Handle **kwargs with validation and defaults"""
    
    def process_kwargs(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Process and validate kwargs for specific tool"""
        # Remove None values
        # Apply defaults for missing optional parameters
        # Validate required parameters
        # Convert data types if needed
        
    def get_required_params(self, tool_name: str) -> List[str]:
        """Get list of required parameters for tool"""
        
    def get_optional_params(self, tool_name: str) -> Dict[str, Any]:
        """Get optional parameters with defaults"""
```

## Data Models

### Tool Registry Structure

```python
TOOLS_REGISTRY = {
    "search_rag_database": {
        "category": "core_rag",
        "ui_placement": "tools",
        "priority": 10,
        "required_params": ["query"],
        "optional_params": {
            "doc_types": ["norms"],
            "k": 5,
            "use_sbert": False
        }
    },
    "generate_letter": {
        "category": "document_generation", 
        "ui_placement": "dashboard",
        "priority": 9,
        "required_params": ["description"],
        "optional_params": {
            "template_id": "compliance_sp31",
            "tone": 0.0,
            "formality": "formal"
        }
    },
    "enterprise_rag_trainer": {
        "category": "advanced_analysis",
        "ui_placement": "service",
        "priority": 5,
        "required_params": [],
        "optional_params": {
            "custom_dir": None,
            "fast_mode": False
        }
    }
}
```

### Response Standardization

All tools will return responses in this format:

```python
# Success Response
{
    "status": "success",
    "data": {
        "results": [...],
        "summary": "...",
        "confidence": 0.95
    },
    "files": ["report.pdf", "analysis.xlsx"],
    "metadata": {
        "processing_time": 2.3,
        "model_used": "sbert_large_nlu_ru",
        "parameters_used": {...}
    },
    "tool_name": "analyze_tender",
    "timestamp": "2025-01-18T10:30:00Z"
}

# Error Response  
{
    "status": "error",
    "error": "Missing required parameter 'query'",
    "metadata": {
        "error_category": "validation",
        "suggestions": "Provide a search query string"
    },
    "tool_name": "search_rag_database", 
    "timestamp": "2025-01-18T10:30:00Z"
}
```

## Error Handling

### Error Categories and Responses

1. **Validation Errors**: Missing/invalid parameters
2. **Processing Errors**: Tool execution failures  
3. **Dependency Errors**: Missing libraries/services
4. **Network Errors**: External service failures
5. **Resource Errors**: Memory/disk space issues

### Retry Strategy

```python
class RetryStrategy:
    """Intelligent retry logic for different error types"""
    
    RETRY_CONFIG = {
        "network": {"max_retries": 3, "backoff": "exponential"},
        "processing": {"max_retries": 2, "backoff": "linear"},
        "validation": {"max_retries": 0, "backoff": None},
        "dependency": {"max_retries": 1, "backoff": None}
    }
```

## Testing Strategy

### Unit Tests
- Parameter validation for all 47+ tools
- Response format standardization
- Error handling scenarios
- **kwargs processing logic

### Integration Tests  
- Tool discovery and registration
- Cross-tool data flow
- API endpoint consistency
- Frontend integration

### Performance Tests
- Tool execution speed benchmarks
- Memory usage optimization
- Concurrent tool execution
- Large dataset processing

### End-to-End Tests
- Complete workflow scenarios
- Multi-tool task chains
- Error recovery testing
- User interface integration

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)
1. Create UnifiedToolsManager class
2. Implement StandardResponse format
3. Build FlexibleParameterHandler
4. Set up tool registry system

### Phase 2: Tool Migration (Week 2)  
1. Migrate core RAG tools (8 tools)
2. Migrate financial tools (12 tools)
3. Migrate project management tools (10 tools)
4. Update all tool signatures to use **kwargs

### Phase 3: Advanced Features (Week 3)
1. Implement auto-discovery system
2. Add comprehensive error handling
3. Build retry and fallback mechanisms
4. Create tool documentation system

### Phase 4: Integration & Testing (Week 4)
1. Update API endpoints
2. Integrate with frontend
3. Comprehensive testing
4. Performance optimization

This design ensures that Enterprise RAG Trainer is properly positioned as one of the 47+ tools rather than the system coordinator, while providing a flexible, maintainable architecture for all construction tools.