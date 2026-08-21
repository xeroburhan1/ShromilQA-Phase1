import { motion, AnimatePresence } from "framer-motion";
import "./SectionModal.css";

export default function SectionModal({ section, onClose }) {
  if (!section) return null;

  return (
    <AnimatePresence>
      <div className="modal-backdrop" onClick={onClose}>
        <motion.div
          className="section-modal"
          onClick={(e) => e.stopPropagation()}
          initial={{ opacity: 0, scale: 0.94, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.94, y: 15 }}
          transition={{ duration: 0.22, ease: "easeOut" }}
        >
          <div className="section-modal__header">
            <div className="section-modal__badge">
              {section.chapter || "Bangladesh Labour Act 2006"}
            </div>
            <h2 className="section-modal__title">
              Section - {section.section || section.number}
            </h2>
            {section.title && (
              <h3 className="section-modal__subtitle">{section.title}</h3>
            )}
            <button className="section-modal__close" onClick={onClose} aria-label="Close modal">
              ✕
            </button>
          </div>

          <div className="section-modal__body">
            {section.text ? (
              <div className="section-modal__text">{section.text}</div>
            ) : (
              <p className="section-modal__loading">Loading section content...</p>
            )}
          </div>

          <div className="section-modal__footer">
            <span className="section-modal__law-tag">Bangladesh Labour Act 2006</span>
            <button className="section-modal__done-btn" onClick={onClose}>
              Close
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
