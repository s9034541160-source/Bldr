# Implementation Plan - Tools System Unification

## Task Overview

Convert the existing fragmented tools system into a unified, **kwargs-based architecture with standardized responses and automatic tool discovery for all 47+ construction tools.

- [x] 1. Create Core Infrastructure Components



  - Implement UnifiedToolsManager class with tool registry and execution engine
  - Build StandardResponse format and FlexibleParameterHandler for **kwargs processing
  - Set up automatic tool discovery system with categorization
  - _Requirements: 1.1, 2.1, 3.1, 4.1_

- [x] 2. Implement Unified Tool Execution System



  - [x] 2.1 Create UnifiedToolsManager class


    - Build central tool registry with ToolInfo schema
    - Implement execute_tool method with **kwargs support
    - Add tool discovery and documentation methods
    - _Requirements: 1.1, 4.1_

  - [x] 2.2 Build StandardResponse formatter

    - Create StandardResponse BaseModel with consistent fields
    - Implement response formatting for success/error cases
    - Add metadata tracking and execution timing
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 2.3 Implement FlexibleParameterHandler

    - Build **kwargs processing with None value filtering
    - Add parameter validation for required/optional params
    - Implement default value application and type conversion
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Migrate Core RAG & Analysis Tools (8 tools)



  - [x] 3.1 Update search_rag_database tool

    - Convert to **kwargs parameter handling
    - Standardize response format with metadata
    - Add SBERT/Nomic embedding model selection
    - _Requirements: 1.2, 2.1, 3.1_

  - [x] 3.2 Update analyze_image tool

    - Implement **kwargs for image_path, analysis_type parameters
    - Standardize OCR/object detection response format
    - Add error handling for missing image libraries
    - _Requirements: 1.2, 2.2, 5.1_

  - [x] 3.3 Update check_normative tool

    - Convert normative_code parameter to **kwargs
    - Standardize compliance checking response format
    - Add confidence scoring and violation detection
    - _Requirements: 1.2, 2.1_

  - [x] 3.4 Update semantic_parse tool

    - Implement **kwargs for text, task, labels parameters
    - Standardize NLP parsing response with confidence scores
    - Add SBERT model integration for Russian text
    - _Requirements: 1.2, 2.1_

- [ ] 4. Migrate Financial & Estimates Tools (12 tools)
  - [ ] 4.1 Update calculate_estimate tool
    - Convert to **kwargs for rate_code, region, quantity
    - Standardize GESN/FER calculation response format
    - Add regional coefficient handling
    - _Requirements: 1.2, 2.1_

  - [ ] 4.2 Update auto_budget tool
    - Implement **kwargs for estimate_data parameter
    - Standardize budget generation response with Excel export
    - Add project integration for data loading
    - _Requirements: 1.2, 2.4_

  - [ ] 4.3 Update calculate_financial_metrics tool
    - Convert to **kwargs for metric type and financial data
    - Standardize ROI/NPV/IRR calculation responses
    - Add real formula implementations with validation
    - _Requirements: 1.2, 2.1_

  - [ ] 4.4 Update parse_gesn_estimate tool
    - Implement **kwargs for estimate_file parameter
    - Standardize estimate parsing response format
    - Add batch processing capabilities
    - _Requirements: 1.2, 2.4_

- [ ] 5. Migrate Project Management Tools (10 tools)
  - [ ] 5.1 Update generate_construction_schedule tool
    - Convert to **kwargs for works and constraints
    - Standardize schedule generation with Gantt JSON output
    - Add NetworkX critical path calculation
    - _Requirements: 1.2, 2.1_

  - [ ] 5.2 Update create_gantt_chart tool
    - Implement **kwargs for tasks and timeline data
    - Standardize Gantt chart response with interactive format
    - Add dependency management and resource allocation
    - _Requirements: 1.2, 2.1_

  - [ ] 5.3 Update monte_carlo_sim tool
    - Convert to **kwargs for project_data parameter
    - Standardize risk analysis response with probability distributions
    - Add scenario generation and confidence intervals
    - _Requirements: 1.2, 2.1_

- [ ] 6. Migrate Document Generation Tools (8 tools)
  - [ ] 6.1 Update generate_letter tool
    - Convert to **kwargs for description, template_id, parameters
    - Standardize letter generation with LM Studio integration
    - Add project data auto-loading and template management
    - _Requirements: 1.2, 2.4_

  - [ ] 6.2 Update improve_letter tool
    - Implement **kwargs for draft text and improvement parameters
    - Standardize letter improvement response format
    - Add tone/formality adjustment capabilities
    - _Requirements: 1.2, 2.1_

  - [ ] 6.3 Update generate_ppr tool
    - Convert to **kwargs for project_data parameter
    - Standardize PPR generation response with document export
    - Add work sequence integration and template selection
    - _Requirements: 1.2, 2.4_

  - [ ] 6.4 Update create_document tool
    - Implement **kwargs for template and data parameters
    - Standardize document creation with DOCX/PDF export
    - Add template management and data validation
    - _Requirements: 1.2, 2.4_

