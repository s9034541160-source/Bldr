# Bldr Empire v2 Dashboard

## Overview

This is the frontend dashboard for Bldr Empire v2, a comprehensive construction project management system with AI-powered tools.

## Features Implemented

1. **Authentication System**
   - Login/logout functionality
   - Role-based access control
   - User session management

2. **Project Management**
   - Create, read, update, delete projects
   - Project details view
   - File attachment capabilities

3. **Task Queue Management**
   - Real-time task monitoring
   - Task retry and cancellation
   - Priority adjustment

4. **Settings Configuration**
   - API/Database settings
   - RAG parameters
   - LLM configuration
   - Tool settings
   - UI preferences (dark/light theme)

5. **Responsive Design**
   - Sidebar navigation
   - Mobile-friendly layout
   - Theme switching (light/dark)

## Technology Stack

- React 18
- TypeScript
- Vite
- Ant Design 5
- Zustand (State Management)
- React Router
- TanStack Query
- Socket.IO (Real-time updates)
- Zod (Validation)

## Architecture

The dashboard follows a component-based architecture with centralized state management using Zustand.

### Key Components

- `App.tsx` - Main application layout
- `AuthHeader.tsx` - Authentication and theme controls
- `Projects.tsx` - Project management interface
- `Queue.tsx` - Task queue monitoring
- `Settings.tsx` - Configuration panel
- Existing components (ControlPanel, AIShell, DBTools, BotControl, FileManager, Analytics, RAGModule, ProFeatures)

### State Management

- `store/index.ts` - Centralized state management with persistence
- User authentication state
- Theme preferences
- Application settings
- Project data

## Installation

```bash
npm install
```

## Development

```bash
npm run dev
```

The application will be available at http://localhost:3001/

## Build

```bash
npm run build
```

## Testing

```bash
npm test
```

## Deployment

```bash
npm run build
```

The built files will be in the `dist` directory.

## API Integration

The dashboard communicates with the Bldr Empire v2 backend API running on http://localhost:8000/

## Current Status

The dashboard is currently in development with the following features implemented:
- Basic layout and navigation
- Authentication system
- Project management
- Task queue monitoring
- Settings configuration
- Theme switching

## Future Enhancements

- Full test coverage
- Advanced analytics dashboard
- Enhanced bot control
- Pro feature locking
- Performance optimizations