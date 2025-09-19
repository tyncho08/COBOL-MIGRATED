# COBOL TO MODERN STACK MIGRATION - COMPREHENSIVE PROMPT

## OBJECTIVE
Migrate the full **Legacy_App** (COBOL system) into a new modern application called **Migrated_App** using the following stack:

- **Backend**: Python 3.11+ with FastAPI  
- **Frontend**: Next.js 14 + TypeScript  
- **Database**: PostgreSQL 15+  
- **Styling**: Tailwind CSS + Heroicons  
- **API**: RESTful with automatic OpenAPI docs  

The result must be a fully functional system, replicating all business logic, workflows, and UI behavior from the legacy app.

---

## INPUT SOURCES
1. **Legacy_App/** (root) → Original COBOL application (**absolute source of truth**).  
2. **documentation/** (root) → Contains multiple forms of documentation:  
   - Parsed COBOL files in JSON in `documentation/parsed/`
   - Functional documentation in `documentation/functional/`
   - Subsystem documentation in `documentation/subsystems/`

⚠️ **Rule of Reference:**  
If at any point the migration requires clarification, design decisions, or missing details → **first consult the original `Legacy_App/` code**, and only then use the documentation in `documentation/`.  
All answers to functionality, logic, and structure must be derived from these two sources. **No assumptions outside them.**

---

## CRITICAL BACKEND DEPENDENCY LESSONS

### ⚠️ PYDANTIC V2 COMPATIBILITY REQUIREMENTS
- **NEVER use `decimal_places` parameter in Field()** - This is not valid in Pydantic v2
- **Use `pydantic[email]==2.5.0`** for EmailStr support
- **Add email-validator==2.1.0** explicitly to requirements.txt
- **SQLAlchemy version compatibility**: Use `sqlalchemy>=1.4.42,<1.5` (NOT 2.x) with `databases==0.8.0`
- **Import changes**: Use `field_validator` instead of `validator` for Pydantic v2
- **Decimal handling**: Use `from decimal import Decimal as PyDecimal` and define decimals as `PyDecimal = Field(PyDecimal("0.00"))`

### 📦 EXACT DEPENDENCY VERSIONS (TESTED & WORKING)
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy>=1.4.42,<1.5
alembic==1.13.0
psycopg2-binary==2.9.9
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
asyncpg==0.29.0
databases==0.8.0
pydantic[email]==2.5.0
email-validator==2.1.0
jinja2==3.1.2
aiofiles==23.2.1
httpx==0.25.2
pytest==7.4.3
pytest-asyncio==0.21.1
```

### 🗄️ POSTGRESQL CONNECTION FIXES
- **OS-specific PostgreSQL paths**: Handle macOS Homebrew (`/opt/homebrew/opt/postgresql@15/bin`) vs Linux paths
- **Service management**: Use `brew services` on macOS, `systemctl` on Linux
- **Authentication setup**: Create superuser with current username on macOS, use `postgres` user on Linux
- **Database initialization**: Check if PostgreSQL data directory exists before initializing
- **Connection retry logic**: Implement 30-second timeout with proper fallback authentication

---

## MIGRATION REQUIREMENTS

### 🎯 CORE REQUIREMENTS
- Generate a **Migrated_App/** folder in the project root containing the new application, fully isolated from other files.  
- Ensure **100% feature parity** with the COBOL system: every button, workflow, tab, and business rule must be functional.  
- **Frontend UI**: Modern, clean, inspired by banking apps (professional look, usability-first).  
- **Backend**: Implement complete business logic and expose all endpoints via FastAPI (auto-generated OpenAPI docs must be available).  
- **Database**: Use PostgreSQL 15+ as the data store, with schema fully aligned with the legacy system's data structures and logic.  
- **Integration**: Frontend and backend must be fully connected, reflecting the same behavior as the original COBOL app.  

### 🔧 SETUP SCRIPT REQUIREMENTS
Provide a script called `run_app.sh` that:
- **Environment Check**: Verify Python 3.11+, Node.js 18+, PostgreSQL installation
- **OS Detection**: Handle macOS (Homebrew) and Linux (apt/yum) package management
- **PostgreSQL Setup**: Auto-install, configure, and start PostgreSQL service
- **Database Creation**: Create database user, database, and grant permissions
- **Port Management**: Clean up ports 3000 and 8000 before starting
- **Dependency Installation**: Install both backend and frontend dependencies
- **Environment Files**: Create .env and .env.local with proper configuration
- **Service Startup**: Start backend and frontend with proper health checks
- **Error Handling**: Provide meaningful error messages and recovery suggestions

### 📋 BUSINESS LOGIC COMPLETENESS
- **All COBOL Programs**: Migrate every .COB file's business logic
- **Data Validation**: Implement all field validations, constraints, and business rules
- **Calculation Engines**: Port all financial calculations, pricing, and tax logic
- **Workflow States**: Implement all document statuses and state transitions
- **Reports**: Create all reports with exact same data and formatting logic
- **Batch Processes**: Implement all background jobs and scheduled tasks
- **Authentication**: Multi-user support with proper permissions and roles

### 🎨 FRONTEND COMPLETENESS CHECKLIST
- **Navigation**: Complete sidebar/menu structure matching COBOL screens
- **Forms**: Every data entry form with proper validation and error handling
- **Lists/Tables**: All data display screens with pagination, search, and sorting
- **Modals**: Selection dialogs, confirmations, and detail views
- **State Management**: Proper React state for complex forms and workflows
- **API Integration**: All CRUD operations connected to backend
- **Responsive Design**: Professional banking-style UI with Tailwind CSS
- **Loading States**: Proper loading indicators and error boundaries

---

## BACKEND ARCHITECTURE PATTERNS

### 🏗️ FASTAPI PROJECT STRUCTURE
```
backend/
├── app/
│   ├── main.py              # FastAPI app initialization
│   ├── database.py          # SQLAlchemy setup
│   ├── models.py            # Pydantic models (validation)
│   ├── schemas/             # SQLAlchemy database models
│   ├── routers/             # API route handlers
│   ├── services/            # Business logic layer
│   ├── utils/               # Helper functions
│   └── config.py            # Configuration management
├── requirements.txt         # Dependencies
├── .env                     # Environment variables
└── alembic/                 # Database migrations
```

### 📊 DATABASE PATTERNS
- **SQLAlchemy ORM**: Use declarative base with proper relationships
- **Migration Strategy**: Alembic for schema versioning
- **Connection Pooling**: Proper connection management for production
- **Data Types**: Map COBOL COMP-3 to DECIMAL, COMP to INTEGER
- **Constraints**: Implement all business rules as database constraints
- **Indexes**: Add proper indexes for performance on large datasets

---

## FRONTEND ARCHITECTURE PATTERNS

### ⚛️ NEXT.JS 14 PROJECT STRUCTURE
```
frontend/
├── src/
│   ├── app/                 # App Router (Next.js 14)
│   │   ├── layout.tsx       # Root layout
│   │   ├── page.tsx         # Home page
│   │   ├── dashboard/       # Dashboard module
│   │   ├── sales/           # Sales module
│   │   ├── purchase/        # Purchase module
│   │   ├── stock/           # Inventory module
│   │   ├── reports/         # Reports module
│   │   └── admin/           # Admin module
│   ├── components/          # Reusable UI components
│   ├── services/            # API service layer
│   ├── types/               # TypeScript interfaces
│   ├── utils/               # Helper functions
│   └── styles/              # Global styles
├── package.json
├── tailwind.config.ts
└── .env.local
```

### 🎯 COMPONENT PATTERNS
- **Page Components**: One per COBOL screen with full functionality
- **Form Components**: Controlled forms with real-time validation
- **Table Components**: Sortable, filterable data grids with pagination
- **Modal Components**: For selections, confirmations, and details
- **Service Layer**: Centralized API calls with error handling
- **Type Safety**: Complete TypeScript interfaces for all data models

---

## TESTING & VALIDATION CHECKLIST

### ✅ BACKEND TESTING
- [ ] All API endpoints respond correctly
- [ ] Database models create without errors
- [ ] Business logic calculations match COBOL results
- [ ] Authentication and authorization work
- [ ] Error handling provides meaningful messages
- [ ] PostgreSQL connection is stable

### ✅ FRONTEND TESTING
- [ ] All pages load without console errors
- [ ] Forms submit and validate correctly
- [ ] Navigation works between all modules
- [ ] Data displays match backend responses
- [ ] Responsive design works on mobile/desktop
- [ ] API integration handles errors gracefully

### ✅ INTEGRATION TESTING
- [ ] Complete user workflows function end-to-end
- [ ] Data persistence works correctly
- [ ] Real-time calculations update properly
- [ ] Multi-user scenarios work without conflicts
- [ ] Performance acceptable with realistic data volumes

---

## DEPLOYMENT READINESS

### 🚀 PRODUCTION CHECKLIST
- [ ] Environment variables properly configured
- [ ] Database connection pooling enabled
- [ ] Frontend build process optimized
- [ ] Security headers implemented
- [ ] HTTPS configuration ready
- [ ] Logging and monitoring configured
- [ ] Backup and recovery procedures documented
- [ ] Performance testing completed

---

## EXPECTED OUTPUTS
- **Migrated_App/** folder containing:  
  - Full backend (FastAPI, Python) with complete business logic
  - Full frontend (Next.js, TypeScript, Tailwind, Heroicons) with all UI screens
  - Database migrations/schema for PostgreSQL  
  - All necessary config files (`package.json`, `requirements.txt`, etc.)
  - Complete API service layer with error handling
  - Comprehensive documentation for setup and usage
- **run_app.sh** script in the root for one-command local execution  
- **fix_backend.sh** script for dependency troubleshooting
- Complete parity with **Legacy_App** in terms of functionality and business rules
- Professional-grade code quality ready for production deployment