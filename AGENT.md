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
- `client/src/hooks/useMainForm.ts`: Main upload workflow for the selected profile, including preview loading, zone validation, download handling, and immediate success-state updates.
- `client/src/lib/profile-session.ts`: Local storage helpers for the active profile session.
- `client/src/pages/MainPage.tsx`: Main app experience for report generation under the selected profile.
- `client/src/pages/HistoryPage.tsx`: User-scoped history UI with filters.
- `client/src/pages/SelectProfilePage.tsx`: Existing-profile selection screen.
- `client/src/pages/CreateProfilePage.tsx`: New-profile creation screen.
- `client/src/components/ZoneInput.tsx`: Zone datalist suggestions sourced from the current uploaded file.
- `client/src/App.tsx`: Routes now point to `/`, `/history`, `/profiles/select`, and `/profiles/new`.

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
- Business rule locked in: accounting-style values in parentheses, for example `(35)`, are treated as negative values, for example `-35`.
- 2026-04-01 re-run verification:
  - `..\.venv\Scripts\python.exe -m pytest` -> 3 passed
  - `npm run build` in `client/` -> passed
  - FastAPI route import check -> passed

## Environment Files

- Added `server/.env` with safe local SQLite defaults and placeholder Supabase Postgres connection details.
- Added `server/.env.example` as a copyable template for deployment and onboarding.
- Added `client/.env` with a local `VITE_API_URL` pointing to the FastAPI server.
- Added `client/.env.example` as a frontend environment template.

## UI Loading States

- Added shadcn `Skeleton` component via MCP-assisted registry command.
- Applied more granular loading feedback across the frontend:
  - profile search loading indicator
  - profile creation loading button state
  - schema preview skeleton while upload profiling runs
  - explicit submit button labels for profiling vs report generation
  - history page skeleton rows during refresh
- Used current React guidance for explicit async pending UI in client components and kept the implementation in local component state.

## Runtime Status

- Backend started successfully with `uvicorn` on `http://127.0.0.1:8000`.
- Verified the backend is responding with HTTP `200` on `/docs`.
- 2026-04-01: Backend restarted cleanly after restoring the structure-first parser path and confirmed healthy on `/docs`.
- 2026-04-01: Backend was restarted again after splitting the profile flow into separate screens and confirmed healthy on `/docs` with HTTP `200`.

## Profile Flow Update

- Split the frontend flow into three separate screens:
  - `client/src/pages/SelectProfilePage.tsx`
  - `client/src/pages/CreateProfilePage.tsx`
  - `client/src/pages/MainPage.tsx`
- Added `Change Profile` navigation on both the main app screen and the history screen.
- The main app UI now updates immediately after a successful report generation by rendering an in-page success summary with the zone, source file name, and generation timestamp.
- Rebuilt the frontend after the screen split and confirmed `npm run build` still passes.
- Removed the extra profile-scoping helper copy from the main screen's current-profile card.
- Updated the main screen styling to stay within the existing teal-centered visual theme instead of introducing a separate success color family.
- Filtered the literal `ZONES` header value out of parsed zone suggestions so it never appears in the frontend list.
- Extended the same teal-centered styling across the select-profile, create-profile, and history screens.
- Updated the shared theme tokens in `client/src/index.css` so default buttons and accents now follow the app's established teal palette instead of the previous neutral dark primary color.
- Added profile-scoped upload persistence in `client/src/lib/upload-session.ts` using IndexedDB so the selected workbook survives navigation away from the upload page and returns automatically when the user comes back.
- Added an explicit remove-file control on the main upload screen so users can clear the persisted workbook and choose another file without changing profiles.
- Added multi-zone generation on the main upload screen by letting users queue zones as removable chips before generating reports.
- Updated the history screen to paginate at 10 records per page, with backend support for `page` and `page_size`.
- Updated the themed navigation buttons, including `View History`, `Change Profile`, and `Back to Select`, so they follow the teal app palette consistently.

## Latest Verification

- Rebuilt the frontend after the theme-token update and confirmed `npm run build` passes.
- Re-ran backend tests with `..\.venv\Scripts\python.exe -m pytest` and confirmed `4 passed`.
- Re-verified the parentheses-negative parser directly:
  - `(35)` -> `-35`
  - `(1,200.50)` -> `-1200.50`
  - `(35%)` -> `-0.35`
  - `-10` -> `-10`
- Restarted the backend and re-verified that `http://127.0.0.1:8000/docs` returns HTTP `200`.
- Expanded backend verification to `6 passed` after adding:
  - negative DP formatter coverage
  - history pagination coverage
- Verified workbook-derived negative formatting using the December zonal distribution file:
  - branch variance sample `-42.4528` now formats as `-42M`
  - DP variance sample `-0.886876003` now formats as `-886.8K`
- Verified live browser behavior with Playwright on `http://localhost:5173`:
  - selected profile routing works
  - workbook upload succeeds and schema preview is shown
  - returning from history restores the uploaded workbook automatically
  - remove-file clears the persisted upload and restores the file picker
  - real report generation succeeds and updates the success card immediately
  - history pagination controls render in the UI

## Reporting and History Update

- Updated `server/app/services/normalization.py` so DP-style negative values now render with a leading minus sign rather than parentheses.
- Updated `server/app/services/reporting.py` so summary variance values use the same millions/billions formatting helpers as the headline metric values.
- Updated `server/app/services/profiles.py`, `server/app/routers/profiles.py`, `server/app/schemas.py`, and `client/src/services/api.ts` to support paginated history responses.
- Added a development-friendly origin regex in `server/app/main.py` so local frontend hosts like `localhost` and `127.0.0.1` are accepted reliably during browser testing.

## Structure Bottleneck Strategy

- The biggest remaining operational bottleneck is the manual rebuild of `mpaStructure.xlsx` whenever the source workbook layout changes.
- The current system is reliable because it uses a tagged structure-header overlay, but it is fragile because it depends on exact column positions and monthly manual maintenance.
- Recommended long-term direction:
  - keep the current structure-overlay workflow as a fallback safety mode
  - add a dynamic schema-detection pipeline as the primary mode
  - separate column identification from column position
- Recommended dynamic mapping design:
  - detect the real header band from the uploaded workbook
  - flatten multi-row headers into canonical header strings
  - identify columns using alias dictionaries and pattern rules rather than fixed indexes
  - identify metric families like `PBT`, `DDA`, `SAV`, `FD`, `DP`, `TRA` by semantic matching
  - detect the active period from the workbook itself and map current-period columns automatically
  - persist approved mappings keyed by a workbook fingerprint so repeated layouts do not need to be re-learned
- Best implementation model for this project:
  - `manual structure mode` for guaranteed compatibility
  - `dynamic mapping mode` for new layouts
  - `mapping review mode` when confidence is low or required fields are ambiguous

## Auto Structure Selection

- Implemented a template-bank approach inside `server/app/services/upload_parser.py`.
- The parser no longer depends on only one active `mpaStructure.xlsx` file.
- It now scans all `mpaStructure*.xlsx` files in the server directory and automatically selects the best-matching structure template based on uploaded body column count.
- Exact column-count matches are preferred first.
- If no exact match exists, the parser can fall back to the nearest available structure template within a small tolerance instead of immediately failing with a mismatch error.
- This removes the need to manually replace `mpaStructure.xlsx` for every recurring report variant that already matches one of the known structure profiles in the template bank.
- The parser still reports the active detected period window from the uploaded workbook itself, for example `Oct-25 to Dec-25`.

## Latest Workbook Verification

- Verified against `DECEMBER ZONAL DISTRIBUTION FOR BRANCHES.xlsx`.
- Direct parser result:
  - `header_row_index = 5`
  - `detected_period_label = Oct-25 to Dec-25`
  - `missing_fields = []`
- Verified that the parser still resolves report-critical fields including:
  - `PBT 2025 YTD ACHVD`
  - `DDA Jul-25`
  - `SAV Jul-25`
  - `FD Jul-25`
  - `DP Jul-25`
  - `TRA Jul-25`
  - `AB Jul-25`
