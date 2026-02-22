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
        await conn.commit()


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


def fill_value(value: Optional[str], options: List[str], seed: str) -> str:
    if value:
        return value
    rng = random.Random(seed)
    return rng.choice(options)


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
    seed = request.name.strip() or "Lillith"
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

    profile = CharacterProfile(
        name=request.name.strip() or "Unnamed",
        role=fill_value(request.role, roles, seed + "role"),
        age=request.age or random.Random(seed + "age").randint(19, 48),
        archetype=fill_value(request.archetype, archetypes, seed + "arch"),
        goal=fill_value(request.goal, goals, seed + "goal"),
        flaw=fill_value(request.flaw, flaws, seed + "flaw"),
        voice=fill_value(request.voice, voices, seed + "voice"),
        appearance=fill_value(request.appearance, appearances, seed + "appearance"),
        backstory=fill_value(request.backstory, backstories, seed + "backstory"),
        quirks=fill_value(request.quirks, quirks, seed + "quirks"),
    )

    return profile


@api_router.get("/ai/models")
async def list_models():
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{LM_STUDIO_URL}/models")
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
                    f"{LM_STUDIO_URL}/chat/completions",
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
