import React, { useState, useRef, useEffect } from "react";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([
    {
      text: "Hello! I'm your EchoBase assistant. Ask me anything about our company policies, products, or labor rules.",
      isUser: false,
    },
  ]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [model, setModel] = useState("gpt-3.5-turbo");
  const messagesEndRef = useRef(null);

  // Scroll to bottom of messages
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleInputChange = (e) => {
    setInputText(e.target.value);
  };

  const handleModelChange = (e) => {
    setModel(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!inputText.trim()) return;

    // Add user message to chat
    const userMessage = { text: inputText, isUser: true };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInputText("");
    setIsLoading(true);

    try {
      // Send query to API
      const response = await fetch("http://localhost:8000/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: inputText,
          model: model,
          top_k: 5,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response");
      }

      const data = await response.json();

      // Add bot response to chat
      const botMessage = { text: data.answer, isUser: false };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      console.error("Error:", error);
      // Add error message to chat
      const errorMessage = {
        text: "Sorry, I encountered an error processing your request. Please try again.",
        isUser: false,
      };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="chat-container">
        <div className="chat-header">
          <h1>EchoBase</h1>
          <div className="model-selector">
            <select value={model} onChange={handleModelChange}>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              <option value="gpt-4">GPT-4</option>
            </select>
          </div>
        </div>

        <div className="chat-messages">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`message ${
                message.isUser ? "user-message" : "bot-message"
              }`}
            >
              {message.text}
            </div>
          ))}

          {isLoading && (
            <div className="loading">
              <div className="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="chat-input-container">
          <input
            type="text"
            value={inputText}
            onChange={handleInputChange}
            placeholder="Ask a question..."
            className="chat-input"
            disabled={isLoading}
          />
          <button
            type="submit"
            className="chat-submit"
            disabled={isLoading || !inputText.trim()}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