- Verified the new auto-template behavior by intentionally pointing the configured fallback path at a wrong structure file while the parser still auto-selected the correct matching template from the template bank.
- Added regression coverage in `server/tests/test_upload_parser.py` for automatic matching-template selection.
- Live API validation with the December workbook succeeded:
  - `POST /generate-report/preview` returned `200` with `ready = true`
  - `POST /generate-report/` returned `200` and generated `ABIA_1_Report.docx`

## Restored Structure Workflow

- Updated the upload parser so the legacy `mpaStructure.xlsx` header-swap workflow is now the primary path again.
- The system now first:
  - reads the tagged header row from `mpaStructure.xlsx`
  - reads the uploaded workbook body with `skiprows=5`
  - validates that the column counts match
  - swaps the structure headers onto the uploaded body
- Dynamic header inference remains as a secondary fallback only when the structure-based path cannot be used.
- Zone suggestions now include zone rows such as `... Total`, matching the original processing workflow more closely.
- Added a regression test proving the parser can reconstruct a report from a matching structure file plus uploaded body.
- Verified the current `mpaStructure.xlsx` contains the expected tagged fields including `PBT 2025 YTD ACHVD`, `DDA Jul-25`, `SAV Jul-25`, `FD Jul-25`, and `DP Jul-25`.

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
- `client/src/pages/MainPage.tsx`: Main application screen for report generation.
- `client/src/pages/HistoryPage.tsx`: Profile-scoped report history screen.
- `client/src/pages/SelectProfilePage.tsx`: Profile selection screen.
- `client/src/pages/CreateProfilePage.tsx`: Profile creation screen.
- `client/src/hooks/useMainForm.ts`: Core client workflow state for upload preview and report generation.
- `client/src/lib/profile-session.ts`: Active-profile browser storage helper.
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
- `/history` -> `HistoryPage`
- `/profiles/select` -> `SelectProfilePage`
- `/profiles/new` -> `CreateProfilePage`

#### `client/src/pages/MainPage.tsx`

Main report-generation screen for the selected profile. It renders:

- current profile information
- change-profile action
- history navigation
- file upload input
- schema preview state
- zone text input with suggestions
- submit button
- loading overlay
- immediate success feedback after a successful report generation

It delegates all behavior to `useMainForm`.

#### `client/src/hooks/useMainForm.ts`

This is the most important client file. Responsibilities:

- manages `file`, `zoneName`, preview state, loading state, and last successful generation state
- validates selected file type
- calls the preview endpoint after file selection
- validates the zone against the parsed zone suggestions
- builds `FormData`
- calls backend using `axios.post`
- expects binary response (`blob`)
- triggers browser-side download
- updates the UI immediately after success through `lastGenerated`
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

- the selected file is previewed first to fetch schema readiness and zone suggestions
- a `FormData` object is created for final generation
- the selected file is appended as `file`
- the zone text is appended as `zone_name`
- the active profile id is appended as `profile_id`
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

## 2026-04-01 October Workbook Validation
- Tested `OCT 2025 MPR DISTRIBUTION.xlsx` against the new parser.
- Fixed `upload_parser` to accept `Path` inputs during direct analysis.
- Added contextual header inheritance so block-style headers carry their family labels across adjacent month and variance columns.
- Verified direct parsing now resolves required report fields for October without rebuilding `mpaStructure.xlsx`.
- Live `/generate-report/preview` for the October workbook returned `ready=true`, `missing_fields=[]`, `period='Aug-25 to Oct-25'`, and `155` zones.
- Added a regression test covering block-style header inference.
- Live `/generate-report/` for the October workbook now returns `200` and a valid `.docx` payload for `Abia 1 Total`.
- Remaining automation gap for this turn: Playwright MCP browser session could not be reopened because the browser backend reported the page/context was already closed.


## 2026-04-02 October Report Verification
- Verified the October workbook end to end using only zones whose names contain `Total`.
- Sampling seed: `20260402`.
- Randomly selected zones: `South-West 5 Total`, `Ilupeju 2 Total`, `North Central 3 Total`, `Delta 2 Total`, `Edo 3 Total`.
- For each selected zone, generated a live report through `POST /generate-report/`.
- Opened each returned `.docx` and checked that key rendered values from the source workbook appeared in the document text.
- Verified title, PBT, DDA, SAV, FD, DP, TRA, AB, and dormant-account values for all 5 reports.
- Result: all checks passed for all 5 randomly selected `Total` zones.


- Verified `Ikorodu 2 Total` specifically with the October workbook.
- Generated a live `IKORODU_2_Report.docx` through the running API.
- Captured the full generated context, extracted the raw source-row values from the workbook, and inspected the rendered `.docx` paragraphs and tables.
- Confirmed the generated report values align with the normalized source values for PBT, DDA, SAV, FD, DP, TRA, AB, AO, CDS, CE, AOB, POS, NXP, and dormant-account sections.


## 2026-04-07 Manual Rollback
- Reverted the core upload parser back to the manual `mpaStructure.xlsx` header-swap workflow as the only active parsing path.
- `parse_uploaded_workbook()` now always reads the uploaded file body with `skiprows=5`, overlays the tagged structure headers, and fails fast on column-count mismatch.
- Dynamic semantic inference is no longer part of the active core flow.
- Updated parser tests to reflect manual-structure behavior, including an explicit mismatch failure test.


## 2026-04-07 Cost To Income Calibration
- Verified the December workbook row for `Abuja 07 Total` and confirmed `PBT Cost to Income Ratio = 1.6238883056509614`.
- Fixed report formatting so cost-to-income ratios use a dedicated ratio formatter instead of the generic percentage formatter.
- `Abuja 07 Total` now renders `162%` in the generated report instead of `2%`.
- Added backend tests covering fractional ratios like `1.6238` and whole percentages like `93.72`.


## 2026-04-07 Dynamic Parser Re-enabled
- Restored the dynamic parser as the primary parsing path in `parse_uploaded_workbook()`.
- The parser now tries semantic/header-based inference first and falls back to the manual `mpaStructure.xlsx` header-swap workflow only when required fields are missing.
- Restored parser tests for direct mapped-header extraction and block-style header inference.
- Kept the manual structure overlay fallback path intact for comparison and safety.


## 2026-04-07 Manual Structure Endpoint
- Reverted the active parser back to the manual `mpaStructure.xlsx` workflow only.
- Added `POST /structure/upload` to upload and replace the active `mpaStructure.xlsx` file.
- The endpoint validates that the uploaded file is an Excel workbook with headers, backs up the existing active structure file, and then activates the new one.
- Added backend tests for structure replacement and non-Excel rejection.


- Added a dedicated frontend structure-management page at `client/src/pages/StructureBuilderPage.tsx`.
- The page supports:
  - uploading a fresh report to preview suggested structure headers,
  - editing every suggested header inline before saving,
  - directly uploading a manually prepared structure file.
- Added backend endpoints:
  - `POST /structure/preview`
  - `POST /structure/save`
  - `POST /structure/upload`
- Added an ellipsis menu on the main upload page to hide `View History` and `Upload Structure File` actions behind a compact menu.


- Refined the Structure Builder UX:
  - added active structure status display using the uploaded/display filename instead of the internal `mpaStructure.xlsx` name,
  - added cancel buttons for both selected source-report files and direct structure uploads,
  - added searchable editable column names once editable headers are available,
  - added a confirmed-tag checklist for common structure tags,
  - made the main-page ellipsis menu fully teal-themed.
- Added `GET /structure/status` to fetch the active structure metadata.
- Fixed duplicate edited-header save failures by auto-resolving duplicate names with suffixes during save instead of rejecting the request.


- Grouped the Structure Builder checklist into `Confirmed` and `Still Missing` sections for easier scanning.
- Restored the ellipsis menu to a white dropdown surface while keeping teal text and hover styling.


