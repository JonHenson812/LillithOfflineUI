from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import json
import random
import asyncio
import aiosqlite
import httpx
import subprocess
import signal


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Local storage paths
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "lillith.sqlite"
PLUGINS_DIR = ROOT_DIR.parent / "plugins"
LM_STUDIO_URL = os.environ["LM_STUDIO_URL"]


def ensure_storage():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)


async def init_db():
    ensure_storage()
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                genre TEXT,
                story_bible TEXT,
                character_profile TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS services (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                base_url TEXT,
                health_url TEXT,
                start_command TEXT,
                stop_command TEXT,
                last_pid INTEGER
            )
            """
        )
        await conn.commit()
    await ensure_default_services()


# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusCheckCreate(BaseModel):
    client_name: str


class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    genre: Optional[str] = None
    story_bible: Optional[str] = None
    character_profile: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    genre: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    story_bible: Optional[str] = None
    character_profile: Optional[Dict[str, Any]] = None


class CharacterAutofillRequest(BaseModel):
    name: str
    role: Optional[str] = None
    age: Optional[int] = None
    archetype: Optional[str] = None
    goal: Optional[str] = None
    flaw: Optional[str] = None
    voice: Optional[str] = None
    appearance: Optional[str] = None
    backstory: Optional[str] = None
    quirks: Optional[str] = None
    model: Optional[str] = None


class CharacterProfile(BaseModel):
    name: str
    role: str
    age: int
    archetype: str
    goal: str
    flaw: str
    voice: str
    appearance: str
    backstory: str
    quirks: str


class StoryBibleRequest(BaseModel):
    project_id: str
    model: str
    tone: Optional[str] = None


class ServiceConfig(BaseModel):
    id: str
    name: str
    base_url: Optional[str] = None
    health_url: Optional[str] = None
    start_command: Optional[str] = None
    stop_command: Optional[str] = None
    last_pid: Optional[int] = None
    status: Optional[str] = None


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    health_url: Optional[str] = None
    start_command: Optional[str] = None
    stop_command: Optional[str] = None


class AppSettings(BaseModel):
    auto_start_services: bool = False
    auto_refresh_services: bool = False


class SettingsUpdate(BaseModel):
    auto_start_services: Optional[bool] = None
    auto_refresh_services: Optional[bool] = None


class PluginInfo(BaseModel):
    name: str
    path: str


def row_to_project(row: aiosqlite.Row) -> Dict[str, Any]:
    data = dict(row)
    if data.get("character_profile"):
        data["character_profile"] = json.loads(data["character_profile"])
    return data


async def fetch_projects() -> List[Dict[str, Any]]:
    await init_db()
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM projects ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
    return [row_to_project(row) for row in rows]


async def fetch_project_by_id(project_id: str) -> Optional[Dict[str, Any]]:
    await init_db()
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,),
        )
        row = await cursor.fetchone()
    if row:
        return row_to_project(row)
    return None


async def insert_project(project: Project) -> None:
    await init_db()
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            """
            INSERT INTO projects (id, name, description, genre, story_bible, character_profile, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project.id,
                project.name,
                project.description,
                project.genre,
                project.story_bible,
                json.dumps(project.character_profile) if project.character_profile else None,
                project.created_at.isoformat(),
                project.updated_at.isoformat(),
            ),
        )
        await conn.commit()


