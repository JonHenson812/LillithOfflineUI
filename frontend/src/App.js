import { useEffect, useMemo, useRef, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, NavLink, useNavigate } from "react-router-dom";
import { Canvas, useFrame } from "@react-three/fiber";
import axios from "axios";
import {
  Bot,
  BookOpen,
  LayoutGrid,
  Plug,
  UserRound,
  Sparkles,
  Orbit,
  ServerCog,
  RefreshCcw,
  Play,
  Square,
  ExternalLink,
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const navItems = [
  {
    path: "/",
    label: "Command Deck",
    icon: LayoutGrid,
    testId: "nav-command-deck",
  },
  {
    path: "/character-builder",
    label: "Character Builder",
    icon: UserRound,
    testId: "nav-character-builder",
  },
  {
    path: "/projects",
    label: "Projects",
    icon: BookOpen,
    testId: "nav-projects",
  },
  {
    path: "/plugins",
    label: "Plugin Bay",
    icon: Plug,
    testId: "nav-plugins",
  },
  {
    path: "/services",
    label: "Services",
    icon: ServerCog,
    testId: "nav-services",
  },
];

const TopBar = ({
  activeProject,
  onlineMode,
  setOnlineMode,
  availableModels,
  selectedModel,
  setSelectedModel,
  modelStatus,
  onRefreshModels,
}) => {
  return (
    <div className="topbar" data-testid="topbar">
      <div className="topbar-left" data-testid="topbar-left">
        <div className="app-title" data-testid="app-title">
          Lillith Offline
        </div>
        <div className="status-chip" data-testid="status-chip">
          <span
            className={`status-dot ${onlineMode ? "online" : "offline"}`}
            data-testid="status-dot"
          />
          <span data-testid="status-text">
            {onlineMode ? "Online research" : "Local mode"}
          </span>
        </div>
      </div>
      <div className="topbar-right" data-testid="topbar-right">
        <div className="model-select" data-testid="model-select">
          <span className="label" data-testid="model-select-label">
            Model
          </span>
          {modelStatus === "ready" ? (
            <select
              className="lilith-select"
              value={selectedModel}
              onChange={(event) => setSelectedModel(event.target.value)}
              data-testid="model-select-input"
            >
              {availableModels.map((model) => (
                <option
                  key={model.id}
                  value={model.id}
                  data-testid={`model-option-${model.id}`}
                >
                  {model.id}
                </option>
              ))}
            </select>
          ) : (
            <span className="model-status" data-testid="model-status">
              {modelStatus === "loading"
                ? "Scanning models..."
                : modelStatus === "empty"
                ? "No models found"
                : "LM Studio offline"}
            </span>
          )}
          <button
            className="icon-button"
            onClick={onRefreshModels}
            data-testid="model-refresh-button"
          >
            <RefreshCcw className="button-icon" data-testid="model-refresh-icon" />
          </button>
        </div>
        <div className="active-project" data-testid="active-project">
          <span className="label" data-testid="active-project-label">
            Active Project
          </span>
          <span className="value" data-testid="active-project-name">
            {activeProject?.name || "No project loaded"}
          </span>
        </div>
        <button
          className="lilith-button secondary"
          onClick={() => setOnlineMode((value) => !value)}
          data-testid="toggle-online-mode"
        >
          {onlineMode ? "Go Offline" : "Enable Online"}
        </button>
      </div>
    </div>
  );
};

const MenuBar = () => {
  const [openMenu, setOpenMenu] = useState(null);
  const navigate = useNavigate();

  const menuItems = [
    {
      id: "file",
      label: "File",
      items: [
        { id: "file-new", label: "New Project", action: "open-projects" },
        { id: "file-open", label: "Open Project", action: "open-projects" },
        { id: "file-save", label: "Save Project", action: "open-projects" },
        { id: "file-export", label: "Export", action: "export" },
      ],
    },
    {
      id: "edit",
      label: "Edit",
      items: [
        { id: "edit-undo", label: "Undo", action: "undo" },
        { id: "edit-redo", label: "Redo", action: "redo" },
        { id: "edit-find", label: "Find", action: "find" },
      ],
    },
    {
      id: "view",
      label: "View",
      items: [
        { id: "view-sidebar", label: "Toggle Sidebar", action: "toggle-sidebar" },
        { id: "view-focus", label: "Focus Mode", action: "focus" },
      ],
    },
    {
      id: "tools",
      label: "Tools",
      items: [
        { id: "tools-services", label: "Services", action: "open-services" },
        { id: "tools-plugins", label: "Plugins", action: "open-plugins" },
      ],
    },
    {
      id: "help",
      label: "Help",
      items: [
        { id: "help-docs", label: "Documentation", action: "docs" },
        { id: "help-support", label: "Support", action: "support" },
      ],
    },
  ];

  const handleAction = (action) => {
    if (action === "open-services") {
      navigate("/services");
    }
    if (action === "open-plugins") {
      navigate("/plugins");
    }
    if (action === "open-projects") {
      navigate("/projects");
    }
    setOpenMenu(null);
  };

  return (
    <div className="menu-bar" data-testid="menu-bar">
      {menuItems.map((menu) => (
        <div key={menu.id} className="menu-item" data-testid={`menu-${menu.id}`}>
          <button
            className="menu-button"
            onClick={() =>
              setOpenMenu((current) => (current === menu.id ? null : menu.id))
            }
            data-testid={`menu-button-${menu.id}`}
          >
            {menu.label}
          </button>
          {openMenu === menu.id && (
            <div
              className="menu-dropdown"
              data-testid={`menu-dropdown-${menu.id}`}
            >
              {menu.items.map((item) => (
                <button
                  key={item.id}
                  className="menu-dropdown-item"
                  onClick={() => handleAction(item.action)}
                  data-testid={`menu-item-${item.id}`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

const SideNav = () => {
  return (
    <aside className="sidebar" data-testid="sidebar">
      <div className="sidebar-header" data-testid="sidebar-header">
        <Bot className="logo-icon" data-testid="sidebar-logo-icon" />
        <div className="sidebar-title" data-testid="sidebar-title">
          Lillith Core
        </div>
      </div>
      <nav className="nav" data-testid="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `nav-link ${isActive ? "active" : ""}`
              }
              data-testid={item.testId}
            >
              <Icon className="nav-icon" data-testid={`${item.testId}-icon`} />
              <span data-testid={`${item.testId}-label`}>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
      <div className="sidebar-footer" data-testid="sidebar-footer">
        <div className="sidebar-meta" data-testid="sidebar-meta">
          <span className="label" data-testid="sidebar-meta-label">
            Plugins
          </span>
          <span className="value" data-testid="sidebar-meta-value">
            Drop-in ready
          </span>
        </div>
        <div className="sidebar-meta" data-testid="sidebar-meta-status">
          <span className="label" data-testid="sidebar-meta-status-label">
            Status
          </span>
          <span className="value" data-testid="sidebar-meta-status-value">
            Listening for updates
          </span>
        </div>
      </div>
    </aside>
  );
};


const AvatarScene = ({ emotion }) => {
  const meshRef = useRef(null);
  const ringRef = useRef(null);
  const colors = useMemo(
    () => ({
      idle: "#53d3ff",
      happy: "#5dffb3",
      curious: "#ffbf63",
      concerned: "#ff7a7a",
    }),
    []
  );
  const color = colors[emotion] || colors.idle;

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    if (meshRef.current) {
      meshRef.current.rotation.y = t * 0.4;
      meshRef.current.rotation.x = Math.sin(t / 2) * 0.1;
      meshRef.current.position.y = Math.sin(t) * 0.15;
    }
    if (ringRef.current) {
      ringRef.current.rotation.z = t * 0.2;
    }
  });

  return (
    <group>
      <ambientLight intensity={0.6} />
      <pointLight position={[4, 4, 4]} intensity={1.2} />
      <mesh ref={meshRef}>
        <sphereGeometry args={[1.2, 64, 64]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.4}
          roughness={0.25}
          metalness={0.6}
        />
      </mesh>
      <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.8, 0.05, 16, 100]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.6}
          roughness={0.4}
        />
      </mesh>
    </group>
  );
};

const Dashboard = () => {
  const [messages, setMessages] = useState([
    {
      id: "intro-1",
      sender: "lillith",
      text: "I’m synced locally and ready to build worlds with you. Where should we begin?",
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [avatarMode, setAvatarMode] = useState("main");
  const [avatarEmotion, setAvatarEmotion] = useState("idle");
  const [serviceHealth, setServiceHealth] = useState([]);
  const [serviceNotice, setServiceNotice] = useState("");
  const [serviceUpdated, setServiceUpdated] = useState("");

  const loadServiceHealth = async () => {
    try {
      const response = await axios.get(`${API}/services`);
      setServiceHealth(response.data);
      setServiceUpdated(new Date().toLocaleTimeString());
    } catch (error) {
      console.error(error);
      setServiceNotice("Unable to load service status.");
    }
  };

  useEffect(() => {
    loadServiceHealth();
  }, []);

  const toggleService = async (serviceId, action) => {
    setServiceNotice("");
    try {
      const response = await axios.post(`${API}/services/${serviceId}/${action}`);
      if (response.data.status === "error") {
        setServiceNotice(response.data.detail || "Service action failed.");
      }
      await loadServiceHealth();
    } catch (error) {
      console.error(error);
      setServiceNotice("Service action failed.");
    }
  };

  const openServicePanel = (service) => {
    if (!service.base_url) {
      setServiceNotice("Set a base URL before opening the service.");
      return;
    }
    window.open(service.base_url, "_blank", "noopener,noreferrer");
  };

  const agentCards = [
    {
      id: "plot-architect",
      name: "Plot Architect",
      focus: "Structures arcs and turning points",
      status: "Active",
    },
    {
      id: "world-weaver",
      name: "World Weaver",
      focus: "Builds lore, cultures, and rules",
      status: "Active",
    },
    {
      id: "character-sentinel",
      name: "Character Sentinel",
      focus: "Tracks motivations + continuity",
      status: "Listening",
    },
    {
      id: "scene-forge",
      name: "Scene Forge",
      focus: "Turns beats into vivid scenes",
      status: "Idle",
    },
  ];

  const miniApps = [
    {
      id: "book-writer",
      name: "Book Writer",
      description: "Draft chapters, summaries, and edits.",
    },
    {
      id: "role-play",
      name: "Role Play",
      description: "Choose-your-own-adventure story engine.",
    },
    {
      id: "graphic-designer",
      name: "Graphic Designer",
      description: "Covers, concept art, and layouts.",
    },
    {
      id: "illustration-video",
      name: "Illustration + Video",
      description: "Connects to Stable Diffusion & ComfyUI.",
    },
    {
      id: "raspberry-pi",
      name: "Raspberry Pi Lab",
      description: "Prototype hardware-driven narratives.",
    },
  ];

  const sendMessage = () => {
    if (!chatInput.trim()) return;
    const userMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: chatInput.trim(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setChatInput("");
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: `lillith-${Date.now()}`,
          sender: "lillith",
          text: "I’m mapping that across the agent grid. Want a character spun up next?",
        },
      ]);
    }, 700);
  };

  return (
    <div className="page" data-testid="dashboard-page">
      <div className="hero" data-testid="dashboard-hero">
        <div className="hero-text" data-testid="dashboard-hero-text">
          <div className="eyebrow" data-testid="dashboard-hero-eyebrow">
            Lillith Offline Command Deck
          </div>
          <h1 className="hero-title" data-testid="dashboard-hero-title">
            Build entire universes without leaving your desktop.
          </h1>
          <p className="hero-subtitle" data-testid="dashboard-hero-subtitle">
            Parallel agents handle the routine. You stay focused on the moments that
            matter.
          </p>
        </div>
        <div className="hero-actions" data-testid="dashboard-hero-actions">
          <button className="lilith-button" data-testid="hero-start-session">
            Start a new session
          </button>
          <button
            className="lilith-button secondary"
            data-testid="hero-open-projects"
          >
            Open saved worlds
          </button>
        </div>
      </div>

      <div className="grid two-column" data-testid="dashboard-main-grid">
        <div className="glass-panel" data-testid="chat-panel">
          <div className="panel-header" data-testid="chat-panel-header">
            <div className="panel-title" data-testid="chat-panel-title">
              Lillith Chat
            </div>
            <span className="panel-badge" data-testid="chat-panel-badge">
              Adaptive voice + memory
            </span>
          </div>
          <div className="chat-window" data-testid="chat-window">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`chat-bubble ${message.sender}`}
                data-testid={`chat-message-${message.id}`}
              >
                <span data-testid={`chat-message-text-${message.id}`}>
                  {message.text}
                </span>
              </div>
            ))}
          </div>
          <div className="chat-input" data-testid="chat-input-row">
            <textarea
              className="lilith-input"
              value={chatInput}
              onChange={(event) => setChatInput(event.target.value)}
              placeholder="Tell Lillith what you want to build..."
              data-testid="chat-input"
            />
            <button
              className="lilith-button"
              onClick={sendMessage}
              data-testid="chat-send-button"
            >
              Send
            </button>
          </div>
        </div>

        <div className="glass-panel" data-testid="avatar-panel">
          <div className="panel-header" data-testid="avatar-panel-header">
            <div className="panel-title" data-testid="avatar-panel-title">
              Avatar Stage
            </div>
            <span className="panel-badge" data-testid="avatar-panel-badge">
              3D sync ready
            </span>
          </div>
          <div className="avatar-stage" data-testid="avatar-stage">
            <Canvas
              className="avatar-canvas"
              data-testid="avatar-canvas"
              camera={{ position: [0, 0, 4], fov: 45 }}
            >
              <AvatarScene emotion={avatarEmotion} />
            </Canvas>
            <div className="avatar-overlay" data-testid="avatar-overlay">
              <span data-testid="avatar-emotion-label">
                Emotion: {avatarEmotion}
              </span>
            </div>
          </div>
          <div className="avatar-controls" data-testid="avatar-emotion-controls">
            {[
              "idle",
              "happy",
              "curious",
              "concerned",
            ].map((mood) => (
              <button
                key={mood}
                className={`lilith-button ${
                  avatarEmotion === mood ? "" : "secondary"
                }`}
                onClick={() => setAvatarEmotion(mood)}
                data-testid={`avatar-emotion-${mood}`}
              >
                {mood}
              </button>
            ))}
          </div>
          <div className="avatar-controls" data-testid="avatar-controls">
            <button
              className={`lilith-button ${
                avatarMode === "main" ? "" : "secondary"
              }`}
              onClick={() => setAvatarMode("main")}
              data-testid="avatar-mode-main"
            >
              Main Window
            </button>
            <button
              className={`lilith-button ${
                avatarMode === "popup" ? "" : "secondary"
              }`}
              onClick={() => setAvatarMode("popup")}
              data-testid="avatar-mode-popup"
            >
              Popup Mode
            </button>
          </div>
          <div className="avatar-status" data-testid="avatar-status">
            Current mode: {avatarMode === "main" ? "Main window" : "Popup window"}.
            Popup mode will be always-on-top + click-through in the Electron build.
          </div>
        </div>
      </div>

      <div className="grid" data-testid="agents-grid">
        {agentCards.map((agent) => (
          <div
            key={agent.id}
            className="glass-panel agent-card"
            data-testid={`agent-card-${agent.id}`}
          >
            <div className="agent-header" data-testid={`agent-header-${agent.id}`}>
              <Orbit className="agent-icon" data-testid={`agent-icon-${agent.id}`} />
              <span data-testid={`agent-name-${agent.id}`}>{agent.name}</span>
            </div>
            <div
              className="agent-focus"
              data-testid={`agent-focus-${agent.id}`}
            >
              {agent.focus}
            </div>
            <span
              className={`agent-status ${agent.status.toLowerCase()}`}
              data-testid={`agent-status-${agent.id}`}
            >
              {agent.status}
            </span>
          </div>
        ))}
      </div>

      <div className="section" data-testid="mini-apps-section">
        <div className="section-header" data-testid="mini-apps-header">
          <div className="section-title" data-testid="mini-apps-title">
            Mini-apps bay
          </div>
          <div className="section-subtitle" data-testid="mini-apps-subtitle">
            Drop-in extensions will appear here instantly.
          </div>
        </div>
        <div className="grid three-column" data-testid="mini-apps-grid">
          {miniApps.map((app) => (
            <div
              key={app.id}
              className="glass-panel mini-app"
              data-testid={`mini-app-card-${app.id}`}
            >
              <div className="mini-app-header" data-testid={`mini-app-header-${app.id}`}>
                <Sparkles className="mini-app-icon" data-testid={`mini-app-icon-${app.id}`} />
                <span data-testid={`mini-app-name-${app.id}`}>{app.name}</span>
              </div>
              <div
                className="mini-app-description"
                data-testid={`mini-app-description-${app.id}`}
              >
                {app.description}
              </div>
              <button
                className="lilith-button secondary"
                data-testid={`mini-app-open-${app.id}`}
              >
                Open mini-app
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const CharacterBuilder = ({
  activeProject,
  onAttachCharacter,
  selectedModel,
  modelStatus,
}) => {
  const [form, setForm] = useState({
    name: "",
    role: "",
    age: "",
    archetype: "",
    goal: "",
    flaw: "",
    voice: "",
    appearance: "",
    backstory: "",
    quirks: "",
  });
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const autofillCharacter = async () => {
    setLoading(true);
    setNotice("");
    if (modelStatus !== "ready" || !selectedModel) {
      setNotice("LM Studio is offline — using fallback generator.");
    }
    try {
      const response = await axios.post(`${API}/characters/autofill`, {
        ...form,
        age: form.age ? Number(form.age) : null,
        model: modelStatus === "ready" ? selectedModel : null,
      });
      setForm({
        ...response.data,
        age: response.data.age ? String(response.data.age) : "",
      });
      setNotice("Lillith generated the missing traits.");
    } catch (error) {
      console.error(error);
      setNotice("Unable to auto-fill right now.");
    } finally {
      setLoading(false);
    }
  };

  const attachCharacter = () => {
    if (!activeProject?.id) {
      setNotice("Load a project before attaching this character.");
      return;
    }
    onAttachCharacter(form);
  };

  const fieldRows = useMemo(
    () => [
      {
        key: "name",
        label: "Name",
        placeholder: "Name your character",
      },
      {
        key: "role",
        label: "Role",
        placeholder: "Protagonist, antagonist, mentor...",
      },
      {
        key: "age",
        label: "Age",
        placeholder: "Age or range",
      },
      {
        key: "archetype",
        label: "Archetype",
        placeholder: "Chosen one, rebel, detective...",
      },
      {
        key: "goal",
        label: "Core goal",
        placeholder: "What drives them forward?",
      },
      {
        key: "flaw",
        label: "Core flaw",
        placeholder: "What holds them back?",
      },
      {
        key: "voice",
        label: "Voice",
        placeholder: "Accent, cadence, tone",
      },
      {
        key: "appearance",
        label: "Appearance",
        placeholder: "Signature look",
      },
    ],
    []
  );

  return (
    <div className="page" data-testid="character-builder-page">
      <div className="page-header" data-testid="character-builder-header">
        <div>
          <div className="eyebrow" data-testid="character-builder-eyebrow">
            Character Builder
          </div>
          <h1 className="page-title" data-testid="character-builder-title">
            Shape a character in minutes, let Lillith handle the rest.
          </h1>
        </div>
        <div className="page-actions" data-testid="character-builder-actions">
          <button
            className="lilith-button"
            onClick={autofillCharacter}
            disabled={loading}
            data-testid="character-autofill-button"
          >
            {loading ? "Generating..." : "Auto-fill missing info"}
          </button>
          <button
            className="lilith-button secondary"
            onClick={attachCharacter}
            data-testid="character-attach-button"
          >
            Attach to active project
          </button>
          <div className="helper" data-testid="character-model-hint">
            Model: {modelStatus === "ready" ? selectedModel || "Select a model" : modelStatus === "empty" ? "No models found" : "LM Studio offline"}
          </div>
        </div>
      </div>

      {notice && (
        <div className="notice" data-testid="character-notice">
          {notice}
        </div>
      )}

      <div className="grid two-column" data-testid="character-builder-grid">
        <div className="glass-panel" data-testid="character-form-panel">
          <div className="panel-header" data-testid="character-form-header">
            <div className="panel-title" data-testid="character-form-title">
              Core Profile
            </div>
            <span className="panel-badge" data-testid="character-form-badge">
              Auto-fill supported
            </span>
          </div>
          <div className="form-grid" data-testid="character-form-grid">
            {fieldRows.map((field) => (
              <label
                key={field.key}
                className="form-field"
                data-testid={`character-field-${field.key}`}
              >
                <span
                  className="field-label"
                  data-testid={`character-${field.key}-label`}
                >
                  {field.label}
                </span>
                <input
                  className="lilith-input"
                  value={form[field.key]}
                  onChange={(event) => handleChange(field.key, event.target.value)}
                  placeholder={field.placeholder}
                  data-testid={`character-${field.key}-input`}
                />
              </label>
            ))}
          </div>
        </div>

        <div className="glass-panel" data-testid="character-detail-panel">
          <div className="panel-header" data-testid="character-detail-header">
            <div className="panel-title" data-testid="character-detail-title">
              Depth + Backstory
            </div>
            <span className="panel-badge" data-testid="character-detail-badge">
              Optional but powerful
            </span>
          </div>
          <label className="form-field" data-testid="character-quirks-field">
            <span
              className="field-label"
              data-testid="character-quirks-label"
            >
              Quirks & habits
            </span>
            <textarea
              className="lilith-input"
              value={form.quirks}
              onChange={(event) => handleChange("quirks", event.target.value)}
              placeholder="Gestures, phrases, rituals..."
              data-testid="character-quirks-input"
            />
          </label>
          <label className="form-field" data-testid="character-backstory-field">
            <span
              className="field-label"
              data-testid="character-backstory-label"
            >
              Backstory
            </span>
            <textarea
              className="lilith-input"
              value={form.backstory}
              onChange={(event) => handleChange("backstory", event.target.value)}
              placeholder="Past events that shaped them"
              data-testid="character-backstory-input"
            />
          </label>
          <div
            className="active-project-hint"
            data-testid="character-active-project-hint"
          >
            Active project: {activeProject?.name || "None loaded"}
          </div>
        </div>
      </div>

      <div className="glass-panel" data-testid="character-preview-panel">
        <div className="panel-header" data-testid="character-preview-header">
          <div className="panel-title" data-testid="character-preview-title">
            Preview
          </div>
          <span className="panel-badge" data-testid="character-preview-badge">
            Ready to save
          </span>
        </div>
        <div className="preview-grid" data-testid="character-preview-grid">
          {Object.entries(form).map(([key, value]) => (
            <div key={key} className="preview-item" data-testid={`preview-${key}`}>
              <span
                className="preview-label"
                data-testid={`preview-${key}-label`}
              >
                {key}
              </span>
              <span
                className="preview-value"
                data-testid={`preview-${key}-value`}
              >
                {value || "—"}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const Projects = ({ activeProject, setActiveProject, selectedModel, modelStatus }) => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [form, setForm] = useState({ name: "", description: "", genre: "" });
  const [editForm, setEditForm] = useState({
    name: "",
    description: "",
    genre: "",
    story_bible: "",
  });
  const [notice, setNotice] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [storyBrief, setStoryBrief] = useState({
    tone: "",
    length: "",
    tags: "",
  });

  const loadProjects = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/projects`);
      setProjects(response.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const createProject = async () => {
    if (!form.name.trim()) {
      setNotice("Project name is required.");
      return;
    }
    try {
      const response = await axios.post(`${API}/projects`, form);
      setNotice("Project created and saved locally.");
      setForm({ name: "", description: "", genre: "" });
      await loadProjects();
      setActiveProject(response.data);
    } catch (error) {
      console.error(error);
      setNotice("Unable to save project right now.");
    }
  };

  const loadProject = async (projectId) => {
    try {
      const response = await axios.get(`${API}/projects/${projectId}`);
      setSelectedProject(response.data);
      setEditForm({
        name: response.data.name || "",
        description: response.data.description || "",
        genre: response.data.genre || "",
        story_bible: response.data.story_bible || "",
      });
      setActiveProject(response.data);
      setNotice("Project loaded.");
    } catch (error) {
      console.error(error);
      setNotice("Unable to load project.");
    }
  };

  const saveProject = async () => {
    if (!selectedProject?.id) return;
    try {
      const response = await axios.put(
        `${API}/projects/${selectedProject.id}`,
        editForm
      );
      setSelectedProject(response.data);
      setActiveProject(response.data);
      setNotice("Project updated.");
      await loadProjects();
    } catch (error) {
      console.error(error);
      setNotice("Unable to update project.");
    }
  };

  const generateStoryBible = async () => {
    if (!selectedProject?.id) {
      setNotice("Load a project before generating the story bible.");
      return;
    }
    if (modelStatus !== "ready" || !selectedModel) {
      setNotice("LM Studio is offline or no model selected.");
      return;
    }
    setIsGenerating(true);
    setNotice("Generating story bible...");
    try {
      const response = await fetch(`${API}/ai/story-bible/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: selectedProject.id,
          model: selectedModel,
          tone: storyBrief.tone || null,
          length: storyBrief.length || null,
          tags: storyBrief.tags || null,
        }),
      });
      if (!response.ok || !response.body) {
        throw new Error("Story bible stream failed");
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let result = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        result += decoder.decode(value);
        setEditForm((prev) => ({ ...prev, story_bible: result }));
      }
      setSelectedProject((prev) =>
        prev ? { ...prev, story_bible: result } : prev
      );
      setActiveProject((prev) =>
        prev && prev.id === selectedProject.id
          ? { ...prev, story_bible: result }
          : prev
      );
      setNotice("Story bible updated.");
    } catch (error) {
      console.error(error);
      setNotice("Unable to generate story bible.");
    } finally {
      setIsGenerating(false);
    }
  };

  const deleteProject = async (projectId) => {
    try {
      await axios.delete(`${API}/projects/${projectId}`);
      setNotice("Project deleted.");
      if (selectedProject?.id === projectId) {
        setSelectedProject(null);
        setEditForm({ name: "", description: "", genre: "", story_bible: "" });
      }
      if (activeProject?.id === projectId) {
        setActiveProject(null);
      }
      await loadProjects();
    } catch (error) {
      console.error(error);
      setNotice("Unable to delete project.");
    }
  };

  return (
    <div className="page" data-testid="projects-page">
      <div className="page-header" data-testid="projects-header">
        <div>
          <div className="eyebrow" data-testid="projects-eyebrow">
            Project Vault
          </div>
          <h1 className="page-title" data-testid="projects-title">
            Save and reload entire story worlds instantly.
          </h1>
        </div>
        <div className="page-actions" data-testid="projects-actions">
          <button
            className="lilith-button"
            onClick={createProject}
            data-testid="project-create-button"
          >
            Save new project
          </button>
        </div>
      </div>

      {notice && (
        <div className="notice" data-testid="projects-notice">
          {notice}
        </div>
      )}

      <div className="grid two-column" data-testid="projects-grid">
        <div className="glass-panel" data-testid="project-create-panel">
          <div className="panel-header" data-testid="project-create-header">
            <div className="panel-title" data-testid="project-create-title">
              Create project
            </div>
            <span className="panel-badge" data-testid="project-create-badge">
              Local SQLite storage
            </span>
          </div>
          <label className="form-field" data-testid="project-name-field">
            <span className="field-label" data-testid="project-name-label">
              Project name
            </span>
            <input
              className="lilith-input"
              value={form.name}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, name: event.target.value }))
              }
              placeholder="Ex: Neon Covenant"
              data-testid="project-name-input"
            />
          </label>
          <label
            className="form-field"
            data-testid="project-description-field"
          >
            <span
              className="field-label"
              data-testid="project-description-label"
            >
              Short description
            </span>
            <textarea
              className="lilith-input"
              value={form.description}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, description: event.target.value }))
              }
              placeholder="High-level summary"
              data-testid="project-description-input"
            />
          </label>
          <label className="form-field" data-testid="project-genre-field">
            <span className="field-label" data-testid="project-genre-label">
              Genre
            </span>
            <input
              className="lilith-input"
              value={form.genre}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, genre: event.target.value }))
              }
              placeholder="Sci-fi, fantasy, thriller"
              data-testid="project-genre-input"
            />
          </label>
          <div className="helper" data-testid="project-create-helper">
            Active project: {activeProject?.name || "None"}
          </div>
        </div>

        <div className="glass-panel" data-testid="project-list-panel">
          <div className="panel-header" data-testid="project-list-header">
            <div className="panel-title" data-testid="project-list-title">
              Saved projects
            </div>
            <span className="panel-badge" data-testid="project-list-badge">
              {loading ? "Loading" : `${projects.length} total`}
            </span>
          </div>
          <div className="project-list" data-testid="project-list">
            {projects.length === 0 && !loading ? (
              <div
                className="empty-state"
                data-testid="project-list-empty"
              >
                No projects saved yet.
              </div>
            ) : (
              projects.map((project) => (
                <div
                  key={project.id}
                  className="project-card"
                  data-testid={`project-card-${project.id}`}
                >
                  <div
                    className="project-card-title"
                    data-testid={`project-card-title-${project.id}`}
                  >
                    {project.name}
                  </div>
                  <div
                    className="project-card-meta"
                    data-testid={`project-card-meta-${project.id}`}
                  >
                    {project.genre || "Genre pending"}
                  </div>
                  <div className="project-card-actions">
                    <button
                      className="lilith-button"
                      onClick={() => loadProject(project.id)}
                      data-testid={`project-card-load-${project.id}`}
                    >
                      Load
                    </button>
                    <button
                      className="lilith-button secondary"
                      onClick={() => deleteProject(project.id)}
                      data-testid={`project-card-delete-${project.id}`}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="glass-panel" data-testid="project-editor-panel">
        <div className="panel-header" data-testid="project-editor-header">
          <div className="panel-title" data-testid="project-editor-title">
            Project detail
          </div>
          <span className="panel-badge" data-testid="project-editor-badge">
            {selectedProject ? "Loaded" : "Select a project"}
          </span>
        </div>
        <div className="grid two-column" data-testid="project-editor-grid">
          <label className="form-field" data-testid="project-edit-name-field">
            <span className="field-label" data-testid="project-edit-name-label">
              Project name
            </span>
            <input
              className="lilith-input"
              value={editForm.name}
              onChange={(event) =>
                setEditForm((prev) => ({ ...prev, name: event.target.value }))
              }
              data-testid="project-edit-name-input"
            />
          </label>
          <label
            className="form-field"
            data-testid="project-edit-genre-field"
          >
            <span
              className="field-label"
              data-testid="project-edit-genre-label"
            >
              Genre
            </span>
            <input
              className="lilith-input"
              value={editForm.genre}
              onChange={(event) =>
                setEditForm((prev) => ({ ...prev, genre: event.target.value }))
              }
              data-testid="project-edit-genre-input"
            />
          </label>
        </div>
        <label
          className="form-field"
          data-testid="project-edit-description-field"
        >
          <span
            className="field-label"
            data-testid="project-edit-description-label"
          >
            Description
          </span>
          <textarea
            className="lilith-input"
            value={editForm.description}
            onChange={(event) =>
              setEditForm((prev) => ({ ...prev, description: event.target.value }))
            }
            data-testid="project-edit-description-input"
          />
        </label>
        <div className="story-bible-briefing" data-testid="story-bible-briefing">
          <div className="section-title" data-testid="story-bible-briefing-title">
            Story bible briefing
          </div>
          <div className="form-grid" data-testid="story-bible-briefing-grid">
            <label className="form-field" data-testid="story-bible-tone-field">
              <span className="field-label" data-testid="story-bible-tone-label">
                Tone
              </span>
              <input
                className="lilith-input"
                value={storyBrief.tone}
                onChange={(event) =>
                  setStoryBrief((prev) => ({ ...prev, tone: event.target.value }))
                }
                placeholder="Cinematic, cozy, grimdark..."
                data-testid="story-bible-tone-input"
              />
            </label>
            <label className="form-field" data-testid="story-bible-length-field">
              <span className="field-label" data-testid="story-bible-length-label">
                Target length
              </span>
              <input
                className="lilith-input"
                value={storyBrief.length}
                onChange={(event) =>
                  setStoryBrief((prev) => ({ ...prev, length: event.target.value }))
                }
                placeholder="1-2 pages, 800 words..."
                data-testid="story-bible-length-input"
              />
            </label>
            <label className="form-field" data-testid="story-bible-tags-field">
              <span className="field-label" data-testid="story-bible-tags-label">
                Focus tags
              </span>
              <input
                className="lilith-input"
                value={storyBrief.tags}
                onChange={(event) =>
                  setStoryBrief((prev) => ({ ...prev, tags: event.target.value }))
                }
                placeholder="factions, politics, romance..."
                data-testid="story-bible-tags-input"
              />
            </label>
          </div>
          <div className="helper" data-testid="story-bible-briefing-helper">
            These notes guide the story bible generator.
          </div>
        </div>
        <label
          className="form-field"
          data-testid="project-edit-story-bible-field"
        >
          <span
            className="field-label"
            data-testid="project-edit-story-bible-label"
          >
            Story bible
          </span>
          <textarea
            className="lilith-input"
            value={editForm.story_bible}
            onChange={(event) =>
              setEditForm((prev) => ({ ...prev, story_bible: event.target.value }))
            }
            placeholder="World rules, themes, key facts"
            data-testid="project-edit-story-bible-input"
          />
        </label>
        <div className="page-actions" data-testid="project-editor-actions">
          <button
            className="lilith-button"
            onClick={saveProject}
            disabled={isGenerating}
            data-testid="project-save-button"
          >
            Save changes
          </button>
          <button
            className="lilith-button secondary"
            onClick={generateStoryBible}
            disabled={isGenerating}
            data-testid="project-generate-story-bible"
          >
            {isGenerating ? "Generating..." : "Generate story bible"}
          </button>
          <div className="helper" data-testid="project-model-hint">
            Model: {modelStatus === "ready" ? selectedModel || "Select a model" : modelStatus === "empty" ? "No models found" : "LM Studio offline"}
          </div>
        </div>
      </div>
    </div>
  );
};

const Services = () => {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState("");
  const [settings, setSettings] = useState({
    auto_start_services: false,
    auto_refresh_services: false,
  });
  const [lastUpdated, setLastUpdated] = useState("");

  const loadServices = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/services`);
      setServices(response.data);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (error) {
      console.error(error);
      setNotice("Unable to load services.");
    } finally {
      setLoading(false);
    }
  };

  const loadSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setSettings(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    loadServices();
    loadSettings();
  }, []);

  useEffect(() => {
    if (!settings.auto_refresh_services) return;
    const interval = setInterval(() => {
      loadServices();
    }, 20000);
    return () => clearInterval(interval);
  }, [settings.auto_refresh_services]);

  const updateSettings = async (updates) => {
    try {
      const response = await axios.put(`${API}/settings`, updates);
      setSettings(response.data);
    } catch (error) {
      console.error(error);
      setNotice("Unable to update settings.");
    }
  };

  const startAllServices = async () => {
    setNotice("");
    try {
      const response = await axios.post(`${API}/services/start-all`);
      const results = response.data.results || [];
      const started = results.filter((item) => item.status === "started").length;
      const errored = results.filter((item) => item.status === "error").length;
      setNotice(
        `Started ${started || 0} services${errored ? ", with some errors." : "."}`
      );
      await loadServices();
    } catch (error) {
      console.error(error);
      setNotice("Unable to start all services.");
    }
  };

  const stopAllServices = async () => {
    setNotice("");
    try {
      const response = await axios.post(`${API}/services/stop-all`);
      const results = response.data.results || [];
      const stopped = results.filter((item) => item.status === "stopped").length;
      const errored = results.filter((item) => item.status === "error").length;
      setNotice(
        `Stopped ${stopped || 0} services${errored ? ", with some errors." : "."}`
      );
      await loadServices();
    } catch (error) {
      console.error(error);
      setNotice("Unable to stop all services.");
    }
  };

  const updateField = (serviceId, field, value) => {
    setServices((prev) =>
      prev.map((service) =>
        service.id === serviceId ? { ...service, [field]: value } : service
      )
    );
  };

  const saveService = async (service) => {
    setNotice("");
    try {
      const response = await axios.put(`${API}/services/${service.id}`, {
        name: service.name,
        base_url: service.base_url,
        health_url: service.health_url,
        start_command: service.start_command,
        stop_command: service.stop_command,
      });
      setServices((prev) =>
        prev.map((item) => (item.id === service.id ? response.data : item))
      );
      setNotice(`${service.name} settings saved.`);
    } catch (error) {
      console.error(error);
      setNotice("Unable to save service settings.");
    }
  };

  const startService = async (service) => {
    setNotice("");
    try {
      const response = await axios.post(`${API}/services/${service.id}/start`);
      if (response.data.status === "error") {
        setNotice(response.data.detail || `Unable to start ${service.name}.`);
      } else {
        setNotice(`${service.name} started.`);
      }
      await loadServices();
    } catch (error) {
      console.error(error);
      setNotice(`Unable to start ${service.name}.`);
    }
  };

  const stopService = async (service) => {
    setNotice("");
    try {
      const response = await axios.post(`${API}/services/${service.id}/stop`);
      if (response.data.status === "error") {
        setNotice(response.data.detail || `Unable to stop ${service.name}.`);
      } else {
        setNotice(`${service.name} stopped.`);
      }
      await loadServices();
    } catch (error) {
      console.error(error);
      setNotice(`Unable to stop ${service.name}.`);
    }
  };

  const openService = (service) => {
    if (!service.base_url) {
      setNotice("Set a base URL before opening the service.");
      return;
    }
    window.open(service.base_url, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="page" data-testid="services-page">
      <div className="page-header" data-testid="services-header">
        <div>
          <div className="eyebrow" data-testid="services-eyebrow">
            Services Console
          </div>
          <h1 className="page-title" data-testid="services-title">
            Start, stop, and route Lillith's local AI tools.
          </h1>
        </div>
        <div className="page-actions" data-testid="services-actions">
          <button
            className="lilith-button"
            onClick={startAllServices}
            data-testid="services-start-all"
          >
            <Play className="button-icon" data-testid="services-start-all-icon" />
            Start all
          </button>
          <button
            className="lilith-button secondary"
            onClick={stopAllServices}
            data-testid="services-stop-all"
          >
            <Square className="button-icon" data-testid="services-stop-all-icon" />
            Stop all
          </button>
          <button
            className="lilith-button secondary"
            onClick={loadServices}
            data-testid="services-refresh-button"
          >
            {loading ? "Refreshing..." : "Refresh status"}
          </button>
        </div>
      </div>

      {notice && (
        <div className="notice" data-testid="services-notice">
          {notice}
        </div>
      )}

      <div className="glass-panel" data-testid="services-preferences">
        <div className="panel-header" data-testid="services-preferences-header">
          <div className="panel-title" data-testid="services-preferences-title">
            Service preferences
          </div>
          <span className="panel-badge" data-testid="services-preferences-badge">
            Local automation
          </span>
        </div>
        <div className="service-preferences" data-testid="services-preferences-body">
          <div className="toggle-row" data-testid="services-auto-start-row">
            <div>
              <div className="field-label" data-testid="services-auto-start-label">
                Auto-start services on launch
              </div>
              <div className="helper" data-testid="services-auto-start-helper">
                Takes effect next time Lillith Offline opens.
              </div>
            </div>
            <button
              className={`toggle-button ${
                settings.auto_start_services ? "active" : ""
              }`}
              onClick={() =>
                updateSettings({
                  auto_start_services: !settings.auto_start_services,
                })
              }
              data-testid="services-auto-start-toggle"
            >
              {settings.auto_start_services ? "Enabled" : "Disabled"}
            </button>
          </div>
          <div className="toggle-row" data-testid="services-auto-refresh-row">
            <div>
              <div
                className="field-label"
                data-testid="services-auto-refresh-label"
              >
                Auto-refresh status (every 20s)
              </div>
              <div className="helper" data-testid="services-auto-refresh-helper">
                Last update: {lastUpdated || "Just now"}
              </div>
            </div>
            <button
              className={`toggle-button ${
                settings.auto_refresh_services ? "active" : ""
              }`}
              onClick={() =>
                updateSettings({
                  auto_refresh_services: !settings.auto_refresh_services,
                })
              }
              data-testid="services-auto-refresh-toggle"
            >
              {settings.auto_refresh_services ? "Enabled" : "Disabled"}
            </button>
          </div>
        </div>
      </div>

      <div className="grid two-column" data-testid="services-grid">
        {services.map((service) => (
          <div
            key={service.id}
            className="glass-panel service-card"
            data-testid={`service-card-${service.id}`}
          >
            <div className="panel-header" data-testid={`service-header-${service.id}`}>
              <div className="panel-title" data-testid={`service-name-${service.id}`}>
                {service.name}
              </div>
              <span
                className={`service-status ${service.status}`}
                data-testid={`service-status-${service.id}`}
              >
                {service.status || "unknown"}
              </span>
            </div>
            <div className="service-actions" data-testid={`service-actions-${service.id}`}>
              <button
                className="lilith-button"
                onClick={() => startService(service)}
                data-testid={`service-start-${service.id}`}
              >
                <Play className="button-icon" data-testid={`service-start-icon-${service.id}`} />
                Start
              </button>
              <button
                className="lilith-button secondary"
                onClick={() => stopService(service)}
                data-testid={`service-stop-${service.id}`}
              >
                <Square className="button-icon" data-testid={`service-stop-icon-${service.id}`} />
                Stop
              </button>
              <button
                className="lilith-button secondary"
                onClick={() => openService(service)}
                data-testid={`service-open-${service.id}`}
              >
                <ExternalLink
                  className="button-icon"
                  data-testid={`service-open-icon-${service.id}`}
                />
                Open UI
              </button>
            </div>

            <div className="form-grid" data-testid={`service-config-${service.id}`}>
              <label className="form-field" data-testid={`service-base-url-${service.id}`}>
                <span className="field-label" data-testid={`service-base-url-label-${service.id}`}>
                  Base URL
                </span>
                <input
                  className="lilith-input"
                  value={service.base_url || ""}
                  onChange={(event) =>
                    updateField(service.id, "base_url", event.target.value)
                  }
                  placeholder="http://localhost:1234"
                  data-testid={`service-base-url-input-${service.id}`}
                />
              </label>
              <label className="form-field" data-testid={`service-health-url-${service.id}`}>
                <span className="field-label" data-testid={`service-health-url-label-${service.id}`}>
                  Health URL
                </span>
                <input
                  className="lilith-input"
                  value={service.health_url || ""}
                  onChange={(event) =>
                    updateField(service.id, "health_url", event.target.value)
                  }
                  placeholder="/health or /models"
                  data-testid={`service-health-url-input-${service.id}`}
                />
              </label>
              <label className="form-field" data-testid={`service-start-cmd-${service.id}`}>
                <span className="field-label" data-testid={`service-start-cmd-label-${service.id}`}>
                  Start command
                </span>
                <input
                  className="lilith-input"
                  value={service.start_command || ""}
                  onChange={(event) =>
                    updateField(service.id, "start_command", event.target.value)
                  }
                  placeholder="Full path to .bat or .exe"
                  data-testid={`service-start-cmd-input-${service.id}`}
                />
              </label>
              <label className="form-field" data-testid={`service-stop-cmd-${service.id}`}>
                <span className="field-label" data-testid={`service-stop-cmd-label-${service.id}`}>
                  Stop command
                </span>
                <input
                  className="lilith-input"
                  value={service.stop_command || ""}
                  onChange={(event) =>
                    updateField(service.id, "stop_command", event.target.value)
                  }
                  placeholder="Optional stop command"
                  data-testid={`service-stop-cmd-input-${service.id}`}
                />
              </label>
            </div>
            <button
              className="lilith-button secondary"
              onClick={() => saveService(service)}
              data-testid={`service-save-${service.id}`}
            >
              Save settings
            </button>
          </div>
        ))}
      </div>

      <div className="glass-panel" data-testid="services-troubleshoot">
        <div className="panel-header" data-testid="services-troubleshoot-header">
          <div className="panel-title" data-testid="services-troubleshoot-title">
            Troubleshooting quick fixes
          </div>
          <span className="panel-badge" data-testid="services-troubleshoot-badge">
            Local install tips
          </span>
        </div>
        <ul className="note-list" data-testid="services-troubleshoot-list">
          <li data-testid="services-troubleshoot-httpx">
            If Stable Diffusion WebUI fails with a <code>socket_options</code> error, update the
            WebUI venv packages: <code>pip install -U httpx httpcore</code> inside the SD
            <code>venv</code>, then relaunch.
          </li>
          <li data-testid="services-troubleshoot-lm">
            For remote LM Studio, make sure the base URL points to the machine running
            the server (example: http://100.77.24.8:1234).
          </li>
          <li data-testid="services-troubleshoot-comfy">
            ComfyUI health checks default to <code>/system_stats</code>; adjust if you use
            a custom port.
          </li>
        </ul>
      </div>
    </div>
  );
};

const PluginBay = () => {
  const [plugins, setPlugins] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchPlugins = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/plugins`);
      setPlugins(response.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlugins();
  }, []);

  return (
    <div className="page" data-testid="plugins-page">
      <div className="page-header" data-testid="plugins-header">
        <div>
          <div className="eyebrow" data-testid="plugins-eyebrow">
            Plugin Bay
          </div>
          <h1 className="page-title" data-testid="plugins-title">
            Drop mini-apps into the plugins folder to expand Lillith.
          </h1>
        </div>
        <button
          className="lilith-button"
          onClick={fetchPlugins}
          data-testid="plugins-refresh-button"
        >
          Refresh list
        </button>
      </div>

      <div className="glass-panel" data-testid="plugins-panel">
        <div className="panel-header" data-testid="plugins-panel-header">
          <div className="panel-title" data-testid="plugins-panel-title">
            Installed plugins
          </div>
          <span className="panel-badge" data-testid="plugins-panel-badge">
            {loading ? "Scanning" : `${plugins.length} detected`}
          </span>
        </div>
        {plugins.length === 0 && !loading ? (
          <div className="empty-state" data-testid="plugins-empty">
            No plugins yet. Add folders to /plugins.
          </div>
        ) : (
          <div className="grid" data-testid="plugins-grid">
            {plugins.map((plugin) => (
              <div
                key={plugin.name}
                className="plugin-card"
                data-testid={`plugin-card-${plugin.name}`}
              >
                <div
                  className="plugin-title"
                  data-testid={`plugin-title-${plugin.name}`}
                >
                  {plugin.name}
                </div>
                <div
                  className="plugin-path"
                  data-testid={`plugin-path-${plugin.name}`}
                >
                  {plugin.path}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="glass-panel" data-testid="plugins-guidance">
        <div className="panel-header" data-testid="plugins-guidance-header">
          <div className="panel-title" data-testid="plugins-guidance-title">
            Plugin onboarding
          </div>
          <span className="panel-badge" data-testid="plugins-guidance-badge">
            Ready for mini-apps
          </span>
        </div>
        <div className="plugin-guidance" data-testid="plugins-guidance-text">
          Each plugin folder should include a manifest.json with the mini-app name,
          entry UI, and capabilities. Lillith will surface it automatically in the
          Mini-apps bay.
        </div>
      </div>
    </div>
  );
};

function App() {
  const [activeProject, setActiveProject] = useState(null);
  const [onlineMode, setOnlineMode] = useState(false);
  const [availableModels, setAvailableModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [modelStatus, setModelStatus] = useState("loading");

  useEffect(() => {
    const stored = localStorage.getItem("lillithActiveProject");
    if (stored) {
      try {
        setActiveProject(JSON.parse(stored));
      } catch (error) {
        console.error(error);
      }
    }
  }, []);

  const fetchModels = async () => {
    setModelStatus("loading");
    try {
      const response = await axios.get(`${API}/ai/models`, { timeout: 5000 });
      const models = response.data.models || [];
      setAvailableModels(models);
      setSelectedModel((prev) => prev || models[0]?.id || "");
      setModelStatus(models.length ? "ready" : "empty");
    } catch (error) {
      console.error(error);
      setAvailableModels([]);
      setSelectedModel("");
      setModelStatus("offline");
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  useEffect(() => {
    if (activeProject) {
      localStorage.setItem("lillithActiveProject", JSON.stringify(activeProject));
    } else {
      localStorage.removeItem("lillithActiveProject");
    }
  }, [activeProject]);

  const attachCharacter = async (character) => {
    if (!activeProject?.id) return;
    try {
      const response = await axios.put(
        `${API}/projects/${activeProject.id}`,
        {
          character_profile: character,
        }
      );
      setActiveProject(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div className="App" data-testid="app-root">
      <BrowserRouter>
        <div className="app-shell" data-testid="app-shell">
          <SideNav />
          <div className="app-main" data-testid="app-main">
            <TopBar
              activeProject={activeProject}
              onlineMode={onlineMode}
              setOnlineMode={setOnlineMode}
              availableModels={availableModels}
              selectedModel={selectedModel}
              setSelectedModel={setSelectedModel}
              modelStatus={modelStatus}
              onRefreshModels={fetchModels}
            />
            <MenuBar />
            <div className="app-content" data-testid="app-content">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route
                  path="/character-builder"
                  element={
                    <CharacterBuilder
                      activeProject={activeProject}
                      onAttachCharacter={attachCharacter}
                      selectedModel={selectedModel}
                      modelStatus={modelStatus}
                    />
                  }
                />
                <Route
                  path="/projects"
                  element={
                    <Projects
                      activeProject={activeProject}
                      setActiveProject={setActiveProject}
                      selectedModel={selectedModel}
                      modelStatus={modelStatus}
                    />
                  }
                />
                <Route path="/plugins" element={<PluginBay />} />
                <Route path="/services" element={<Services />} />
              </Routes>
            </div>
          </div>
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;
