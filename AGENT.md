# MP-Analyzer Repository Analysis

## Purpose

This repository is a two-part application for generating zone-based management reports from uploaded MPR spreadsheet data.

- The `client/` directory contains a React + TypeScript single-page app used to upload a spreadsheet and enter a zone name.
- The `server/` directory contains a FastAPI service that parses the uploaded spreadsheet, computes report metrics, fills a Word template, and returns the generated `.docx` file.

The dominant business workflow is:

1. User selects an Excel or CSV file in the frontend.
2. User enters a zone name.
3. Frontend sends multipart form data to the backend.
4. Backend reads the spreadsheet using a predefined structure template.
5. Backend calculates zone-level and branch-level metrics.
6. Backend renders a Word document from `mpatemplate.docx`.
7. Backend returns the generated report for browser download.

## Implementation Status

- 2026-04-01: Began V1 productization implementation.
- Added a new backend application package under `server/app/`.
- Introduced SQLAlchemy-backed profile and report history models.
- Added profile search/create endpoints and profile-scoped history endpoint.
- Added upload preview and zone suggestion endpoints.
- Started replacing the brittle numeric cleaning logic with centralized negative-safe parsing and formatting helpers.
- Started replacing the `mpaStructure.xlsx` monthly retagging dependency with a dynamic multi-row header parser plus fallback compatibility path.
- Added client API service layer for profiles, preview, generation, and history.
- Reworked the main page around profile selection, upload preview, and zone suggestions.
- Replaced the unused login route with a history page scoped to the selected profile stored in local storage.
- Added Alembic scaffolding and an initial migration for `profiles` and `report_runs`.

## Implemented V1 Architecture

### Backend

- `server/Main.py`: Thin compatibility entry that now exposes `app` from `server/app/main.py`.
- `server/app/main.py`: FastAPI assembly, CORS, startup DB initialization, router registration.
- `server/app/db.py`: SQLAlchemy engine, session factory, and declarative base.
- `server/app/models.py`: `Profile` and `ReportRun` persistence models.
- `server/app/schemas.py`: Pydantic request/response contracts for profiles, history, preview, and zones.
- `server/app/routers/profiles.py`: Profile search/create and profile-scoped history endpoints.
- `server/app/routers/reports.py`: Upload preview, zone suggestion, and report generation endpoints.
- `server/app/services/upload_parser.py`: Dynamic multi-row header parsing, fallback structure parsing, zone extraction, mapping summary, and file fingerprinting.
- `server/app/services/normalization.py`: Centralized string normalization, negative-safe numeric parsing, and formatting helpers.
- `server/app/services/reporting.py`: Report orchestration, history write-through, context building, and Word template rendering.

### Frontend

- `client/src/services/api.ts`: Central API client for profiles, preview, history, and report generation.
- `client/src/hooks/useMainForm.ts`: Main upload workflow with profile selection, preview loading, zone validation, and download handling.
- `client/src/pages/MainPage.tsx`: Main profile-aware upload experience.
- `client/src/pages/HistoryPage.tsx`: User-scoped history UI with filters.
- `client/src/components/ZoneInput.tsx`: Zone datalist suggestions sourced from the current uploaded file.
- `client/src/App.tsx`: Routes now point to `/` and `/history`.

## Implemented API Surface

- `GET /profiles`
- `POST /profiles`
- `GET /profiles/{profile_id}/history`
- `POST /uploads/zones`
- `POST /generate-report/preview`
- `POST /generate-report/`

## Verification Results

- Frontend production build completed successfully with `npm run build` in `client/`.
- Backend route import check succeeded and exposed the new profile/history/preview/report endpoints.
- Backend tests passed with `python -m pytest` from the repository virtual environment.
- Verified parser coverage for:
  - negative and parenthesized numeric values
  - multi-row header mapping
  - profile uniqueness behavior
- 2026-04-01 re-run verification:
  - `..\.venv\Scripts\python.exe -m pytest` -> 3 passed
  - `npm run build` in `client/` -> passed
  - FastAPI route import check -> passed

## Environment Files

- Added `server/.env` with safe local SQLite defaults and placeholder Supabase Postgres connection details.
- Added `server/.env.example` as a copyable template for deployment and onboarding.
- Added `client/.env` with a local `VITE_API_URL` pointing to the FastAPI server.
- Added `client/.env.example` as a frontend environment template.

## Database Defaults

