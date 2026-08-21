import { motion } from "framer-motion";
import Seal from "./Seal";
import "./MessageBubble.css";
import "./TypingIndicator.css";

export default function TypingIndicator() {
  return (
    <motion.div
      className="bubble-row"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <div className="bubble-avatar">
        <Seal size={26} />
      </div>
      <div className="bubble bubble--bot typing-bubble">
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </div>
    </motion.div>
  );
}
