import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import Seal from "./Seal";
import "./MessageBubble.css";

export default function MessageBubble({ role, content, isError, citations, onSelectSection }) {
  const isUser = role === "user";

  return (
    <motion.div
      className={`bubble-row ${isUser ? "bubble-row--user" : ""}`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, ease: "easeOut" }}
    >
      {!isUser && (
        <div className="bubble-avatar">
          <Seal size={26} />
        </div>
      )}

      <div className={`bubble-col ${isUser ? "bubble-col--user" : ""}`}>
        <div className={`bubble ${isUser ? "bubble--user" : "bubble--bot"} ${isError ? "bubble--error" : ""}`}>
          <div className="bubble__content">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        </div>

        {!isUser && citations && citations.length > 0 && (
          <div className="citation-row">
            {citations.map((c) => (
              <button
                key={c.section}
                className="citation-chip"
                title={c.title ? `${c.title} — Click to view full section` : "Click to view full section"}
                onClick={() => onSelectSection && onSelectSection(c)}
              >
                Section - {c.section}
              </button>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