- Updated the backend default database target to Supabase-compatible PostgreSQL.
- Added `psycopg[binary]` to backend dependencies for SQLAlchemy Postgres connectivity.
- Updated `server/.env`, `server/.env.example`, and `server/alembic.ini` with clear Supabase credential placeholders.
- Credentials should be inserted in `server/.env` by replacing:
  - `YOUR_SUPABASE_PASSWORD`
  - `YOUR_SUPABASE_HOST`
- Added backend normalization so `.env` database URLs are accepted whether they use `postgresql://` or `postgresql+psycopg://`, and surrounding quotes are stripped automatically.
- Added backend normalization to strip Supabase pooler query options like `pgbouncer` and `connection_limit` that `psycopg` does not accept directly.

## Project Structure

### Root

- `.git/`: Git metadata.
- `.venv/`: Local Python virtual environment.
- `client/`: Frontend application.
- `server/`: Backend API and reporting assets.
- `mpa/`: Present but not used by the currently discovered execution flow.
- `.idea/`, `.qodo/`: IDE and tooling metadata.

### Client

- `client/package.json`: Frontend dependencies and scripts.
- `client/vite.config.ts`: Vite build config and `@` alias mapping to `src/`.
- `client/components.json`: `shadcn/ui` style and alias configuration.
- `client/src/main.tsx`: React bootstrap entry point.
- `client/src/App.tsx`: Route registration.
- `client/src/pages/MainPage.tsx`: Main upload screen.
- `client/src/pages/Login.tsx`: Placeholder route with no implemented behavior.
- `client/src/hooks/useMainForm.ts`: Core client workflow state, validation, API call, file download, and error handling.
- `client/src/components/`: Presentational UI components.
- `client/src/components/ui/`: Reusable `shadcn/ui` primitives.
- `client/src/types/types.ts`: Shared TypeScript interfaces for component props and hook contracts.
- `client/src/index.css`: Tailwind v4 and theme tokens.
- `client/public/`: Static assets and deployment redirect file.

### Server

- `server/Main.py`: Main FastAPI application, business logic, formatting helpers, and report generation pipeline.
- `server/requirements.txt`: Python dependencies.
- `server/mpatemplate.docx`: Word template used for final report rendering.
- `server/mpaStructure.xlsx`: Spreadsheet column structure used to normalize uploaded files.
- `server/mpaStructure AUGUST.xlsx`, `server/mpaStructureAUGUST ZONAL DISTRIBUTION structure.xlsx`, `server/mpaStructure - old.xlsx`: Historical or alternate structure files.
- `server/notebook.ipynb`: Exploratory notebook, likely used during data preparation or prototyping.
- `server/package-lock.json`: Empty npm lockfile with no meaningful package contents.

## Architecture Patterns

## 1. High-Level Style

The system follows a simple client-server architecture:

- Presentation layer: React SPA in `client/`
- Application and processing layer: FastAPI app in `server/`
- Template-based output generation: Word document rendering using `docxtpl`

## 2. Frontend Pattern

The frontend is a thin orchestration layer with a light componentized UI:

- `MainPage.tsx` composes the screen.
- `useMainForm.ts` centralizes state and submission behavior.
- Small presentational components handle input, button, and loading overlay concerns.

This is effectively a "container + presentational components" pattern, with the custom hook acting as the container/controller.

## 3. Backend Pattern

The backend is a monolithic service module:

- API endpoint definitions
- data parsing
- metric calculation
- formatting
- document rendering
- cleanup

all live in `server/Main.py`.

There is no explicit service layer, repository layer, or domain module split yet. The code is functional and direct, but tightly coupled.

## 4. Data Integration Pattern

The backend uses a schema-alignment approach:

- It first reads the header row from `mpaStructure.xlsx`
- It then reads the uploaded data without headers
- It assigns the structure template columns to the uploaded dataset

This means the uploaded file is expected to match the known column count and layout after skipping the first five rows.

## 5. Output Generation Pattern

The report is produced using template-based document generation:

- compute values into a flat `context` dictionary
- inject context into `mpatemplate.docx`
- save to a temporary `.docx`
- return it as a downloadable file

This makes the Word template part of the runtime contract, not just a static asset.

## Key Components

### Frontend

#### `client/src/main.tsx`

Bootstraps React and wraps the app in `BrowserRouter`.

#### `client/src/App.tsx`

Defines application routes:

- `/` -> `MainPage`
- `/login` -> `Login`

#### `client/src/pages/MainPage.tsx`

Main user-facing screen. It renders:

