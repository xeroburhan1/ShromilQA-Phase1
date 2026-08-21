import { motion, AnimatePresence } from "framer-motion";
import Seal from "./Seal";
import "./Sidebar.css";

function formatDate(iso) {
  const d = new Date(iso);
  const today = new Date();
  const isToday = d.toDateString() === today.toDateString();
  if (isToday) {
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}

export default function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  isOpen,
  onClose,
}) {
  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="sidebar-scrim"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
        )}
      </AnimatePresence>

      <aside className={`sidebar ${isOpen ? "sidebar--open" : ""}`}>
        <div className="sidebar__brand" onClick={onNewChat} style={{ cursor: 'pointer' }}>
          <Seal size={34} />
          <div>
            <div className="sidebar__brand-name">Shromik QA</div>
            <div className="sidebar__brand-tag">Labour Law Assistant</div>
          </div>
        </div>

        <button className="sidebar__new-chat" onClick={onNewChat}>
          <svg className="sidebar__icon" width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
            <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          New chat
        </button>

        <div className="sidebar__section-label">Recent</div>

        <nav className="sidebar__history">
          <AnimatePresence initial={false}>
            {sessions.map((s) => (
              <motion.div
                key={s.id}
                layout
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                transition={{ duration: 0.18 }}
                className={`sidebar__item ${
                  s.id === activeSessionId ? "sidebar__item--active" : ""
                }`}
                onClick={() => onSelectSession(s.id)}
              >
                <span className="sidebar__item-title">{s.title || "New chat"}</span>
                <span className="sidebar__item-date">{formatDate(s.updated_at)}</span>
                <button
                  className="sidebar__item-delete"
                  title="Delete chat"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(s.id);
                  }}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden>
                    <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
              </motion.div>
            ))}
          </AnimatePresence>

          {sessions.length === 0 && (
            <div className="sidebar__empty">No conversations yet</div>
          )}
        </nav>
      </aside>
    </>
  );
}
