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
