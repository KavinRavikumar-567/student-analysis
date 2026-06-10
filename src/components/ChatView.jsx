import React, { useState, useRef, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { X, Send, Cpu, User, RefreshCw, Terminal } from 'lucide-react';

const ChatView = () => {
  const { isChatOpen, setIsChatOpen, chatHistory, sendChatMessage, isLoading } = useApp();
  const [inputValue, setInputValue] = useState('');
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom of chat when new messages arrive or drawer opens
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory, isChatOpen]);

  // Focus input when chat opens
  useEffect(() => {
    if (isChatOpen && inputRef.current) {
      setTimeout(() => inputRef.current.focus(), 150);
    }
  }, [isChatOpen]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;
    sendChatMessage(inputValue);
    setInputValue('');
  };

  return (
    <>
      {/* Background Overlay */}
      {isChatOpen && (
        <div 
          onClick={() => setIsChatOpen(false)}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 transition-opacity duration-300"
        />
      )}

      {/* Slide-in Sidebar Panel */}
      <div 
        className={`fixed top-0 right-0 h-full w-full sm:w-[460px] bg-[#070914] border-l border-electricBlue/20 backdrop-blur-xl z-50 flex flex-col shadow-[0_0_40px_rgba(0,0,0,0.85)] transition-all duration-300 transform ${
          isChatOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Panel Header */}
        <div className="p-4 border-b border-electricBlue/15 flex items-center justify-between bg-[#0a0c1a]">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-electricBlue/10 border border-electricBlue/25 rounded-xl">
              <Cpu className="w-5 h-5 text-electricBlue text-glow-blue animate-pulse" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-white tracking-wider uppercase">DataOrbit AI Analyst</h3>
              <div className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-mintGreen rounded-full animate-ping" />
                <span className="text-[10px] text-gray-400 font-semibold uppercase">Telemetry Core Active</span>
              </div>
            </div>
          </div>
          
          <button 
            onClick={() => setIsChatOpen(false)}
            className="p-2 text-gray-400 hover:text-white bg-white/[0.04] border border-white/5 hover:border-white/10 rounded-xl transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Console Header Banner */}
        <div className="bg-[#05060d] border-b border-white/5 px-4 py-2 flex items-center gap-1.5 text-[10px] text-gray-500 font-mono">
          <Terminal className="w-3.5 h-3.5 text-accentViolet" />
          <span>telemetry_db_link = http://localhost:8000/chat</span>
        </div>

        {/* Message Log */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth">
          {chatHistory.map((msg, index) => {
            const isUser = msg.sender === 'user';
            return (
              <div 
                key={index}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
              >
                <div 
                  className={`max-w-[85%] rounded-2xl p-3.5 text-sm leading-relaxed ${
                    isUser 
                      ? 'bg-gradient-to-br from-electricBlue to-[#1e88e5] text-spaceBg font-medium shadow-[0_4px_15px_rgba(79,195,247,0.2)] rounded-tr-none animate-slide-in-right' 
                      : 'bg-white/[0.04] border border-electricBlue/15 text-gray-200 rounded-tl-none animate-slide-in-left shadow-[0_4px_12px_rgba(0,0,0,0.15)]'
                  }`}
                >
                  {/* Sender Icon */}
                  <div className="flex items-center gap-1.5 mb-1.5 text-[10px] uppercase tracking-wider font-semibold opacity-75">
                    {isUser ? (
                      <>
                        <User className="w-3 h-3" />
                        <span>Officer Command</span>
                      </>
                    ) : (
                      <>
                        <Cpu className="w-3 h-3 text-accentViolet" />
                        <span>AI Retrievable Core</span>
                      </>
                    )}
                  </div>

                  <p className="whitespace-pre-line">{msg.text}</p>

                  {/* Sources Pills */}
                  {!isUser && msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-white/5">
                      <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest mb-1.5">
                        Telemetry References:
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.sources.map((src, idx) => (
                          <span 
                            key={idx}
                            className="text-[9px] bg-[#0b0c16] border border-white/[0.06] text-gray-400 px-2 py-0.5 rounded-md font-mono"
                          >
                            {src}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {/* Typing Indicator */}
          {isLoading && (
            <div className="flex flex-col items-start">
              <div className="bg-white/[0.04] border border-electricBlue/15 rounded-2xl rounded-tl-none p-3.5 flex items-center space-x-1.5 animate-slide-in-left">
                <span className="w-2 h-2 bg-electricBlue rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-accentViolet rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-mintGreen rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input Bar Form */}
        <form 
          onSubmit={handleSend}
          className="p-4 border-t border-electricBlue/15 bg-[#0a0c1a] flex gap-2"
        >
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Query student telemetry records..."
            disabled={isLoading}
            className="flex-1 bg-white/[0.03] border border-electricBlue/15 focus:border-electricBlue/40 focus:bg-white/[0.06] rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-electricBlue/30 transition-all font-medium disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="p-3 bg-gradient-to-r from-electricBlue to-accentViolet text-spaceBg rounded-xl hover:brightness-110 disabled:opacity-40 active:scale-95 transition-all flex items-center justify-center flex-shrink-0 shadow-[0_0_10px_rgba(79,195,247,0.15)]"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </>
  );
};

export default ChatView;
