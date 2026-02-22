# Lillith Offline PRD

## Original Problem Statement
Build "Lillith Offline" (desktop-first, then web UI) to automate writing books. The app should run locally, go online only for research, and use parallel agents. Core needs: navigation shell, character builder with auto-fill, project save/load locally, 3D avatar placeholder, and a plugin system for mini-apps (book writer, role play, graphic designer, illustration/video via Stable Diffusion/ComfyUI, Raspberry Pi lab). The experience should be eye‑catching and non-corporate.

## Architecture Decisions
- Frontend: React (CRA + Tailwind utilities) with custom stylized UI.
- Backend: FastAPI (existing service), extended with local JSON storage for offline projects.
- Storage: Local JSON file `/app/backend/data/projects.json` managed by backend API.
- Plugin discovery: Directory scan from `/app/plugins`.
- AI: Character auto-fill uses deterministic local generator for now (placeholder until LM Studio integration).

## Implemented (MVP)
- Desktop-style app shell with navigation (Command Deck, Character Builder, Projects, Plugin Bay).
- Command Deck dashboard with chat panel and avatar stage placeholder.
- Character Builder with auto-fill endpoint and attach-to-project flow.
- Project Vault with create/load/edit/save/delete using local JSON storage.
- Active project state stored in localStorage for fast resume.
- Plugin Bay with scan + refresh for `/app/plugins`.
- Online/offline mode toggle UI.

## Prioritized Backlog
### P0
- Electron desktop shell packaging.
- Integrate LM Studio for text generation + character autofill (replace placeholder).
- 3D avatar runtime (main window + popup) integration.

### P1
- ComfyUI/Stable Diffusion integration for illustration mini-app.
- Plugin manifest loader + dynamic mini-app registry.
- Project “story bible” auto-generation with agent workflow.

### P2
- Android companion app with project pack import/export.
- Cross-device sync (manual then live).
- Voice options + multi-voice avatar settings.
