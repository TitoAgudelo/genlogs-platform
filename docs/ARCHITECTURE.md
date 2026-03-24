# Genlogs Platform - Complete Technical Documentation

A comprehensive guide to understand every layer of the Genlogs freight analytics platform: database models, backend services, API endpoints, and frontend implementation.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Monorepo Structure](#2-monorepo-structure)
3. [Backend: Database Layer](#3-backend-database-layer)
4. [Backend: Data Access Layer](#4-backend-data-access-layer)
5. [Backend: Services (Business Logic)](#5-backend-services-business-logic)
6. [Backend: API Routes](#6-backend-api-routes)
7. [Backend: Application Startup](#7-backend-application-startup)
8. [Frontend: Application Shell](#8-frontend-application-shell)
9. [Frontend: Components Deep Dive](#9-frontend-components-deep-dive)
10. [Frontend: Styling System](#10-frontend-styling-system)
11. [Data Flow Walkthroughs](#11-data-flow-walkthroughs)
12. [Testing](#12-testing)
13. [How to Run](#13-how-to-run)

---

## 1. Project Overview

Genlogs is a **logistics analytics platform** that lets users:

- **Search carriers** operating between two US cities (e.g., "New York" to "Washington DC")
- **Visualize routes** on Google Maps with up to 3 alternative driving routes
- **Ask natural language questions** about freight data (e.g., "Which carriers go from SF to LA?")

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript |
| Backend | Python, FastAPI |
| Database | SQLite via SQLAlchemy ORM |
| Maps | Google Maps JavaScript API + Places API |
| Monorepo | Turborepo + pnpm workspaces |

---

## 2. Monorepo Structure

```
genlogs-platform/
├── apps/
│   ├── web/                  # Next.js frontend (port 3000)
│   ├── api/                  # FastAPI backend (port 8000)
│   └── docs/                 # Docs app (port 3001, boilerplate)
├── packages/
│   ├── ui/                   # Shared React component library
│   ├── typescript-config/    # Shared tsconfig presets
│   └── eslint-config/        # Shared ESLint presets
├── turbo.json                # Turborepo pipeline configuration
├── pnpm-workspace.yaml       # Workspace package discovery
└── package.json              # Root scripts and dev dependencies
```

### How Turborepo Works Here

`turbo.json` defines the task pipeline:

```json
{
  "tasks": {
    "build": { "dependsOn": ["^build"] },   // Build dependencies first
    "lint":  { "dependsOn": ["^lint"] },
    "dev":   { "cache": false, "persistent": true }  // No caching for dev
  }
}
```

- `"^build"` means: before building an app, build all its workspace dependencies first (e.g., `@repo/ui` builds before `web`).
- `"persistent": true` keeps the dev server running (doesn't exit).
- Running `pnpm dev` at the root starts all apps in parallel.

---

## 3. Backend: Database Layer

### 3.1 Database Connection (`apps/api/db/database.py`)

```python
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "genlogs.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

**What each piece does:**

| Variable | Purpose |
|----------|---------|
| `DB_PATH` | Resolves to `apps/api/genlogs.db` - the SQLite file location |
| `engine` | SQLAlchemy engine - manages the actual database connection pool |
| `check_same_thread: False` | Required for SQLite in web servers - SQLite by default only allows the thread that created the connection to use it. FastAPI uses multiple threads, so this flag disables that restriction |
| `SessionLocal` | A factory that creates new database sessions. `autocommit=False` means you must explicitly call `db.commit()`. `autoflush=False` means changes aren't automatically sent to the DB before queries |
| `Base` | The declarative base class - all ORM models inherit from this so SQLAlchemy knows about them |

**The `get_db()` dependency:**

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

This is a **FastAPI dependency** using Python's generator pattern. FastAPI calls `next()` to get the session, injects it into route handlers, and after the response is sent, the `finally` block closes the session. This ensures connections are never leaked.

### 3.2 Normalized Database Schema (`apps/api/db/models.py`)

The database uses a **normalized relational model** with 7 entities that model the real-world pipeline: cameras capture images, images are processed to detect trucks, sightings track truck locations, and trips represent computed movements between cities.

**Entity Relationship Diagram:**

```
cameras ──1:N──> image_transactions ──1:N──> image_processing_results
                       │
                       └──1:N──> truck_sightings <──N:1── trucks ──N:1──> carriers
                                                            │                │
                                                            └──1:N──> trips <┘
```

#### 3.2.1 cameras

Physical camera devices installed on US highways.

```python
class Camera(Base):
    __tablename__ = "cameras"

    camera_id    = Column(String, primary_key=True)    # e.g., "cam-001"
    latitude     = Column(Float, nullable=False)        # e.g., 40.7580
    longitude    = Column(Float, nullable=False)        # e.g., -73.9855
    highway_name = Column(String, nullable=False)       # e.g., "I-95 New York"
```

**Purpose:** Represents the physical infrastructure. Each camera has a fixed GPS location on a specific highway. This is the entry point of the data pipeline.

#### 3.2.2 image_transactions

Each image captured by a camera. One camera produces many images over time.

```python
class ImageTransaction(Base):
    __tablename__ = "image_transactions"

    image_id           = Column(String, primary_key=True)
    camera_id          = Column(String, ForeignKey("cameras.camera_id"), nullable=False)
    timestamp          = Column(String, nullable=False)     # ISO 8601 format
    storage_path       = Column(String, nullable=False)     # e.g., "s3://genlogs-images/img-0001.jpg"
    weather_conditions = Column(String, nullable=True)      # e.g., "clear", "rainy"
    vehicle_speed      = Column(Float, nullable=True)       # estimated mph
```

**Key design decisions:**
- `storage_path` enables **reprocessing** - if the AI model improves, old images can be re-analyzed
- `weather_conditions` and `vehicle_speed` are nullable because they may not always be available
- The FK to `cameras` lets you query "all images from camera X"

#### 3.2.3 image_processing_results

Stores AI analysis results. One image can produce multiple results (plate detection, logo detection, truck number).

```python
class ImageProcessingResult(Base):
    __tablename__ = "image_processing_results"

    result_id        = Column(String, primary_key=True)
    image_id         = Column(String, ForeignKey("image_transactions.image_id"), nullable=False)
    analysis_type    = Column(String, nullable=False)    # "plate", "logo", or "truck_number"
    detected_value   = Column(String, nullable=False)    # e.g., "NY-KS-1001" or "Knight-Swift"
    confidence_score = Column(Float, nullable=False)     # 0.0 to 1.0
```

**Why one-to-many?** A single image might contain a visible license plate AND a company logo. Each detection is a separate row, which allows:
- Independent confidence scores per detection type
- Querying all plate detections vs all logo detections separately
- Adding new analysis types without schema changes

#### 3.2.4 carriers

Transport companies registered with USDOT.

```python
class Carrier(Base):
    __tablename__ = "carriers"

    carrier_id       = Column(String, primary_key=True)
    name             = Column(String, nullable=False)     # e.g., "Knight-Swift Transport Services"
    usdot_number     = Column(String, nullable=False)     # e.g., "USDOT-2247642"
    headquarters_city = Column(String, nullable=False)    # e.g., "Phoenix"
```

**Why a separate carriers table?** The old schema stored `carrier_name` directly in trips. The normalized design:
- Eliminates data duplication (carrier name stored once, not in every trip)
- Adds structured carrier metadata (USDOT number, HQ city)
- Enables carrier-centric queries ("show me all trucks owned by UPS")

#### 3.2.5 trucks

Individual trucks, each belonging to one carrier.

```python
class Truck(Base):
    __tablename__ = "trucks"

    truck_id      = Column(String, primary_key=True)
    license_plate = Column(String, nullable=False)    # e.g., "NY-KS-1001"
    usdot_number  = Column(String, nullable=False)    # truck-level USDOT
    carrier_id    = Column(String, ForeignKey("carriers.carrier_id"), nullable=False)
```

**Relationship:** One carrier owns many trucks. The FK enforces referential integrity - you can't create a truck without a valid carrier.

#### 3.2.6 truck_sightings

When a truck is detected at a camera location. This is the bridge between raw images and truck tracking.

```python
class TruckSighting(Base):
    __tablename__ = "truck_sightings"

    sighting_id      = Column(String, primary_key=True)
    truck_id         = Column(String, ForeignKey("trucks.truck_id"), nullable=False)
    image_id         = Column(String, ForeignKey("image_transactions.image_id"), nullable=False)
    timestamp        = Column(String, nullable=False)
    latitude         = Column(Float, nullable=False)
    longitude        = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
```

**Key relationships:**
- One image can detect **multiple trucks** (trucks traveling together)
- One truck appears in **many sightings** over time (as it passes different cameras)
- The `latitude`/`longitude` come from the camera but are denormalized here for query performance

#### 3.2.7 trips

Precomputed movement records between cities. **Trips are derived from sightings**, not calculated on-the-fly.

```python
class Trip(Base):
    __tablename__ = "trips"

    trip_id          = Column(String, primary_key=True)
    truck_id         = Column(String, ForeignKey("trucks.truck_id"), nullable=False)
    carrier_id       = Column(String, ForeignKey("carriers.carrier_id"), nullable=False)
    origin_city      = Column(String, nullable=False)
    destination_city = Column(String, nullable=False)
    trip_date        = Column(String, nullable=False)
```

**Critical design change from the old schema:**
- **No more `trucks_per_day` column.** Instead, `trucks_per_day` is computed as `COUNT(trip_id)` grouped by carrier. Each row represents ONE truck's ONE trip. 10 Knight-Swift trucks on NY→DC = 10 trip rows.
- **No more `carrier_name` column.** The carrier name comes from a JOIN with the `carriers` table via `carrier_id`.
- This is **proper normalization** - no derived/aggregated data stored in the table.

**SQL equivalent:**

```sql
CREATE TABLE trips (
    trip_id          TEXT PRIMARY KEY,
    truck_id         TEXT NOT NULL REFERENCES trucks(truck_id),
    carrier_id       TEXT NOT NULL REFERENCES carriers(carrier_id),
    origin_city      TEXT NOT NULL,
    destination_city TEXT NOT NULL,
    trip_date        TEXT NOT NULL
);
```

### 3.3 Database Seeding (`apps/api/db/seed.py`)

The seed module populates all 7 tables with realistic pipeline data on startup.

**Seed data summary:**

| Table | Records | Description |
|-------|---------|-------------|
| cameras | 8 | Cameras on I-95, I-5, US-101, I-395, I-405 |
| carriers | 8 | 6 route carriers + UPS + FedEx |
| trucks | 59 | One truck per trip (matching the required trucks/day counts) |
| image_transactions | 118 | 2 per truck (origin camera + destination camera) |
| image_processing_results | 236 | 2 per image (plate detection + logo detection) |
| truck_sightings | 118 | 1 per image (truck spotted at camera location) |
| trips | 59 | One trip per truck per day |

**Route data (trucks_per_day = number of trip records per carrier):**

| Route | Carrier | Trip Records (= Trucks/Day) |
|-------|---------|-----------|
| New York → Washington DC | Knight-Swift Transport Services | 10 |
| New York → Washington DC | J.B. Hunt Transport Services Inc | 7 |
| New York → Washington DC | YRC Worldwide | 5 |
| San Francisco → Los Angeles | XPO Logistics | 9 |
| San Francisco → Los Angeles | Schneider | 6 |
| San Francisco → Los Angeles | Landstar Systems | 2 |
| Chicago → Detroit | UPS Inc. | 11 |
| Chicago → Detroit | FedEx Corp | 9 |

**Fallback carriers** (returned when a searched route has no data):

| Carrier | Trucks/Day |
|---------|-----------|
| UPS Inc. | 11 |
| FedEx Corp | 9 |

**How the pipeline data is generated:**

For each truck on a route, the seed creates a complete pipeline trace:
1. **Origin image** - camera captures the truck departing
2. **Processing results** - plate and logo detected from origin image
3. **Origin sighting** - truck location recorded at origin camera
4. **Destination image** - camera captures the truck arriving
5. **Processing results** - plate and logo detected from destination image
6. **Destination sighting** - truck location recorded at destination camera
7. **Trip record** - precomputed trip from origin city to destination city

**Idempotency:** The function checks `db.query(Camera).count() > 0` before inserting, so it only seeds on the very first startup.

---

## 4. Backend: Data Access Layer

### Repository Pattern (`apps/api/data/trips.py`)

This module implements the **Repository Pattern** - it abstracts database queries behind simple function calls. The rest of the application never writes raw SQL; it calls these functions instead.

**Dataclasses:**

```python
@dataclass(frozen=True)
class TripRecord:
    trip_id: str
    truck_id: str
    carrier_id: str
    carrier_name: str       # Resolved via JOIN with carriers table
    origin_city: str
    destination_city: str
    trip_date: str

@dataclass(frozen=True)
class CarrierVolume:
    carrier_name: str
    trucks_per_day: int     # Computed as COUNT(trip_id) per carrier
```

`frozen=True` makes instances **immutable** - once created, you cannot change any field. This prevents accidental mutations.

**Key repository functions:**

```python
def get_all_trips() -> list[TripRecord]:
    """Returns every trip with carrier name resolved via JOIN."""
    # SELECT t.*, c.name FROM trips t JOIN carriers c ON t.carrier_id = c.carrier_id
    rows = db.query(TripModel, Carrier.name) \
             .join(Carrier, TripModel.carrier_id == Carrier.carrier_id).all()

def get_carrier_volumes(origin: str, destination: str) -> list[CarrierVolume]:
    """Count trips per carrier on a route (= trucks per day)."""
    # SELECT c.name, COUNT(t.trip_id) as trucks_per_day
    # FROM trips t JOIN carriers c ON t.carrier_id = c.carrier_id
    # WHERE LOWER(t.origin_city) = ? AND LOWER(t.destination_city) = ?
    # GROUP BY c.name ORDER BY COUNT(t.trip_id) DESC

def get_unique_cities() -> list[str]:
    """Returns sorted, deduplicated list of all origin + destination cities."""

def get_unique_routes() -> list[dict[str, str]]:
    """Returns sorted list of all origin→destination pairs."""
```

**The JOIN pattern:** Since the normalized schema stores `carrier_id` (not `carrier_name`) in the trips table, every query that needs carrier names must JOIN with the carriers table. This is the standard trade-off of normalization: queries are slightly more complex, but data integrity is guaranteed and updates only happen in one place.

**The COUNT pattern:** `trucks_per_day` is no longer a stored column. It's computed as `COUNT(trip_id)` grouped by carrier. 10 Knight-Swift trip rows = 10 trucks/day.

**Session Management:**

Each function creates its own session and closes it in a `finally` block:

```python
db = SessionLocal()
try:
    # ... do work ...
finally:
    db.close()  # Always close, even if an error occurs
```

This prevents connection leaks.

---

## 5. Backend: Services (Business Logic)

### 5.1 Search Service (`apps/api/services/search_service.py`)

This service handles the core carrier search logic.

**The CarrierResult dataclass:**

```python
@dataclass(frozen=True)
class CarrierResult:
    carrier_name: str
    trucks_per_day: int
```

**`search_carriers()` function:**

```python
def search_carriers(origin: str, destination: str, db: Session | None = None) -> list[CarrierResult]:
```

**Step-by-step logic:**

1. **Query with JOIN + GROUP BY** to compute trucks_per_day from trip counts:
   ```python
   rows = (
       db.query(
           Carrier.name,
           func.count(TripModel.trip_id).label("trucks_per_day"),
       )
       .join(Carrier, TripModel.carrier_id == Carrier.carrier_id)
       .filter(
           func.lower(TripModel.origin_city) == origin.strip().lower(),
           func.lower(TripModel.destination_city) == destination.strip().lower(),
       )
       .group_by(Carrier.name)
       .order_by(func.count(TripModel.trip_id).desc())
       .all()
   )
   ```
   - JOINs `trips` with `carriers` to get carrier names
   - `COUNT(trip_id)` per carrier = number of trucks on that route per day
   - `func.lower()` for case-insensitive city matching
   - Results sorted by truck count descending (busiest carrier first)

2. **If matches found**, return them as `CarrierResult` objects

3. **If no matches**, return **fallback carriers** (UPS and FedEx). This ensures the user always gets a result, even for routes not in the database.

### 5.2 AI Service (`apps/api/services/ai_service.py`)

This is the most complex service. It implements a **rule-based NLP system** that converts natural language questions into SQL queries.

**The pipeline (4 stages):**

```
User Query → Extract Entities → Classify Query Type → Build SQL → Execute & Explain
```

#### Stage 1: Entity Extraction

**City extraction (`_extract_cities`):**

```python
KNOWN_CITIES = {
    "new york", "washington dc", "san francisco", "los angeles",
    "chicago", "detroit", "dallas", "houston", "miami", "atlanta",
    "seattle", "portland", "boston", "philadelphia", "denver", "salt lake city",
}
```

The function:
1. Converts the query to lowercase
2. Searches for each known city name (longest first, to avoid "new" matching before "new york")
3. Records the **position** of each match in the query string
4. Sorts matches by position - the first city mentioned is treated as the **origin**, the second as the **destination**
5. Replaces matched text with underscores to prevent re-matching (e.g., "san francisco" won't also match "san")

Example: `"carriers from New York to Los Angeles"` → origin: `"new york"`, destination: `"los angeles"`

**Carrier extraction (`_extract_carrier`):**

Searches for known carrier names (hardcoded list) in the query text. Returns the first match.

#### Stage 2: Query Classification

```python
def _classify_query(query: str) -> str:
    if "how many" / "count" / "total" / "number"  → "count"
    if "top" / "most" / "busiest" / "highest"      → "top"
    if "route" / "routes" / "lane" / "lanes"        → "routes"
    else                                             → "carriers"  (default)
```

Each classification changes how the SQL is built and how results are formatted.

#### Stage 3: SQL Generation

The service dynamically builds a display SQL string reflecting the normalized JOIN-based schema:

```sql
-- Base structure (carriers query)
SELECT c.name AS carrier_name, COUNT(t.trip_id) AS trucks_per_day
FROM trips t
JOIN carriers c ON t.carrier_id = c.carrier_id
WHERE t.origin_city = 'New York' AND t.destination_city = 'Washington DC'
GROUP BY c.name
ORDER BY trucks_per_day DESC

-- If query_type == "top":
... ORDER BY trucks_per_day DESC LIMIT 5
```

**Important note:** This SQL string is generated for **display purposes only**. The actual query execution uses SQLAlchemy ORM (not raw SQL), so there is no SQL injection risk from the display SQL.

#### Stage 4: Execution & Explanation

**`_execute_on_dataset()`** runs the actual query via SQLAlchemy ORM with a JOIN between `trips` and `carriers`, GROUP BY carrier name, and COUNT of trip records. If no results are found and both origin+destination were provided, it returns fallback carriers.

**`_generate_explanation()`** produces a human-readable sentence:
- Count query: `"There are 3 carriers operating between New York and Washington DC with a combined 22 trucks per day."`
- Carrier query: `"The top carriers between New York and Washington DC are: Knight-Swift (10 trucks/day), J.B. Hunt (7 trucks/day), YRC Worldwide (5 trucks/day)"`

**The complete return value:**

```python
@dataclass(frozen=True)
class AIQueryResult:
    sql: str          # The generated SQL (for display)
    results: list     # The actual query results
    explanation: str  # Human-readable explanation
```

---

## 6. Backend: API Routes

### 6.1 Search Route (`apps/api/routes/search.py`)

```
POST /search
```

**Request/Response schemas (Pydantic models):**

```python
class SearchRequest(BaseModel):
    origin: str           # e.g., "New York"
    destination: str      # e.g., "Washington DC"

class CarrierResponse(BaseModel):
    carrier_name: str     # e.g., "Knight-Swift Transport Services"
    trucks_per_day: int   # e.g., 10

class SearchResponse(BaseModel):
    origin: str
    destination: str
    carriers: list[CarrierResponse]
    total_carriers: int
```

**What Pydantic does here:**
- **Validates** incoming JSON - if `origin` is missing, FastAPI returns a 422 error automatically
- **Serializes** outgoing data - the response is automatically converted to JSON
- **Documents** the API - FastAPI generates OpenAPI/Swagger docs from these models

**Handler:**

```python
@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    results = search_carriers(request.origin, request.destination)
    return SearchResponse(
        origin=request.origin,
        destination=request.destination,
        carriers=[CarrierResponse(...) for r in results],
        total_carriers=len(results),
    )
```

**Example request:**
```json
POST /search
{ "origin": "New York", "destination": "Washington DC" }
```

**Example response:**
```json
{
  "origin": "New York",
  "destination": "Washington DC",
  "carriers": [
    { "carrier_name": "Knight-Swift Transport Services", "trucks_per_day": 10 },
    { "carrier_name": "J.B. Hunt Transport Services Inc", "trucks_per_day": 7 },
    { "carrier_name": "YRC Worldwide", "trucks_per_day": 5 }
  ],
  "total_carriers": 3
}
```

### 6.2 AI Query Route (`apps/api/routes/ai_query.py`)

```
POST /ai-query
```

**Schemas:**

```python
class AIQueryRequest(BaseModel):
    query: str    # Natural language question

class AIQueryResponse(BaseModel):
    query: str          # The original question (echoed back)
    sql: str            # Generated SQL
    results: list       # Query results
    explanation: str    # Human-readable answer
```

**Example request:**
```json
POST /ai-query
{ "query": "Which carriers operate between New York and Washington DC?" }
```

**Example response:**
```json
{
  "query": "Which carriers operate between New York and Washington DC?",
  "sql": "SELECT c.name AS carrier_name, COUNT(t.trip_id) AS trucks_per_day\nFROM trips t\nJOIN carriers c ON t.carrier_id = c.carrier_id\nWHERE t.origin_city = 'New York' AND t.destination_city = 'Washington DC'\nGROUP BY c.name\nORDER BY trucks_per_day DESC",
  "results": [
    { "carrier_name": "Knight-Swift Transport Services", "trucks_per_day": 10, "origin": "New York", "destination": "Washington DC" },
    { "carrier_name": "J.B. Hunt Transport Services Inc", "trucks_per_day": 7, "origin": "New York", "destination": "Washington DC" },
    { "carrier_name": "YRC Worldwide", "trucks_per_day": 5, "origin": "New York", "destination": "Washington DC" }
  ],
  "explanation": "The top carriers between New York and Washington DC are: Knight-Swift Transport Services (10 trucks/day), J.B. Hunt Transport Services Inc (7 trucks/day), YRC Worldwide (5 trucks/day)"
}
```

### 6.3 Metadata Routes (`apps/api/routes/metadata.py`)

```
GET /cities  → { "cities": ["Los Angeles", "New York", "San Francisco", "Washington DC"] }
GET /routes  → { "routes": [{"origin": "New York", "destination": "Washington DC"}, ...] }
```

These are simple lookup endpoints used to populate dropdowns or provide available options.

### 6.4 Health Check (in `main.py`)

```
GET /  → { "status": "ok", "service": "genlogs-api" }
```

---

## 7. Backend: Application Startup

### `apps/api/main.py`

**The lifespan context manager:**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_database()   # Runs ONCE when the server starts
    yield             # Server runs here (handles requests)
    # Cleanup code would go after yield (none needed here)
```

FastAPI's `lifespan` replaces the older `@app.on_event("startup")` pattern. It ensures `seed_database()` runs before the first request is handled.

**CORS middleware:**

```python
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001,https://genlogs-platform-web.vercel.app",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Why CORS is needed:** The frontend runs on `localhost:3000` and the API on `localhost:8000`. Browsers block cross-origin requests by default (Same-Origin Policy). This middleware tells the browser which origins are allowed. The origins are configurable via the `ALLOWED_ORIGINS` environment variable for deployment flexibility.

**Router registration:**

```python
app.include_router(search_router, tags=["search"])
app.include_router(ai_query_router, tags=["ai"])
app.include_router(metadata_router, tags=["metadata"])
```

Each router is a separate module with its own endpoints. `tags` group endpoints in the auto-generated Swagger docs (accessible at `http://localhost:8000/docs`).

---

## 8. Frontend: Application Shell

### 8.1 Root Layout (`apps/web/app/layout.tsx`)

This is a **Next.js Server Component** (no `"use client"` directive). It defines the HTML shell:

```tsx
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <GoogleMapsProvider>       {/* Loads Google Maps SDK */}
          <header className="header">
            <h1><span>Gen</span>logs</h1>
            <span>Freight Analytics Platform</span>
          </header>
          {children}               {/* Page content renders here */}
        </GoogleMapsProvider>
      </body>
    </html>
  );
}
```

**Key details:**
- `localFont` loads custom Geist fonts as CSS variables (`--font-geist-sans`, `--font-geist-mono`)
- `GoogleMapsProvider` wraps the entire app so all components can use Google Maps
- `metadata` export sets the page title and description for SEO

### 8.2 Google Maps Provider (`apps/web/app/components/GoogleMapsProvider.tsx`)

```tsx
const GOOGLE_MAPS_API_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "";

export default function GoogleMapsProvider({ children }) {
  if (!GOOGLE_MAPS_API_KEY || GOOGLE_MAPS_API_KEY === "YOUR_GOOGLE_MAPS_API_KEY_HERE") {
    return <>{children}</>;  // Render without Maps if no key
  }

  return (
    <LoadScript googleMapsApiKey={GOOGLE_MAPS_API_KEY} libraries={["places"]}>
      {children}
    </LoadScript>
  );
}
```

**How it works:**
- `NEXT_PUBLIC_` prefix makes the env var available in the browser (Next.js convention)
- `LoadScript` from `@react-google-maps/api` injects the Google Maps `<script>` tag
- `libraries: ["places"]` also loads the Places API for city autocomplete
- If no API key is set, the app still works - just without maps/autocomplete

### 8.3 Main Page (`apps/web/app/page.tsx`)

This is a **Client Component** (`"use client"`) because it uses React hooks for interactivity.

**State management:**

```tsx
const [activeTab, setActiveTab] = useState<Tab>("search");     // Which tab is visible
const [searchResult, setSearchResult] = useState(null);         // API response data
const [searchedCities, setSearchedCities] = useState(null);     // Cities for the map
const [loading, setLoading] = useState(false);                  // Loading spinner
const [error, setError] = useState("");                         // Error message
```

**The `handleSearch` function:**

```tsx
const handleSearch = async (origin: string, destination: string) => {
  setLoading(true);                          // 1. Show spinner
  setError("");                              // 2. Clear previous errors

  try {
    const res = await fetch(`${API_URL}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ origin, destination }),
    });

    if (!res.ok) throw new Error(`API error: ${res.status}`);

    const data = await res.json();
    setSearchResult(data);                   // 3. Store results
    setSearchedCities({ origin, destination }); // 4. Trigger map render
  } catch {
    setError("Failed to search...");         // 5. Show error if anything fails
    setSearchResult(null);
    setSearchedCities(null);
  } finally {
    setLoading(false);                       // 6. Hide spinner
  }
};
```

**Tab rendering (conditional rendering pattern):**

```tsx
{activeTab === "search" && (
  <div>
    <SearchForm onSearch={handleSearch} loading={loading} />
    {error && <div className="error-message">{error}</div>}
    {loading && <div className="loading"><div className="spinner" /></div>}
    {!loading && searchedCities && <RouteMap origin={...} destination={...} />}
    {!loading && <CarrierList result={searchResult} />}
  </div>
)}

{activeTab === "ai" && <AIChat />}
```

Only the active tab's content is rendered in the DOM. React unmounts the other tab entirely.

---

## 9. Frontend: Components Deep Dive

### 9.1 SearchForm

**File:** `apps/web/app/components/SearchForm.tsx`

**Props:**
```tsx
interface SearchFormProps {
  onSearch: (origin: string, destination: string) => void;
  loading: boolean;
}
```

**How it works:**
1. Two `PlacesAutocomplete` inputs for origin and destination
2. A submit button that's disabled when either field is empty or when loading
3. On form submit, calls `onSearch(origin, destination)` to notify the parent

**`useCallback` optimization:**
```tsx
const handleOriginChange = useCallback((val: string) => setOrigin(val), []);
```
`useCallback` memoizes the function so it doesn't get recreated on every render. This prevents `PlacesAutocomplete` from re-rendering unnecessarily (since its `onChange` prop stays the same reference).

### 9.2 PlacesAutocomplete

**File:** `apps/web/app/components/PlacesAutocomplete.tsx`

This wraps Google's Places Autocomplete API into a React component.

**Lifecycle:**

```
Component mounts
  └→ useEffect #1: Check if `google.maps.places` exists
       ├→ If yes: setIsGoogleLoaded(true)
       └→ If no: recheck after 1 second (the script might still be loading)

isGoogleLoaded becomes true
  └→ useEffect #2: Create Autocomplete instance
       ├→ Attach to the <input> element via ref
       ├→ Restrict to US cities: { types: ["(cities)"], componentRestrictions: { country: "us" } }
       └→ Listen for "place_changed" event
            └→ Extract city name from formatted_address (before first comma)
               e.g., "New York, NY, USA" → "New York"
```

**Why `useRef` for the input?**
Google Maps Autocomplete needs a reference to the actual DOM element (`<input>`) to attach its dropdown. React's `useRef` gives us that reference without causing re-renders.

**Why `useRef` for the autocomplete instance?**
```tsx
const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);
```
We store the Autocomplete instance in a ref to prevent creating duplicate instances. The `useEffect` checks `autocompleteRef.current` before creating a new one.

### 9.3 CarrierList

**File:** `apps/web/app/components/CarrierList.tsx`

Renders search results as a ranked table.

**Three states:**

1. **No search yet** (`result === null`): Shows placeholder text
2. **No carriers found** (`result.carriers.length === 0`): Shows "no results" message
3. **Results available**: Renders the route info bar + table

**Route info bar:**
```
[New York] → [Washington DC]           3 carriers found
```

**Table structure:**
```
| Rank | Carrier                           | Trucks / Day |
|------|-----------------------------------|-------------|
| #1   | Knight-Swift Transport Services   | [10]        |
| #2   | J.B. Hunt Transport Services Inc  | [7]         |
| #3   | YRC Worldwide                     | [5]         |
```

The `trucks_per_day` values are displayed in green badges (`trucks-badge` class).

**Pluralization detail:**
```tsx
{result.total_carriers} carrier{result.total_carriers !== 1 ? "s" : ""} found
```
Shows "1 carrier found" vs "3 carriers found".

### 9.4 AIChat

**File:** `apps/web/app/components/AIChat.tsx`

A self-contained chat interface for natural language queries.

**State:**
```tsx
const [query, setQuery] = useState("");        // Current input text
const [loading, setLoading] = useState(false);
const [result, setResult] = useState(null);    // API response
const [error, setError] = useState("");
```

**Suggestion chips:**
```tsx
const SUGGESTIONS = [
  "Which carriers operate between New York and Washington DC?",
  "Top carriers from San Francisco to Los Angeles",
  "How many carriers operate from Dallas to Houston?",
  "Show me all UPS routes",
  "What are the busiest freight routes?",
];
```

Clicking a chip both sets the input text AND immediately fires the query:
```tsx
onClick={() => {
  setQuery(s);     // Update the input
  handleQuery(s);  // Fire immediately (don't wait for submit)
}}
```

**Result display (three sections):**

1. **Generated SQL** - shown in a monospace green `<pre>` block
2. **Explanation** - human-readable paragraph
3. **Results table** - dynamically built from the result keys

**Dynamic table rendering:**
```tsx
// Headers: take keys from the first result object
Object.keys(result.results[0]).map(key => <th>{key.replace(/_/g, " ")}</th>)
// e.g., "carrier_name" → "carrier name", "trucks_per_day" → "trucks per day"

// Cells: numeric values get green badges, strings render as-is
{typeof val === "number" ? <span className="trucks-badge">{val}</span> : val}
```

### 9.5 RouteMap

**File:** `apps/web/app/components/RouteMap.tsx`

Renders a Google Map with up to 3 driving routes between two cities.

**Lifecycle:**

```
Props change (new origin/destination)
  └→ useEffect: Request directions from Google
       ├→ Create DirectionsService
       ├→ Call .route() with { provideRouteAlternatives: true }
       └→ On success: split into up to 3 separate DirectionsResult objects

Render:
  ├→ GoogleMap component (dark theme)
  ├→ DirectionsRenderer x3 (one per route, different colors)
  └→ Route detail cards (distance + duration for each)
```

**Route colors:**
```tsx
const ROUTE_COLORS = ["#3b82f6", "#10b981", "#f59e0b"];
//                     Blue        Green       Amber
```

**Why separate DirectionsResult objects?**
Google's `DirectionsRenderer` can only render one route at a time with one color. To show 3 routes with different colors, the code splits the single result into 3 objects:

```tsx
const multipleResults = routes.map((route) => ({
  ...result,
  routes: [route],  // Each result contains just one route
}));
```

**Renderer options per route:**
```tsx
{
  polylineOptions: {
    strokeColor: ROUTE_COLORS[index],
    strokeWeight: index === 0 ? 5 : 3,       // Primary route is thicker
    strokeOpacity: index === 0 ? 1 : 0.6,    // Alternatives are semi-transparent
  },
  suppressMarkers: index > 0,                 // Only show A/B markers on first route
  preserveViewport: index > 0,                // Don't re-zoom for each route
}
```

**Dark theme map styling:**
```tsx
const MAP_OPTIONS = {
  styles: [
    { elementType: "geometry", stylers: [{ color: "#1d2c4d" }] },       // Land
    { elementType: "labels.text.fill", stylers: [{ color: "#8ec3b9" }] }, // Labels
    { featureType: "water", stylers: [{ color: "#0e1626" }] },           // Water
    { featureType: "road", stylers: [{ color: "#304a7d" }] },            // Roads
  ],
};
```

---

## 10. Frontend: Styling System

### Design Tokens (CSS Custom Properties)

```css
:root {
  --background:    #0f172a;   /* Dark navy page background */
  --foreground:    #e2e8f0;   /* Light gray text */
  --card-bg:       #1e293b;   /* Slightly lighter card background */
  --card-border:   #334155;   /* Subtle border */
  --primary:       #3b82f6;   /* Blue - buttons, links, active tab */
  --primary-hover: #2563eb;   /* Darker blue on hover */
  --accent:        #10b981;   /* Green - trucks badge, SQL code */
  --muted:         #94a3b8;   /* Gray - labels, secondary text */
  --error:         #ef4444;   /* Red - error messages */
  --input-bg:      #1e293b;   /* Input field background */
  --input-border:  #475569;   /* Input field border */
  --radius:        8px;       /* Border radius for cards, inputs, buttons */
}
```

These values come from the **Tailwind CSS color palette** (slate/blue/emerald/red shades), giving a professional dark theme.

### Component Styles

| Class | Purpose |
|-------|---------|
| `.container` | Max-width 1200px centered layout |
| `.card` | Dark card with border and padding |
| `.btn` | Blue button with hover/disabled states |
| `.carrier-table` | Full-width table with header styling |
| `.trucks-badge` | Green pill badge for numeric values |
| `.suggestion-chip` | Blue outline pill for AI suggestions |
| `.spinner` | CSS-only loading animation (rotating border) |
| `.pac-container` | Google Places dropdown (overrides Google's defaults) |

### Responsive Design

```css
@media (max-width: 768px) {
  .search-form { flex-direction: column; }
  .form-group { min-width: 100%; }
  .route-details { flex-direction: column; }
}
```

On mobile, the search form stacks vertically and route detail cards stack instead of sitting side-by-side.

---

## 11. Data Flow Walkthroughs

### Flow 1: Carrier Search

```
User types "New York" in origin input
  └→ PlacesAutocomplete shows Google Places suggestions
       └→ User selects "New York, NY, USA"
            └→ place_changed event fires
                 └→ Extract "New York" (before first comma)
                      └→ onChange("New York") → SearchForm.setOrigin("New York")

User types "Washington DC" in destination (same flow)

User clicks "Search"
  └→ form.onSubmit → handleSearch("New York", "Washington DC")
       └→ setLoading(true), setError("")
            └→ fetch POST /search { origin: "New York", destination: "Washington DC" }

Backend receives request
  └→ Pydantic validates the JSON
       └→ search_carriers("New York", "Washington DC")
            └→ SQLAlchemy: JOIN trips + carriers, GROUP BY carrier name, COUNT trips
                 └→ Knight-Swift: 10 trips, J.B. Hunt: 7 trips, YRC: 5 trips
                      └→ Response: { carriers: [...], total_carriers: 3 }

Frontend receives response
  └→ setSearchResult(data) → CarrierList renders the table
  └→ setSearchedCities({...}) → RouteMap mounts
       └→ Google Directions API → up to 3 routes rendered on map
```

### Flow 2: AI Query

```
User clicks suggestion chip "Which carriers operate between New York and Washington DC?"
  └→ setQuery(text) + handleQuery(text)
       └→ fetch POST /ai-query { query: "Which carriers operate between New York and Washington DC?" }

Backend receives request
  └→ _extract_cities("which carriers operate between new york and washington dc?")
       └→ Finds "new york" at position 35, "washington dc" at position 51
       └→ Returns ("new york", "washington dc")
  └→ _extract_carrier(...) → None (no carrier name found)
  └→ _classify_query(...) → "carriers" (matches "carriers" keyword)
  └→ Build SQL:
       SELECT c.name AS carrier_name, COUNT(t.trip_id) AS trucks_per_day
       FROM trips t JOIN carriers c ON t.carrier_id = c.carrier_id
       WHERE t.origin_city = 'New York' AND t.destination_city = 'Washington DC'
       GROUP BY c.name ORDER BY trucks_per_day DESC
  └→ _execute_on_dataset(origin="new york", destination="washington dc")
       └→ SQLAlchemy JOIN + GROUP BY → 3 carrier results
  └→ _generate_explanation("carriers", "new york", "washington dc", None, results)
       └→ "The top carriers between New York and Washington DC are: Knight-Swift (10 trucks/day), ..."
  └→ Response: { sql: "...", results: [...], explanation: "..." }

Frontend receives response
  └→ setResult(data)
       └→ AIChat renders: SQL block + Explanation + Results table
```

---

## 12. Testing

### Test Setup

**Framework:** Vitest + React Testing Library + jsdom

```typescript
// vitest.config.ts
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",    // Simulates a browser DOM in Node.js
    setupFiles: "./test/setup.ts",
  },
});
```

### Test Suites

| File | Tests | What's Covered |
|------|-------|---------------|
| `page.test.tsx` | Tab switching, search flow, result display | Main page integration |
| `SearchForm.test.tsx` | Form validation, submission, loading states | Form component |
| `CarrierList.test.tsx` | Empty states, table rendering, pluralization | Results display |
| `AIChat.test.tsx` | Input handling, API calls, error states | AI assistant |

### Test Patterns Used

**Mocking fetch:**
```tsx
global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  json: () => Promise.resolve(mockData),
});
```

**User interaction:**
```tsx
const user = userEvent.setup();
await user.type(screen.getByPlaceholderText("..."), "New York");
await user.click(screen.getByText("Search"));
```

**Async assertions:**
```tsx
await waitFor(() => {
  expect(screen.getByText("Knight-Swift")).toBeInTheDocument();
});
```

---

## 13. How to Run

### Prerequisites

- Node.js >= 18
- pnpm 9.x
- Python 3.11+

### Backend

```bash
cd apps/api
pip install fastapi uvicorn sqlalchemy
uvicorn main:app --reload --port 8000
```

The database is created automatically on first startup (`genlogs.db` in `apps/api/`).

### Frontend

```bash
# From the root
pnpm install
pnpm dev
```

This starts the Next.js dev server on `http://localhost:3000`.

### Environment Variables

Create `apps/web/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

### API Docs

FastAPI auto-generates interactive docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Running Tests

```bash
cd apps/web
pnpm test
```
