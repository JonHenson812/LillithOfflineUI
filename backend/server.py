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


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Local storage paths
DATA_DIR = ROOT_DIR / "data"
PROJECTS_FILE = DATA_DIR / "projects.json"
PLUGINS_DIR = ROOT_DIR.parent / "plugins"
FILE_LOCK = asyncio.Lock()


def ensure_storage():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    if not PROJECTS_FILE.exists():
        PROJECTS_FILE.write_text("[]", encoding="utf-8")


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


class PluginInfo(BaseModel):
    name: str
    path: str


def serialize_project(project: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(project)
    for key in ["created_at", "updated_at"]:
        value = data.get(key)
        if isinstance(value, datetime):
            data[key] = value.isoformat()
    return data


def deserialize_project(project: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(project)
    for key in ["created_at", "updated_at"]:
        if isinstance(data.get(key), str):
            data[key] = datetime.fromisoformat(data[key])
    return data


async def read_projects() -> List[Dict[str, Any]]:
    ensure_storage()
    async with FILE_LOCK:
        raw = PROJECTS_FILE.read_text(encoding="utf-8") or "[]"
        projects = json.loads(raw)
    return [deserialize_project(project) for project in projects]


async def write_projects(projects: List[Dict[str, Any]]) -> None:
    ensure_storage()
    serializable = [serialize_project(project) for project in projects]
    async with FILE_LOCK:
        PROJECTS_FILE.write_text(json.dumps(serializable, indent=2), encoding="utf-8")


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
    projects = await read_projects()
    return projects


@api_router.post("/projects", response_model=Project)
async def create_project(project: ProjectCreate):
    if not project.name.strip():
        raise HTTPException(status_code=400, detail="Project name is required")
    projects = await read_projects()
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
    projects.append(new_project.model_dump())
    await write_projects(projects)
    return new_project


@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    projects = await read_projects()
    for project in projects:
        if project["id"] == project_id:
            return project
    raise HTTPException(status_code=404, detail="Project not found")


@api_router.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, update: ProjectUpdate):
    projects = await read_projects()
    update_data = update.model_dump(exclude_unset=True)
    for index, project in enumerate(projects):
        if project["id"] == project_id:
            project.update(update_data)
            project["updated_at"] = datetime.now(timezone.utc)
            projects[index] = project
            await write_projects(projects)
            return project
    raise HTTPException(status_code=404, detail="Project not found")


@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    projects = await read_projects()
    updated = [project for project in projects if project["id"] != project_id]
    if len(updated) == len(projects):
        raise HTTPException(status_code=404, detail="Project not found")
    await write_projects(updated)
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


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