async def persist_project(project: Dict[str, Any]) -> Dict[str, Any]:
    await init_db()
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            """
            UPDATE projects
            SET name = ?, description = ?, genre = ?, story_bible = ?, character_profile = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                project["name"],
                project.get("description"),
                project.get("genre"),
                project.get("story_bible"),
                json.dumps(project.get("character_profile"))
                if project.get("character_profile")
                else None,
                project["updated_at"],
                project["id"],
            ),
        )
        await conn.commit()
    return project


async def remove_project(project_id: str) -> bool:
    await init_db()
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            "DELETE FROM projects WHERE id = ?",
            (project_id,),
        )
        await conn.commit()
        return cursor.rowcount > 0


async def update_project_story_bible(project_id: str, story_bible: str) -> None:
    project = await fetch_project_by_id(project_id)
    if not project:
        return
    project["story_bible"] = story_bible
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    await persist_project(project)


def normalize_lm_url(base_url: str) -> str:
    trimmed = base_url.rstrip("/")
    if trimmed.endswith("/v1"):
        return trimmed
    return f"{trimmed}/v1"


async def ensure_default_services() -> None:
    defaults = [
        {
            "id": "lm_studio",
            "name": "LM Studio",
            "base_url": LM_STUDIO_URL,
            "health_url": f"{normalize_lm_url(LM_STUDIO_URL)}/models",
            "start_command": '"C:\\Users\\Jonathan\\AppData\\Local\\Programs\\LM Studio\\LM Studio.exe"',
            "stop_command": 'taskkill /IM "LM Studio.exe" /F',
        },
        {
            "id": "comfyui",
            "name": "ComfyUI",
            "base_url": "http://127.0.0.1:8188",
            "health_url": "http://127.0.0.1:8188/system_stats",
            "start_command": "C:\\ComfyUI\\run_nvidia_gpu.bat",
            "stop_command": "",
        },
        {
            "id": "stable_diffusion",
            "name": "Stable Diffusion WebUI",
            "base_url": "http://127.0.0.1:7860",
            "health_url": "http://127.0.0.1:7860/sdapi/v1/sd-models",
            "start_command": "C:\\Users\\JHens\\sd.webui\\webui-user.bat",
            "stop_command": "",
        },
    ]

    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute("SELECT id FROM services")
        rows = await cursor.fetchall()
        existing = {row[0] for row in rows}
        for service in defaults:
            if service["id"] in existing:
                continue
            await conn.execute(
                """
                INSERT INTO services (id, name, base_url, health_url, start_command, stop_command, last_pid)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    service["id"],
                    service["name"],
                    service["base_url"],
                    service["health_url"],
                    service["start_command"],
                    service["stop_command"],
                    None,
                ),
            )
        await conn.commit()


async def fetch_service(service_id: str) -> Optional[Dict[str, Any]]:
    await init_db()
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM services WHERE id = ?",
            (service_id,),
        )
        row = await cursor.fetchone()
    if row:
        return dict(row)
    return None


async def fetch_services() -> List[Dict[str, Any]]:
    await init_db()
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM services ORDER BY name")
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def update_service(service_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    service = await fetch_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    service.update({key: value for key, value in update_data.items() if value is not None})
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            """
            UPDATE services
            SET name = ?, base_url = ?, health_url = ?, start_command = ?, stop_command = ?
            WHERE id = ?
            """,
            (
                service["name"],
                service.get("base_url"),
                service.get("health_url"),
                service.get("start_command"),
                service.get("stop_command"),
                service_id,
            ),
        )
        await conn.commit()
    return service


async def update_service_pid(service_id: str, pid: Optional[int]) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE services SET last_pid = ? WHERE id = ?",
            (pid, service_id),
        )
        await conn.commit()


def launch_command(command: str) -> int:
    if os.name == "nt":
        process = subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        process = subprocess.Popen(command, shell=True, start_new_session=True)
    return process.pid


def stop_process(pid: int) -> None:
    if os.name == "nt":
        subprocess.Popen(f"taskkill /PID {pid} /F", shell=True)
    else:
        os.kill(pid, signal.SIGTERM)


async def get_service_status(service: Dict[str, Any]) -> str:
    health_url = service.get("health_url")
    if not health_url:
        return "unknown"
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(health_url)
            return "online" if response.status_code < 400 else "offline"
    except httpx.HTTPError:
        return "offline"


async def get_lm_studio_base() -> str:
    service = await fetch_service("lm_studio")
    if service and service.get("base_url"):
        return service["base_url"]
    return LM_STUDIO_URL


def fill_value(value: Optional[str], options: List[str], seed: str) -> str:
    if value:
        return value
    rng = random.Random(seed)
    return rng.choice(options)


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    if "{" in text and "}" in text:
        start = text.find("{")
        end = text.rfind("}")
        snippet = text[start : end + 1]
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            return None
    return None


