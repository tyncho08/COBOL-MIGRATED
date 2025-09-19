# COBOL TO MODERN STACK MIGRATION - ONE SHOT PROMPT

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

## MIGRATION REQUIREMENTS
- Generate a **Migrated_App/** folder in the project root containing the new application, fully isolated from other files.  
- Ensure **100% feature parity** with the COBOL system: every button, workflow, tab, and business rule must be functional.  
- **Frontend UI**: Modern, clean, inspired by banking apps (professional look, usability-first).  
- **Backend**: Implement complete business logic and expose all endpoints via FastAPI (auto-generated OpenAPI docs must be available).  
- **Database**: Use PostgreSQL 15+ as the data store, with schema fully aligned with the legacy system’s data structures and logic.  
- **Integration**: Frontend and backend must be fully connected, reflecting the same behavior as the original COBOL app.  
- **Setup script**: Provide a script called `run_app.sh` that:  
  - Prepares the local environment  
  - Cleans up ports if necessary  
  - Installs dependencies  
  - Run the app 

---

## EXPECTED OUTPUTS
- **Migrated_App/** folder containing:  
  - Full backend (FastAPI, Python)  
  - Full frontend (Next.js, TypeScript, Tailwind, Heroicons)  
  - Database migrations/schema for PostgreSQL  
  - All necessary config files (`package.json`, `pyproject.toml` or `requirements.txt`, etc.)  
- **run_app** script in the root for local execution  
- Complete parity with **Legacy_App** in terms of functionality and rules  