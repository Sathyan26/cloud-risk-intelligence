import { useState } from "react";
import { api } from "../api";

export default function AssistantChat() {
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!question.trim() || loading) return;
    const q = question;
    setQuestion("");
    setLoading(true);
    setHistory((h) => [...h, { role: "user", text: q }]);
    try {
      const result = await api.askAssistant(q);
      setHistory((h) => [...h, { role: "assistant", text: result.answer, toolCalls: result.tool_calls }]);
    } catch (err) {
      setHistory((h) => [...h, { role: "assistant", text: `Error: ${err.message}`, isError: true }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card assistant">
      <h3>Ask the Assistant</h3>
      <div className="chat-history">
        {history.length === 0 && (
          <div className="chat-hint">Try: "Which customers are at the highest risk of churning?"</div>
        )}
        {history.map((m, i) => (
          <div key={i} className={`chat-message ${m.role}`}>
            <div className="chat-bubble">
              {m.text}
              {m.toolCalls && m.toolCalls.length > 0 && (
                <div className="tool-calls">Used: {m.toolCalls.map((t) => t.tool).join(", ")}</div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="chat-message assistant">
            <div className="chat-bubble">Thinking...</div>
          </div>
        )}
      </div>
      <form onSubmit={handleSubmit} className="chat-form">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about risk, churn, or data quality..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          Ask
        </button>
      </form>
    </div>
  );
}
