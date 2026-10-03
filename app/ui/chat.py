from fastapi.responses import HTMLResponse

CHAT_HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>ChatSQL Pro | Text-to-SQL Clarification Engine</title>
  <style>
    :root {
      --bg-primary: #0b0f19;
      --bg-secondary: #131b2e;
      --bg-tertiary: #1e293b;
      --bg-elevated: #24324a;
      --accent: #38bdf8;
      --accent-hover: #0284c7;
      --accent-glow: rgba(56, 189, 248, 0.25);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      --border-color: #2a374f;
      --success: #10b981;
      --success-glow: rgba(16, 185, 129, 0.2);
      --warning: #f59e0b;
      --danger: #ef4444;
      --code-bg: #070a12;
      --sidebar-width: 280px;
      --header-height: 56px;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg-primary);
      color: var(--text-main);
      height: 100vh;
      height: 100dvh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }

    /* -------------------------------------------------------------
       GLOBAL HEADER (RESPONSIVE)
       ------------------------------------------------------------- */
    .app-header {
      height: var(--header-height);
      background-color: rgba(19, 27, 46, 0.95);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 1rem;
      z-index: 50;
      flex-shrink: 0;
      gap: 0.5rem;
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 0.85rem;
      min-width: 0;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: 700;
      font-size: 1.05rem;
      color: var(--text-main);
      text-decoration: none;
      flex-shrink: 0;
    }

    .brand-icon {
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1rem;
      box-shadow: 0 0 12px var(--accent-glow);
      flex-shrink: 0;
    }

    .brand-text {
      white-space: nowrap;
    }

    .nav-mode-tabs {
      display: flex;
      background: var(--bg-primary);
      padding: 3px;
      border-radius: 8px;
      border: 1px solid var(--border-color);
      gap: 3px;
    }

    .nav-mode-btn {
      background: none;
      border: none;
      color: var(--text-muted);
      padding: 0.4rem 0.75rem;
      font-size: 0.82rem;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.35rem;
      transition: all 0.2s;
      white-space: nowrap;
    }

    .nav-mode-btn:hover { color: var(--text-main); }
    .nav-mode-btn.active {
      background: var(--bg-elevated);
      color: var(--accent);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
    }

    .nav-text-short { display: none; }
    .nav-text-full { display: inline; }

    .header-right {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-shrink: 0;
    }

    .header-badges {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.75rem;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      border: 1px solid transparent;
      white-space: nowrap;
    }

    .badge-db {
      background: rgba(16, 185, 129, 0.12);
      color: var(--success);
      border-color: rgba(16, 185, 129, 0.3);
    }

    .badge-ai {
      background: rgba(56, 189, 248, 0.12);
      color: var(--accent);
      border-color: rgba(56, 189, 248, 0.3);
    }

    .badge-text-short { display: none; }
    .badge-text-full { display: inline; }

    /* Layout Containers */
    .view-container {
      display: flex;
      flex: 1;
      height: calc(100vh - var(--header-height));
      height: calc(100dvh - var(--header-height));
      overflow: hidden;
      position: relative;
    }

    /* -------------------------------------------------------------
       VIEW 1: CHAT TUTOR VIEW
       ------------------------------------------------------------- */
    #chat-view {
      display: flex;
      width: 100%;
      height: 100%;
      overflow: hidden;
      position: relative;
    }

    /* Sidebar Drawer */
    .sidebar-backdrop {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(11, 15, 25, 0.75);
      backdrop-filter: blur(4px);
      z-index: 1040;
      opacity: 0;
      transition: opacity 0.25s ease;
    }

    .sidebar-backdrop.active {
      display: block;
      opacity: 1;
    }

    .sidebar {
      width: var(--sidebar-width);
      background-color: var(--bg-secondary);
      border-right: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
      transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), margin-right 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      z-index: 1050;
    }

    .sidebar.collapsed {
      transform: translateX(-100%);
      margin-right: calc(-1 * var(--sidebar-width));
    }

    .sidebar-header {
      padding: 0.85rem 1rem;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .btn-new-chat {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      background: linear-gradient(135deg, #0284c7, #0369a1);
      color: #ffffff;
      border: 1px solid rgba(56, 189, 248, 0.4);
      padding: 0.55rem 0.9rem;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.84rem;
      cursor: pointer;
      transition: all 0.2s;
      min-height: 38px;
    }

    .btn-new-chat:hover {
      background: linear-gradient(135deg, #0369a1, #075985);
      transform: translateY(-1px);
    }

    .btn-sidebar-close {
      display: none;
      background: var(--bg-tertiary);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      width: 34px;
      height: 34px;
      border-radius: 6px;
      cursor: pointer;
      align-items: center;
      justify-content: center;
      font-size: 1rem;
      flex-shrink: 0;
    }

    .sidebar-title {
      font-size: 0.74rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-dim);
      padding: 0.75rem 1rem 0.25rem;
      font-weight: 700;
    }

    .history-list {
      flex: 1;
      overflow-y: auto;
      padding: 0.35rem 0.65rem;
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      -webkit-overflow-scrolling: touch;
    }

    .history-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.55rem 0.75rem;
      border-radius: 6px;
      cursor: pointer;
      color: var(--text-muted);
      font-size: 0.84rem;
      border: 1px solid transparent;
      user-select: none;
      min-height: 38px;
    }

    .history-item:hover {
      background-color: var(--bg-tertiary);
      color: var(--text-main);
    }

    .history-item.active {
      background-color: var(--bg-elevated);
      color: var(--accent);
      font-weight: 600;
      border-color: rgba(56, 189, 248, 0.3);
    }

    .history-item-title {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      flex: 1;
      margin-right: 0.5rem;
    }

    .btn-delete-chat {
      background: none;
      border: none;
      color: var(--text-dim);
      cursor: pointer;
      padding: 4px;
      border-radius: 4px;
      font-size: 0.85rem;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .history-item:hover .btn-delete-chat { opacity: 0.8; }
    .btn-delete-chat:hover { color: var(--danger); opacity: 1; }

    .sidebar-footer {
      padding: 0.75rem 1rem;
      border-top: 1px solid var(--border-color);
      background-color: rgba(11, 15, 25, 0.5);
    }

    /* Main Chat Layout */
    .chat-main {
      flex: 1;
      display: flex;
      flex-direction: column;
      height: 100%;
      overflow: hidden;
      min-width: 0;
    }

    .chat-topbar {
      height: 46px;
      background-color: rgba(19, 27, 46, 0.7);
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      padding: 0 1rem;
      gap: 0.75rem;
      flex-shrink: 0;
    }

    .btn-sidebar-toggle {
      background: var(--bg-tertiary);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      width: 32px;
      height: 32px;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1rem;
      flex-shrink: 0;
      transition: all 0.15s;
    }

    .btn-sidebar-toggle:hover {
      color: var(--text-main);
      border-color: var(--accent);
    }

    .chat-topbar-title {
      font-weight: 600;
      font-size: 0.92rem;
      color: var(--text-main);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    #chat-viewport {
      flex: 1;
      overflow-y: auto;
      padding: 1.25rem 1rem;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
      scroll-behavior: smooth;
      -webkit-overflow-scrolling: touch;
    }

    /* Welcome Hero */
    .welcome-hero {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      margin: auto 0;
      padding: 1.5rem 0.5rem;
      max-width: 760px;
      margin-left: auto;
      margin-right: auto;
      width: 100%;
    }

    .hero-badge {
      background: rgba(56, 189, 248, 0.12);
      color: var(--accent);
      border: 1px solid rgba(56, 189, 248, 0.3);
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.78rem;
      font-weight: 600;
      margin-bottom: 1rem;
      text-align: center;
    }

    .hero-title {
      font-size: clamp(1.4rem, 4.5vw, 2.1rem);
      font-weight: 800;
      letter-spacing: -0.03em;
      margin-bottom: 0.65rem;
      background: linear-gradient(135deg, #ffffff 40%, #94a3b8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      line-height: 1.25;
    }

    .hero-subtitle {
      font-size: clamp(0.85rem, 2.5vw, 0.95rem);
      color: var(--text-muted);
      line-height: 1.55;
      margin-bottom: 1.5rem;
      max-width: 600px;
    }

    .suggestion-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 0.75rem;
      width: 100%;
    }

    .suggestion-card {
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 0.85rem 1rem;
      text-align: left;
      cursor: pointer;
      transition: all 0.2s;
    }

    .suggestion-card:hover {
      background: var(--bg-tertiary);
      border-color: var(--accent);
      transform: translateY(-2px);
    }

    .suggestion-title {
      font-size: 0.86rem;
      font-weight: 600;
      color: var(--text-main);
      margin-bottom: 0.25rem;
    }

    .suggestion-desc {
      font-size: 0.76rem;
      color: var(--text-muted);
      line-height: 1.4;
    }

    /* Message Bubbles */
    .message {
      display: flex;
      gap: 0.75rem;
      max-width: 860px;
      width: 100%;
      margin: 0 auto;
    }

    .message.user { flex-direction: row-reverse; }

    .avatar-icon {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.9rem;
      flex-shrink: 0;
    }

    .avatar-user {
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      color: #fff;
    }

    .avatar-assistant {
      background: linear-gradient(135deg, #334155, #1e293b);
      border: 1px solid var(--border-color);
      color: var(--accent);
    }

    .bubble {
      padding: 0.85rem 1.1rem;
      border-radius: 12px;
      max-width: calc(100% - 46px);
      line-height: 1.6;
      font-size: 0.9rem;
      word-break: break-word;
      overflow-wrap: break-word;
    }

    .message.user .bubble {
      background: linear-gradient(135deg, #0284c7, #0369a1);
      color: #ffffff;
      border-bottom-right-radius: 2px;
    }

    .message.assistant .bubble {
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-bottom-left-radius: 2px;
      width: 100%;
    }

    /* Layman Terms & Efficiency Cards */
    .layman-card {
      background: rgba(56, 189, 248, 0.05);
      border-left: 3px solid var(--accent);
      padding: 0.75rem 0.9rem;
      border-radius: 4px;
      margin-bottom: 0.75rem;
      font-size: 0.88rem;
      line-height: 1.5;
    }

    .layman-header {
      font-weight: 700;
      color: var(--accent);
      margin-bottom: 0.3rem;
      display: flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.82rem;
    }

    .efficiency-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.65rem;
      margin: 0.75rem 0;
    }

    .efficiency-card {
      padding: 0.7rem 0.85rem;
      border-radius: 8px;
      font-size: 0.82rem;
      line-height: 1.4;
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
    }

    .card-time {
      background: rgba(16, 185, 129, 0.08);
      border: 1px solid rgba(16, 185, 129, 0.25);
    }
    .card-time .eff-title { color: var(--success); font-weight: 700; }

    .card-memory {
      background: rgba(168, 85, 247, 0.08);
      border: 1px solid rgba(168, 85, 247, 0.25);
    }
    .card-memory .eff-title { color: #c084fc; font-weight: 700; }

    /* SQL Block */
    .sql-box {
      margin: 0.75rem 0;
      background: var(--code-bg);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      overflow: hidden;
      width: 100%;
    }

    .sql-box-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.35rem 0.75rem;
      background: var(--bg-tertiary);
      border-bottom: 1px solid var(--border-color);
      font-size: 0.74rem;
      color: var(--text-muted);
      font-weight: 600;
      gap: 0.5rem;
    }

    .btn-copy-sql {
      background: none;
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      border-radius: 4px;
      padding: 3px 8px;
      font-size: 0.72rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      min-height: 26px;
    }

    .btn-copy-sql:hover { color: var(--text-main); border-color: var(--accent); }

    .sql-code-text {
      padding: 0.75rem 0.85rem;
      font-family: 'JetBrains Mono', Consolas, monospace;
      font-size: 0.84rem;
      color: #7dd3fc;
      overflow-x: auto;
      white-space: pre;
      -webkit-overflow-scrolling: touch;
      line-height: 1.5;
    }

    /* Table Results */
    .table-container {
      margin-top: 0.75rem;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      overflow-x: auto;
      overflow-y: auto;
      max-height: 250px;
      -webkit-overflow-scrolling: touch;
      width: 100%;
    }

    table { width: 100%; border-collapse: collapse; font-size: 0.8rem; text-align: left; }
    th {
      background-color: var(--bg-tertiary);
      color: var(--text-muted);
      font-weight: 600;
      padding: 0.5rem 0.75rem;
      position: sticky;
      top: 0;
      border-bottom: 1px solid var(--border-color);
      white-space: nowrap;
    }
    td {
      padding: 0.45rem 0.75rem;
      border-bottom: 1px solid var(--border-color);
      color: var(--text-main);
      white-space: nowrap;
    }
    tr:nth-child(even) { background-color: rgba(255, 255, 255, 0.02); }
    tr:hover { background-color: rgba(56, 189, 248, 0.05); }

    /* Clarification Options */
    .clarification-card {
      background: rgba(245, 158, 11, 0.08);
      border: 1px solid rgba(245, 158, 11, 0.3);
      border-radius: 8px;
      padding: 0.85rem;
      margin-top: 0.35rem;
    }

    .clarification-title { font-weight: 700; color: var(--warning); font-size: 0.88rem; margin-bottom: 0.35rem; }
    .options-grid { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.6rem; }
    .option-btn {
      background: var(--bg-tertiary);
      border: 1px solid rgba(245, 158, 11, 0.4);
      color: var(--text-main);
      padding: 0.45rem 0.85rem;
      border-radius: 6px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      min-height: 36px;
      display: inline-flex;
      align-items: center;
      transition: all 0.15s;
    }
    .option-btn:hover { background: rgba(245, 158, 11, 0.25); border-color: var(--warning); }

    .meta-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 0.65rem;
      padding-top: 0.45rem;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      font-size: 0.74rem;
      color: var(--text-dim);
      gap: 0.5rem;
      flex-wrap: wrap;
    }

    /* Input Bar */
    .chat-input-bar {
      padding: 0.75rem 1rem calc(0.75rem + env(safe-area-inset-bottom, 0px));
      background: linear-gradient(180deg, transparent, var(--bg-primary) 35%);
      flex-shrink: 0;
    }

    .chat-form {
      max-width: 860px;
      margin: 0 auto;
      display: flex;
      gap: 0.5rem;
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 0.35rem 0.45rem 0.35rem 0.85rem;
      align-items: flex-end;
    }

    .chat-form:focus-within { border-color: var(--accent); box-shadow: 0 0 12px var(--accent-glow); }

    #prompt-input {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: var(--text-main);
      font-size: 16px; /* Prevents auto-zoom on iOS */
      resize: none;
      max-height: 120px;
      line-height: 1.45;
      padding: 0.45rem 0;
      font-family: inherit;
    }

    .btn-send {
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      color: #ffffff;
      border: none;
      border-radius: 8px;
      padding: 0 1rem;
      font-weight: 600;
      font-size: 0.86rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.35rem;
      height: 38px;
      flex-shrink: 0;
      transition: all 0.2s;
    }

    .btn-send:hover {
      background: linear-gradient(135deg, #0369a1, #0284c7);
    }

    /* -------------------------------------------------------------
       VIEW 2: LEETCODE TOP 50 SQL BATTLEGROUND ARENA
       ------------------------------------------------------------- */
    #battleground-view {
      display: none;
      width: 100%;
      height: 100%;
      overflow: hidden;
      flex-direction: column;
    }

    .battleground-topbar {
      min-height: 48px;
      background-color: var(--bg-secondary);
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.35rem 1rem;
      flex-shrink: 0;
      gap: 0.5rem;
      flex-wrap: wrap;
    }

    .battleground-controls {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
    }

    .problem-select-btn {
      display: flex;
      align-items: center;
      gap: 0.45rem;
      background: var(--bg-tertiary);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 0.35rem 0.75rem;
      border-radius: 6px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      min-height: 34px;
      white-space: nowrap;
      transition: all 0.15s;
    }

    .problem-select-btn:hover { border-color: var(--accent); }

    .progress-pill {
      font-size: 0.78rem;
      color: var(--accent);
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.3);
      padding: 0.25rem 0.6rem;
      border-radius: 9999px;
      font-weight: 600;
      white-space: nowrap;
    }

    /* Arena Mobile Segmented Switcher */
    .arena-mobile-tabs {
      display: none;
      background: var(--bg-primary);
      border-bottom: 1px solid var(--border-color);
      padding: 4px 0.75rem;
      gap: 4px;
      flex-shrink: 0;
    }

    .arena-mobile-tab {
      flex: 1;
      background: none;
      border: 1px solid transparent;
      color: var(--text-muted);
      padding: 0.45rem 0.5rem;
      font-size: 0.82rem;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.35rem;
      transition: all 0.15s;
      min-height: 34px;
    }

    .arena-mobile-tab.active {
      background: var(--bg-elevated);
      color: var(--accent);
      border-color: rgba(56, 189, 248, 0.3);
      box-shadow: 0 1px 4px rgba(0,0,0,0.3);
    }

    .arena-grid {
      display: grid;
      grid-template-columns: 45% 55%;
      flex: 1;
      height: calc(100% - 48px);
      overflow: hidden;
    }

    /* Problem Description Pane */
    .problem-pane {
      background-color: var(--bg-primary);
      border-right: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      height: 100%;
      overflow-y: auto;
      padding: 1.25rem;
      -webkit-overflow-scrolling: touch;
    }

    .problem-header {
      margin-bottom: 1.1rem;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .problem-meta {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
    }

    .diff-badge {
      font-size: 0.74rem;
      padding: 0.2rem 0.55rem;
      border-radius: 9999px;
      font-weight: 700;
    }

    .diff-Easy { background: rgba(16, 185, 129, 0.15); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.4); }
    .diff-Medium { background: rgba(245, 158, 11, 0.15); color: var(--warning); border: 1px solid rgba(245, 158, 11, 0.4); }
    .diff-Hard { background: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.4); }

    .category-badge {
      font-size: 0.74rem;
      color: var(--text-muted);
      background: var(--bg-tertiary);
      padding: 0.2rem 0.55rem;
      border-radius: 6px;
    }

    .problem-title {
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--text-main);
      line-height: 1.35;
    }

    .problem-section {
      margin-bottom: 1.2rem;
      line-height: 1.6;
      font-size: 0.9rem;
    }

    .section-title {
      font-size: 0.8rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--accent);
      margin-bottom: 0.45rem;
      display: flex;
      align-items: center;
      gap: 0.35rem;
    }

    .layman-box {
      background: var(--bg-secondary);
      border-left: 3px solid var(--accent);
      padding: 0.85rem 1rem;
      border-radius: 6px;
      font-size: 0.9rem;
      line-height: 1.55;
    }

    /* Code Studio Pane */
    .studio-pane {
      background-color: var(--bg-secondary);
      display: flex;
      flex-direction: column;
      height: 100%;
      overflow: hidden;
      min-width: 0;
    }

    .studio-header {
      height: 40px;
      background: var(--bg-tertiary);
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 0.85rem;
      font-size: 0.78rem;
      color: var(--text-muted);
      flex-shrink: 0;
      gap: 0.5rem;
    }

    .studio-actions {
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }

    .btn-studio-action {
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      padding: 0.3rem 0.65rem;
      border-radius: 5px;
      font-size: 0.76rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.3rem;
      min-height: 30px;
      white-space: nowrap;
      transition: all 0.15s;
    }

    .btn-studio-action:hover { color: var(--text-main); border-color: var(--accent); }

    .editor-wrapper {
      flex: 1;
      display: flex;
      flex-direction: column;
      background: var(--code-bg);
      position: relative;
      min-height: 130px;
    }

    #sql-editor {
      flex: 1;
      width: 100%;
      height: 100%;
      background: transparent;
      border: none;
      color: #7dd3fc;
      font-family: 'JetBrains Mono', Consolas, monospace;
      font-size: 14px;
      padding: 0.85rem;
      resize: none;
      outline: none;
      line-height: 1.5;
      -webkit-overflow-scrolling: touch;
    }

    .studio-footer {
      padding: 0.55rem 0.85rem;
      background: var(--bg-secondary);
      border-top: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.6rem;
      flex-shrink: 0;
    }

    .btn-run-code {
      background: var(--bg-tertiary);
      color: var(--text-main);
      border: 1px solid var(--border-color);
      padding: 0.5rem 1rem;
      border-radius: 6px;
      font-weight: 600;
      font-size: 0.84rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
      min-height: 38px;
      transition: all 0.15s;
    }

    .btn-run-code:hover { background: var(--bg-elevated); border-color: var(--accent); }

    .btn-submit-code {
      background: linear-gradient(135deg, #059669, #10b981);
      color: #ffffff;
      border: none;
      padding: 0.5rem 1.2rem;
      border-radius: 6px;
      font-weight: 600;
      font-size: 0.84rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
      min-height: 38px;
      box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
      transition: all 0.15s;
    }

    .btn-submit-code:hover { background: linear-gradient(135deg, #047857, #059669); transform: translateY(-1px); }

    /* Output Console Drawer */
    .console-drawer {
      height: 200px;
      max-height: 50%;
      min-height: 140px;
      background: var(--bg-primary);
      border-top: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      flex-shrink: 0;
    }

    .console-tabs {
      height: 34px;
      background: var(--bg-secondary);
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      padding: 0 0.75rem;
      gap: 0.5rem;
      flex-shrink: 0;
    }

    .console-tab {
      background: none;
      border: none;
      color: var(--text-dim);
      font-size: 0.78rem;
      font-weight: 600;
      padding: 0.3rem 0.6rem;
      border-radius: 4px;
      cursor: pointer;
    }

    .console-tab.active { color: var(--accent); background: var(--bg-tertiary); }

    .console-body {
      flex: 1;
      overflow-y: auto;
      padding: 0.75rem;
      font-size: 0.84rem;
      -webkit-overflow-scrolling: touch;
    }

    .status-pill-accepted { color: var(--success); font-weight: 700; display: inline-flex; align-items: center; gap: 0.35rem; }
    .status-pill-wrong { color: var(--danger); font-weight: 700; display: inline-flex; align-items: center; gap: 0.35rem; }
    .status-pill-error { color: var(--warning); font-weight: 700; display: inline-flex; align-items: center; gap: 0.35rem; }

    /* Mini Tables Comparison in Console */
    .console-diff-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.75rem;
      margin-top: 0.75rem;
    }

    /* -------------------------------------------------------------
       MODALS & DIALOGS (RESPONSIVE)
       ------------------------------------------------------------- */
    /* Problems Catalog Modal */
    dialog.problems-modal {
      border: 1px solid var(--border-color);
      border-radius: 14px;
      background: var(--bg-secondary);
      color: var(--text-main);
      padding: 0;
      max-width: 720px;
      width: 94vw;
      height: 82vh;
      max-height: 720px;
      box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.9);
      position: fixed;
      inset: 0;
      margin: auto;
      overflow: hidden;
    }

    dialog.problems-modal:not([open]) {
      display: none !important;
    }

    dialog.problems-modal[open] {
      display: flex;
      flex-direction: column;
      z-index: 1000;
    }

    dialog.problems-modal::backdrop {
      background: rgba(11, 15, 25, 0.82);
      backdrop-filter: blur(6px);
      -webkit-backdrop-filter: blur(6px);
    }

    .problems-modal-header {
      padding: 0.9rem 1.25rem;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: var(--bg-secondary);
      flex-shrink: 0;
    }

    .problems-filter-bar {
      padding: 0.75rem 1.25rem;
      background: var(--bg-primary);
      border-bottom: 1px solid var(--border-color);
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      flex-shrink: 0;
    }

    .filter-input {
      flex: 1 1 160px;
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 0.45rem 0.75rem;
      color: var(--text-main);
      font-size: 0.84rem;
      outline: none;
      min-height: 34px;
    }

    .filter-input:focus, .filter-select:focus {
      border-color: var(--accent);
    }

    .filter-select {
      flex: 0 1 auto;
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 0.45rem 0.75rem;
      color: var(--text-main);
      font-size: 0.84rem;
      outline: none;
      cursor: pointer;
      min-height: 34px;
    }

    .problem-items-container {
      flex: 1;
      overflow-y: auto;
      padding: 0.75rem 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.45rem;
      -webkit-overflow-scrolling: touch;
    }

    .catalog-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.65rem 0.85rem;
      border-radius: 8px;
      background: var(--bg-primary);
      border: 1px solid var(--border-color);
      cursor: pointer;
      transition: all 0.15s ease;
      gap: 0.5rem;
    }

    .catalog-item:hover {
      background: var(--bg-elevated);
      border-color: var(--accent);
      transform: translateX(2px);
    }

    .catalog-item-left {
      display: flex;
      align-items: center;
      gap: 0.65rem;
      min-width: 0;
    }

    .catalog-item-num {
      color: var(--text-dim);
      font-size: 0.8rem;
      font-weight: 700;
      min-width: 28px;
      flex-shrink: 0;
    }

    .catalog-item-title {
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--text-main);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* Auth Dialog */
    dialog.auth-modal {
      border: 1px solid var(--border-color);
      border-radius: 16px;
      background: var(--bg-secondary);
      color: var(--text-main);
      padding: 0;
      max-width: 440px;
      width: 92vw;
      box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.9);
      position: fixed;
      inset: 0;
      margin: auto;
      overflow: hidden;
    }

    dialog.auth-modal:not([open]) {
      display: none !important;
    }

    dialog.auth-modal[open] {
      display: block;
      z-index: 1000;
    }

    dialog.auth-modal::backdrop {
      background: rgba(11, 15, 25, 0.82);
      backdrop-filter: blur(6px);
      -webkit-backdrop-filter: blur(6px);
    }

    .auth-modal-content { padding: 1.5rem; }
    .auth-modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.25rem; }
    .auth-title { font-size: 1.15rem; font-weight: 700; }

    .btn-close-modal {
      background: var(--bg-tertiary);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      cursor: pointer;
      font-size: 0.95rem;
      width: 32px;
      height: 32px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s;
    }
    .btn-close-modal:hover {
      background: var(--bg-elevated);
      color: var(--text-main);
      border-color: var(--accent);
    }

    .auth-tabs { display: flex; background: var(--bg-primary); border-radius: 8px; padding: 3px; margin-bottom: 1.25rem; border: 1px solid var(--border-color); }
    .auth-tab { flex: 1; background: none; border: none; color: var(--text-muted); padding: 0.5rem; font-size: 0.84rem; font-weight: 600; border-radius: 6px; cursor: pointer; min-height: 34px; }
    .auth-tab.active { background: var(--bg-elevated); color: var(--text-main); }
    .social-auth-group { display: flex; flex-direction: column; gap: 0.65rem; margin-bottom: 1.25rem; }
    .btn-social { display: flex; align-items: center; justify-content: center; gap: 0.75rem; padding: 0.65rem 1rem; border-radius: 8px; font-weight: 600; font-size: 0.86rem; cursor: pointer; border: 1px solid var(--border-color); min-height: 40px; }
    .btn-google { background: #ffffff; color: #1f2937; }
    .btn-github { background: #181717; color: #ffffff; border-color: #334155; }
    .auth-divider { display: flex; align-items: center; text-align: center; margin: 1.1rem 0; color: var(--text-dim); font-size: 0.78rem; }
    .auth-divider::before, .auth-divider::after { content: ''; flex: 1; border-bottom: 1px solid var(--border-color); }
    .auth-divider span { padding: 0 0.75rem; }
    .auth-form-fields { display: flex; flex-direction: column; gap: 0.85rem; }
    .auth-input-group label { display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.3rem; color: var(--text-muted); }
    .auth-input-group input { width: 100%; background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: 6px; padding: 0.6rem 0.75rem; color: var(--text-main); font-size: 16px; outline: none; min-height: 40px; }
    .btn-auth-submit { margin-top: 0.5rem; width: 100%; background: linear-gradient(135deg, #0284c7, #38bdf8); color: #ffffff; border: none; border-radius: 8px; padding: 0.7rem; font-weight: 600; font-size: 0.92rem; cursor: pointer; min-height: 42px; }
    .auth-error-banner { background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); color: #fca5a5; padding: 0.6rem 0.85rem; border-radius: 6px; font-size: 0.82rem; margin-top: 0.85rem; display: none; }

    /* Chrome Ask Gemini-Style Side Panel */
    .side-panel-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(11, 15, 25, 0.65);
      backdrop-filter: blur(4px);
      -webkit-backdrop-filter: blur(4px);
      z-index: 1199;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.25s ease;
    }

    .side-panel-backdrop.open {
      opacity: 1;
      pointer-events: auto;
    }

    .ai-side-panel {
      position: fixed;
      top: 0;
      right: 0;
      width: 480px;
      max-width: 100vw;
      height: 100vh;
      height: 100dvh;
      background: var(--bg-secondary);
      border-left: 1px solid var(--border-color);
      box-shadow: -15px 0 45px rgba(0, 0, 0, 0.7);
      z-index: 1200;
      display: flex;
      flex-direction: column;
      transform: translateX(100%);
      transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .ai-side-panel.open {
      transform: translateX(0);
    }

    .side-panel-header {
      padding: 0.85rem 1.15rem;
      background: var(--bg-tertiary);
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }

    .ai-panel-title-group {
      display: flex;
      align-items: center;
      gap: 0.65rem;
    }

    .ai-sparkle-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      background: linear-gradient(135deg, #0284c7, #818cf8);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.1rem;
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.35);
    }

    .ai-panel-title {
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--text-main);
    }

    .ai-panel-subtitle {
      font-size: 0.72rem;
      color: var(--text-dim);
    }

    .side-panel-tabs {
      display: flex;
      background: var(--bg-primary);
      border-bottom: 1px solid var(--border-color);
      padding: 0.35rem 0.75rem 0;
      gap: 0.35rem;
      flex-shrink: 0;
    }

    .side-panel-tab {
      flex: 1;
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--text-dim);
      font-size: 0.82rem;
      font-weight: 600;
      padding: 0.6rem 0.5rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
      transition: all 0.15s;
      min-height: 36px;
    }

    .side-panel-tab:hover {
      color: var(--text-muted);
    }

    .side-panel-tab.active {
      color: var(--accent);
      border-bottom-color: var(--accent);
      background: rgba(56, 189, 248, 0.04);
      border-top-left-radius: 6px;
      border-top-right-radius: 6px;
    }

    .side-panel-body {
      flex: 1;
      overflow-y: auto;
      padding: 1.15rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
      -webkit-overflow-scrolling: touch;
    }

    .ai-card {
      background: var(--bg-primary);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 0.9rem;
    }

    .ai-card-header {
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--accent);
      margin-bottom: 0.45rem;
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }

    .ai-critique-box {
      background: rgba(245, 158, 11, 0.08);
      border: 1px solid rgba(245, 158, 11, 0.3);
      border-radius: 8px;
      padding: 0.85rem 1rem;
      font-size: 0.88rem;
      line-height: 1.5;
      color: #fde68a;
    }

    .ai-critique-title {
      font-weight: 700;
      color: var(--warning);
      font-size: 0.82rem;
      margin-bottom: 0.35rem;
      display: flex;
      align-items: center;
      gap: 0.35rem;
    }

    .btn-apply-solution {
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      color: #ffffff;
      border: none;
      padding: 0.55rem 1.1rem;
      border-radius: 6px;
      font-weight: 600;
      font-size: 0.84rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      transition: all 0.2s;
      min-height: 38px;
    }

    .btn-apply-solution:hover {
      background: linear-gradient(135deg, #0369a1, #0284c7);
      transform: translateY(-1px);
    }

    .btn-ask-ai-error {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      margin-top: 0.6rem;
      background: linear-gradient(135deg, #9333ea, #c084fc);
      color: #ffffff;
      border: none;
      padding: 0.45rem 0.9rem;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(168, 85, 247, 0.3);
      transition: all 0.2s;
      min-height: 36px;
    }

    .btn-ask-ai-error:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(168, 85, 247, 0.45);
    }

    .ai-loading-spinner {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem 1.5rem;
      gap: 1rem;
      color: var(--text-muted);
      font-size: 0.9rem;
      text-align: center;
    }

    .ai-pulse-dot {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      border: 3px solid rgba(56, 189, 248, 0.2);
      border-top-color: var(--accent);
      animation: spin 0.85s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    /* Scrollbars */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-thumb { background: var(--bg-elevated); border-radius: 9999px; }

    /* -------------------------------------------------------------
       RESPONSIVE BREAKPOINTS (TABLETS & MOBILE)
       ------------------------------------------------------------- */
    @media (max-width: 1024px) {
      .badge-text-full { display: none; }
      .badge-text-short { display: inline; }
      .nav-mode-btn { padding: 0.35rem 0.6rem; font-size: 0.8rem; }
    }

    @media (max-width: 900px) {
      /* Arena Responsive Layout with Mobile Tabs */
      .arena-mobile-tabs {
        display: flex;
      }

      .arena-grid {
        display: flex;
        flex-direction: column;
        height: calc(100% - 48px - 44px);
      }

      .problem-pane {
        display: flex;
        width: 100%;
        height: 100%;
        border-right: none;
      }

      .studio-pane {
        display: none;
        width: 100%;
        height: 100%;
      }

      .console-drawer {
        height: 220px;
        max-height: 45%;
      }
    }

    @media (max-width: 768px) {
      /* Header on Tablets / Mobile */
      .app-header {
        padding: 0 0.75rem;
      }

      .header-badges {
        display: none; /* Keep header clean and uncrowded on mobile */
      }

      .nav-text-full { display: none; }
      .nav-text-short { display: inline; }

      /* Off-Canvas Drawer for Sidebar */
      .sidebar {
        position: fixed;
        top: 0;
        left: 0;
        bottom: 0;
        height: 100vh;
        height: 100dvh;
        z-index: 1100;
        transform: translateX(-100%);
        margin-right: 0 !important;
        box-shadow: 10px 0 35px rgba(0, 0, 0, 0.7);
      }

      .sidebar.mobile-open {
        transform: translateX(0);
      }

      .btn-sidebar-close {
        display: flex;
      }

      /* Chat viewport */
      #chat-viewport {
        padding: 1rem 0.65rem;
        gap: 1rem;
      }

      .message {
        gap: 0.5rem;
      }

      .bubble {
        padding: 0.75rem 0.9rem;
        max-width: calc(100% - 40px);
      }

      .efficiency-grid {
        grid-template-columns: 1fr;
      }

      .chat-input-bar {
        padding: 0.5rem 0.65rem calc(0.5rem + env(safe-area-inset-bottom, 0px));
      }
    }

    @media (max-width: 640px) {
      .brand-text { display: none; }

      .suggestion-grid {
        grid-template-columns: 1fr;
      }

      .console-diff-grid {
        grid-template-columns: 1fr;
      }

      .problems-filter-bar {
        flex-direction: column;
        padding: 0.65rem 1rem;
      }

      .filter-input, .filter-select {
        width: 100%;
        flex: 1 1 100%;
      }

      .catalog-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.35rem;
      }

      .studio-footer {
        flex-direction: row;
      }

      .btn-run-code, .btn-submit-code {
        flex: 1;
      }

      .ai-side-panel {
        width: 100%;
      }
    }

    /* -------------------------------------------------------------
       VIEW 3: ADMIN & CSV INGESTION STUDIO
       ------------------------------------------------------------- */
    #admin-view {
      display: none;
      width: 100%;
      height: 100%;
      overflow-y: auto;
      flex-direction: column;
      padding: 1.5rem;
      gap: 1.5rem;
      background: var(--bg-primary);
    }

    .admin-container {
      max-width: 1100px;
      margin: 0 auto;
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      padding-bottom: 3rem;
    }

    .admin-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 1rem;
    }

    .admin-title-group h2 {
      font-size: 1.35rem;
      font-weight: 700;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .admin-title-group p {
      font-size: 0.82rem;
      color: var(--text-muted);
      margin-top: 0.25rem;
    }

    .admin-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.25rem;
    }
    @media (max-width: 850px) {
      .admin-grid { grid-template-columns: 1fr; }
    }

    .admin-card {
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    .admin-card-title {
      font-size: 0.92rem;
      font-weight: 600;
      color: var(--accent);
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }

    .admin-input-group {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }

    .admin-input-group label {
      font-size: 0.76rem;
      font-weight: 600;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .admin-input {
      background: var(--bg-tertiary);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 0.55rem 0.75rem;
      color: var(--text-main);
      font-size: 0.85rem;
      outline: none;
      transition: border-color 0.2s;
    }
    .admin-input:focus {
      border-color: var(--accent);
    }

    .admin-dropzone {
      border: 2px dashed var(--border-color);
      border-radius: 8px;
      background: rgba(30, 41, 59, 0.4);
      padding: 1.75rem 1.25rem;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
    }
    .admin-dropzone:hover, .admin-dropzone.dragover {
      border-color: var(--accent);
      background: rgba(56, 189, 248, 0.05);
    }
    .admin-dropzone-icon {
      font-size: 2.2rem;
    }
    .admin-dropzone-text {
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--text-main);
    }
    .admin-dropzone-subtext {
      font-size: 0.75rem;
      color: var(--text-dim);
    }

    .admin-file-badge {
      display: none;
      align-items: center;
      justify-content: space-between;
      background: var(--bg-tertiary);
      border: 1px solid var(--accent);
      border-radius: 6px;
      padding: 0.5rem 0.75rem;
      font-size: 0.82rem;
      color: var(--text-main);
    }

    .mode-options {
      display: flex;
      gap: 0.75rem;
      flex-wrap: wrap;
    }
    .mode-label {
      display: flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.8rem;
      color: var(--text-muted);
      cursor: pointer;
    }

    .schema-preview-card {
      display: none;
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 1.25rem;
      flex-direction: column;
      gap: 1rem;
    }

    .table-scroll {
      max-height: 280px;
      overflow-y: auto;
      border: 1px solid var(--border-color);
      border-radius: 6px;
    }
    .admin-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.8rem;
    }
    .admin-table th {
      background: var(--bg-tertiary);
      padding: 0.5rem 0.75rem;
      color: var(--text-dim);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 0.72rem;
      position: sticky;
      top: 0;
      z-index: 2;
      border-bottom: 1px solid var(--border-color);
      white-space: nowrap;
    }
    .admin-table td {
      padding: 0.45rem 0.75rem;
      border-bottom: 1px solid var(--border-color);
      color: var(--text-main);
    }
    .type-select {
      background: var(--bg-elevated);
      color: var(--accent);
      border: 1px solid var(--border-color);
      border-radius: 4px;
      padding: 0.25rem 0.5rem;
      font-size: 0.75rem;
      font-weight: 600;
      outline: none;
    }

    .btn-ingest-run {
      background: linear-gradient(135deg, #0284c7, #2563eb);
      color: white;
      border: none;
      border-radius: 6px;
      padding: 0.65rem 1.4rem;
      font-weight: 600;
      font-size: 0.88rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      transition: all 0.2s;
    }
    .btn-ingest-run:hover {
      box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4);
    }
    .btn-ingest-run:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .alert-box {
      border-radius: 6px;
      padding: 0.75rem 1rem;
      font-size: 0.85rem;
      display: none;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
    }
    .alert-success {
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid var(--success);
      color: #34d399;
    }
    .alert-error {
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid var(--danger);
      color: #f87171;
    }
  </style>