## 2026-04-07 Backend Logging And August Debugging
- Added staged backend logging in `server/app/services/upload_parser.py` and `server/app/services/reporting.py` so the manual parse flow now logs:
  - upload/body read start and completion
  - structure-template candidate selection
  - exact or nearest structure-template choice
  - header overlay completion
  - parse completion with structure path, missing fields, and zone count
  - report context build start/completion
  - branch-metric processing
  - template render start/completion
  - cleanup start/completion
- Added logging bootstrap in `server/app/main.py` using a consistent timestamped INFO format.
- Fixed a manual-parser edge case where the active `server/mpaStructure.xlsx` could be ignored if another `mpaStructure*.xlsx` sibling had the same column count.
- The parser now always prefers the configured active `mpaStructure.xlsx` first, then only falls back to sibling templates when the active structure does not match.
- Added a regression test in `server/tests/test_upload_parser.py` to ensure the active structure file wins when multiple templates share the same column count.
- Added a reporting validation test in `server/tests/test_reporting.py` to guarantee missing tagged columns raise a clear HTTP error instead of a raw `KeyError`.
- Verified with `AUGUST ZONAL DISTRIBUTION FOR BRANCHES.xlsx` that the original `'PBT Cost to Income Ratio'` failure path is gone once the active structure is preferred.
- Current August finding for `Abuja 07 Total`: the next blocking issue is now explicit and logged clearly as missing active-structure tags:
  - `CDS2 ACTIVE`
  - `CDS2 INACTIVE`
  - `CDS2 No. of Cards Issued`


## 2026-04-07 Log Readability And Structure Verification
- Reworded backend logs in `server/app/services/upload_parser.py` and `server/app/services/reporting.py` into plain-English step markers such as:
  - `[Parser] Step 1/4: Reading uploaded report body...`
  - `[Parser] Step 2/4: Selecting structure template...`
  - `[Report] Starting generation...`
  - `[Structure] Active structure replaced successfully...`
- Confirmed via Playwright on `http://localhost:5173` that the Structure Builder displays the active structure display name and can upload a direct structure file through the UI.
- For Playwright verification, ran a local SQLite-backed backend on `127.0.0.1:8000` because the previously running Supabase-backed server process was hanging during startup and browser requests were stalling.
- Browser-verified workflow:
  - uploaded `AUGUST ZONAL DISTRIBUTION FOR BRANCHES.xlsx` as the active structure file
  - confirmed the Structure Builder shows `AUGUST ZONAL DISTRIBUTION FOR BRANCHES.xlsx` as the active structure display name with `442` headers
  - returned to the upload page and attempted to generate `Abuja 07 Total` from the same August workbook
- Key finding from the browser run and backend logs:
  - before the latest parser correction, the manual parser still fell through to sibling template `server/mpaStructure AUGUST.xlsx` because it had an exact 461-column match
  - this proved the system was not strictly using the active `server/mpaStructure.xlsx` after a direct structure replacement
- Corrected the parser so the manual mode now uses only the configured active `server/mpaStructure.xlsx`.
- If the active structure header count does not match the uploaded report body, the parser now fails immediately with an active-structure mismatch instead of silently switching to a sibling `mpaStructure*.xlsx` file.
- Updated `server/app/services/reporting.py` so `ValueError` from workbook parsing becomes a clean HTTP `400` preview/generation error rather than a raw `500`.


## 2026-04-08 Structure Builder Full Column Editing
- Verified the August structure-preview pipeline returns all uploaded columns for manual editing:
  - `header_count = 461`
  - `original_headers` length = `461`
  - `suggested_headers` length = `461`
- Updated `client/src/pages/StructureBuilderPage.tsx` so the editable grid is built from the full maximum column count instead of assuming both header arrays are always identical in length.
- Added explicit UI copy in the suggestion summary stating that every uploaded column remains editable even when no suggestion is available yet.
- Added a visible `Showing X of Y columns` indicator beside the header search so it is clear the editor is not hiding unmapped columns unless the current search text filters them out.
- Rebuilt the frontend successfully with `npm run build`.


## 2026-04-08 Database Connection Clarification
- Verified the temporary local history count came from `server/mp_analyzer_playwright.db`, which contains:
  - `profiles = 2`
  - `report_runs = 4`
- Confirmed there is no MySQL dependency in this repo; the local database used during Playwright verification is SQLite.
- Fixed `server/app/config.py` so the backend always loads `server/.env` via an absolute path, even when started from the repository root.
- Verified the Supabase connection from the repository root after the config fix:
  - `profiles = 1`
  - `report_runs = 38`
- Restarted the backend on `127.0.0.1:8000` against Supabase, replacing the temporary local SQLite-backed process.


## 2026-04-08 Mystery Server Troubleshooting
- Verified that `http://127.0.0.1:8000/profiles/1/history` was still responding even when the user believed no backend had been started.
- Traced the listener with `netstat -ano` and found a local process bound to `127.0.0.1:8000`:
  - PID `50192`
  - process name `python3.11`
  - start time `2026-04-08 10:56:45`
- Identified the most recent server log sink in the repo as:
  - `server/uvicorn8000-supabase.err.log`
- Stopped PID `50192` and verified the endpoint no longer responds:
  - `URLError [WinError 10061] No connection could be made because the target machine actively refused it`


## 2026-04-08 September Abuja 07 Calibration
- Used the September source workbook `SEPTEMBER ZONAL DISTRIBUTION FOR BRANCHES.xlsx` together with the user-provided source-of-truth write-up `SEPT MPR_OSCAR (1).docx` to compare the manual structure path against the expected output for `Abuja 07 Total`.
- Confirmed the drift was caused by ambiguous tagged columns in the active `mpaStructure.xlsx`, not by numeric formatting alone.
- Root causes found in the manual structure file:
  - duplicate `PBT 2025 YTD ACHVD` headers where the first occurrence pointed to an old historical year and the second occurrence held the real 2025 achieved value
  - duplicate `DP` month and `DP YTD Variance` tags where the system was reading the wrong deposit block instead of the domiciliary deposit block used in the write-up
  - `TRA May-25`, `TRA Jun-25`, `TRA Jul-25`, and `TRA YTD Variance` were tagged against the wrong TRA subsection instead of the `TRA TOTAL RISK ASSETS` block used in the write-up
  - `AB Jun-25`, `AB Jul-25`, and `AB VAR` were mapped to the wrong agency-banking subsection instead of the value block used in the write-up
- Fine-tuned `server/app/services/upload_parser.py` so the manual parser now applies alias corrections after the normal header swap:
  - prefers the later duplicate for `PBT 2025 YTD ACHVD`
  - prefers the later duplicate DP month/YTD columns
  - aliases TRA month slots to the `TRA TOTAL RISK ASSETS` block
  - aliases AB month/variance slots to the `AB VALUE` block
- Fine-tuned `server/app/services/reporting.py` so write-up-facing presentation now matches the September reference document better:
  - `AB VAR` is rendered as a magnitude for the write-up table
  - `NXP YOY VAR` is rendered as a magnitude
  - zero NXP monthly values render as `0.00`
- Fixed `server/app/config.py` so relative `.env` overrides like `./mpaStructure.xlsx` and `./mpatemplate.docx` are resolved relative to `server/`, preventing silent path drift when the backend is started from the repository root.
- Re-verified `Abuja 07 Total` after the calibration:
  - `PBT`: `13.53B`, `43.17B`, `31`, `3.06B`, `9.88B`, `143`
  - `DDA`: `58.25B`, `60.11B`, `66.19B`, `40`, `13.08B`
  - `SAV`: `23.77B`, `23.83B`, `24.09B`, `44`, `1.36B`
  - `FD`: `5.77B`, `5.06B`, `4.76B`, `35`, `2.97B`
  - `DP`: `59.9M`, `59.8M`, `58M`, `160`, `35.9M`
  - `TRA`: `5.62B`, `5.39B`, `5.63B`, `3`, `307M`
  - `AB`: `297.70M`, `99.50M`, `198.20M`
  - `NXP`: `0.00`, `0.00`, `0.00`, `554.50K`
