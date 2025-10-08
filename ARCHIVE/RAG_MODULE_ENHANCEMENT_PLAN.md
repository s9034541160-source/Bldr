# RAG Module Enhancement Plan

## Current State Analysis
The current RAG Module (`RAGModule.tsx`) is a very basic chat interface with WebSocket connectivity. It lacks the comprehensive features expected for a RAG system management interface.

## User Requirements
As expressed by the user, the RAG Module should include:
1. Detailed information about documents the system is trained on
2. Summary information about the NTD (НТД) database
3. List of NTD documents with statuses
4. Integration with existing File Manager and DB Tools functionality

## Proposed Enhancements

### 1. Enhanced RAG Dashboard
- **Training Status Panel**: Show current training progress, last training date, and document count
- **Document Statistics**: Pie chart showing document type distribution
- **Performance Metrics**: NDCG, coverage, confidence, and violation metrics
- **Database Summary**: Total chunks, indexed documents, and storage usage

### 2. Document Management Section
- **Trained Documents List**: Table showing all documents with:
  - Document name/path
  - Type (norms, PPR, estimates, RD)
  - Status (trained, pending, error)
  - Last trained date
  - Size and chunk count
- **Filtering and Search**: By type, status, and name
- **Actions**: Re-train, view details, remove from training

### 3. NTD Database Integration
- **NTD Summary Panel**: 
  - Total NTD documents
  - Actual vs Outdated vs Pending counts
  - Last update date
- **NTD Document List**:
  - Name and category
  - Status (actual, outdated, pending)
  - Source and last check date
  - Violations count

### 4. Training Controls
- **Folder Selection**: Integration with File Manager for training folder selection
- **Training Progress**: Real-time progress tracking with WebSocket
- **Training History**: List of past training sessions with dates and results

### 5. Query Interface
- **Enhanced Query Input**: With category filtering and k-value selection
- **Query History**: List of recent queries with results
- **Result Visualization**: Better display of retrieved chunks with metadata

## Implementation Steps

### Step 1: Backend API Enhancement
- Ensure all necessary endpoints exist for RAG data retrieval
- Add endpoints for document management if needed
- Implement proper error handling and data validation

### Step 2: Frontend Component Development
- Create new RAGModule component with tabs for different sections
- Implement data fetching with TanStack Query
- Add proper loading and error states
- Integrate with existing WebSocket for real-time updates

### Step 3: UI/UX Design
- Use Ant Design components for consistent look and feel
- Implement responsive design for different screen sizes
- Add proper data visualization components (charts, tables)
- Ensure accessibility standards

### Step 4: Integration Testing
- Test all new functionality with real data
- Verify WebSocket connections and real-time updates
- Test error scenarios and edge cases
- Validate performance with large datasets

## Technical Considerations

### Performance
- Implement pagination for large document lists
- Use caching for frequently accessed data
- Optimize WebSocket usage to avoid unnecessary updates

### Security
- Ensure all API calls are properly authenticated
- Validate user permissions for document management actions
- Sanitize user inputs to prevent injection attacks

### Scalability
- Design components to handle growing document collections
- Implement efficient data fetching strategies
- Consider virtualization for large lists

## File Structure
```
src/
├── components/
│   ├── RAGModule/
│   │   ├── index.tsx          # Main RAG Module component
│   │   ├── Dashboard.tsx      # RAG Dashboard with metrics
│   │   ├── Documents.tsx      # Document management
│   │   ├── NTDList.tsx        # NTD database integration
│   │   ├── Training.tsx       # Training controls and history
│   │   ├── QueryInterface.tsx # Enhanced query interface
│   │   └── types.ts           # TypeScript types
│   └── RAGModule.tsx          # Current component (to be replaced)
└── services/
    └── ragApi.ts              # RAG-specific API functions
```

## Dependencies
- Ant Design for UI components
- TanStack Query for data fetching
- Recharts for data visualization
- Existing WebSocket hook
- Existing API service

## Timeline
1. **Day 1**: Backend API review and enhancement
2. **Day 2-3**: Frontend component development
3. **Day 4**: UI/UX refinement
4. **Day 5**: Integration testing and documentation

## Success Criteria
- User can view detailed information about trained documents
- NTD database information is clearly displayed with status indicators
- Training controls are intuitive and functional
- Performance is acceptable with large document collections
- All functionality is properly tested and documented