def safe_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_character_profile(request: CharacterAutofillRequest, ai_data: Optional[Dict[str, Any]] = None) -> CharacterProfile:
    seed = request.name.strip() or "Lillith"
    ai_data = ai_data or {}

    roles = ["Protagonist", "Antagonist", "Mentor", "Rogue", "Mystic"]
    archetypes = ["Reluctant hero", "Visionary", "Survivor", "Trickster", "Guardian"]
    goals = [
        "Protects a fragile secret",
        "Seeks redemption",
        "Wants to rebuild a lost home",
        "Chases forbidden knowledge",
        "Keeps the crew together",
    ]
    flaws = [
        "Trusts too easily",
        "Carries a hidden fear",
        "Avoids vulnerability",
        "Obsessed with control",
        "Haunted by a past mistake",
    ]
    voices = [
        "Low and measured",
        "Quick, razor-sharp wit",
        "Soft-spoken with intensity",
        "Confident, rhythmic cadence",
        "Warm but guarded",
    ]
    appearances = [
        "Wears layered streetwear and tech charms",
        "Scar across the brow, eyes that never settle",
        "Elegant silhouette with ceremonial tattoos",
        "Practical gear, dusted with travel marks",
        "Minimalist style with bold accent color",
    ]
    backstories = [
        "Raised in an isolated enclave guarding ancient archives.",
        "Former agent who walked away from a corrupt regime.",
        "Grew up as a performer hiding a secret lineage.",
        "Survivor of a fallen city, carrying its memory forward.",
        "Trained by a collective that values balance above all.",
    ]
    quirks = [
        "Sketches symbols while thinking",
        "Keeps a pocket recorder of ambient sounds",
        "Collects small mechanical trinkets",
        "Has a ritual tea routine before decisions",
        "Talks to inanimate objects when stressed",
    ]

    name = (ai_data.get("name") or request.name or "Unnamed").strip()
    role = ai_data.get("role") or request.role or fill_value(None, roles, seed + "role")
    age = (
        safe_int(ai_data.get("age"))
        or request.age
        or random.Random(seed + "age").randint(19, 48)
    )
    archetype = (
        ai_data.get("archetype")
        or request.archetype
        or fill_value(None, archetypes, seed + "arch")
    )
    goal = ai_data.get("goal") or request.goal or fill_value(None, goals, seed + "goal")
    flaw = ai_data.get("flaw") or request.flaw or fill_value(None, flaws, seed + "flaw")
    voice = ai_data.get("voice") or request.voice or fill_value(None, voices, seed + "voice")
    appearance = (
        ai_data.get("appearance")
        or request.appearance
        or fill_value(None, appearances, seed + "appearance")
    )
    backstory = (
        ai_data.get("backstory")
        or request.backstory
        or fill_value(None, backstories, seed + "backstory")
    )
    quirk_value = ai_data.get("quirks") or request.quirks or fill_value(None, quirks, seed + "quirks")

    return CharacterProfile(
        name=name,
        role=role,
        age=age,
        archetype=archetype,
        goal=goal,
        flaw=flaw,
        voice=voice,
        appearance=appearance,
        backstory=backstory,
        quirks=quirk_value,
    )


# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)

    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()

    _ = await db.status_checks.insert_one(doc)
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)

    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])

    return status_checks


@api_router.get("/projects", response_model=List[Project])
async def list_projects():
    projects = await fetch_projects()
    return projects


@api_router.post("/projects", response_model=Project)
async def create_project(project: ProjectCreate):
    if not project.name.strip():
        raise HTTPException(status_code=400, detail="Project name is required")
    now = datetime.now(timezone.utc)
    new_project = Project(
        id=str(uuid.uuid4()),
        name=project.name.strip(),
        description=project.description,
        genre=project.genre,
        story_bible=None,
        character_profile=None,
        created_at=now,
        updated_at=now,
    )
    await insert_project(new_project)
    return new_project


@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    project = await fetch_project_by_id(project_id)
    if project:
        return project
    raise HTTPException(status_code=404, detail="Project not found")


@api_router.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, update: ProjectUpdate):
    project = await fetch_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    update_data = update.model_dump(exclude_unset=True)
    project.update(update_data)
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    updated_project = await persist_project(project)
    return updated_project


@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    removed = await remove_project(project_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "deleted"}


@api_router.post("/characters/autofill", response_model=CharacterProfile)
async def autofill_character(request: CharacterAutofillRequest):
    ai_data: Optional[Dict[str, Any]] = None
    if request.model:
        lm_base = normalize_lm_url(await get_lm_studio_base())
        prompt = (
            "Fill in missing character details. Return ONLY valid JSON with keys: "
            "name, role, age, archetype, goal, flaw, voice, appearance, backstory, quirks. "
            "Use the provided details as truth and complete the rest. "
            f"Input: {request.model_dump(exclude_none=True)}"
        )
        payload = {
            "model": request.model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a character designer that outputs JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{lm_base}/chat/completions",
                    json=payload,
                )
                response.raise_for_status()
                content = (
                    response.json()
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                ai_data = extract_json_from_text(content)
        except httpx.HTTPError:
            ai_data = None

    profile = build_character_profile(request, ai_data)
    return profile


@api_router.get("/ai/models")
async def list_models():
    lm_base = normalize_lm_url(await get_lm_studio_base())
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{lm_base}/models")
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="LM Studio is unavailable") from exc

    models = [
        {"id": model.get("id")}
        for model in payload.get("data", [])
        if model.get("id")
    ]
    return {"models": models}