- Backend verification after the calibration:
  - `pytest tests/test_upload_parser.py tests/test_reporting.py` passed from `server/`: `9 passed`


## 2026-04-08 September Full Docx Audit
- Ran a full comparison of every zone present in `SEPT MPR_OSCAR (1).docx` against the current manual-system output from `SEPTEMBER ZONAL DISTRIBUTION FOR BRANCHES.xlsx`.
- Confirmed the September write-up contains 8 zone sections and 112 tables:
  - `ABUJA 07`
  - `ABUJA 08`
  - `ABUJA 09`
  - `ABUJA 10`
  - `COKER-TRADE FAIR`
  - `IKEJA`
  - `IKORODU 1`
  - `IKORODU 2`
- Found that the `.docx` does not keep the exact same table order for every zone, so later-zone comparisons had to be classified by table header meaning rather than by a fixed table index.
- Full-audit findings after the Abuja 07 calibration:
  - `ABUJA 07`: only presentation drift remained (`58.0M` in the write-up vs `58M` in the app)
  - `ABUJA 08`: 3 mismatches, all in sign/format handling for DP and TRA YTD values
  - `ABUJA 09`: 3 mismatches, including a sign issue on DDA YTD, DP formatting, and `NXP` zero display
  - `ABUJA 10`: 2 mismatches, both sign handling on `FD`/`DP` YTD values
  - `COKER-TRADE FAIR`: 6 mismatches, including sign handling plus `AB` magnitude formatting (`2.211B` vs `2211.20M`)
  - `IKEJA`: 3 mismatches, all in `TRA` interpretation/sign handling and DP sign handling
  - `IKORODU 1`: 12 mismatches, with the major remaining issue being that the write-up swaps `DDA` and `SAV` relative to the current system for this zone
  - `IKORODU 2`: 3 mismatches, including sign handling and a `DMT_ACT_value3` mismatch where the write-up shows `227%` but the workbook row contains a normalized percentage value used by the app
- Conclusion from the full audit:
  - the Abuja 07 calibration generalized well for many core sections
  - the biggest remaining system issues are:
    - sign/presentation rules for YTD variance fields, which are not consistent with how the write-up chooses to display adverse variances
    - a likely `DDA`/`SAV` label swap in the structure or write-up for `IKORODU 1`
    - some write-up tables use billions notation where the app is still outputting millions notation for the same magnitude


## 2026-04-08 Formatter Rule Update
- Updated `server/app/services/normalization.py` to follow the new user-defined scaling rules:
  - million-scaled columns (`N'm`, `$'m`) now use:
    - `< 1000` as `M`
    - `>= 1000` as `B`
  - thousand-scaled columns (`$'000`) now use:
    - `< 1000` as `K`
    - `>= 1000` as `M`
- Implemented a shared scaled-number formatter that:
  - keeps up to 2 decimal places
  - collapses exact integers to no decimal places
  - keeps one decimal place only when the second decimal is zero
  - uses truncation (`ROUND_DOWN`) to stay aligned with the provided examples such as `234,787 -> 234.78B`
- `format_billions` and `format_dp_millions` now both follow the million-scaled rule.
- `format_millions` now follows the thousand-scaled rule.
- Added regression coverage in `server/tests/test_normalization.py` for the user examples:
  - `1 -> 1M`
  - `123 -> 123M`
  - `1,234 -> 1.23B`
  - `234,787 -> 234.78B`
  - and the corresponding `$'000` examples for `K/M`
- Updated `server/tests/test_reporting.py` to align magnitude formatting expectations with the new scaling rule.
- Verified:
  - `pytest tests/test_normalization.py tests/test_reporting.py` passed from `server/`: `9 passed`


## 2026-04-08 Sign And Plain-Count Clarifications Applied
- Applied the new user clarification that plain-count sections should not use K/M/B formatting:
  - `ACCOUNTS OPENED`
  - `CARDS`
  - `CHANNELS ENROLLED`
  - `AGENTS ONBOARDED`
  - `POS`
- Confirmed the current reporting layer already renders those sections as plain comma-separated integers, so no code change was needed there.
- Applied the user’s sign/presentation guidance to variance-style report outputs:
  - `DDA_value5`
  - `SAV_value5`
  - `FD_value5`
  - `DP_value5`
  - `TRA_value5`
  now render as magnitudes in the report context.
- Kept `NXP` monthly zero values as `0.00`.
- Added tests in `server/tests/test_reporting.py` for:
  - absolute magnitude formatting for billion- and DP-scaled variance outputs
  - zero-safe `NXP` formatting
- Re-verified:
  - `pytest tests/test_normalization.py tests/test_reporting.py` passed from `server/`: `11 passed`
- Spot-checked September examples after the change:
  - `ABUJA 08 Total`: `DP_value5 = 7.55M`, `TRA_value5 = 3.17B`
  - `ABUJA 10 Total`: `FD_value5 = 2.2B`, `DP_value5 = 6.4M`
  - `COKER-TRADE FAIR Total`: `DDA_value5 = 4.05B`, `DP_value5 = 0.37M`, `TRA_value5 = 251.28M`


## 2026-04-08 Formatter Calibration Follow-Up
- Refined the million-scaled formatter so values below `1M` now render in `K`:
  - example: `0.3725 -> 372.5K`
- Refined the thousand-scaled formatter so very large values can roll up to `B`:
  - example: `2211279.746 -> 2.21B`
- Corrected `AB` report values back to the thousand-scaled formatter after confirming the raw workbook values are in thousands, not millions.
- Re-verified five workbook-driven September zones after the change:
  - `ABUJA 07 Total`
  - `ABUJA 08 Total`
  - `ABUJA 10 Total`
  - `COKER-TRADE FAIR Total`
  - `IKORODU 1 Total`
- Test status after the follow-up:
  - `pytest tests/test_normalization.py tests/test_reporting.py` passed from `server/`: `11 passed`


## 2026-04-08 Full Audit Rerun After Final Formatter Rules
- Reran the full September `.docx` audit after applying:
  - workbook-as-truth for `IKORODU 1` `DDA`/`SAV`
  - `K/M/B` formatter corrections
  - thousand-scale `AB` formatter with `B` rollover
- The remaining mismatches now split into two categories:
  - cosmetic precision/presentation drift
  - a small set of real semantic mismatches
- Cosmetic drift examples:
  - `59.8M` vs `59.83M`
  - `554.50K` vs `554.5K`
  - `2.211B` vs `2.21B`
  - `0.00` vs `0K`
- Real semantic mismatches that remain:
  - `IKEJA Total`: `TRA_value4` write-up shows `145`, app shows `1`
  - `IKORODU 1 Total`: write-up still swaps `DDA` and `SAV` relative to the workbook, but the app now intentionally follows the workbook
  - `IKORODU 2 Total`: `DMT_ACT_value3` write-up shows `227`, app shows workbook-driven `2`
- Full-audit status after the rerun:
  - all 8 zones still have at least one mismatch if exact string equality is enforced
  - most remaining mismatches are now precision/style differences rather than wrong source-column extraction


## 2026-04-08 December Structure Update And Audit
- Confirmed the active structure was updated to `DECEMBER ZONAL DISTRIBUTION FOR BRANCHES.xlsx` via `server/mpaStructure.meta.json`.
- Parsed `DECEMBER ZONAL DISTRIBUTION FOR BRANCHES.xlsx` successfully with:
  - `period = Oct-25 to Dec-25`
  - `missing_fields = []`
  - `zones = 154`