- [ ] 7. Migrate Advanced Analysis Tools (9 tools)
  - [ ] 7.1 Update analyze_tender tool
    - Convert to **kwargs for tender_data parameter
    - Standardize tender analysis response with risk assessment
    - Add compliance checking and cost analysis
    - _Requirements: 1.2, 2.1_

  - [ ] 7.2 Update comprehensive_analysis tool
    - Implement **kwargs for analysis scope and data
    - Standardize comprehensive analysis pipeline response
    - Add multi-tool coordination and result aggregation
    - _Requirements: 1.2, 2.1_

  - [ ] 7.3 Update analyze_bentley_model tool
    - Convert to **kwargs for IFC file path and analysis type
    - Standardize BIM model analysis response format
    - Add IFC element extraction and property analysis
    - _Requirements: 1.2, 2.1_

  - [ ] 7.4 Update enterprise_rag_trainer tool
    - Implement **kwargs for training parameters (custom_dir, fast_mode)
    - Standardize RAG training response with progress tracking
    - Add WebSocket integration for real-time updates
    - _Requirements: 1.2, 2.1_

- [ ] 8. Implement Enhanced Error Handling System
  - [ ] 8.1 Create error categorization system
    - Build error category detection (validation, processing, network, dependency)
    - Implement category-specific error messages and suggestions
    - Add error logging with detailed context information
    - _Requirements: 5.1, 5.2_

  - [ ] 8.2 Build retry mechanism with exponential backoff
    - Implement retry logic for network and processing errors
    - Add exponential backoff for network failures
    - Create retry configuration per error category
    - _Requirements: 5.1, 5.3_

  - [ ] 8.3 Add dependency checking and guidance
    - Implement missing dependency detection
    - Add installation guidance for missing libraries
    - Create fallback mechanisms for optional dependencies
    - _Requirements: 5.4_

- [ ] 9. Create Tool Discovery and Documentation System
  - [ ] 9.1 Implement automatic tool discovery
    - Build tool scanning and registration system
    - Add category-based tool organization
    - Implement priority-based tool loading
    - _Requirements: 4.1, 4.3_

  - [ ] 9.2 Build tool documentation generator
    - Create parameter documentation extraction
    - Add usage examples and code snippets
    - Implement interactive API documentation
    - _Requirements: 4.2_

  - [ ] 9.3 Add tool capability querying
    - Implement tool feature and category queries
    - Add tool dependency and requirement checking
    - Create tool compatibility matrix
    - _Requirements: 4.3_

- [ ] 10. Update API Endpoints and Integration
  - [ ] 10.1 Update FastAPI endpoints for unified tools
    - Modify /tools/execute endpoint to use **kwargs
    - Add /tools/discover endpoint for tool listing
    - Implement /tools/docs/{tool_name} for documentation
    - _Requirements: 1.3, 4.1_

  - [ ] 10.2 Update coordinator agent integration
    - Modify CoordinatorAgent to use unified tool system
    - Update tool awareness and capability detection
    - Add dynamic tool discovery for plan generation
    - _Requirements: 1.1, 4.1_

  - [ ] 10.3 Add backward compatibility layer
    - Implement legacy parameter format conversion
    - Add deprecation warnings for old API usage
    - Create alias system for renamed tools
    - _Requirements: 7.1, 7.2, 7.4_

- [ ] 11. Implement Performance Optimizations
  - [ ] 11.1 Add tool execution caching
    - Implement result caching for expensive operations
    - Add cache invalidation and TTL management
    - Create cache size limits and cleanup strategies
    - _Requirements: 6.3, 6.4_

  - [ ] 11.2 Build parallel tool execution
    - Implement concurrent tool execution for independent tasks
    - Add resource management and throttling
    - Create execution queue and priority handling
    - _Requirements: 6.2_

  - [ ] 11.3 Optimize parameter validation
    - Implement fast parameter validation (<10ms)
    - Add parameter schema caching
    - Create validation result memoization
    - _Requirements: 6.1_

- [ ] 12. Create Comprehensive Testing Suite
  - [ ] 12.1 Build unit tests for all tools
    - Create parameter validation tests for 47+ tools
    - Add response format standardization tests
    - Implement error handling scenario tests
    - _Requirements: 1.4, 2.3, 5.2_

  - [ ] 12.2 Add integration tests
    - Create tool discovery and registration tests
    - Add cross-tool data flow validation
    - Implement API endpoint consistency tests
    - _Requirements: 4.1, 1.3_

  - [ ] 12.3 Build performance benchmarks
    - Create tool execution speed benchmarks
    - Add memory usage optimization tests
    - Implement concurrent execution performance tests
    - _Requirements: 6.1, 6.2_

- [x] 13. Update Frontend Integration



  - [x] 13.1 Update frontend API client

    - Modify API calls to use **kwargs format
    - Add standardized response handling
    - Implement error display and retry mechanisms
    - _Requirements: 2.1, 5.1_

  - [x] 13.2 Add tool discovery UI

    - Create dynamic tool listing from discovery API
    - Add tool documentation display
    - Implement tool category filtering and search
    - _Requirements: 4.1, 4.2_

  - [x] 13.3 Update dashboard and tools tabs

    - Implement dashboard tiles for high-impact tools
    - Add tools tab for professional tools
    - Hide service tools from user interface
    - _Requirements: UI placement from design_

- [x] 14. Final Integration and Deployment





  - [x] 14.1 Complete system integration testing

    - Test all 47+ tools with unified system
    - Validate multi-agent system integration
    - Verify WebSocket and Celery integration
    - _Requirements: All requirements_


  - [ ] 14.2 Performance optimization and cleanup
    - Optimize tool loading and execution performance
    - Clean up deprecated code and unused imports
    - Implement final error handling improvements
    - _Requirements: 6.1, 6.4_


  - [ ] 14.3 Documentation and deployment preparation
    - Create comprehensive system documentation
    - Add deployment guides and configuration
    - Prepare migration scripts for existing installations
    - _Requirements: 7.3_