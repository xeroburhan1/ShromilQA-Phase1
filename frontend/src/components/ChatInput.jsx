import { useRef } from "react";
import { motion } from "framer-motion";
import "./ChatInput.css";

export default function ChatInput({ value, onChange, onSend, disabled }) {
  const textareaRef = useRef(null);

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function handleInput(e) {
    onChange(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 160) + "px";
    }
  }

  function submit() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }

  return (
    <div className="chat-input">
      <div className="chat-input__box">
        <textarea
          ref={textareaRef}
          className="chat-input__textarea"
          placeholder="Message Shromik QA..."
          rows={1}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
        />
        <motion.button
          className="chat-input__send"
          whileTap={{ scale: 0.9 }}
          disabled={!value.trim() || disabled}
          onClick={submit}
          aria-label="Send message"
        >
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
            <path
              d="M4 12L20 4L14 20L11 13L4 12Z"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          </svg>
        </motion.button>
      </div>
    </div>
  );
}