- Initial December generation failed because the new structure file exposed card blocks as:
  - `AO 224 CARDS NOVEMBER No. of Cards Issued`
  - `AO 234 ACTIVE`
  - `AO 235 INACTIVE`
  - `AO 224 CARDS DECEMBER No. of Cards Issued`
  - `AO 234 ACTIVE__2`
  - `AO 235 INACTIVE__2`
  instead of the expected `CDS1` / `CDS2` tags.
- Updated the manual alias resolver in `server/app/services/upload_parser.py` so the last two detected card blocks are mapped automatically to:
  - `CDS1 No. of Cards Issued`
  - `CDS1 ACTIVE`
  - `CDS1 INACTIVE`
  - `CDS2 No. of Cards Issued`
  - `CDS2 ACTIVE`
  - `CDS2 INACTIVE`
- Added a regression test in `server/tests/test_upload_parser.py` for the December-style card block aliasing.
- Verified the December report context now builds successfully for `ABUJA 07 Total`.
- Ran a December full audit against `DECEMBER MPR - CORRECTED.docx`.
- December audit result:
  - no zone is yet a perfect exact-string match
  - a large share of the remaining drift is still precision-only, e.g.:
    - `59.4M` vs `59.49M`
    - `3.70B` vs `3.7B`
    - `554.50K` vs `554.5K`
  - key real December semantic mismatches remain in:
    - `IKEJA` where `SAV` and `FD` appear swapped between the workbook-driven app output and the corrected write-up
    - `IKORODU 1` where `DDA` and `SAV` appear swapped
    - `IKORODU 2` where `DMT_ACT_value3` differs materially (`148` in the write-up vs workbook-driven `1`)
- Verification after the December alias fix:
  - `pytest tests/test_upload_parser.py tests/test_reporting.py` passed from `server/`: `12 passed`


## 2026-04-09 December Targeted Inspection
- Inspected the December workbook directly for the three user-specified concern areas:
  - `IKEJA SAV/FD`
  - `IKORODU 1 DDA/SAV`
  - `IKORODU 2 DMT_ACT_value3`
- Findings:
  - `IKEJA` workbook values show the app is correct:
    - `SAV` rows in the workbook are `37.99B`, `37.75B`, `38.44B`, `8.66B`
    - `FD` rows in the workbook are `44.65B`, `31.82B`, `21.21B`, `9.84B`
    - the earlier mismatch came from the December write-up audit classifier, which assumed the larger of the two rolling blocks must be `SAV`; for `IKEJA`, `FD` is actually larger than `SAV`
  - `IKORODU 1` workbook values also show the app is correct:
    - `DDA` is `33.21B`, `34.92B`, `35.03B`, `4.83B`
    - `SAV` is `36.79B`, `37.68B`, `38.62B`, `5.67B`
    - the earlier mismatch again came from the write-up table classifier rather than the report extraction
  - `IKORODU 2 DMT_ACT_value3` is a real app issue:
    - workbook raw `% Reactivated DMT_ACT = 1.483652843719201`
    - corrected write-up shows `148%`
    - current app output is `1` because `format_percentage()` only multiplies by 100 when the value is `<= 1`
- Conclusion:
  - `IKEJA SAV/FD` is not a workbook-mapping bug
  - `IKORODU 1 DDA/SAV` is not a workbook-mapping bug
  - `IKORODU 2 DMT_ACT_value3` is a real percentage-scaling bug in the reporting layer


## 2026-04-09 December DMT Reactivation Fix
- Added a dedicated `_format_reactivated_percentage()` helper in `server/app/services/reporting.py`.
- Switched `DMT_ACT_value3` to use the dedicated reactivation formatter instead of the generic `format_percentage()`.
- The new rule treats `% Reactivated DMT_ACT` as a ratio-like field whenever the absolute value is below `10`, so:
  - `0.079748... -> 8`
  - `1.483652... -> 148`
- Added regression coverage in `server/tests/test_reporting.py` for both cases.
- Verified for `IKORODU 2 Total` in the December workbook:
  - `DMT_ACT_value1 = 11,512`
  - `DMT_ACT_value2 = 172`
  - `DMT_ACT_value3 = 148`
- Verification:
  - `pytest tests/test_reporting.py` passed from `server/`: `8 passed`


## 2026-04-13 Point One Rollback Baseline
- Marked this state as **Point One** before starting the dynamic-writeup phase.
- Point One behavior:
  - manual `mpaStructure.xlsx` header-swap remains the extraction source of truth
  - Word document rendering still uses `docxtpl` and the existing `mpatemplate.docx`
  - report tables remain template-driven and must not be replaced in this phase
  - only write-up/summary placeholders should become dynamic in Phase 1
- Rollback target if needed:
  - restore static summary placeholders in `server/app/services/reporting.py`
  - remove/ignore the new `server/app/analysis` layer


## 2026-04-13 Phase 1 Dynamic Write-Up
- Implemented Phase 1 of dynamic analysis while preserving the existing Word document tables.
- Added a backend analysis layer:
  - `server/app/analysis/models.py`
  - `server/app/analysis/narratives.py`
  - `server/app/analysis/__init__.py`
- The report renderer still builds all existing table values from the workbook-driven reporting context.
- The new analysis layer only replaces summary/write-up placeholders such as:
  - `PBT_summary`
  - `DDA_summary`
  - `SAV_summary`
  - `FD_summary`
  - `DP_summary`
  - `TRA_summary`
  - `AB_summary`
  - `CDS_summary`
  - `POS_summary`
- `server/app/services/reporting.py` now calls `build_report_analysis()` after the existing context is built, then merges the generated summaries back into the `docxtpl` context.
- No Word template structure changes were made; tables remain intact and template-driven.
- Added regression coverage in `server/tests/test_analysis_narratives.py`.
- Verification:
  - `pytest tests/test_analysis_narratives.py tests/test_reporting.py` passed from `server/`: `9 passed`
  - live context check with `DECEMBER ZONAL DISTRIBUTION FOR BRANCHES.xlsx` and `ABUJA 07 Total` produced dynamic summary text instead of static placeholders.


## 2026-04-13 Phase 2 Analytical Write-Up
- Upgraded the dynamic write-up layer from fact-only sentences to analytical movement commentary.
- `server/app/analysis/narratives.py` now includes helpers for:
  - reading formatted values such as `1.23B`, `372.5K`, percentages, commas, and accounting negatives like `(14.16M)`
  - detecting growth, decline, or broadly flat movement between periods
  - calculating displayed percentage movement between prior and current period values
  - describing favorable/adverse variance language for write-ups
  - wording branch contribution as percentages instead of bare numbers
- The Word document tables remain unchanged and template-driven.
- The Phase 2 write-up now gives clearer movement commentary for rolling-period sections:
  - `DDA_summary`
  - `SAV_summary`
  - `FD_summary`
  - `DP_summary`
  - `TRA_summary`
  - `AB_summary`
- Added tests for:
  - growth wording
  - decline wording
  - branch contribution wording
  - adverse accounting-negative variance wording
- Verification:
  - `pytest tests/test_analysis_narratives.py tests/test_reporting.py` passed from `server/`: `10 passed`


## 2026-04-13 Phase 2 Variance Language Calibration
- Tuned branch-level narrative wording so negative variance values are called out explicitly.
- Behavior:
  - positive branch variance renders as `a MOM variance of ...`
  - negative branch variance renders as `a negative MOM variance of ...`
  - PBT branch monthly variance uses the same negative-aware wording with `monthly variance`
- Added punctuation handling in `ReportAnalysis.to_template_context()` so generated summaries do not end with a full stop before being inserted into the Word template; this prevents rendered `..` output because the template already supplies final punctuation.
- Cleaned the TRA summary wording so `YTD variance` remains properly capitalized.
- Verified with `North-East 2 Total` from `DECEMBER ZONAL DISTRIBUTION FOR BRANCHES.xlsx`.
- North-East 2 DDA rendered output now includes:
  - `Gombe led the zone with 55% contribution and a negative MOM variance of -1.93B`
  - `Potiskum recorded the lowest contribution at 4%, with a MOM variance of 17.3M`
