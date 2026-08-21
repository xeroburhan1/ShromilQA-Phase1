import { useEffect, useRef, useState } from "react";
import { AnimatePresence } from "framer-motion";
import Sidebar from "./components/Sidebar";
import ChatHeader from "./components/ChatHeader";
import MessageBubble from "./components/MessageBubble";
import TypingIndicator from "./components/TypingIndicator";
import EmptyState from "./components/EmptyState";
import ChatInput from "./components/ChatInput";
import SectionModal from "./components/SectionModal";
import { chatApi } from "./api/chatApi";
import "./App.css";

const LAST_SESSION_KEY = "shromikqa:lastSessionId";

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(
    localStorage.getItem(LAST_SESSION_KEY) || null
  );
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedSection, setSelectedSection] = useState(null);

  const scrollRef = useRef(null);

  // Load the session list once on mount.
  useEffect(() => {
    chatApi
      .listSessions()
      .then(setSessions)
      .catch(() => setSessions([]));
  }, []);

  // Whenever the active session changes, load its messages (if any).
  useEffect(() => {
    if (!activeSessionId) {
      setMessages([]);
      return;
    }
    localStorage.setItem(LAST_SESSION_KEY, activeSessionId);
    chatApi
      .getSession(activeSessionId)
      .then((s) => setMessages(s.messages))
      .catch(() => {
        // Session may no longer exist server-side; start fresh.
        setActiveSessionId(null);
        localStorage.removeItem(LAST_SESSION_KEY);
      });
  }, [activeSessionId]);

  // Auto-scroll to latest message.
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isSending]);

  async function handleSend(text) {
    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { id: `local-${Date.now()}`, role: "user", content: text }]);
    setIsSending(true);

    try {
      const res = await chatApi.sendMessage(text, activeSessionId);
      setMessages((prev) => [...prev, res.reply]);

      if (!activeSessionId) {
        setActiveSessionId(res.session_id);
      }
      const updated = await chatApi.listSessions();
      setSessions(updated);
    } catch (err) {
      setError(err.message || "Something went wrong reaching Shromik QA.");
    } finally {
      setIsSending(false);
    }
  }

  function handleNewChat() {
    setActiveSessionId(null);
    localStorage.removeItem(LAST_SESSION_KEY);
    setMessages([]);
    setError(null);
    setSidebarOpen(false);
  }

  function handleSelectSession(id) {
    setActiveSessionId(id);
    setSidebarOpen(false);
  }

  async function handleDeleteSession(id) {
    await chatApi.deleteSession(id).catch(() => {});
    setSessions((prev) => prev.filter((s) => s.id !== id));
    if (id === activeSessionId) {
      handleNewChat();
    }
  }

  async function handleSelectSection(citation) {
    if (citation.text) {
      setSelectedSection(citation);
      return;
    }

    try {
      const data = await chatApi.getSection(citation.section);
      setSelectedSection(data);
    } catch (err) {
      setSelectedSection({ section: citation.section, title: citation.title, text: "Section content not available." });
    }
  }

  const activeTitle = sessions.find((s) => s.id === activeSessionId)?.title;

  return (
    <div className="app">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="chat-panel">
        <ChatHeader title={activeTitle} onMenuClick={() => setSidebarOpen((v) => !v)} onNewChat={handleNewChat} />

        <div className="chat-scroll" ref={scrollRef}>
          {messages.length === 0 ? (
            <EmptyState onPick={handleSend} />
          ) : (
            <div className="chat-messages">
              <AnimatePresence initial={false}>
                {messages.map((m) => (
                  <MessageBubble
                    key={m.id}
                    role={m.role}
                    content={m.content}
                    citations={m.citations}
                    onSelectSection={handleSelectSection}
                  />
                ))}
                {isSending && <TypingIndicator key="typing" />}
                {error && (
                  <MessageBubble key="error" role="assistant" isError content={`⚠️ ${error}`} />
                )}
              </AnimatePresence>
            </div>
          )}
        </div>

        <ChatInput value={input} onChange={setInput} onSend={handleSend} disabled={isSending} />
      </main>

      <SectionModal section={selectedSection} onClose={() => setSelectedSection(null)} />
    </div>
  );
}