</head>
<body>

<!-- Global Header -->
<header class="app-header">
  <div class="header-left">
    <a href="/" class="brand">
      <div class="brand-icon">⚡</div>
      <span class="brand-text">ChatSQL Pro</span>
    </a>
    <div class="nav-mode-tabs">
      <button class="nav-mode-btn active" id="tab-nav-chat" onclick="switchView('chat')">
        <span class="nav-text-full">💬 Chat & Tutor</span>
        <span class="nav-text-short">💬 Chat</span>
      </button>
      <button class="nav-mode-btn" id="tab-nav-battleground" onclick="switchView('battleground')">
        <span class="nav-text-full">⚔️ SQL Battleground (Top 50)</span>
        <span class="nav-text-short">⚔️ Arena</span>
      </button>
      <button class="nav-mode-btn" id="tab-nav-admin" onclick="switchView('admin')">
        <span class="nav-text-full">🛠️ Data Studio (CSV Upload)</span>
        <span class="nav-text-short">🛠️ Studio</span>
      </button>
    </div>
  </div>

  <div class="header-right">
    <div class="header-badges">
      <span class="badge badge-db">
        <span class="badge-text-full">🟢 PostgreSQL (34M Rows)</span>
        <span class="badge-text-short">🟢 34M DB</span>
      </span>
      <span class="badge badge-ai">
        <span class="badge-text-full">⚡ AI SQL Mentor · Active</span>
        <span class="badge-text-short">⚡ AI Active</span>
      </span>
    </div>
    <div id="header-user-slot">
      <button class="btn-studio-action" onclick="openAuthModal('login')">Sign In</button>
    </div>
  </div>