- Verification:
  - `pytest tests/test_analysis_narratives.py tests/test_reporting.py` passed from `server/`: `10 passed`


## 2026-04-13 Phase 2 Template-Aware Variance And Month Calibration
- Updated the report context and Word template so branch bullet lines can use dynamic variance labels instead of hardcoded `MOM variance`.
- Branch variance values now include the Naira sign in generated narrative/bullet output:
  - `₦-1.93B`
  - `₦17.3M`
- Branch variance labels now resolve from the value sign:
  - negative values render as `Negative MOM variance`
  - positive values render as `Positive MOM variance`
  - zero values remain `MOM variance`
- Updated `server/mpatemplate.docx` branch bullets to use new placeholders:
  - `*_branch_high_var_label`
  - `*_branch_low_var_label`
- Added detected-period month placeholders to `server/mpatemplate.docx` so report headings/table labels follow the uploaded report period:
  - `period_month_1`
  - `period_month_2`
  - `period_month_3`
  - `period_month_previous`
  - `period_month_current`
  - `report_month`
- Added backend period-label parsing in `server/app/services/reporting.py`; example:
  - `Oct-25 to Dec-25` renders `OCTOBER`, `NOVEMBER`, `DECEMBER`
  - `Sep-25 to Nov-25` renders current/report month as `NOVEMBER`
- Verified by rendering `North-East 2 Total` from `DECEMBER ZONAL DISTRIBUTION FOR BRANCHES.xlsx`.
- Rendered DDA output now includes:
  - `Gombe led the zone with 55% contribution and a Negative MOM variance of ₦-1.93B`
  - `Potiskum recorded the lowest contribution at 4%, with a Positive MOM variance of ₦17.3M`
- Verification:
  - `pytest tests/test_analysis_narratives.py tests/test_reporting.py` passed from `server/`: `12 passed`


## 2026-04-13 Netlify Deployment Check
- Checked `https://mp-analyzer.netlify.app`.
- The site loads and redirects to `/profiles/select`, but the deployed profile page crashes with:
  - `TypeError: r.map is not a function`
- Network inspection showed the deployed frontend requested:
  - `GET https://mp-analyzer.netlify.app/profiles`
- Diagnosis:
  - the deployed Netlify build is missing or misconfigured `VITE_API_URL`
  - because the API base URL is missing, Axios uses a relative `/profiles` URL
  - Netlify returns the React app HTML instead of backend JSON
  - the profile screen then tries to call `.map()` on a non-array response
- Client hardening added:
  - `client/src/services/api.ts` validates that `/profiles` returns an array and throws a clear API configuration error otherwise
  - `client/src/pages/SelectProfilePage.tsx` catches profile-loading errors and displays a visible error instead of crashing the whole page
- Deployment action still required:
  - set `VITE_API_URL` in Netlify to the deployed backend API URL
  - rebuild/redeploy the Netlify site after setting the variable
- Verification:
  - `npm run build` passed from `client/`


## 2026-07-17 Root Dev Entrypoint Rollback
- Removed the temporary root-level `package.json` and `package-lock.json`.
- The project is back to manual startup from the app directories:
  - backend should be started from `server/`
  - frontend should be started from `client/`
- Reason:
  - the helper script depended on a root `node_modules` install and was less reliable than the explicit per-app commands for this repo


## 2026-07-20 June 2026 Template Conversion Prep
- Used `JUNE 2026 MPR REVIEW FORMAT.docx` as the source-of-truth reference document.
- Used `new mpa template.docx` as the in-progress target template.
- The original target template file was locked, so the conversion was saved as a new file:
  - `C:\Users\Chidera Aniekwe\Documents\new mpa template.converted.docx`
- Also created a safety backup:
  - `C:\Users\Chidera Aniekwe\Documents\new mpa template.backup.before-codex.docx`
- Converted remaining narrative prose in the target template into placeholders for:
  - PBT commentary (`PBT_summary_1` to `PBT_summary_3`)
  - DDA commentary (`DDA_summary_1` to `DDA_summary_2`)
  - Savings commentary (`SAV_summary_1` to `SAV_summary_3`)
  - Fixed Deposit commentary (`FD_summary_1` to `FD_summary_2`)
  - Domiciliary Deposit commentary (`DP_summary_1` to `DP_summary_2`)
  - Total Risk Assets commentary (`TRA_summary_1` to `TRA_summary_3`)
  - Agency Banking commentary (`AB_summary_1`)
  - Accounts Opened summary (`AO_summary`)
  - Cards summary (`CDS_summary`)
  - Channels Enrolled summary (`CE_summary`)
  - Agents Onboarded summary (`AOB_summary`)
  - Dormant Accounts summary (`DMT_ACT_summary`)
  - POS summary (`POS_summary`)
  - NXP summary (`NXP_summary`)
  - Final overall summary (`FINAL_summary_1` to `FINAL_summary_3`)
- Added the two new requested top-level placeholders:
  - `zone_branch_count`
  - `zonal_head_name`
- Fixed table placeholder consistency in the converted template:
  - corrected PBT `% ON BUDGET` from `PBT_value2` to `PBT_value3`
  - standardized month placeholders to lowercase backend-friendly names:
    - `period_month_1`
    - `period_month_2`
    - `period_month_3`
- Verified the converted template exposes the new placeholders through `docxtpl`.


## 2026-07-20 June 2026 Template Wiring
- Wired the new June 2026 template contract into the backend reporting pipeline.
- Updated `server/app/services/reporting.py` to add:
  - `zone_branch_count` derived from the branch rows under the selected zone
  - `zonal_head_name` derived from the workbook column literally named `ZONAL HEAD`
  - uppercase compatibility aliases required by the converted Word template:
    - `ZONAL_HEAD_NAME`
    - `PERIOD_MONTH_1`
    - `PERIOD_MONTH_2`
    - `PERIOD_MONTH_3`
  - additional narrative helper context sourced from the workbook, including:
    - negative-variance branch lists
    - top budget-performing branches for DDA, SAV, FD, and DP
    - LDR high/low branch signals
    - accounts-opened summary signals
    - active-branch count for agents onboarded
- Rebuilt `server/app/analysis/narratives.py` so it now emits the June-style split placeholders expected by the new template:
  - `PBT_summary_1` to `PBT_summary_3`
  - `DDA_summary_1` to `DDA_summary_2`
  - `SAV_summary_1` to `SAV_summary_3`
  - `FD_summary_1` to `FD_summary_2`
  - `DP_summary_1` to `DP_summary_2`
  - `TRA_summary_1` to `TRA_summary_3`
  - `AB_summary_1`
  - `AO_summary`
  - `CDS_summary`
  - `CE_summary`
  - `AOB_summary`
  - `DMT_ACT_summary`
  - `POS_summary`
  - `NXP_summary`
  - `FINAL_summary_1` to `FINAL_summary_3`
- Preserved legacy aggregate summary keys as compatibility output while introducing the new split keys.
- Updated `server/app/analysis/models.py` so generated summary paragraphs keep their punctuation, which matches the new template layout.
- Updated the structure builder checklist in `client/src/pages/StructureBuilderPage.tsx` to include `ZONAL HEAD`, so the new required column is visible during structure tagging.
- Fixed a frontend typing issue in `client/src/hooks/useMainForm.ts` uncovered during build verification.
- Saved the converted live template as:
  - `server/mpatemplate.june-2026.docx`
- Updated template defaults to point at the new file:
  - `server/app/config.py`
  - `server/.env`
- Important runtime note:
  - `server/mpatemplate.docx` was locked by another process during implementation, so it could not be overwritten in place on July 20, 2026.
  - the backend is now configured to use `server/mpatemplate.june-2026.docx` instead, which contains the converted June 2026 placeholders.