- file upload input
- zone text input
- submit button
- loading overlay

It delegates all behavior to `useMainForm`.

#### `client/src/hooks/useMainForm.ts`

This is the most important client file. Responsibilities:

- manages `file`, `zoneName`, and `isLoading` state
- validates selected file type
- builds `FormData`
- calls backend using `axios.post`
- expects binary response (`blob`)
- triggers browser-side download
- maps backend errors into user-friendly SweetAlert messages

### Backend

#### `server/Main.py`

This is the system core. Responsibilities:

- creates FastAPI app
- enables permissive CORS
- defines numeric columns to sanitize and convert
- formats numeric values for report display
- computes branch ranking metrics in `process_data`
- exposes `/get-balance`
- exposes `/generate-report/`
- reads upload into temp storage
- normalizes spreadsheet columns
- extracts zone row and branch statistics
- creates report context
- renders `mpatemplate.docx`
- returns the generated file
- schedules temp file cleanup

#### `server/mpaStructure.xlsx`

Acts like a structural schema reference for uploaded spreadsheets.

#### `server/mpatemplate.docx`

Acts like the presentation template for the final report. The keys in the backend `context` dictionary must match placeholders in this document.

## Entry Points

### Frontend Entry Point

- `client/src/main.tsx`

Execution starts when Vite serves `index.html`, which mounts the React tree and renders `App`.

### Backend Entry Point

- `server/Main.py`

The runtime object is `app = FastAPI()`. There is no launcher script in the repository, so the backend is likely intended to be started with a command such as:

```powershell
uvicorn Main:app --reload
```

from the `server/` directory, or an equivalent module path depending on how the environment is started.

### Primary Functional Entry Route

- `POST /generate-report/`

This is the main business endpoint and the core application workflow.

## Dependencies

### Frontend-Critical Libraries

From `client/package.json`:

- `react`, `react-dom`: UI runtime.
- `react-router-dom`: route handling.
- `axios`: backend HTTP requests.
- `sweetalert2`: user notifications and error dialogs.
- `framer-motion`: animation for loading and UI transitions.
- `tailwindcss`, `@tailwindcss/vite`: styling system.
- `lucide-react`: icons.
- `@radix-ui/react-label`, `@radix-ui/react-slot`, `class-variance-authority`, `clsx`, `tailwind-merge`: UI composition utilities associated with `shadcn/ui`.

### Backend-Critical Libraries

From `server/requirements.txt`:

- `fastapi`, `starlette`, `uvicorn`: web API runtime.
- `python-multipart`: required for file uploads.
- `pandas`, `numpy`, `openpyxl`: spreadsheet reading and data manipulation.
- `docxtpl`, `python-docx`, `docxcompose`, `Jinja2`: Word template rendering stack.
- `pydantic`: request/response model ecosystem used by FastAPI.

### Runtime Assets

These are not libraries, but they are essential runtime dependencies:

- `server/mpaStructure.xlsx`
- `server/mpatemplate.docx`

If either is missing, report generation fails.

### External APIs

No third-party web APIs were found in the source.

The only network API dependency discovered is the frontend calling the backend URL provided by `VITE_API_URL`.

## Data Flow

## 1. UI Input

The user interacts with the form in `client/src/pages/MainPage.tsx`.

- File selection is handled by `handleFileChange`
- Zone text input is handled by `handleZoneChange`
- Form submission is handled by `handleSubmit`

## 2. Client Request Construction

In `client/src/hooks/useMainForm.ts`:

- a `FormData` object is created
- the selected file is appended as `file`
- the zone text is appended as `zone_name`
- `axios.post(API_URL, formData, { responseType: "blob" })` sends the request

This means the frontend expects the backend to return a downloadable binary file, not JSON.

## 3. Backend File Intake

In `server/Main.py`, the `/generate-report/` endpoint:

- validates file extension
- copies the upload into a temporary file
- prepares a temporary output path
- verifies the structure and template files exist

## 4. Backend Spreadsheet Normalization

The backend:

- reads column headers from `mpaStructure.xlsx`
- reads uploaded rows from the user file after skipping five rows
- checks column count compatibility
- creates a DataFrame with template-aligned column names
- sanitizes listed numeric columns by removing non-digit characters except dots
- converts those columns to numeric values

## 5. Zone Filtering and Metric Extraction

The backend then:

- finds the row where `ZONES` exactly matches the submitted zone name
- computes summary branch rankings via `process_data`
- extracts many KPI fields from the matched zone row
- computes percentages, totals, and formatted display values