</header>

<div class="view-container">

  <!-- =============================================================
       VIEW 1: CHAT TUTOR VIEW
       ============================================================= -->
  <div id="chat-view">
    <!-- Backdrop for mobile drawer -->
    <div class="sidebar-backdrop" id="sidebar-backdrop" onclick="toggleSidebar(false)"></div>

    <aside class="sidebar" id="sidebar">
      <div class="sidebar-header">
        <button class="btn-new-chat" id="btn-new-chat">
          <span>＋</span> New Chat
        </button>
        <button class="btn-sidebar-close" id="btn-close-sidebar" onclick="toggleSidebar(false)" title="Close Sidebar">✕</button>
      </div>

      <div class="sidebar-title">Recent Chats</div>
      <div class="history-list" id="history-list">
        <div style="padding: 1rem; color: var(--text-dim); font-size: 0.82rem; text-align: center;">Loading chats...</div>
      </div>

      <div class="sidebar-footer" id="sidebar-footer">
        <button class="btn-new-chat" style="background: var(--bg-tertiary);" onclick="openAuthModal('login')">
          👤 Sign In / Register
        </button>
      </div>
    </aside>

    <main class="chat-main">
      <div class="chat-topbar">
        <button class="btn-sidebar-toggle" id="btn-toggle-sidebar" title="Toggle Sidebar">☰</button>
        <div class="chat-topbar-title" id="chat-header-title">New Conversation</div>
      </div>

      <div id="chat-viewport">
        <div class="welcome-hero" id="welcome-hero">
          <div class="hero-badge">🎓 AI SQL Mentor for Learners & Pros</div>
          <h1 class="hero-title">Master SQL with Intuitive Concepts</h1>
          <p class="hero-subtitle">
            Ask database questions in plain English, query your database with real-time optimization, or practice top interview questions.
          </p>

          <div class="suggestion-grid">
            <div class="suggestion-card" onclick="sendQuickPrompt('give 10 sql interview question')">
              <div class="suggestion-title">🎯 10 SQL Interview Questions</div>
              <div class="suggestion-desc">Practice realistic questions with explanations & efficiency tips</div>
            </div>
            <div class="suggestion-card" onclick="sendQuickPrompt('Explain what a SQL JOIN is with everyday analogies')">
              <div class="suggestion-title">🔍 Explain JOINs with Real-World Analogies</div>
              <div class="suggestion-desc">Everyday analogies for INNER, LEFT, and FULL outer joins</div>
            </div>
            <div class="suggestion-card" onclick="sendQuickPrompt('Show top 5 customers from the database')">
              <div class="suggestion-title">⚡ Show Top 5 Customers</div>
              <div class="suggestion-desc">Executes live read-only query with time & memory breakdown</div>
            </div>
            <div class="suggestion-card" onclick="sendQuickPrompt('Difference between WHERE and HAVING explained simply')">
              <div class="suggestion-title">💡 WHERE vs HAVING</div>
              <div class="suggestion-desc">Why filter early to conserve database memory</div>
            </div>
          </div>
        </div>
      </div>

      <div class="chat-input-bar">
        <form class="chat-form" id="chat-form">
          <textarea id="prompt-input" rows="1" placeholder="Ask a SQL question, query database, or practice..."></textarea>
          <button type="submit" class="btn-send" id="btn-send">Send ➔</button>
        </form>
      </div>
    </main>
  </div>

  <!-- =============================================================
       VIEW 2: LEETCODE TOP 50 SQL BATTLEGROUND ARENA
       ============================================================= -->
  <div id="battleground-view">
    <div class="battleground-topbar">
      <div class="battleground-controls">
        <button class="problem-select-btn" onclick="openProblemCatalog()">
          <span>📋</span> Challenge (<span id="current-q-index">1</span>/50)
        </button>
        <span class="progress-pill" id="arena-progress-badge">🏆 Solved: 0 / 50</span>
      </div>

      <div class="battleground-controls">
        <button class="btn-studio-action" style="background: rgba(56, 189, 248, 0.1); border-color: rgba(56, 189, 248, 0.3); color: var(--accent); font-weight: 600;" onclick="openAiSidePanel('hint')">💡 Hint</button>
        <button class="btn-studio-action" style="background: rgba(168, 85, 247, 0.1); border-color: rgba(168, 85, 247, 0.3); color: #c084fc; font-weight: 600;" onclick="openAiSidePanel('solution')">👁 Solution</button>
      </div>
    </div>

    <!-- Mobile/Tablet Segmented Switcher (<900px) -->
    <div class="arena-mobile-tabs" id="arena-mobile-tabs">
      <button class="arena-mobile-tab active" id="btn-pane-problem" onclick="switchArenaPane('problem')">
        📖 Problem Description
      </button>
      <button class="arena-mobile-tab" id="btn-pane-studio" onclick="switchArenaPane('studio')">
        💻 Code Studio & Output
      </button>
    </div>

    <div class="arena-grid">
      <!-- Left: Problem Description -->
      <div class="problem-pane" id="arena-problem-pane">
        <div class="problem-header">
          <div class="problem-meta">
            <span class="diff-badge diff-Easy" id="q-diff-badge">Easy</span>
            <span class="category-badge" id="q-category-badge">Select & Filtering</span>
            <span style="font-size: 0.78rem; color: var(--text-dim);" id="q-acceptance-rate">Acceptance: 89%</span>
          </div>
          <div class="problem-title" id="q-title">1. High-Value Premium Products</div>
        </div>

        <div class="problem-section">
          <div class="section-title">📖 Problem Description</div>
          <div class="layman-box" id="q-layman-desc">Loading challenge details...</div>
        </div>

        <div class="problem-section">
          <div class="section-title">📂 Relevant Database Tables</div>
          <div style="font-size: 0.86rem; color: var(--text-muted);" id="q-tables-used">products</div>
        </div>

        <div class="problem-section" id="q-solution-box" style="display: none;">
          <div class="section-title">🎓 Solution Breakdown & Concept Walkthrough</div>
          <div class="layman-card" id="q-layman-explanation"></div>
          <div class="efficiency-grid">
            <div class="efficiency-card card-time">
              <div class="eff-title">🚀 Time Efficiency</div>
              <div id="q-time-tip"></div>
            </div>
            <div class="efficiency-card card-memory">
              <div class="eff-title">💾 Memory Efficiency</div>
              <div id="q-mem-tip"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Interactive Code Studio -->
      <div class="studio-pane" id="arena-studio-pane">
        <div class="studio-header">
          <span>SQL (PostgreSQL 15 Dialect)</span>
          <div class="studio-actions">
            <button class="btn-studio-action" onclick="resetStarterCode()">↺ Reset Code</button>
          </div>
        </div>

        <div class="editor-wrapper">
          <textarea id="sql-editor" spellcheck="false" placeholder="Write your SQL solution here..."></textarea>
        </div>

        <div class="studio-footer">
          <button class="btn-run-code" onclick="runUserCode()">
            <span>▶</span> Run Code
          </button>
          <button class="btn-submit-code" onclick="submitUserCode()">
            <span>🚀</span> Submit Solution
          </button>
        </div>

        <!-- Output Console -->
        <div class="console-drawer">
          <div class="console-tabs">
            <button class="console-tab active" id="tab-console-result">Test Results</button>
          </div>
          <div class="console-body" id="console-output">
            <div style="color: var(--text-dim); text-align: center; padding: 1.5rem;">
              Click <strong>Run Code</strong> or <strong>Submit Solution</strong> to test your query against the live database.
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