- Verification:
  - backend tests: `..\.venv\Scripts\python.exe -m pytest tests/test_analysis_narratives.py tests/test_reporting.py` -> `12 passed`
  - frontend build: `npm run build` in `client/` -> passed
  - verified the new template placeholder contract directly with `docxtpl` against `server/mpatemplate.june-2026.docx`


## 2026-07-20 Apapa Metadata Fix
- Investigated the incorrect `Apapa` output where the generated report showed:
  - `BRANCH NO: 11`
  - `ZONAL HEAD: nan`
- Verified against:
  - `C:\Users\Chidera Aniekwe\Documents\JUNE'26 ZONAL DISTRIBUTION FOR BRANCHES.xlsx`
  - `C:\Users\Chidera Aniekwe\Documents\JUNE 2026 MPR REVIEW FORMAT.docx`
- Root cause:
  - branch selection logic was using substring matching on `ZONES`, so `Apapa` was incorrectly pulling in `Apapa 2` rows
  - zonal head was being read from the `... Total` summary row, where the workbook cell is blank
- Fix applied in `server/app/services/reporting.py`:
  - branch rows are now matched by exact zone name after removing the `Total` suffix
  - blank `BRANCHES` rows are excluded from branch counting
  - `zonal_head_name` now falls back to the first non-empty `ZONAL HEAD` value from the matched branch rows
- Added regression coverage in `server/tests/test_reporting.py` for the overlapping-zone-name case (`Apapa` vs `Apapa 2`).
- Verification:
  - `..\.venv\Scripts\python.exe -m pytest tests/test_reporting.py tests/test_analysis_narratives.py` -> `13 passed`
  - regenerated report now shows:
    - `BRANCH NO: 7`
    - `ZONAL HEAD: ROBERT ORAGBON`
  - regenerated file saved to:
    - `server/generated-reports/APAPA_Report_fixed.docx`


## 2026-07-20 Narrative Language Pass
- Updated `server/app/services/reporting.py` so the PBT narrative context now includes:
  - `PBT_negative_mom_branches`
  instead of only the previous `PBT_negative_mom_branch_count`.
- Updated `server/app/analysis/narratives.py` so the PBT summary now lists the branches with negative MOM variance and their figures directly, instead of only stating the branch count.
- Updated `server/app/analysis/narratives.py` so:
  - `Domiciliary Deposits` narrative lines use `$`
  - `NXP` narrative lines use `$`
- Refreshed `server/tests/test_analysis_narratives.py` to assert:
  - the branch-by-branch negative MOM wording in `PBT_summary_3`
  - dollar-prefixed DP summary text
  - dollar-prefixed NXP summary text
- Verification:
  - `..\.venv\Scripts\python.exe -m pytest tests/test_analysis_narratives.py tests/test_reporting.py` -> `13 passed`
  - regenerated report saved to:
    - `server/generated-reports/APAPA_Report_language-pass.docx`
  - verified rendered output examples:
    - `Expected run rate settled at ₦113.47B, while cost-to-income ratio closed at 73%. Branches with negative MOM variance in the current month include Creek Road (₦208.26M), Trinity 2 (₦51.48M), Apapa (₦42.97M), Trinity 1 (₦33.28M), and Marine Road (₦25.98M).`
    - `NXP closed at $7.3M in December, from $16.58M in November, while the year-on-year variance closed at $34.12M.`


## 2026-07-20 Dynamic Table Font Colouring Phase 1
- Implemented dynamic month-trend font colouring for table values in `server/app/services/reporting.py`.
- Rule implemented:
  - month 2 is compared against month 1
  - month 3 is compared against month 2
  - if the newer value is higher, the newer month is coloured green
  - if the newer value is lower, the newer month is coloured red
  - if the values are equal, the newer month remains black
- Added a `_trend_rich_text()` helper that emits `docxtpl.RichText` with:
  - green: `008000`
  - red: `FF0000`
  - neutral: `000000`
- Preserved plain string month values for narratives and added parallel rich-text context keys for table rendering:
  - `DDA_value2_r`, `DDA_value3_r`
  - `SAV_value2_r`, `SAV_value3_r`
  - `FD_value2_r`, `FD_value3_r`
  - `DP_value2_r`, `DP_value3_r`
  - `TRA_value2_r`, `TRA_value3_r`
  - `NXP_value2_r`, `NXP_value3_r`
- Updated `server/mpatemplate.june-2026.docx` placeholders so the month 2 / month 3 cells now use `{{r ...}}` rich-text tags for the trend-sensitive fields above.
- Added regression coverage in `server/tests/test_reporting.py` for rich-text colour output.
- Verification:
  - `..\.venv\Scripts\python.exe -m pytest tests/test_reporting.py tests/test_analysis_narratives.py` -> `14 passed`
  - regenerated report saved to:
    - `server/generated-reports/APAPA_Report_colored.docx`
  - verified the rendered `.docx` XML contains both:
    - `008000`
    - `FF0000`


## 2026-07-20 Currency-In-Table And Agency Banking Colouring Pass
- Moved table currency signs out of the Word template and into backend-rendered values.
- Updated `server/app/services/reporting.py` so monetary table fields now carry their own signs:
  - `₦` for naira-denominated table values
  - `$` for Domiciliary Deposit and NXP table values
- Updated the rich-text trend helper so the sign and the numeric value are rendered in the same colored run.
- Added Agency Banking month comparison support:
  - `AB_value2_r` now compares the second month against the first month
  - the Agency Banking month-2 value is colored using the same red/green rule
- Rebuilt `server/mpatemplate.june-2026.docx` safely from the converted source template after an intermediate XML patch corrupted the document structure.
- Reapplied the rich-text placeholders through structured XML editing rather than raw regex replacement.
- Template outcome after the rebuild:
  - hardcoded table currency runs were removed for the backend-driven monetary placeholders
  - only the remaining section-label currency text stayed in the template
- Verification:
  - `..\.venv\Scripts\python.exe -m pytest tests/test_reporting.py tests/test_analysis_narratives.py` -> `14 passed`
  - regenerated report saved to:
    - `server/generated-reports/APAPA_Report_currency-colored.docx`
  - verified in the rendered `.docx` XML:
    - green trend runs: `008000`
    - red trend runs: `FF0000`
    - backend-driven dollar table values such as `$61.73M`, `$65.69M`, `$16.58M`, `$7.3M`


## 2026-07-20 Variance Colour Rule
- Implemented the next table-colour rule for variance cells:
  - negative YOY/YTD variance values render in red
  - positive YOY/YTD variance values render in green
- Added a dedicated variance formatter split in `server/app/services/reporting.py`:
  - `_format_variance_text()` for narrative-safe plain values
  - `_variance_rich_text()` for table rendering with colour and currency sign in the same run
- Negative table variance values now use accounting-style parentheses in the rendered table values.
- Added rich-text table placeholders for:
  - `PBT_value4_r`
  - `DDA_value5_r`
  - `SAV_value5_r`
  - `FD_value5_r`
  - `DP_value5_r`
  - `TRA_value5_r`
  - `NXP_value4_r`
- Reused the existing Agency Banking month-2 colour rule from the prior pass.
- Verification:
  - `..\.venv\Scripts\python.exe -m pytest tests/test_reporting.py tests/test_analysis_narratives.py` -> `14 passed`
  - regenerated report saved to:
    - `server/generated-reports/APAPA_Report_variance-colored.docx`
  - verified rendered XML includes:
    - green runs: `008000`
    - red runs: `FF0000`
    - negative variance examples such as `($95.2M)` and `($34.12M)` in the table output


## 2026-07-20 Variance Display Calibration
- Adjusted the YOY/YTD variance display style to match the desired preview format:
  - the rendered value now shows only the number and currency sign
  - accounting parentheses are no longer shown in the table output
  - colour still follows the original numeric sign, so negative values remain red and positive values remain green
- Kept the sign-handling logic centralized in `server/app/services/reporting.py`:
  - `_format_variance_text()` now returns the plain formatted magnitude for display
  - `_variance_rich_text()` still applies the correct colour and currency sign in the same rich-text run