## 6. Report Context Assembly

The extracted values are transformed into a flat dictionary named `context`.

This dictionary includes:

- headline KPI values
- formatted strings for financial numbers
- placeholder summary text
- branch comparison metrics returned from `process_data`

## 7. Document Rendering

The backend:

- loads `mpatemplate.docx`
- renders it with `DocxTemplate.render(context)`
- saves a `.docx` to a temp path

## 8. Response Back to Browser

The backend returns a `FileResponse` with Word MIME type and a generated filename.

On the frontend:

- the blob response is turned into a browser object URL
- a temporary anchor is created
- the report download is triggered programmatically
- success or error dialogs are shown to the user

## 9. Cleanup

The backend schedules temp input and output files for deletion via `BackgroundTasks`.

## Main Execution Trace

### Frontend

1. `index.html` loads Vite bundle
2. `client/src/main.tsx` mounts React
3. `client/src/App.tsx` routes `/` to `MainPage`
4. `MainPage.tsx` calls `useMainForm`
5. `useMainForm.ts` sends multipart request to backend
6. browser downloads returned `.docx`

### Backend

1. ASGI server loads `server/Main.py`
2. `app = FastAPI()` registers middleware and routes
3. request hits `POST /generate-report/`
4. uploaded file is stored temporarily
5. spreadsheet is parsed into a DataFrame
6. zone data and branch metrics are computed
7. Word template is rendered
8. generated document is returned
9. temp files are cleaned up

## Important Design Observations

- The backend is the business heart of the system; nearly all domain logic resides in `server/Main.py`.
- The frontend is intentionally thin and behaves mostly as an upload/download shell.
- The upload pipeline depends heavily on spreadsheet shape assumptions, especially skipped header rows and exact column count matching.
- The Word template and structure spreadsheet are effectively part of the application schema.
- The `/login` route exists but is currently not implemented.
- The `client/src/components/FileInputs.tsx` component exists but is not actually used correctly by `MainPage.tsx`; `MainPage` imports `FileInput` from `lucide-react` instead of the local component.
- The repository appears to be a working internal tool rather than a heavily layered production platform.

## Risks and Architectural Constraints

- Single-file backend concentration makes future maintenance harder.
- Business logic is coupled to file format details and template field names.
- Wide-open CORS is convenient for development but risky for production.
- Environment configuration is minimal and relies on `VITE_API_URL`.
- Missing tests mean spreadsheet format changes could break the pipeline silently until runtime.

## Suggested Next Refactoring Layers

If this repository is going to grow, the cleanest architectural split would be:

1. `server/api/` for route definitions
2. `server/services/` for report generation orchestration
3. `server/domain/` for metric computation and formatting
4. `server/templates/` for document and schema assets
5. `server/models/` for typed request and report context structures

On the frontend:

1. keep `pages/` for screens
2. keep `components/` for pure UI
3. move API logic into `services/`
4. keep hooks focused on UI state only

## Analysis Steps Performed

This document was produced by following these inspection steps:

1. Listed the repository root to identify top-level modules and tooling folders.
2. Enumerated all tracked files to find likely entry points and manifests.
3. Read `client/package.json` to identify frontend stack and scripts.
4. Read `server/requirements.txt` to identify backend runtime dependencies.
5. Read `client/src/main.tsx` and `client/src/App.tsx` to locate frontend boot and routes.
6. Read `server/Main.py` to trace backend setup, endpoints, and processing logic.
7. Read `client/src/pages/MainPage.tsx` and `client/src/hooks/useMainForm.ts` to trace the UI workflow and backend call.
8. Read supporting client components and types to understand the view composition.
9. Read `client/vite.config.ts`, `client/components.json`, and `client/src/index.css` to confirm build and UI infrastructure.
10. Searched the repository for `VITE_API_URL`, `generate-report`, `get-balance`, `FastAPI`, `DocxTemplate`, and related terms to validate the main execution path.
11. Consolidated the results into this architectural summary and data-flow documentation.

## Representative Files

- Frontend boot: `client/src/main.tsx`
- Frontend routing: `client/src/App.tsx`
- Main screen: `client/src/pages/MainPage.tsx`
- Frontend workflow logic: `client/src/hooks/useMainForm.ts`
- Backend application: `server/Main.py`
- Backend structure schema: `server/mpaStructure.xlsx`
- Backend output template: `server/mpatemplate.docx`