</div>

  <!-- =============================================================
       VIEW 3: ADMIN & DATA STUDIO (AUTOMATED CSV INGESTION)
       ============================================================= -->
  <div id="admin-view" style="display: none;">
    <div class="admin-container">
      <div class="admin-header">
        <div class="admin-title-group">
          <h2>🛠️ Data Studio & CSV Ingestion Engine</h2>
          <p>Define your database and table, upload any CSV, and let our engine automatically detect schema types and stream data into PostgreSQL.</p>
        </div>
        <div style="display: flex; gap: 0.5rem; align-items: center;">
          <button class="btn-studio-action" onclick="loadAdminTables()">🔄 Refresh Tables</button>
        </div>
      </div>

      <!-- Ingestion Setup Form -->
      <div class="admin-grid">
        <!-- Card 1: Destination Config -->
        <div class="admin-card">
          <div class="admin-card-title">🎯 1. Target Destination</div>
          
          <div class="admin-input-group">
            <label for="admin-db-name">Target Database</label>
            <input type="text" id="admin-db-name" class="admin-input" placeholder="e-commerce" value="e-commerce">
            <span style="font-size: 0.72rem; color: var(--text-dim);">Database will be automatically created in PostgreSQL if it doesn't already exist.</span>
          </div>

          <div class="admin-input-group">
            <label for="admin-table-name">Target Table Name</label>
            <input type="text" id="admin-table-name" class="admin-input" placeholder="e.g. suppliers (auto-filled on file drop)">
          </div>

          <div class="admin-input-group">
            <label>Table Mode / Conflict Policy</label>
            <div class="mode-options">
              <label class="mode-label">
                <input type="radio" name="admin-mode" value="replace" checked>
                <span>Replace (Drop & Recreate)</span>
              </label>
              <label class="mode-label">
                <input type="radio" name="admin-mode" value="fail">
                <span>Fail if Exists</span>
              </label>
              <label class="mode-label">
                <input type="radio" name="admin-mode" value="append">
                <span>Append Data</span>
              </label>
            </div>
          </div>
        </div>

        <!-- Card 2: CSV / Excel Upload & File Dropzone -->
        <div class="admin-card">
          <div class="admin-card-title">📁 2. Upload CSV or Excel Dataset</div>
          
          <div class="admin-dropzone" id="admin-dropzone" onclick="document.getElementById('admin-csv-file').click()" ondragover="handleAdminDragOver(event)" ondragleave="handleAdminDragLeave(event)" ondrop="handleAdminDrop(event)">
            <div class="admin-dropzone-icon">📄</div>
            <div class="admin-dropzone-text">Click or drag & drop a .csv or .xlsx (Excel) file here</div>
            <div class="admin-dropzone-subtext">Automatic type inference · Supports multi-sheet workbooks (e.g. carCategories, carModels)</div>
            <input type="file" id="admin-csv-file" accept=".csv, .xlsx, .xls" style="display: none;" onchange="handleAdminFileSelected(event)">
          </div>

          <div class="admin-file-badge" id="admin-file-badge">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span id="badge-file-icon">📊</span>
              <div>
                <strong id="badge-filename">filename.csv</strong>
                <div style="font-size: 0.72rem; color: var(--text-muted);" id="badge-filesize">0 KB</div>
              </div>
            </div>
            <button class="btn-studio-action" style="padding: 0.2rem 0.5rem; font-size: 0.75rem;" onclick="resetAdminFile(event)">Remove</button>
          </div>
        </div>
      </div>

      <!-- Card 3: Auto-Detected Schema Preview & Confirmation -->
      <div class="schema-preview-card" id="schema-preview-card">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
          <div class="admin-card-title">🔍 3. Schema & Data Type Preview</div>
          <div style="font-size: 0.8rem; color: var(--accent);" id="preview-metrics">Detected 0 columns · ~0 rows</div>
        </div>

        <!-- Excel Multi-Sheet Switcher Bar -->
        <div id="excel-sheets-bar" style="display: none; align-items: center; gap: 0.6rem; flex-wrap: wrap; background: var(--bg-tertiary); padding: 0.6rem 0.85rem; border-radius: 8px; border: 1px solid var(--border-color);">
          <span style="font-size: 0.76rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase;">Sheets in Workbook:</span>
          <div id="excel-sheets-pills" style="display: flex; gap: 0.4rem; flex-wrap: wrap;"></div>
        </div>

        <div style="font-size: 0.78rem; color: var(--text-muted);">
          The engine automatically inferred the PostgreSQL column types below. You can adjust any type dropdown before running the ingestion:
        </div>

        <div class="table-scroll">
          <table class="admin-table">
            <thead>
              <tr>
                <th>Original Header</th>
                <th>PostgreSQL Column</th>
                <th>Inferred Type (Click to override)</th>
                <th>Sample Value (Row 1)</th>
              </tr>
            </thead>
            <tbody id="preview-schema-tbody">
              <!-- Populated dynamically -->
            </tbody>
          </table>
        </div>

        <!-- Sample Rows Data Preview -->
        <div style="margin-top: 0.5rem;">
          <div style="font-size: 0.76rem; font-weight: 600; color: var(--text-dim); text-transform: uppercase; margin-bottom: 0.35rem;">Sample Rows Preview (Top 5)</div>
          <div class="table-scroll">
            <table class="admin-table" id="preview-data-table">
              <!-- Populated dynamically -->
            </table>
          </div>
        </div>

        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem; margin-top: 0.5rem;">
          <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
            <button class="btn-ingest-run" id="btn-run-ingest" onclick="executeCsvIngestion()">
              <span>🚀</span> Stream This Sheet into PostgreSQL
            </button>
            <button class="btn-ingest-run" id="btn-run-all-sheets" style="display: none; background: linear-gradient(135deg, #059669, #10b981);" onclick="executeAllSheetsIngestion()">
              <span>📦</span> Ingest ALL Sheets (Multiple Tables)
            </button>
          </div>
          <div id="ingest-spinner-msg" style="font-size: 0.82rem; color: var(--text-muted); display: none;">
            ⏳ Ingesting rows into PostgreSQL via streaming COPY...
          </div>
        </div>

        <!-- Success & Error Alerts -->
        <div class="alert-box alert-success" id="admin-alert-success">
          <span id="alert-success-text">🎉 Data successfully imported!</span>
          <button class="btn-studio-action" onclick="openChatWithNewTable()">💬 Chat with this Table ➔</button>
        </div>
        <div class="alert-box alert-error" id="admin-alert-error">
          <span id="alert-error-text">❌ Ingestion error</span>
        </div>
      </div>

      <!-- Card 4: Active Database Tables Inspector -->
      <div class="admin-card" style="margin-top: 0.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div class="admin-card-title">🗄️ Active Tables in Database (<span id="active-db-label">e-commerce</span>)</div>
          <span style="font-size: 0.75rem; color: var(--text-dim);">Auto-refreshed with schema cache</span>
        </div>

        <div class="table-scroll" style="max-height: 250px;">
          <table class="admin-table">
            <thead>
              <tr>
                <th>Table Name</th>
                <th>Row Count</th>
                <th>Columns</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody id="admin-tables-tbody">
              <tr>
                <td colspan="4" style="text-align: center; color: var(--text-dim);">Loading active tables...</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <!-- Chrome "Ask Gemini"-Style AI Side Panel -->
  <div class="side-panel-backdrop" id="side-panel-backdrop" onclick="closeAiSidePanel()"></div>

<aside class="ai-side-panel" id="ai-side-panel" aria-label="Groq AI SQL Assistant">
  <div class="side-panel-header">
    <div class="ai-panel-title-group">
      <div class="ai-sparkle-icon">✨</div>
      <div>
        <div class="ai-panel-title">Groq AI Assistant</div>
        <div class="ai-panel-subtitle">Live SQL Editor Monitoring & Solution Mentor</div>
      </div>
    </div>
    <button class="btn-close-modal" onclick="closeAiSidePanel()" title="Close Panel (Esc)">✕</button>
  </div>

  <div class="side-panel-tabs">
    <button class="side-panel-tab active" id="panel-tab-hint" onclick="switchPanelTab('hint')">
      💡 Smart Hint
    </button>
    <button class="side-panel-tab" id="panel-tab-solution" onclick="switchPanelTab('solution')">
      🎓 Full Solution
    </button>
  </div>

  <div class="side-panel-body" id="ai-panel-content">
    <!-- Populated dynamically by Groq AI -->
  </div>
</aside>

<!-- Problems Catalog Dialog -->
<dialog class="problems-modal" id="catalog-dialog">
  <div class="problems-modal-header">
    <div style="font-weight: 700; font-size: 1.1rem;">⚔️ SQL Battleground Catalog</div>
    <button class="btn-close-modal" onclick="document.getElementById('catalog-dialog').close()">✕</button>
  </div>
  <div class="problems-filter-bar">
    <input type="text" class="filter-input" id="filter-search" placeholder="Search challenges by title..." oninput="renderProblemCatalogList()">
    <select class="filter-select" id="filter-diff" onchange="renderProblemCatalogList()">
      <option value="">All Difficulties</option>
      <option value="Easy">Easy</option>
      <option value="Medium">Medium</option>
      <option value="Hard">Hard</option>
    </select>
    <select class="filter-select" id="filter-cat" onchange="renderProblemCatalogList()">
      <option value="">All Categories</option>
      <option value="Select & Filtering">Select & Filtering</option>
      <option value="Basic Joins">Basic Joins</option>
      <option value="Aggregation & Grouping">Aggregation & Grouping</option>
      <option value="Sorting & Grouping">Sorting & Grouping</option>
      <option value="Advanced Joins">Advanced Joins</option>
      <option value="Subqueries & Window Functions">Subqueries & Window Functions</option>
    </select>
  </div>
  <div class="problem-items-container" id="catalog-items-list">
    <!-- Populated via API -->
  </div>
