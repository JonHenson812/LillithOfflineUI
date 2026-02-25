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
- 3D Avatar: Three.js canvas scene with environment presets, character presets, Ready Player Me default, GLB upload, and optional ambientCG textures.
- Electron: Desktop shell scaffolding with packaging config (Windows .exe via electron-builder).

## Implemented (MVP + Phase 1 + Improvements)
- Desktop-style app shell with navigation (Command Deck, Character Builder, Projects, Visual Studio, Plugin Bay, Services).
- Command Deck dashboard with chat panel, 3D avatar stage, and service health widget.
- 3D avatar canvas with idle + emotion states (happy/curious/concerned), walking loop + approach on interaction.
- Avatar customization: environment presets, character presets, Ready Player Me default, GLB/GLTF upload, texture URL support.
- Character Builder with LM Studio auto-fill (fallback if LM unavailable) and attach-to-project flow.
- Project Vault with create/load/edit/save/delete using SQLite storage.
- Story Bible prompt editor (tone, length, tags) before generation.
- Visual Studio mini-apps for Stable Diffusion (txt2img) and ComfyUI workflows, with service status badges and default ComfyUI workflow prefill.
- Online/offline mode toggle UI.
- LM Studio model scan endpoint + dropdown with refresh button.
- Streaming story bible generation endpoint + UI button with live updates.
- Services Console with start/stop (per service + bulk), health checks, editable commands + URLs.
- Service preferences: auto-start toggle, auto-refresh toggle (20s), last-updated indicator.
- Standard menu bar (File/Edit/View/Tools/Help) and troubleshooting tips for local installs.
- Electron main/preload scaffolding and build config for Windows packaging.

## Prioritized Backlog
### P0
- Electron build verification on Windows + always-on-top click-through avatar popup.
- Real 3D avatar model loading with visemes + emotion rigging.

### P1
- ComfyUI/Stable Diffusion advanced presets + gallery management.
- Plugin manifest loader + dynamic mini-app registry.
- Project “story bible” expansion into chapters + beat sheets.

### P2
- Android companion app with project pack import/export.
- Cross-device sync (manual then live).
- Voice options + multi-voice avatar settings.
