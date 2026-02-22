# Lillith Offline PRD

## Original Problem Statement
Build "Lillith Offline" (desktop-first, then web UI) to automate writing books. The app should run locally, go online only for research, and use parallel agents. Core needs: navigation shell, character builder with auto-fill, project save/load locally, 3D avatar placeholder, and a plugin system for mini-apps (book writer, role play, graphic designer, illustration/video via Stable Diffusion/ComfyUI, Raspberry Pi lab). The experience should be eye‑catching and non-corporate.

## Architecture Decisions
- Frontend: React (CRA + Tailwind utilities) with custom stylized UI.
- Backend: FastAPI, extended with local SQLite storage for offline projects.
- Storage: SQLite file `/app/backend/data/lillith.sqlite` for projects and settings; local storage for UI state.
- Plugin discovery: Directory scan from `/app/plugins`.
- AI: LM Studio integration (OpenAI-compatible API) for story-bible generation; streaming responses.
- Services control: Backend-managed service registry for LM Studio, ComfyUI, and Stable Diffusion with start/stop commands.

## Implemented (MVP + Phase 1 + Improvements)
- Desktop-style app shell with navigation (Command Deck, Character Builder, Projects, Plugin Bay, Services).
- Command Deck dashboard with chat panel and avatar stage placeholder.
- Character Builder with LM Studio auto-fill (fallback if LM unavailable) and attach-to-project flow.
- Project Vault with create/load/edit/save/delete using SQLite storage.
- Story Bible prompt editor (tone, length, tags) before generation.
- Active project state stored in localStorage for fast resume.
- Plugin Bay with scan + refresh for `/app/plugins`.
- Online/offline mode toggle UI.
- LM Studio model scan endpoint + dropdown with refresh button.
- Streaming story bible generation endpoint + UI button with live updates.
- Services Console with start/stop (per service + bulk), health checks, editable commands + URLs.
- Service preferences: auto-start toggle, auto-refresh toggle (20s), last-updated indicator.
- Standard menu bar (File/Edit/View/Tools/Help) and troubleshooting tips for local installs.

## Prioritized Backlog
### P0
- Electron desktop shell packaging.
- 3D avatar runtime (main window + popup) integration.

### P1
- ComfyUI/Stable Diffusion integration for illustration mini-app.
- Plugin manifest loader + dynamic mini-app registry.
- Project “story bible” expansion into chapters + beat sheets.

### P2
- Android companion app with project pack import/export.
- Cross-device sync (manual then live).
- Voice options + multi-voice avatar settings.