- Verification:
  - regenerated report saved to:
    - `server/generated-reports/APAPA_Report_variance-no-parens.docx`
  - verified rendered XML includes:
    - `$95.2M`
    - `$34.12M`
    - `008000`
    - `FF0000`
  - verified rendered XML no longer includes:
    - `($95.2M)`
    - `($34.12M)`


## 2026-07-20 Agency Banking Variance And Branch Pressure Pass
- Applied the same no-parentheses variance display rule to the Agency Banking table.
- Updated `server/mpatemplate.june-2026.docx` so Agency Banking variance now renders through `{{r AB_value3_r}}` instead of the plain `{{AB_value3}}` placeholder.
- Extended `server/app/services/reporting.py` narrative context with:
  - `AB_negative_variance_branches`
- Tightened the analysis wording in `server/app/analysis/narratives.py` so branch-variance callouts are shorter and more direct across the key lines:
  - `Negative branch pressure came from ...`
  - `Negative MOM variance came from ...`
  - explicit `No branch recorded ...` fallback where no negative branch variance exists
- Verification:
  - `..\.venv\Scripts\python.exe -m pytest tests/test_reporting.py tests/test_analysis_narratives.py` -> `15 passed`
  - confirmed the June template now exposes:
    - `AB_value3_r`
    - `AB_value2_r`
    - `AB_summary_1`


## 2026-07-20 Uploaded-Workbook Period Detection Fix
- Fixed manual-structure mode so `detected_period_label` now comes from the uploaded workbook's raw headers instead of the saved structure headers.
- Root cause:
  - the active edited structure file can retain mixed legacy month-bearing headers
  - those saved structure headers caused period detection to drift to values like `Dec-25 to May-26`
  - the raw June workbook itself was correctly exposing `Apr-26 to Jun-26`
- Updated `server/app/services/upload_parser.py`:
  - `parse_uploaded_workbook()` now reads the raw workbook headers first
  - the parsed report still uses the manual structure for column mapping
  - only the period-label source changed, improving month-name accuracy without breaking the manual workflow
- Added regression coverage in `server/tests/test_upload_parser.py` to prove:
  - a mismatched structure period does not override the uploaded workbook's actual period window
- Verification:
  - direct parse of `JUNE'26 ZONAL DISTRIBUTION FOR BRANCHES.xlsx` now returns:
    - `Apr-26 to Jun-26`
  - `..\.venv\Scripts\python.exe -m pytest tests/test_upload_parser.py tests/test_reporting.py tests/test_analysis_narratives.py` -> `21 passed`


## 2026-07-21 Contribution Percentage Tightening Pass
- Tightened branch contribution wording so very small positive shares no longer read like `0%` or noisy fractional percentages.
- Updated `server/app/services/reporting.py`:
  - added `_format_share_percentage()`
  - true zero contribution still renders as `0`
  - any positive contribution below `1%` now renders as `less than 1`
  - all existing branch share fields now flow through that shared formatter
- This keeps the existing template wording natural, so places that already append `%` will now read as:
  - `less than 1%`
- Added regression coverage in `server/tests/test_reporting.py` for:
  - tiny positive share -> `less than 1`
  - zero share -> `0`
  - ordinary share -> rounded whole percentage text
- Verification:
  - `..\.venv\Scripts\python.exe -m pytest tests/test_reporting.py tests/test_analysis_narratives.py tests/test_upload_parser.py` -> `22 passed`


## 2026-07-21 Summary Variance Language And Structure Upload Review Pass
- Tightened summary variance language across the report engine so headline variance sentences now explicitly state whether the variance is positive or negative.
- Updated `server/app/services/reporting.py` with summary-only variance helpers:
  - `_summary_variance_direction()`
  - `_summary_variance_display()`
- Summary behavior now differs intentionally from the table behavior:
  - tables keep red/green sign signaling without parentheses
  - summaries render negative variance values in plain black text with parentheses, for example `(₦268.36M)`
- Updated `server/app/analysis/narratives.py` so summary wording now reads more directly, for example:
  - `closed the period under review`
  - `YOY negative variance of (...)`
  - `negative variance pressure came from ...`
- Tightened branch naming in negative-variance lists so entries now render with the `branch` suffix, for example:
  - `Benin branch (₦1.21B)`
- Verification:
  - `..\.venv\Scripts\python.exe -m pytest tests/test_reporting.py tests/test_analysis_narratives.py tests/test_upload_parser.py` -> `22 passed`
  - `npm run build` in `client/` -> passed


## 2026-07-21 Structure Builder Upload Review Revert
- Reverted the temporary structure-builder UI change that added an edit/review step to the direct structure upload flow.
- Restored the prior behavior in `client/src/pages/StructureBuilderPage.tsx`:
  - direct structure uploads once again replace the active structure file immediately
  - the existing report-based structure preview/editor flow remains unchanged
- The summary-variance tightening work from the same pass remains intact.
- Verification:
  - `npm run build` in `client/` -> passed


## 2026-07-21 Cards Narrative Tightening Pass
- Updated the cards narrative in `server/app/analysis/narratives.py` to follow the new exact sentence pattern requested by the user:
  - current-month cards issued
  - percentage growth from the previous period
  - previous-month cards issued with year
  - active cards count
  - inactive cards count
  - explicit low-issuance branch callout for branches that issued fewer than 100 cards in the current period
- Added cards-specific narrative context in `server/app/services/reporting.py`:
  - `CDS_previous_issued`
  - `CDS_current_issued`
  - `CDS_growth_pct`
  - `CDS_low_issuance_branches`
  - `CDS_low_issuance_branch_label`
- Current-period low-issuance branches are derived from branch rows using `CDS2 No. of Cards Issued`, which the current manual structure workflow treats as the latest card-issuance month.
- Confirmed current structure-builder behavior remains:
  - direct uploaded structure files are not editable after upload
  - editable review is still available only in the `Build From Current Report` preview/editor flow


## 2026-07-21 Direct Structure Review Revert
- Reverted the temporary direct-upload review pass for prepared structure files.
- Restored the prior behavior:
  - `Upload Prepared Structure File` now replaces the active structure immediately again
  - no separate editable review step runs for direct structure uploads
- `Build From Current Report` remains the only editable structure-review flow.


## 2026-07-21 NXP Zero-Case Narrative Tightening
- Tightened the NXP narrative in `server/app/analysis/narratives.py` for fully flat zero cases.
- New behavior:
  - when previous-month NXP, current-month NXP, and YOY variance are all zero, the report no longer says:
    - `NXP closed at $0.00 in June, from $0.00 in May, while the year-on-year variance closed at $0K.`
  - it now reads more naturally:
    - `NXP remained flat at $0.00 in June and May, with no year-on-year variance recorded.`
- Added regression coverage in `server/tests/test_analysis_narratives.py`.
- Verification:
  - `..\.venv\Scripts\python.exe -m pytest tests/test_analysis_narratives.py` -> `3 passed`
  - `..\.venv\Scripts\python.exe -m pytest tests/test_reporting.py` -> `14 passed`


## 2026-07-21 Broader Zero-Case Narrative Tightening
- Extended the flat-zero narrative tightening in `server/app/analysis/narratives.py` beyond NXP.
- Added clearer zero-activity wording for:
  - Domiciliary Deposits
  - Agency Banking
  - Channels Enrolled
  - Agents Onboarded
  - Dormant Account Reactivation
  - POS
- Example behavior:
  - flat zero monetary lines now say `remained flat ... with no ... variance recorded`
  - zero operational activity lines now say `No ... activity was recorded`
- Added regression coverage in `server/tests/test_analysis_narratives.py` for all of the above zero-case summaries.
- Verification:
  - `..\.venv\Scripts\python.exe -m pytest tests/test_analysis_narratives.py` -> `3 passed`
  - `..\.venv\Scripts\python.exe -m pytest tests/test_reporting.py` -> `14 passed`
