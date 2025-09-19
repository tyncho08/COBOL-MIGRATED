# COMPREHENSIVE COBOL ANALYSIS PIPELINE - ACAS SYSTEM

## Overview
Execute a five-phase analysis pipeline to completely document, analyze, and prepare the ACAS (Applewood Computers Accounting System) COBOL codebase for modernization. Each phase builds upon the previous, creating increasingly sophisticated analysis and documentation.

## System Context
- **Application**: ACAS - Complete ERP with GL, AR/AP, Stock Control, and IRS modules
- **Technology**: GnuCOBOL with file-based storage and partial MySQL/MariaDB
- **Scale**: 278 programs, 175 copybooks, 500K+ lines of code
- **Age**: 45+ years of continuous operation and enhancement

## EXECUTION PHASES:

### Step 1: COBOL Structure Extraction and Parsing
**Prompt**: `1_parser_prompt.md`
**Input**: `Legacy_App/` (all COBOL source files)
**Output**: `documentation/parsed/`

**Objectives**:
- Parse 100% of COBOL programs and copybooks
- Extract complete program structure (all divisions)
- Map all dependencies (CALL, COPY, PERFORM)
- Calculate initial complexity metrics
- Create JSON representation of entire codebase

**Key Deliverables**:
- `documentation/parsed/parsed-structures/` - Individual JSON files per program
- `documentation/parsed/scripts/` - All the scripts needed for COBOL parsing, including node_modules folder
- `documentation/parsed/parser-summary.md` - Complete inventory and statistics
- `documentation/parsed/dependency-graph.md` - Dependency graph data (markdown format)
- `documentation/parsed/parser-errors.md` - Error log for any parsing issues (markdown format)

### Validation Checkpoint
**Input:** Outputs of Step 1
**Validation Criteria:**
- Check: All expected output files exist
- Check: JSON files validate against schema
- Check: No critical programs missing from parser-summary.md
- Check: Dependency graph has no undefined references
- Fix: Rerun parser for failed files
- Fix: Manually create JSON for critical unparseable files
**Continue only when:** Parse success rate >95% and all critical programs processed

### Step 2: Deep Code Analysis and Visualization
**Prompt**: `2_parsed_analysis_prompt.md`
**Input**: 
- `Legacy_App/` (for validation)
- `documentation/parsed/parsed-structures/`
- `documentation/parsed/parser-summary.md`
**Output**: `documentation/parsed/parser_analysis/`

**Objectives**:
- In this step do the analysis directly, don’t generate a script — except for database-related tasks.
- Generate visualizations of system architecture
- Calculate advanced metrics (Halstead, Maintainability Index)
- Identify code quality issues and technical debt
- Create searchable documentation
- Build metrics database for queries

**Key Deliverables**:
- `documentation/parsed/parser_analysis/visualizations/` - Graphs and charts (markdown format)
- `documentation/parsed/parser_analysis/metrics/` - Metrics (markdown format)
- `documentation/parsed/parser_analysis/technical_docs/` - Auto-generated technical documentation (markdown format)
- `documentation/parsed/parser_analysis/database/` - SQLite database with all metrics

### Validation Checkpoint
**Input:** Outputs of Step 2 + all prior outputs
**Process:**
- Detect gaps, inconsistencies, missing coverage or broken dependencies
- Rewrite/correct outputs so Step 2 is 100% valid before continuing

### Step 3: Functional Business Logic Documentation
**Prompt**: `3_functional_prompt.md`
**Input**:
- `Legacy_App/` (source of truth)
- All outputs from `documentation/parsed/`
**Output**: `documentation/functional/`

**Objectives**:
- In this step do the analysis directly, don’t generate a script.
- Document WHAT the system does in business terms
- Map all business processes end-to-end
- Create comprehensive data dictionary
- Document all calculations and business rules
- Assess technical debt and migration readiness

**Key Deliverables**:
- `documentation/functional/analysis/functional_overview.md` - Executive system summary
- `documentation/functional/analysis/program_catalog.md` - Alphabetical listing of all COBOL programs
- `documentation/functional/analysis/data_dictionary.md` - Complete data catalog
- `documentation/functional/analysis/business_flow.md` - End-to-end process documentation
- `documentation/functional/analysis/system_architecture.md` - Program call graphs, Module structure, integration patterns
- `documentation/functional/analysis/cobol_patterns.md` - Common COBOL coding patterns
- `documentation/functional/analysis/migration_roadmap.md` - Modernization strategy
- `documentation/functional/analysis/calculation_engine.md` - All business calculations

### Validation Checkpoint
**Input:** Outputs of Step 3 + all prior outputs
**Process:**
- Detect gaps, inconsistencies, missing coverage or broken dependencies
- Rewrite/correct outputs so Step 3 is 100% valid before continuing