</dialog>

<!-- Native Auth Modal -->
<dialog class="auth-modal" id="auth-dialog">
  <div class="auth-modal-content">
    <div class="auth-modal-header">
      <div class="auth-title" id="auth-modal-title">Sign In to ChatSQL</div>
      <button class="btn-close-modal" id="btn-close-auth">✕</button>
    </div>

    <div class="auth-tabs">
      <button class="auth-tab active" id="tab-login" onclick="switchAuthTab('login')">Sign In</button>
      <button class="auth-tab" id="tab-register" onclick="switchAuthTab('register')">Create Account</button>
    </div>

    <div class="social-auth-group">
      <button class="btn-social btn-google" onclick="loginWithGoogle()">
        <svg width="18" height="18" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
        </svg>
        Continue with Google
      </button>

      <button class="btn-social btn-github" onclick="loginWithGithub()">
        <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
          <path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
        </svg>
        Continue with GitHub
      </button>
    </div>

    <div class="auth-divider"><span>or with email</span></div>

    <form id="auth-form" onsubmit="handleAuthSubmit(event)">
      <div class="auth-form-fields">
        <div class="auth-input-group" id="group-name" style="display: none;">
          <label for="input-auth-name">Your Full Name</label>
          <input type="text" id="input-auth-name" placeholder="John Doe">
        </div>
        <div class="auth-input-group">
          <label for="input-auth-email">Email Address</label>
          <input type="email" id="input-auth-email" placeholder="learner@example.com" required>
        </div>
        <div class="auth-input-group">
          <label for="input-auth-password">Password</label>
          <input type="password" id="input-auth-password" placeholder="At least 6 characters" required>
        </div>
        <button type="submit" class="btn-auth-submit" id="btn-submit-auth">Sign In</button>
      </div>
      <div class="auth-error-banner" id="auth-error-msg"></div>
    </form>
  </div>
</dialog>

