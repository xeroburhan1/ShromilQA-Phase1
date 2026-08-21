import Seal from "./Seal";
import "./ChatHeader.css";

export default function ChatHeader({ title, onMenuClick, onNewChat }) {
  return (
    <header className="chat-header">
      <button className="chat-header__menu" onClick={onMenuClick} aria-label="Toggle history">
        <span />
        <span />
        <span />
      </button>

      <div className="chat-header__identity">
        <button className="chat-header__logo" title="New chat" aria-label="New chat" onClick={onNewChat}>
          <Seal size={34} />
        </button>
        <div>
          <div className="chat-header__title">{title || "Shromik QA"}</div>
          <div className="chat-header__subtitle">Bangladesh Labour Law Assistant</div>
        </div>
      </div>

      <div className="chat-header__badge" title="Answers are grounded in Sections 1-354 (Chapters I-XXI) of the Act">
        Based on Bangladesh Labour Act 2006
      </div>
    </header>
  );
}
