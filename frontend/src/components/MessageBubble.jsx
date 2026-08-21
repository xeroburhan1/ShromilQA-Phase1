import { useState } from "react";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Seal from "./Seal";
import "./MessageBubble.css";

/**
 * Pre-processes markdown text from LLM to ensure tables and linebreaks
 * are correctly formatted for Markdown parsing.
 */
function preprocessMarkdown(text) {
  if (!text) return "";
  let formatted = String(text);

  // Unescape double-escaped newlines if present
  formatted = formatted.replace(/\\n/g, "\n");

  // Fix tables where pipe separators missing newlines: e.g., "|| |---" -> "|\n|---"
  formatted = formatted.replace(/\|\|\s*\|/g, "|\n|");

  // Ensure double newline around markdown tables for GFM parser
  formatted = formatted.replace(/([^\n])\n(\|[^\n]+\|\n\|[\s:-|-]+\|)/g, "$1\n\n$2");

  return formatted;
}

/**
 * Custom Code Block Component with Header and Copy Code button
 */
function CodeBlock({ inline, className, children, ...props }) {
  const [copied, setCopied] = useState(false);
  const match = /language-(\w+)/.exec(className || "");
  const language = match ? match[1] : "";
  const codeString = String(children).replace(/\n$/, "");

  if (inline || !className) {
    return (
      <code className="inline-code" {...props}>
        {children}
      </code>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(codeString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="code-block-container">
      <div className="code-block-header">
        <span className="code-block-lang">{language || "code"}</span>
        <button className="code-block-copy" onClick={handleCopy} title="Copy code">
          {copied ? (
            <>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
              <span>Copied!</span>
            </>
          ) : (
            <>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              <span>Copy code</span>
            </>
          )}
        </button>
      </div>
      <pre className="code-block-pre">
        <code className={className} {...props}>
          {children}
        </code>
      </pre>
    </div>
  );
}

/**
 * Custom Table Renderer with responsive scrolling wrapper
 */
function TableRenderer({ children }) {
  return (
    <div className="markdown-table-wrapper">
      <table className="markdown-table">{children}</table>
    </div>
  );
}

export default function MessageBubble({ role, content, isError, citations, onSelectSection }) {
  const isUser = role === "user";
  const [copiedReply, setCopiedReply] = useState(false);

  const hasContent = content && String(content).trim().length > 0;
  const rawContent = hasContent
    ? content
    : isUser
    ? ""
    : "⚠️ *(No response text returned. Please try rephrasing your question.)*";

  const processedContent = isUser ? rawContent : preprocessMarkdown(rawContent);

  const handleCopyReply = () => {
    if (!content) return;
    navigator.clipboard.writeText(content);
    setCopiedReply(true);
    setTimeout(() => setCopiedReply(false), 2000);
  };

  return (
    <motion.div
      className={`bubble-row ${isUser ? "bubble-row--user" : ""}`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.24, ease: "easeOut" }}
    >
      {!isUser && (
        <div className="bubble-avatar" title="Shromik QA AI Assistant">
          <Seal size={28} />
        </div>
      )}

      <div className={`bubble-col ${isUser ? "bubble-col--user" : ""}`}>
        <div className={`bubble ${isUser ? "bubble--user" : "bubble--bot"} ${isError ? "bubble--error" : ""}`}>
          <div className="bubble__content">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code: CodeBlock,
                table: TableRenderer,
                a: ({ href, children }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer">
                    {children}
                  </a>
                ),
              }}
            >
              {processedContent}
            </ReactMarkdown>
          </div>
        </div>

        {!isUser && !isError && (
          <div className="message-toolbar">
            <button className="copy-reply-btn" onClick={handleCopyReply} title="Copy response">
              {copiedReply ? (
                <>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
        )}

        {!isUser && citations && citations.length > 0 && (
          <div className="citation-row">
            <span className="citation-label">Sources:</span>
            {citations.map((c) => (
              <button
                key={c.section}
                className="citation-chip"
                title={c.title ? `${c.title} — Click to view full section` : "Click to view full section"}
                onClick={() => onSelectSection && onSelectSection(c)}
              >
                Section {c.section}
              </button>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