<script>
  let activeConversationId = null;
  let currentUser = null;
  let currentAuthMode = 'login';
  let currentView = 'chat'; // 'chat' or 'battleground'
  let currentArenaPane = 'problem'; // 'problem' or 'studio' for mobile/tablet (<900px)

  // Battleground State
  let allBattlegroundQuestions = [];
  let currentProblem = null;

  // View Switcher
  function switchView(viewName) {
    currentView = viewName;
    const chatView = document.getElementById('chat-view');
    const battlegroundView = document.getElementById('battleground-view');
    const adminView = document.getElementById('admin-view');
    const tabChat = document.getElementById('tab-nav-chat');
    const tabBattle = document.getElementById('tab-nav-battleground');
    const tabAdmin = document.getElementById('tab-nav-admin');

    if (chatView) chatView.style.display = 'none';
    if (battlegroundView) battlegroundView.style.display = 'none';
    if (adminView) adminView.style.display = 'none';

    if (tabChat) tabChat.classList.remove('active');
    if (tabBattle) tabBattle.classList.remove('active');
    if (tabAdmin) tabAdmin.classList.remove('active');

    if (viewName === 'battleground') {
      if (battlegroundView) battlegroundView.style.display = 'flex';
      if (tabBattle) tabBattle.classList.add('active');
      if (allBattlegroundQuestions.length === 0) {
        initBattleground();
      }
    } else if (viewName === 'admin') {
      if (adminView) adminView.style.display = 'flex';
      if (tabAdmin) tabAdmin.classList.add('active');
      loadAdminTables();
    } else {
      if (chatView) chatView.style.display = 'flex';
      if (tabChat) tabChat.classList.add('active');
    }
  }

  // Mobile/Tablet Arena Pane Switcher
  function switchArenaPane(paneName) {
    currentArenaPane = paneName;
    const btnProblem = document.getElementById('btn-pane-problem');
    const btnStudio = document.getElementById('btn-pane-studio');
    const problemPane = document.getElementById('arena-problem-pane');
    const studioPane = document.getElementById('arena-studio-pane');

    if (paneName === 'studio') {
      btnStudio.classList.add('active');
      btnProblem.classList.remove('active');
      if (window.innerWidth <= 900) {
        problemPane.style.display = 'none';
        studioPane.style.display = 'flex';
      }
    } else {
      btnProblem.classList.add('active');
      btnStudio.classList.remove('active');
      if (window.innerWidth <= 900) {
        studioPane.style.display = 'none';
        problemPane.style.display = 'flex';
      }
    }
  }

  // Handle window resizing for arena panes
  window.addEventListener('resize', () => {
    const problemPane = document.getElementById('arena-problem-pane');
    const studioPane = document.getElementById('arena-studio-pane');
    if (window.innerWidth > 900) {
      if (problemPane) problemPane.style.display = 'flex';
      if (studioPane) studioPane.style.display = 'flex';
    } else {
      switchArenaPane(currentArenaPane);
    }
  });

  // Responsive Sidebar Drawer Toggle
  function toggleSidebar(forceState) {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    const isMobile = window.innerWidth <= 768;

    if (isMobile) {
      const open = forceState !== undefined ? forceState : !sidebar.classList.contains('mobile-open');
      if (open) {
        sidebar.classList.add('mobile-open');
        backdrop.classList.add('active');
      } else {
        sidebar.classList.remove('mobile-open');
        backdrop.classList.remove('active');
      }
    } else {
      sidebar.classList.toggle('collapsed');
      backdrop.classList.remove('active');
    }
  }

  // Auth Helpers
  function getAuthHeader() {
    const token = localStorage.getItem('chatsql_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }

  async function checkCurrentUser() {
    const token = localStorage.getItem('chatsql_token');
    if (!token) {
      renderLoggedOutFooter();
      loadHistoryList();
      return;
    }
    try {
      const res = await fetch('/api/v1/auth/me', { headers: getAuthHeader() });
      if (res.ok) {
        currentUser = await res.json();
        renderLoggedInFooter(currentUser);
      } else {
        localStorage.removeItem('chatsql_token');
        renderLoggedOutFooter();
      }
    } catch {
      renderLoggedOutFooter();
    }
    loadHistoryList();
  }

  function renderLoggedInFooter(user) {
    const slot = document.getElementById('header-user-slot');
    const sidebarFooter = document.getElementById('sidebar-footer');
    const avatar = user.avatar_url || `https://api.dicebear.com/7.x/identicon/svg?seed=${user.email}`;

    const profileHtml = `
      <div style="display: flex; align-items: center; gap: 0.5rem;">
        <img src="${avatar}" style="width: 28px; height: 28px; border-radius: 50%; border: 1px solid var(--border-color);" alt="${escapeHtml(user.name)}">
        <span style="font-size: 0.82rem; font-weight: 600; max-width: 90px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(user.name)}</span>
        <button class="btn-studio-action" onclick="logout()" title="Sign Out">Sign Out</button>
      </div>
    `;
    slot.innerHTML = profileHtml;
    sidebarFooter.innerHTML = profileHtml;
  }

  function renderLoggedOutFooter() {
    const slot = document.getElementById('header-user-slot');
    const sidebarFooter = document.getElementById('sidebar-footer');
    const btnHtml = `<button class="btn-studio-action" onclick="openAuthModal('login')">👤 Sign In</button>`;
    slot.innerHTML = btnHtml;
    sidebarFooter.innerHTML = btnHtml;
  }

  function logout() {
    localStorage.removeItem('chatsql_token');
    currentUser = null;
    renderLoggedOutFooter();
    startNewChat();
    loadHistoryList();
    if (currentView === 'battleground') initBattleground();
  }

  // Auth Dialog
  const authDialog = document.getElementById('auth-dialog');
  document.getElementById('btn-close-auth').addEventListener('click', () => authDialog.close());

  function openAuthModal(mode) {
    currentAuthMode = mode;
    switchAuthTab(mode);
    authDialog.showModal();
  }

  function switchAuthTab(mode) {
    currentAuthMode = mode;
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const groupName = document.getElementById('group-name');
    const title = document.getElementById('auth-modal-title');
    const submitBtn = document.getElementById('btn-submit-auth');
    document.getElementById('auth-error-msg').style.display = 'none';

    if (mode === 'register') {
      tabRegister.classList.add('active');
      tabLogin.classList.remove('active');
      groupName.style.display = 'block';
      title.innerText = 'Create Learner Account';
      submitBtn.innerText = 'Create Account';
    } else {
      tabLogin.classList.add('active');
      tabRegister.classList.remove('active');
      groupName.style.display = 'none';
      title.innerText = 'Sign In to ChatSQL';
      submitBtn.innerText = 'Sign In';
    }
  }

  async function handleAuthSubmit(e) {
    e.preventDefault();
    const errorBanner = document.getElementById('auth-error-msg');
    errorBanner.style.display = 'none';
    const email = document.getElementById('input-auth-email').value.trim();
    const password = document.getElementById('input-auth-password').value;
    const name = document.getElementById('input-auth-name').value.trim();

    const endpoint = currentAuthMode === 'register' ? '/api/v1/auth/register' : '/api/v1/auth/login';
    const payload = currentAuthMode === 'register' ? { name, email, password } : { email, password };

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) {
        errorBanner.innerText = data.detail || 'Authentication failed.';
        errorBanner.style.display = 'block';
        return;
      }
      localStorage.setItem('chatsql_token', data.access_token);
      currentUser = data.user;
      renderLoggedInFooter(currentUser);
      authDialog.close();
      loadHistoryList();
      if (currentView === 'battleground') initBattleground();
    } catch (err) {
      errorBanner.innerText = 'Network error: ' + err.message;
      errorBanner.style.display = 'block';
    }
  }

  async function loginWithGoogle() {
    try {
      const res = await fetch('/api/v1/auth/oauth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: 'google', email: 'learner@gmail.com', name: 'Google Learner' })
      });
      const data = await res.json();
      if (res.ok) {
        localStorage.setItem('chatsql_token', data.access_token);
        currentUser = data.user;
        renderLoggedInFooter(currentUser);
        authDialog.close();
        loadHistoryList();
        if (currentView === 'battleground') initBattleground();
      }
    } catch (err) { alert('Google auth error: ' + err.message); }
  }

  async function loginWithGithub() {
    try {
      const res = await fetch('/api/v1/auth/oauth/github', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: 'github', email: 'developer@github.com', name: 'GitHub Developer' })
      });
      const data = await res.json();
      if (res.ok) {
        localStorage.setItem('chatsql_token', data.access_token);
        currentUser = data.user;
        renderLoggedInFooter(currentUser);
        authDialog.close();
        loadHistoryList();
        if (currentView === 'battleground') initBattleground();
      }
    } catch (err) { alert('GitHub auth error: ' + err.message); }
  }

  // -------------------------------------------------------------
  // CHAT VIEW SCRIPTS
  // -------------------------------------------------------------
  const promptInput = document.getElementById('prompt-input');
  const chatForm = document.getElementById('chat-form');
  const sendBtn = document.getElementById('btn-send');
  const chatViewport = document.getElementById('chat-viewport');

  document.getElementById('btn-toggle-sidebar').addEventListener('click', () => toggleSidebar());
  document.getElementById('btn-new-chat').addEventListener('click', () => {
    startNewChat();
    if (window.innerWidth <= 768) toggleSidebar(false);
  });

  promptInput.addEventListener('input', () => {
    promptInput.style.height = 'auto';
    promptInput.style.height = Math.min(promptInput.scrollHeight, 120) + 'px';
  });

  promptInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event('submit'));
    }
  });

  function startNewChat() {
    activeConversationId = null;
    document.getElementById('chat-header-title').innerText = 'New Conversation';
    document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
    chatViewport.innerHTML = `
      <div class="welcome-hero" id="welcome-hero">
        <div class="hero-badge">🎓 AI SQL Mentor for Learners & Pros</div>
        <h1 class="hero-title">Master SQL with Intuitive Concepts</h1>
        <p class="hero-subtitle">
          Ask database questions in plain English, query your database with real-time optimization, or practice top interview questions.
        </p>
        <div class="suggestion-grid">
          <div class="suggestion-card" onclick="sendQuickPrompt('give 10 sql interview question')">
            <div class="suggestion-title">🎯 10 SQL Interview Questions</div>
            <div class="suggestion-desc">Practice realistic questions with explanations & efficiency tips</div>
          </div>
          <div class="suggestion-card" onclick="sendQuickPrompt('Explain what a SQL JOIN is with everyday analogies')">
            <div class="suggestion-title">🔍 Explain JOINs with Real-World Analogies</div>
            <div class="suggestion-desc">Everyday analogies for INNER, LEFT, and FULL outer joins</div>
          </div>
          <div class="suggestion-card" onclick="sendQuickPrompt('Show top 5 customers from the database')">
            <div class="suggestion-title">⚡ Show Top 5 Customers</div>
            <div class="suggestion-desc">Executes live read-only query with time & memory breakdown</div>
          </div>
          <div class="suggestion-card" onclick="sendQuickPrompt('Difference between WHERE and HAVING explained simply')">
            <div class="suggestion-title">💡 WHERE vs HAVING</div>
            <div class="suggestion-desc">Why filter early to conserve database memory</div>
          </div>
        </div>
      </div>
    `;
    promptInput.focus();
  }

  function sendQuickPrompt(text) {
    promptInput.value = text;
    chatForm.dispatchEvent(new Event('submit'));
  }

  async function loadHistoryList() {
    const listEl = document.getElementById('history-list');
    try {
      const res = await fetch('/api/v1/conversations', { headers: getAuthHeader() });
      if (!res.ok) { listEl.innerHTML = '<div style="padding: 1rem; color: var(--text-dim); font-size: 0.82rem; text-align: center;">No chat history yet.</div>'; return; }
      const conversations = await res.json();
      if (!conversations || conversations.length === 0) {
        listEl.innerHTML = '<div style="padding: 1rem; color: var(--text-dim); font-size: 0.82rem; text-align: center;">No previous conversations.</div>';
        return;
      }
      listEl.innerHTML = conversations.map(c => `
        <div class="history-item ${c.id === activeConversationId ? 'active' : ''}" onclick="selectConversation('${c.id}')" id="conv-item-${c.id}">
          <span class="history-item-title" title="${escapeHtml(c.title)}">${escapeHtml(c.title)}</span>
          <button class="btn-delete-chat" onclick="deleteConversation(event, '${c.id}')" title="Delete chat">🗑</button>
        </div>
      `).join('');
    } catch {
      listEl.innerHTML = '<div style="padding: 1rem; color: var(--text-dim); font-size: 0.82rem; text-align: center;">Unable to load history.</div>';
    }
  }

  async function selectConversation(conversationId) {
    activeConversationId = conversationId;
    document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
    const activeItem = document.getElementById(`conv-item-${conversationId}`);
    if (activeItem) activeItem.classList.add('active');

    if (window.innerWidth <= 768) toggleSidebar(false);

    try {
      const res = await fetch(`/api/v1/conversations/${conversationId}`, { headers: getAuthHeader() });
      if (!res.ok) return;
      const data = await res.json();
      document.getElementById('chat-header-title').innerText = data.title || 'Conversation';
      chatViewport.innerHTML = '';
      if (data.messages) {
        data.messages.forEach(msg => {
          if (msg.role === 'user') {
            appendUserMessage(msg.content);
          } else {
            const meta = msg.metadata || {};
            if (meta.sql) {
              renderSuccessResponse({
                generated_sql: meta.sql,
                explanation: msg.content,
                time_efficiency_tip: meta.time_tip,
                memory_efficiency_tip: meta.memory_tip,
                row_count: meta.row_count,
              });
            } else {
              renderGeneralResponse({ explanation: msg.content });
            }
          }
        });
      }
      chatViewport.scrollTop = chatViewport.scrollHeight;
    } catch (err) { console.error('Error loading conversation:', err); }
  }

  async function deleteConversation(event, conversationId) {
    event.stopPropagation();
    if (!confirm('Are you sure you want to delete this conversation?')) return;
    try {
      const res = await fetch(`/api/v1/conversations/${conversationId}`, { method: 'DELETE', headers: getAuthHeader() });
      if (res.ok) {
        if (activeConversationId === conversationId) startNewChat();
        loadHistoryList();
      }
    } catch (err) { alert('Delete failed: ' + err.message); }
  }

  function formatMarkdown(text) {
    if (!text) return '';
    let escaped = escapeHtml(text);
    escaped = escaped.replace(/```(?:sql)?\n([\s\S]*?)```/g, '<div class="sql-box"><div class="sql-code-text">$1</div></div>');
    escaped = escaped.replace(/`([^`]+)`/g, '<code style="background: var(--code-bg); padding: 2px 5px; border-radius: 4px; color: var(--accent); font-family: monospace;">$1</code>');
    escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    escaped = escaped.replace(/^### (.*$)/gim, '<h3 style="margin: 0.85rem 0 0.4rem; color: var(--accent); font-size: 1.05rem;">$1</h3>');
    escaped = escaped.replace(/^## (.*$)/gim, '<h2 style="margin: 1rem 0 0.5rem; color: var(--text-main); font-size: 1.15rem;">$1</h2>');
    escaped = escaped.replace(/^---$/gim, '<hr style="border: none; border-top: 1px solid var(--border-color); margin: 0.85rem 0;">');
    escaped = escaped.replace(/^\* (.*$)/gim, '<div style="margin-left: 1rem;">• $1</div>');
    escaped = escaped.replace(/^- (.*$)/gim, '<div style="margin-left: 1rem;">• $1</div>');
    escaped = escaped.replace(/\n/g, '<br>');
    return escaped;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  }

  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = promptInput.value.trim();
    if (!prompt) return;

    const hero = document.getElementById('welcome-hero');
    if (hero) hero.remove();

    appendUserMessage(prompt);
    promptInput.value = '';
    promptInput.style.height = 'auto';
    sendBtn.disabled = true;

    appendLoadingMessage();

    try {
      const response = await fetch('/api/v1/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
        body: JSON.stringify({ prompt: prompt, conversation_id: activeConversationId })
      });
      removeLoadingMessage();
      const data = await response.json();
      if (!response.ok) {
        appendErrorMessage(data.detail || 'An unexpected error occurred.');
        return;
      }
      activeConversationId = data.conversation_id;
      loadHistoryList();

      if (data.status === 'clarification_needed') {
        renderClarificationResponse(data);
      } else if (data.status === 'general_response') {
        renderGeneralResponse(data);
      } else if (data.status === 'success') {
        renderSuccessResponse(data);
      }
    } catch (err) {
      removeLoadingMessage();
      appendErrorMessage('Network or server error: ' + err.message);
    } finally {
      sendBtn.disabled = false;
      promptInput.focus();
    }
  });

  function appendUserMessage(text) {
    const msg = document.createElement('div');
    msg.className = 'message user';
    msg.innerHTML = `<div class="avatar-icon avatar-user">👤</div><div class="bubble">${escapeHtml(text)}</div>`;
    chatViewport.appendChild(msg);
    chatViewport.scrollTop = chatViewport.scrollHeight;
  }

  function appendLoadingMessage() {
    const msg = document.createElement('div');
    msg.className = 'message assistant loading-msg';
    msg.id = 'loading-bubble';
    msg.innerHTML = `
      <div class="avatar-icon avatar-assistant">⚡</div>
      <div class="bubble" style="display: flex; align-items: center; gap: 0.5rem; color: var(--text-muted);">
        <span>Optimizing query & preparing explanation...</span>
      </div>
    `;
    chatViewport.appendChild(msg);
    chatViewport.scrollTop = chatViewport.scrollHeight;
  }

  function removeLoadingMessage() {
    const el = document.getElementById('loading-bubble');
    if (el) el.remove();
  }

  function appendErrorMessage(text) {
    const msg = document.createElement('div');
    msg.className = 'message assistant';
    msg.innerHTML = `
      <div class="avatar-icon avatar-assistant" style="color: var(--danger);">⚠️</div>
      <div class="bubble" style="background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.3); color: #fca5a5;">
        ${escapeHtml(text)}
      </div>
    `;
    chatViewport.appendChild(msg);
    chatViewport.scrollTop = chatViewport.scrollHeight;
  }

  function renderGeneralResponse(data) {
    const msg = document.createElement('div');
    msg.className = 'message assistant';
    const formattedText = formatMarkdown(data.explanation || '');
    msg.innerHTML = `
      <div class="avatar-icon avatar-assistant">⚡</div>
      <div class="bubble">
        <div>${formattedText}</div>
        <div class="meta-bar">
          <span>💡 AI SQL Mentor</span>
          <span>⚡ ${data.execution_time_ms ? data.execution_time_ms + 'ms' : 'Fast'}</span>
        </div>
      </div>
    `;
    chatViewport.appendChild(msg);
    chatViewport.scrollTop = chatViewport.scrollHeight;
  }

  function renderClarificationResponse(data) {
    const msg = document.createElement('div');
    msg.className = 'message assistant';
    let optionsHtml = '';
    if (data.options && data.options.length > 0) {
      optionsHtml = `
        <div class="options-grid">
          ${data.options.map(opt => `<button class="option-btn" onclick="sendOptionChoice('${opt}')">${escapeHtml(opt)}</button>`).join('')}
        </div>
      `;
    }
    msg.innerHTML = `
      <div class="avatar-icon avatar-assistant">🤔</div>
      <div class="bubble">
        <div class="clarification-card">
          <div class="clarification-title">🤔 Clarification Required</div>
          <div>${escapeHtml(data.question || 'Please select an option to proceed:')}</div>
          ${optionsHtml}
        </div>
      </div>
    `;
    chatViewport.appendChild(msg);
    chatViewport.scrollTop = chatViewport.scrollHeight;
  }

  function renderSuccessResponse(data) {
    const msg = document.createElement('div');
    msg.className = 'message assistant';

    let laymanHtml = '';
    if (data.explanation) {
      laymanHtml = `
        <div class="layman-card">
          <div class="layman-header">💡 Plain English Explanation</div>
          <div>${escapeHtml(data.explanation)}</div>
        </div>
      `;
    }

    let sqlHtml = '';
    if (data.generated_sql) {
      const escapedSql = escapeHtml(data.generated_sql);
      sqlHtml = `
        <div class="sql-box">
          <div class="sql-box-header">
            <span>Verified Read-Only SQL</span>
            <button class="btn-copy-sql" onclick="copySql(this, '${escapedSql.replace(/'/g, "\\'")}')">📋 Copy SQL</button>
          </div>
          <div class="sql-code-text">${escapedSql}</div>
        </div>
      `;
    }

    let effHtml = '';
    if (data.time_efficiency_tip || data.memory_efficiency_tip) {
      effHtml = `
        <div class="efficiency-grid">
          <div class="efficiency-card card-time">
            <div class="eff-title">🚀 Time Efficiency</div>
            <div>${escapeHtml(data.time_efficiency_tip || 'Optimized for indexed seeks.')}</div>
          </div>
          <div class="efficiency-card card-memory">
            <div class="eff-title">💾 Memory Efficiency</div>
            <div>${escapeHtml(data.memory_efficiency_tip || 'Streaming limits RAM usage.')}</div>
          </div>
        </div>
      `;
    }

    let tableHtml = '';
    if (data.columns && data.data && data.data.length > 0) {
      const headerCols = data.columns.map(c => `<th>${escapeHtml(c)}</th>`).join('');
      const rowsHtml = data.data.map(row => {
        const cells = row.map(val => `<td>${escapeHtml(String(val !== null ? val : 'NULL'))}</td>`).join('');
        return `<tr>${cells}</tr>`;
      }).join('');
      tableHtml = `
        <div class="table-container">
          <table><thead><tr>${headerCols}</tr></thead><tbody>${rowsHtml}</tbody></table>
        </div>
      `;
    }

    msg.innerHTML = `
      <div class="avatar-icon avatar-assistant">⚡</div>
      <div class="bubble">
        ${laymanHtml}
        ${sqlHtml}
        ${effHtml}
        ${tableHtml}
        <div class="meta-bar">
          <span>Rows: ${data.row_count !== null ? data.row_count : (data.data ? data.data.length : 0)}</span>
          <span>Latency: ${data.execution_time_ms ? data.execution_time_ms + 'ms' : 'N/A'}</span>
        </div>
      </div>
    `;
    chatViewport.appendChild(msg);
    chatViewport.scrollTop = chatViewport.scrollHeight;
  }

  function copySql(button, sqlText) {
    navigator.clipboard.writeText(sqlText).then(() => {
      button.innerText = '✓ Copied!';
      setTimeout(() => { button.innerText = '📋 Copy SQL'; }, 2000);
    });
  }

  function sendOptionChoice(optionText) {
    promptInput.value = optionText;
    chatForm.dispatchEvent(new Event('submit'));
  }

  // -------------------------------------------------------------
  // BATTLEGROUND SCRIPTS (LEETCODE TOP 50 SQL)
  // -------------------------------------------------------------
  async function initBattleground() {
    try {
      const res = await fetch('/api/v1/battleground/questions', { headers: getAuthHeader() });
      if (res.ok) {
        allBattlegroundQuestions = await res.json();
        updateProgressBadge();
        if (allBattlegroundQuestions.length > 0) {
          loadProblem(allBattlegroundQuestions[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to load battleground questions:', err);
    }
  }

  async function updateProgressBadge() {
    try {
      const res = await fetch('/api/v1/battleground/progress', { headers: getAuthHeader() });
      if (res.ok) {
        const prog = await res.json();
        document.getElementById('arena-progress-badge').innerText = `🏆 Solved: ${prog.solved_count} / ${prog.total_questions}`;
      }
    } catch {}
  }

  function openProblemCatalog() {
    renderProblemCatalogList();
    document.getElementById('catalog-dialog').showModal();
  }

  function renderProblemCatalogList() {
    const listEl = document.getElementById('catalog-items-list');
    if (!listEl) return;
    if (!allBattlegroundQuestions || allBattlegroundQuestions.length === 0) {
      listEl.innerHTML = '<div style="padding: 2.5rem; color: var(--text-muted); text-align: center;">⏳ Loading challenges from database...</div>';
      initBattleground().then(() => renderProblemCatalogList());
      return;
    }
    const searchVal = (document.getElementById('filter-search')?.value || '').toLowerCase().trim();
    const diffVal = document.getElementById('filter-diff')?.value || '';
    const catVal = document.getElementById('filter-cat')?.value || '';

    const filtered = allBattlegroundQuestions.filter(q => {
      if (diffVal && q.difficulty !== diffVal) return false;
      if (catVal && q.category !== catVal) return false;
      if (searchVal && !q.title.toLowerCase().includes(searchVal) && !q.category.toLowerCase().includes(searchVal)) return false;
      return true;
    });

    if (filtered.length === 0) {
      listEl.innerHTML = '<div style="padding: 2.5rem; color: var(--text-dim); text-align: center;">No challenges match your filters. Try clearing search.</div>';
      return;
    }

    listEl.innerHTML = filtered.map(q => `
      <div class="catalog-item" onclick="selectProblemFromCatalog('${q.id}')">
        <div class="catalog-item-left">
          <span class="catalog-item-num">#${q.number}</span>
          <div style="min-width: 0;">
            <div class="catalog-item-title">${escapeHtml(q.title)}</div>
            <div style="font-size: 0.75rem; color: var(--text-dim); margin-top: 2px;">${escapeHtml(q.category)}</div>
          </div>
          ${q.is_solved ? '<span style="color: var(--success); font-size: 0.9rem;" title="Solved">✅</span>' : ''}
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem; flex-shrink: 0;">
          <span class="diff-badge diff-${q.difficulty}">${q.difficulty}</span>
          <span style="font-size: 0.76rem; color: var(--text-dim);">${q.acceptance_rate}</span>
        </div>
      </div>
    `).join('');
  }

  function selectProblemFromCatalog(problemId) {
    document.getElementById('catalog-dialog').close();
    loadProblem(problemId);
  }

  async function loadProblem(problemId) {
    try {
      const res = await fetch(`/api/v1/battleground/questions/${problemId}`, { headers: getAuthHeader() });
      if (!res.ok) return;
      currentProblem = await res.json();

      document.getElementById('current-q-index').innerText = currentProblem.number;
      document.getElementById('q-title').innerText = `${currentProblem.number}. ${currentProblem.title}`;
      document.getElementById('q-layman-desc').innerText = currentProblem.layman_description;
      document.getElementById('q-tables-used').innerText = currentProblem.tables_used.join(', ');
      document.getElementById('q-acceptance-rate').innerText = `Acceptance: ${currentProblem.acceptance_rate}`;

      const badge = document.getElementById('q-diff-badge');
      badge.className = `diff-badge diff-${currentProblem.difficulty}`;
      badge.innerText = currentProblem.difficulty;
      document.getElementById('q-category-badge').innerText = currentProblem.category;

      document.getElementById('sql-editor').value = currentProblem.starter_code;
      document.getElementById('q-solution-box').style.display = 'none';

      // Clear console
      document.getElementById('console-output').innerHTML = `
        <div style="color: var(--text-dim); text-align: center; padding: 1.5rem;">
          Loaded problem <strong>${escapeHtml(currentProblem.title)}</strong>. Write your solution and click <strong>Run Code</strong>.
        </div>
      `;
    } catch (err) {
      console.error('Error loading problem detail:', err);
    }
  }

  function resetStarterCode() {
    if (currentProblem) {
      document.getElementById('sql-editor').value = currentProblem.starter_code;
      if (window.innerWidth <= 900) switchArenaPane('studio');
    }
  }

  async function runUserCode() {
    if (!currentProblem) return;
    const sql = document.getElementById('sql-editor').value.trim();
    if (!sql) return;

    if (window.innerWidth <= 900) switchArenaPane('studio');

    const consoleEl = document.getElementById('console-output');
    consoleEl.innerHTML = '<div style="color: var(--accent); padding: 1rem;">Executing query against PostgreSQL...</div>';

    try {
      const res = await fetch('/api/v1/battleground/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_id: currentProblem.id, sql: sql })
      });
      const data = await res.json();
      renderConsoleOutput(data, false);
    } catch (err) {
      consoleEl.innerHTML = `<div style="color: var(--danger); padding: 1rem;">Network Error: ${escapeHtml(err.message)}</div>`;
    }
  }

  async function submitUserCode() {
    if (!currentProblem) return;
    const sql = document.getElementById('sql-editor').value.trim();
    if (!sql) return;

    if (window.innerWidth <= 900) switchArenaPane('studio');

    const consoleEl = document.getElementById('console-output');
    consoleEl.innerHTML = '<div style="color: var(--accent); padding: 1rem;">Evaluating test cases and recording submission...</div>';

    try {
      const res = await fetch('/api/v1/battleground/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
        body: JSON.stringify({ question_id: currentProblem.id, sql: sql })
      });
      const data = await res.json();
      renderConsoleOutput(data, true);
      if (data.is_solved) {
        updateProgressBadge();
        initBattleground(); // refresh list
      }
    } catch (err) {
      consoleEl.innerHTML = `<div style="color: var(--danger); padding: 1rem;">Network Error: ${escapeHtml(err.message)}</div>`;
    }
  }

  let activeSidePanelTab = 'hint';
  let lastExecutionError = null;
  let lastSolutionData = null;

  function openAiSidePanel(tab = 'hint', focusError = false) {
    const panel = document.getElementById('ai-side-panel');
    const backdrop = document.getElementById('side-panel-backdrop');
    if (!panel || !backdrop) return;

    panel.classList.add('open');
    backdrop.classList.add('open');

    const errToPass = focusError ? lastExecutionError : null;
    switchPanelTab(tab, errToPass);
  }

  function closeAiSidePanel() {
    const panel = document.getElementById('ai-side-panel');
    const backdrop = document.getElementById('side-panel-backdrop');
    if (panel) panel.classList.remove('open');
    if (backdrop) backdrop.classList.remove('open');
  }

  function switchPanelTab(tab, errorMsg = null) {
    activeSidePanelTab = tab;
    const tabHint = document.getElementById('panel-tab-hint');
    const tabSol = document.getElementById('panel-tab-solution');

    if (tab === 'hint') {
      tabHint.classList.add('active');
      tabSol.classList.remove('active');
      loadAiHint(errorMsg);
    } else {
      tabSol.classList.add('active');
      tabHint.classList.remove('active');
      loadAiSolution();
    }
  }

  async function loadAiHint(errorMessage = null) {
    if (!currentProblem) return;
    const contentEl = document.getElementById('ai-panel-content');
    const userSql = document.getElementById('sql-editor').value;

    contentEl.innerHTML = `
      <div class="ai-loading-spinner">
        <div class="ai-pulse-dot"></div>
        <div>
          <strong style="color: var(--text-main);">Groq AI is analyzing your SQL code...</strong>
          <div style="font-size: 0.78rem; color: var(--text-dim); margin-top: 0.35rem;">Monitoring editor clauses, filter conditions, and potential pitfalls</div>
        </div>
      </div>
    `;

    try {
      const res = await fetch('/api/v1/battleground/hint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_id: currentProblem.id,
          user_sql: userSql,
          error_message: errorMessage || lastExecutionError
        })
      });

      if (!res.ok) {
        throw new Error('Groq AI hint service unavailable');
      }

      const data = await res.json();
      renderHintInPanel(data);
    } catch (err) {
      contentEl.innerHTML = `
        <div class="ai-card" style="border-color: rgba(239, 68, 68, 0.4);">
          <div style="color: var(--danger); font-weight: 700; margin-bottom: 0.5rem;">⚠️ Failed to load AI Hint</div>
          <div style="color: var(--text-muted); font-size: 0.85rem;">${escapeHtml(err.message)}</div>
          <button class="btn-studio-action" style="margin-top: 0.75rem;" onclick="loadAiHint()">🔄 Try Again</button>
        </div>
      `;
    }
  }

  function renderHintInPanel(data) {
    const contentEl = document.getElementById('ai-panel-content');

    let critiqueHtml = '';
    if (data.specific_critique) {
      critiqueHtml = `
        <div class="ai-critique-box">
          <div class="ai-critique-title">🔍 Editor Code Analysis</div>
          <div>${formatMarkdown(data.specific_critique)}</div>
        </div>
      `;
    }

    contentEl.innerHTML = `
      ${critiqueHtml}

      <div class="ai-card">
        <div class="ai-card-header">💡 Smart Hint</div>
        <div style="font-size: 0.92rem; line-height: 1.6;">${formatMarkdown(data.hint)}</div>
      </div>

      <div class="ai-card">
        <div class="ai-card-header">🎯 Intuitive Concept</div>
        <div style="font-size: 0.88rem; line-height: 1.5; color: var(--text-muted);">${formatMarkdown(data.layman_analogy)}</div>
      </div>

      <div class="ai-card">
        <div class="ai-card-header">⚡ Efficiency Pointer</div>
        <div style="font-size: 0.86rem; color: #a7f3d0; line-height: 1.5;">${formatMarkdown(data.efficiency_pointer)}</div>
      </div>

      <button class="btn-studio-action" style="width: 100%; justify-content: center; padding: 0.6rem; font-weight: 600;" onclick="loadAiHint()">
        🔄 Re-analyze Editor with Groq AI
      </button>
    `;
  }

  async function loadAiSolution() {
    if (!currentProblem) return;
    const contentEl = document.getElementById('ai-panel-content');
    const userSql = document.getElementById('sql-editor').value;

    contentEl.innerHTML = `
      <div class="ai-loading-spinner">
        <div class="ai-pulse-dot"></div>
        <div>
          <strong style="color: var(--text-main);">Groq AI is preparing the solution walkthrough...</strong>
          <div style="font-size: 0.78rem; color: var(--text-dim); margin-top: 0.35rem;">Structuring optimal PostgreSQL syntax and efficiency breakdown</div>
        </div>
      </div>
    `;

    try {
      const res = await fetch('/api/v1/battleground/solution', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_id: currentProblem.id,
          user_sql: userSql
        })
      });

      if (!res.ok) {
        throw new Error('Groq AI solution service unavailable');
      }

      const data = await res.json();
      lastSolutionData = data;
      renderSolutionInPanel(data);
    } catch (err) {
      contentEl.innerHTML = `
        <div class="ai-card" style="border-color: rgba(239, 68, 68, 0.4);">
          <div style="color: var(--danger); font-weight: 700; margin-bottom: 0.5rem;">⚠️ Failed to load Solution</div>
          <div style="color: var(--text-muted); font-size: 0.85rem;">${escapeHtml(err.message)}</div>
          <button class="btn-studio-action" style="margin-top: 0.75rem;" onclick="loadAiSolution()">🔄 Try Again</button>
        </div>
      `;
    }
  }

  function renderSolutionInPanel(data) {
    const contentEl = document.getElementById('ai-panel-content');
    const escapedSql = escapeHtml(data.sql);

    contentEl.innerHTML = `
      <div class="ai-card">
        <div class="ai-card-header">🎓 Step-by-Step Logic Breakdown</div>
        <div style="font-size: 0.9rem; line-height: 1.6;">${formatMarkdown(data.explanation)}</div>
      </div>

      <div class="sql-box" style="margin: 0;">
        <div class="sql-box-header">
          <span>Verified Solution Query</span>
          <button class="btn-copy-sql" onclick="copyCurrentSolution(this)">📋 Copy SQL</button>
        </div>
        <div class="sql-code-text">${escapedSql}</div>
      </div>

      <button class="btn-apply-solution" style="width: 100%; justify-content: center; padding: 0.65rem;" onclick="insertSolutionIntoEditor()">
        🚀 Insert Solution into Editor
      </button>

      <div class="efficiency-grid" style="margin: 0;">
        <div class="efficiency-card card-time">
          <div class="eff-title">🚀 Time Optimization</div>
          <div style="font-size: 0.84rem;">${formatMarkdown(data.time_efficiency_tip)}</div>
        </div>
        <div class="efficiency-card card-memory">
          <div class="eff-title">💾 Memory Optimization</div>
          <div style="font-size: 0.84rem;">${formatMarkdown(data.memory_efficiency_tip)}</div>
        </div>
      </div>
    `;
  }

  function insertSolutionIntoEditor() {
    if (!lastSolutionData || !lastSolutionData.sql) return;
    const editor = document.getElementById('sql-editor');
    if (!editor) return;
    editor.value = lastSolutionData.sql.trim() + '\n';
    editor.focus();
    closeAiSidePanel();
    if (window.innerWidth <= 900) switchArenaPane('studio');
  }

  function copyCurrentSolution(btn) {
    if (!lastSolutionData || !lastSolutionData.sql) return;
    copySql(btn, lastSolutionData.sql);
  }

  function renderConsoleOutput(data, isSubmission) {
    const consoleEl = document.getElementById('console-output');
    let statusClass = 'status-pill-wrong';
    let icon = '❌';

    if (data.status === 'Accepted') {
      statusClass = 'status-pill-accepted';
      icon = '✅';
      lastExecutionError = null;
    } else if (data.status === 'Runtime Error') {
      statusClass = 'status-pill-error';
      icon = '⚠️';
      lastExecutionError = data.error || data.message;
    } else {
      lastExecutionError = data.error || data.message || 'Query result did not match expected test case';
    }

    let tablesDiffHtml = '';
    if (data.user_data && data.expected_data) {
      tablesDiffHtml = `
        <div class="console-diff-grid">
          <div>
            <div style="font-weight: 700; color: var(--accent); margin-bottom: 0.35rem; font-size: 0.82rem;">Your Output (${data.user_data.length} rows):</div>
            ${renderMiniTable(data.user_columns, data.user_data)}
          </div>
          <div>
            <div style="font-weight: 700; color: var(--success); margin-bottom: 0.35rem; font-size: 0.82rem;">Expected Output (${data.expected_data.length} rows):</div>
            ${renderMiniTable(data.expected_columns, data.expected_data)}
          </div>
        </div>
      `;
    }

    let askAiErrorBtn = '';
    if (data.status === 'Runtime Error' || data.status === 'Wrong Answer') {
      askAiErrorBtn = `
        <button class="btn-ask-ai-error" onclick="openAiSidePanel('hint', true)">
          ✨ Ask Groq AI to Diagnose & Fix This Error ➔
        </button>
      `;
    }

    consoleEl.innerHTML = `
      <div>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem; gap: 0.5rem; flex-wrap: wrap;">
          <span class="${statusClass}" style="font-size: 0.95rem;">${icon} ${data.status}</span>
          <span style="font-size: 0.75rem; color: var(--text-dim);">Latency: ${data.execution_time_ms}ms</span>
        </div>
        <div style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">${escapeHtml(data.message)}</div>
        ${data.error ? `<div style="background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); padding: 0.6rem; border-radius: 6px; color: #fca5a5; font-family: monospace; font-size: 0.8rem; word-break: break-word;">${escapeHtml(data.error)}</div>` : ''}
        ${askAiErrorBtn}
        ${tablesDiffHtml}
      </div>
    `;
  }

  function renderMiniTable(cols, rows) {
    if (!cols || !rows || rows.length === 0) {
      return '<div style="color: var(--text-dim); font-size: 0.78rem;">Empty result set.</div>';
    }
    const headers = cols.map(c => `<th>${escapeHtml(c)}</th>`).join('');
    const bodyRows = rows.slice(0, 5).map(r => {
      const cells = r.map(c => `<td>${escapeHtml(String(c !== null ? c : 'NULL'))}</td>`).join('');
      return `<tr>${cells}</tr>`;
    }).join('');

    return `
      <div class="table-container" style="max-height: 140px;">
        <table><thead><tr>${headers}</tr></thead><tbody>${bodyRows}</tbody></table>
      </div>
    `;
  }

  // Close side panel and dialogs on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const panel = document.getElementById('ai-side-panel');
      if (panel && panel.classList.contains('open')) {
        closeAiSidePanel();
      }
    }
  });

  // Close dialogs on outside backdrop click
  ['catalog-dialog', 'auth-dialog'].forEach(id => {
    const dlg = document.getElementById(id);
    if (!dlg) return;
    dlg.addEventListener('click', (e) => {
      const rect = dlg.getBoundingClientRect();
      const isInDialog = (
        rect.top <= e.clientY &&
        e.clientY <= rect.top + rect.height &&
        rect.left <= e.clientX &&
        e.clientX <= rect.left + rect.width
      );
      if (!isInDialog) dlg.close();
    });
  });

  // =============================================================
  // ADMIN & CSV INGESTION STUDIO LOGIC
  // =============================================================
  let selectedAdminFile = null;
  let adminPreviewData = null;
  let lastIngestedTable = null;

  function handleAdminDragOver(e) {
    e.preventDefault();
    const zone = document.getElementById('admin-dropzone');
    if (zone) zone.classList.add('dragover');
  }

  function handleAdminDragLeave(e) {
    e.preventDefault();
    const zone = document.getElementById('admin-dropzone');
    if (zone) zone.classList.remove('dragover');
  }

  function handleAdminDrop(e) {
    e.preventDefault();
    const zone = document.getElementById('admin-dropzone');
    if (zone) zone.classList.remove('dragover');
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processAdminFile(e.dataTransfer.files[0]);
    }
  }

  function handleAdminFileSelected(e) {
    if (e.target && e.target.files && e.target.files.length > 0) {
      processAdminFile(e.target.files[0]);
    }
  }

  function resetAdminFile(e) {
    if (e) e.stopPropagation();
    selectedAdminFile = null;
    adminPreviewData = null;
    const fileInput = document.getElementById('admin-csv-file');
    if (fileInput) fileInput.value = '';
    const badge = document.getElementById('admin-file-badge');
    if (badge) badge.style.display = 'none';
    const previewCard = document.getElementById('schema-preview-card');
    if (previewCard) previewCard.style.display = 'none';
    const successAlert = document.getElementById('admin-alert-success');
    if (successAlert) successAlert.style.display = 'none';
    const errorAlert = document.getElementById('admin-alert-error');
    if (errorAlert) errorAlert.style.display = 'none';
  }

  async function processAdminFile(file, sheetName = null) {
    const fn = file.name.toLowerCase();
    const isCsv = fn.endsWith('.csv');
    const isExcel = fn.endsWith('.xlsx') || fn.endsWith('.xls') || fn.endsWith('.xlsm');
    if (!isCsv && !isExcel) {
      alert('Please select a valid CSV (.csv) or Excel (.xlsx, .xls) file.');
      return;
    }
    selectedAdminFile = file;

    // Show badge
    const badge = document.getElementById('admin-file-badge');
    const badgeName = document.getElementById('badge-filename');
    const badgeSize = document.getElementById('badge-filesize');
    const badgeIcon = document.getElementById('badge-file-icon');
    if (badge && badgeName && badgeSize) {
      badgeName.textContent = file.name;
      const kb = (file.size / 1024).toFixed(1);
      badgeSize.textContent = `${kb} KB`;
      if (badgeIcon) badgeIcon.textContent = isExcel ? '📗' : '📊';
      badge.style.display = 'flex';
    }

    // Hide old alerts
    const successAlert = document.getElementById('admin-alert-success');
    if (successAlert) successAlert.style.display = 'none';
    const errorAlert = document.getElementById('admin-alert-error');
    if (errorAlert) errorAlert.style.display = 'none';

    // Call preview API
    const formData = new FormData();
    formData.append('file', file);
    if (sheetName) {
      formData.append('sheet_name', sheetName);
    }

    try {
      const res = await fetch('/api/v1/admin/preview-csv', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Failed to inspect dataset schema.');
      }

      adminPreviewData = await res.json();
      renderSchemaPreview(adminPreviewData);
    } catch (err) {
      console.error('Error previewing file:', err);
      const errorAlert = document.getElementById('admin-alert-error');
      const errorText = document.getElementById('alert-error-text');
      if (errorAlert && errorText) {
        errorText.textContent = `❌ ${err.message}`;
        errorAlert.style.display = 'flex';
      }
    }
  }

  function renderSchemaPreview(data) {
    const tableInput = document.getElementById('admin-table-name');
    if (tableInput) {
      tableInput.value = data.suggested_table_name;
    }

    const metrics = document.getElementById('preview-metrics');
    if (metrics) {
      const sheetInfo = data.active_sheet ? ` · Sheet: "${data.active_sheet}"` : '';
      metrics.textContent = `Detected ${data.total_columns} columns · ~${data.estimated_rows.toLocaleString()} rows${sheetInfo}`;
    }

    // Multi-sheet bar & Batch Button
    const sheetsBar = document.getElementById('excel-sheets-bar');
    const sheetsPills = document.getElementById('excel-sheets-pills');
    const btnAllSheets = document.getElementById('btn-run-all-sheets');

    if (data.is_excel && data.sheet_names && data.sheet_names.length > 1) {
      if (sheetsBar && sheetsPills) {
        sheetsPills.innerHTML = '';
        data.sheet_names.forEach(sheet => {
          const btn = document.createElement('button');
          const isActive = sheet === data.active_sheet;
          btn.className = 'btn-studio-action';
          btn.style.cssText = isActive
            ? 'background: var(--accent); color: #0b0f19; font-weight: 700; border-color: var(--accent);'
            : 'background: var(--bg-elevated); color: var(--text-muted); border-color: var(--border-color);';
          btn.textContent = `📄 ${sheet}`;
          btn.onclick = () => processAdminFile(selectedAdminFile, sheet);
          sheetsPills.appendChild(btn);
        });
        sheetsBar.style.display = 'flex';
      }
      if (btnAllSheets) {
        btnAllSheets.style.display = 'inline-flex';
        btnAllSheets.innerHTML = `<span>📦</span> Ingest ALL ${data.sheet_names.length} Sheets (Multiple Tables)`;
      }
    } else {
      if (sheetsBar) sheetsBar.style.display = 'none';
      if (btnAllSheets) btnAllSheets.style.display = 'none';
    }

    // Populate Schema Mapping Table
    const tbody = document.getElementById('preview-schema-tbody');
    if (tbody) {
      tbody.innerHTML = '';
      const supportedTypes = data.supported_types || ['TEXT', 'INTEGER', 'BIGINT', 'NUMERIC', 'BOOLEAN', 'DATE', 'TIMESTAMPTZ', 'UUID', 'JSONB'];

      data.columns.forEach((col) => {
        const tr = document.createElement('tr');

        // Sample value
        let sampleVal = '';
        if (data.sample_rows && data.sample_rows.length > 0) {
          sampleVal = data.sample_rows[0][col.sanitized_name] ?? '';
        }

        let selectHtml = `<select class="type-select" data-col="${col.sanitized_name}">`;
        supportedTypes.forEach(t => {
          const selected = t === col.inferred_type ? 'selected' : '';
          selectHtml += `<option value="${t}" ${selected}>${t}</option>`;
        });
        selectHtml += '</select>';

        tr.innerHTML = `
          <td style="color: var(--text-dim);">${col.original_name}</td>
          <td><code style="color: var(--accent); font-weight: 600;">${col.sanitized_name}</code></td>
          <td>${selectHtml}</td>
          <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: monospace; font-size: 0.75rem; color: var(--text-muted);">${sampleVal}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    // Populate Top 5 Sample Rows Table
    const dataTable = document.getElementById('preview-data-table');
    if (dataTable && data.sample_rows && data.sample_rows.length > 0) {
      const colNames = data.columns.map(c => c.sanitized_name);
      let theadHtml = '<thead><tr>' + colNames.map(c => `<th>${c}</th>`).join('') + '</tr></thead>';
      let tbodyHtml = '<tbody>';
      data.sample_rows.forEach(row => {
        tbodyHtml += '<tr>';
        colNames.forEach(c => {
          tbodyHtml += `<td style="font-family: monospace; font-size: 0.75rem;">${row[c] ?? ''}</td>`;
        });
        tbodyHtml += '</tr>';
      });
      tbodyHtml += '</tbody>';
      dataTable.innerHTML = theadHtml + tbodyHtml;
    }

    const previewCard = document.getElementById('schema-preview-card');
    if (previewCard) previewCard.style.display = 'flex';
  }

  async function executeAllSheetsIngestion() {
    if (!selectedAdminFile) {
      alert('Please select an Excel file first.');
      return;
    }

    const dbInput = document.getElementById('admin-db-name');
    const modeRadio = document.querySelector('input[name="admin-mode"]:checked');
    const dbName = dbInput ? dbInput.value.trim() : 'e-commerce';
    const mode = modeRadio ? modeRadio.value : 'replace';

    const runBtn = document.getElementById('btn-run-ingest');
    const btnAllSheets = document.getElementById('btn-run-all-sheets');
    const spinnerMsg = document.getElementById('ingest-spinner-msg');
    const successAlert = document.getElementById('admin-alert-success');
    const errorAlert = document.getElementById('admin-alert-error');

    if (runBtn) runBtn.disabled = true;
    if (btnAllSheets) btnAllSheets.disabled = true;
    if (spinnerMsg) {
      spinnerMsg.textContent = '⏳ Batch streaming all Excel sheets into PostgreSQL tables...';
      spinnerMsg.style.display = 'block';
    }
    if (successAlert) successAlert.style.display = 'none';
    if (errorAlert) errorAlert.style.display = 'none';

    const formData = new FormData();
    formData.append('file', selectedAdminFile);
    formData.append('db_name', dbName);
    formData.append('mode', mode);

    try {
      const res = await fetch('/api/v1/admin/import-all-sheets', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Batch ingestion failed.');
      }

      const result = await res.json();
      lastIngestedTable = result.tables.length > 0 ? result.tables[0].table : null;

      if (successAlert) {
        const succText = document.getElementById('alert-success-text');
        if (succText) {
          const tableSummaries = result.tables.map(t => `${t.table} (${t.rows_inserted.toLocaleString()} rows)`).join(', ');
          succText.textContent = `🎉 Batch Ingestion Complete! Successfully created ${result.tables.length} tables [${tableSummaries}] in database "${result.database}" (${result.total_rows_inserted.toLocaleString()} total rows).`;
        }
        successAlert.style.display = 'flex';
      }

      loadAdminTables();
      if (typeof fetchSchemaOverview === 'function') {
        fetchSchemaOverview();
      }
    } catch (err) {
      console.error('Batch ingestion error:', err);
      if (errorAlert) {
        const errorText = document.getElementById('alert-error-text');
        if (errorText) errorText.textContent = `❌ ${err.message}`;
        errorAlert.style.display = 'flex';
      }
    } finally {
      if (runBtn) runBtn.disabled = false;
      if (btnAllSheets) btnAllSheets.disabled = false;
      if (spinnerMsg) spinnerMsg.style.display = 'none';
    }
  }

  async function executeCsvIngestion() {
    if (!selectedAdminFile) {
      alert('Please select a CSV or Excel file first.');
      return;
    }

    const dbInput = document.getElementById('admin-db-name');
    const tableInput = document.getElementById('admin-table-name');
    const modeRadio = document.querySelector('input[name="admin-mode"]:checked');

    const dbName = dbInput ? dbInput.value.trim() : 'e-commerce';
    const tableName = tableInput ? tableInput.value.trim() : '';
    const mode = modeRadio ? modeRadio.value : 'replace';

    if (!tableName) {
      alert('Please specify a target table name.');
      if (tableInput) tableInput.focus();
      return;
    }

    // Collect custom/inferred column types
    const typeSelects = document.querySelectorAll('.type-select');
    const customTypes = {};
    typeSelects.forEach(s => {
      const col = s.getAttribute('data-col');
      if (col) customTypes[col] = s.value;
    });

    const runBtn = document.getElementById('btn-run-ingest');
    const btnAllSheets = document.getElementById('btn-run-all-sheets');
    const spinnerMsg = document.getElementById('ingest-spinner-msg');
    const successAlert = document.getElementById('admin-alert-success');
    const errorAlert = document.getElementById('admin-alert-error');

    if (runBtn) runBtn.disabled = true;
    if (btnAllSheets) btnAllSheets.disabled = true;
    if (spinnerMsg) {
      spinnerMsg.textContent = '⏳ Ingesting rows into PostgreSQL via streaming COPY...';
      spinnerMsg.style.display = 'block';
    }
    if (successAlert) successAlert.style.display = 'none';
    if (errorAlert) errorAlert.style.display = 'none';

    const formData = new FormData();
    formData.append('file', selectedAdminFile);
    formData.append('db_name', dbName);
    formData.append('table_name', tableName);
    formData.append('mode', mode);
    formData.append('column_types', JSON.stringify(customTypes));
    if (adminPreviewData && adminPreviewData.active_sheet) {
      formData.append('sheet_name', adminPreviewData.active_sheet);
    }

    try {
      const res = await fetch('/api/v1/admin/import-csv', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Ingestion failed on database server.');
      }

      const result = await res.json();
      lastIngestedTable = result.table;

      // Show success
      if (successAlert) {
        const succText = document.getElementById('alert-success-text');
        if (succText) {
          succText.textContent = `🎉 Ingestion Complete! Successfully streamed ${result.rows_inserted.toLocaleString()} rows into "${result.database}.${result.table}".`;
        }
        successAlert.style.display = 'flex';
      }

      // Refresh tables list
      loadAdminTables();

      // Trigger schema cache refresh on server
      if (typeof fetchSchemaOverview === 'function') {
        fetchSchemaOverview();
      }
    } catch (err) {
      console.error('Ingestion error:', err);
      if (errorAlert) {
        const errorText = document.getElementById('alert-error-text');
        if (errorText) errorText.textContent = `❌ ${err.message}`;
        errorAlert.style.display = 'flex';
      }
    } finally {
      if (runBtn) runBtn.disabled = false;
      if (spinnerMsg) spinnerMsg.style.display = 'none';
    }
  }

  function openChatWithNewTable(tableName) {
    const targetTable = tableName || lastIngestedTable || 'the new table';
    switchView('chat');
    const input = document.getElementById('prompt-input');
    if (input) {
      input.value = `Show the first 5 records from ${targetTable}`;
      input.focus();
    }
  }

  async function loadAdminTables() {
    const tbody = document.getElementById('admin-tables-tbody');
    const activeDbLabel = document.getElementById('active-db-label');
    const dbInput = document.getElementById('admin-db-name');
    if (activeDbLabel && dbInput && dbInput.value) {
      activeDbLabel.textContent = dbInput.value;
    }

    try {
      const res = await fetch('/api/v1/admin/tables');
      if (!res.ok) return;
      const tables = await res.json();

      if (!tbody) return;
      tbody.innerHTML = '';

      if (tables.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-dim); padding: 1rem;">No tables found in public schema.</td></tr>';
        return;
      }

      tables.forEach(t => {
        const tr = document.createElement('tr');
        const colList = t.columns.map(c => `<span style="display: inline-block; background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: 4px; padding: 1px 5px; margin: 1px; font-size: 0.72rem; color: var(--text-muted); font-family: monospace;">${c}</span>`).join(' ');

        tr.innerHTML = `
          <td><strong style="color: var(--accent);">${t.table_name}</strong></td>
          <td><span style="background: rgba(16, 185, 129, 0.15); color: #34d399; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">${t.row_count.toLocaleString()} rows</span></td>
          <td style="max-width: 450px; overflow-x: auto;">${colList}</td>
          <td>
            <button class="btn-studio-action" style="padding: 0.25rem 0.6rem; font-size: 0.75rem;" onclick="openChatWithNewTable('${t.table_name}')">💬 Query</button>
          </td>
        `;
        tbody.appendChild(tr);
      });
    } catch (err) {
      console.warn('Failed to load tables list:', err);
    }
  }

  // Initialize
  checkCurrentUser();
  initBattleground();
</script>

</body>
</html>
"""


def render_chat_page() -> HTMLResponse:
    """Returns the rendered Text-to-SQL modern chat UI."""
    return HTMLResponse(content=CHAT_HTML_CONTENT, status_code=200)


def get_chat_html_response() -> HTMLResponse:
    """Convenience wrapper for backward compatibility."""
    return render_chat_page()