@api_router.post("/ai/story-bible/stream")
async def stream_story_bible(request: StoryBibleRequest):
    project = await fetch_project_by_id(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    lm_base = normalize_lm_url(await get_lm_studio_base())

    prompt = (
        "You are Lillith, a narrative architect. Create a rich story bible with "
        "sections for Overview, Themes, World Rules, Key Locations, Factions, "
        "Technology or Magic System, Character Dynamics, and Plot Seeds. "
        f"Project name: {project.get('name')}. "
        f"Genre: {project.get('genre') or 'Not specified'}. "
        f"Description: {project.get('description') or 'No description provided'}. "
        f"Tone: {request.tone or 'Cinematic, immersive, and character-driven'}."
    )

    payload = {
        "model": request.model,
        "stream": True,
        "messages": [
            {
                "role": "system",
                "content": "You are Lillith Offline, a precise story bible engine.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    async def event_stream():
        full_text = ""
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{lm_base}/chat/completions",
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data = line[6:].strip()
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                delta = (
                                    chunk.get("choices", [{}])[0]
                                    .get("delta", {})
                                    .get("content")
                                )
                                if delta:
                                    full_text += delta
                                    yield delta
                            except json.JSONDecodeError:
                                continue
        finally:
            if full_text:
                await update_project_story_bible(request.project_id, full_text)

    return StreamingResponse(event_stream(), media_type="text/plain")


@api_router.get("/services", response_model=List[ServiceConfig])
async def list_services():
    services = await fetch_services()
    statuses = await asyncio.gather(
        *[get_service_status(service) for service in services], return_exceptions=True
    )
    for service, status in zip(services, statuses):
        service["status"] = status if isinstance(status, str) else "offline"
    return services


@api_router.put("/services/{service_id}", response_model=ServiceConfig)
async def update_service_endpoint(service_id: str, update: ServiceUpdate):
    updated = await update_service(service_id, update.model_dump(exclude_unset=True))
    updated["status"] = await get_service_status(updated)
    return updated


@api_router.post("/services/{service_id}/start")
async def start_service(service_id: str):
    service = await fetch_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    command = service.get("start_command")
    if not command:
        raise HTTPException(status_code=400, detail="No start command configured")
    try:
        pid = launch_command(command)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to start service") from exc
    await update_service_pid(service_id, pid)
    return {"status": "started", "pid": pid}


@api_router.post("/services/{service_id}/stop")
async def stop_service(service_id: str):
    service = await fetch_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    command = service.get("stop_command")
    if command:
        try:
            launch_command(command)
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Failed to stop service") from exc
        await update_service_pid(service_id, None)
        return {"status": "stopped"}
    pid = service.get("last_pid")
    if not pid:
        raise HTTPException(status_code=400, detail="No running process found")
    try:
        stop_process(pid)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to stop service") from exc
    await update_service_pid(service_id, None)
    return {"status": "stopped"}


@api_router.post("/services/start-all")
async def start_all_services():
    services = await fetch_services()
    results = []
    for service in services:
        command = service.get("start_command")
        if not command:
            results.append({"id": service["id"], "status": "skipped"})
            continue
        try:
            pid = launch_command(command)
            await update_service_pid(service["id"], pid)
            results.append({"id": service["id"], "status": "started", "pid": pid})
        except Exception:
            results.append({"id": service["id"], "status": "error"})
    return {"results": results}


@api_router.post("/services/stop-all")
async def stop_all_services():
    services = await fetch_services()
    results = []
    for service in services:
        command = service.get("stop_command")
        if command:
            try:
                launch_command(command)
                await update_service_pid(service["id"], None)
                results.append({"id": service["id"], "status": "stopped"})
            except Exception:
                results.append({"id": service["id"], "status": "error"})
            continue
        pid = service.get("last_pid")
        if not pid:
            results.append({"id": service["id"], "status": "skipped"})
            continue
        try:
            stop_process(pid)
            await update_service_pid(service["id"], None)
            results.append({"id": service["id"], "status": "stopped"})
        except Exception:
            results.append({"id": service["id"], "status": "error"})
    return {"results": results}


@api_router.get("/plugins", response_model=List[PluginInfo])
async def list_plugins():
    ensure_storage()
    plugins = [
        PluginInfo(name=path.name, path=str(path))
        for path in PLUGINS_DIR.iterdir()
        if path.is_dir()
    ]
    return plugins


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_db():
    await init_db()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