### Step 4: Subsystem Identification and Architecture
**Prompt**: `4_subsystems_prompt.md`
**Input**:
- `Legacy_App/` (for validation)
- All outputs from `documentation/parsed/`
- All outputs from `documentation/functional/`
**Output**: `documentation/subsystems/`

**Objectives**:
- In this step do the analysis directly, don’t generate a script.
- Identify natural subsystem boundaries
- Document subsystem interactions and contracts
- Create migration-ready architecture documentation
- Define data ownership and governance
- Plan for independent subsystem evolution

**Key Deliverables**:
- `documentation/subsystems/analysis/master_subsystems_architecture.md` - Overall architecture
- `documentation/subsystems/analysis/subsystems_inventory.md` - Table with all subsystems, their purpose, and criticality
- `documentation/subsystems/analysis/integration_architecture.md` - How subsystems communicate
- `documentation/subsystems/analysis/data_ownership_map.md` - Which subsystem owns which business entities
- `documentation/subsystems/analysis/process_allocation.md` - Which business processes run in which subsystems
- `documentation/subsystems/analysis/dependency_analysis.md` - All subsystem relationships
- `documentation/subsystems/analysis/` - Coupling, cohesion, and risk analysis (markdown format)
- Individual subsystem specifications in `documentation/subsystems/identified_subsystems/`
- `documentation/subsystems/diagrams/` - Mermaid diagrams of all interactions (markdown format)
- Complete subsystem governance model

### Validation Checkpoint
**Input:** Outputs of Step 4 + all prior outputs
**Process:**
- Detect gaps, inconsistencies, missing coverage or broken dependencies
- Rewrite/correct outputs so Step 4 is 100% valid before continuing

### Step 5: Full Reconciliation & Final Completion
**Input:** All corrected outputs from Steps 1–4
**Process:**
- Re-check the whole pipeline end-to-end
- Auto-fix any last gaps or mismatches across steps
- Ensure consistency (e.g., business rule exists in code + functional docs + subsystem definition)
- Guarantee 100% coverage with no blockers or missing artifacts

## EXECUTION REQUIREMENTS:

### Sequential Execution
- Each step MUST complete successfully before the next begins
- Each step uses all previous outputs as additional context
- Validation checkpoints between each phase

### Quality Standards
- 100% coverage - every program must be analyzed
- Every business rule must be documented
- All dependencies must be mapped bidirectionally
- Documentation must be understandable by non-COBOL developers

### Analysis Depth
- Think ultra mega hard at each step
- Document everything exhaustively
- Capture both the obvious and the subtle
- Identify patterns, anti-patterns, and anomalies
- Consider both current state and future state

## SUCCESS CRITERIA:

1. **Completeness**
   - All 278 programs parsed and analyzed
   - All 175 copybooks mapped and documented
   - Every business process documented end-to-end
   - All subsystems identified with clear boundaries

2. **Accuracy**
   - Business logic preserved exactly
   - Dependencies correctly mapped
   - Calculations documented precisely
   - No functionality missed or misunderstood

3. **Usability**
   - Documentation readable by all stakeholders
   - Visualizations interactive and insightful
   - Clear migration path identified
   - Actionable recommendations provided

4. **Migration Readiness**
   - Subsystems ready for independent migration
   - Technical debt clearly identified
   - Risk assessment completed
   - Phased approach documented

## FINAL OUTPUT STRUCTURE:
```
documentation/
├── parsed/
│   ├── scripts/                  # Individual scripts from Step 1
│   ├── parsed-structures/        # Individual program JSONs
│   ├── parser-summary.md         # System inventory
│   └── parser_analysis/          # Deep analysis results
│       ├── visualizations/       # Interactive graphs
│       ├── metrics/              # Metrics
│       ├── technical_docs/       # Technical docs
│       └── database/             # Metrics database
├── functional/
│   └── analysis/                 # All functional documentation
└── subsystems/
    ├── identified_subsystems/    # Individual specifications
    ├── diagrams/                 # Architecture diagrams
    └── analysis/                 # All the analysis
```

Remember: This analysis forms the foundation for a multi-million dollar modernization effort. The quality and completeness of this documentation will directly impact the success of the migration project. Every detail matters. Every edge case must be captured. Every business rule must be preserved.

## Master Quality Checklist:
- [ ] Step 1: All COBOL files parsed, <5% failure rate
- [ ] Step 2: All metrics calculated, visualizations render
- [ ] Step 3: Business logic documented without technical jargon
- [ ] Step 4: Clean subsystem boundaries, no orphaned code
- [ ] All validation checkpoints passed
- [ ] Zero duplicate functionality across steps
- [ ] 100% traceability from code to documentation