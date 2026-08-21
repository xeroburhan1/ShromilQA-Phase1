import { motion } from "framer-motion";
import Seal from "./Seal";
import "./EmptyState.css";

const SUGGESTIONS = [
  "What can you do?",
  "Why should I trust you?",
  "What's the notice period for terminating a permanent worker?",
  "What is a woman worker entitled to around childbirth?",
];

export default function EmptyState({ onPick }) {
  return (
    <motion.div
      className="empty-state"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
    >
      <div className="empty-state__seal">
        <Seal size={52} />
      </div>
      <h1 className="empty-state__title">Hi, I'm Shromik QA.</h1>
      <p className="empty-state__subtitle">
        Ask me about the Bangladesh Labour Act 2006 — leave, wages, working
        hours, termination, safety, trade unions, dispute resolution, and more. Shromik QA cites the exact section behind every
        answer across all 354 sections (Chapters I-XXI).
      </p>

      <div className="empty-state__chips">
        {SUGGESTIONS.map((s) => (
          <button key={s} className="empty-state__chip" onClick={() => onPick(s)}>
            {s}
          </button>
        ))}
      </div>
    </motion.div>
  );
}
