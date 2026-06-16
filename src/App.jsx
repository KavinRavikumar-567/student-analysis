import React from 'react';
import { useApp } from './context/AppContext';
import StarField from './components/StarField';
import InsightsView from './components/InsightsView';
import ChatView from './components/ChatView';
import { 
  Orbit, 
  MessageSquare, 
  BarChart3, 
  Radio, 
  Cpu 
} from 'lucide-react';

const App = () => {
  const { isChatOpen, setIsChatOpen, fileInfo } = useApp();

  return (
    <div className="relative min-h-screen flex flex-col font-space select-none">
      {/* 1. Drift Particle Background */}
      <StarField />

      {/* 2. Command Deck Header */}
      <header className="sticky top-0 z-30 bg-[#050710]/80 border-b border-electricBlue/10 backdrop-blur-md px-6 py-4 flex items-center justify-between">
        {/* Logo and Telemetry Connection */}
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-electricBlue/10 border border-electricBlue/20 rounded-xl relative group">
            <Orbit className="w-6 h-6 text-electricBlue animate-[spin_8s_linear_infinite] group-hover:scale-110 transition-transform" />
            <div className="absolute inset-0 bg-electricBlue/10 blur-md rounded-full -z-10" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-base tracking-wider text-glow-blue text-white uppercase">
                DataOrbit
              </span>
              <span className="text-[10px] text-gray-500 font-mono tracking-widest uppercase hidden sm:inline">
                v1.0.0
              </span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-mintGreen rounded-full animate-pulse" />
              <span className="text-[9px] text-gray-400 font-semibold tracking-wider uppercase font-mono">
                System Link Established
              </span>
            </div>
          </div>
        </div>

        {/* Chat Control Trigger */}
        <div className="flex items-center space-x-3">
          {fileInfo && (
            <div className="hidden lg:flex flex-col text-right text-[10px] text-gray-500 font-mono leading-none">
              <span>Telemetry Feed Active:</span>
              <span className="text-white font-semibold truncate max-w-[120px] mt-0.5">
                {fileInfo.filename}
              </span>
            </div>
          )}
          <button
            onClick={() => setIsChatOpen(!isChatOpen)}
            className={`relative p-2.5 rounded-xl border transition-all ${
              isChatOpen
                ? 'bg-electricBlue/25 border-electricBlue text-electricBlue shadow-[0_0_15px_rgba(79,195,247,0.25)]'
                : 'bg-white/[0.03] border-white/10 hover:border-electricBlue/30 text-gray-300 hover:text-white'
            }`}
            title="Toggle AI Analyst Panel"
          >
            <Cpu className="w-5 h-5" />
            <span className="absolute -top-1 -right-1 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-mintGreen opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-mintGreen"></span>
            </span>
          </button>
        </div>
      </header>

      {/* 3. Main Operational Deck */}
      <main className="flex-1 flex flex-col justify-start relative z-10 w-full">
        <InsightsView />
      </main>

      {/* 4. Slide-in Conversational Console */}
      <ChatView />

      {/* 5. Floating Orbital Chat Trigger */}
      {!isChatOpen && (
        <button
          onClick={() => setIsChatOpen(true)}
          className="fixed bottom-6 right-6 z-40 bg-gradient-to-tr from-electricBlue to-accentViolet text-spaceBg font-semibold text-xs uppercase tracking-widest px-5 py-3.5 rounded-full shadow-[0_0_20px_rgba(79,195,247,0.4)] hover:shadow-[0_0_30px_rgba(179,136,255,0.6)] hover:brightness-110 active:scale-95 transition-all flex items-center gap-2 group border border-white/15"
        >
          <MessageSquare className="w-4 h-4 text-spaceBg group-hover:rotate-12 transition-transform" />
          <span>Ask AI Analyst</span>
        </button>
      )}

      {/* 6. Footer Copyright */}
      <footer className="py-5 border-t border-white/[0.04] bg-[#050710]/50 text-center text-[10px] text-gray-500 font-mono tracking-widest relative z-20">
        &copy; {new Date().getFullYear()} DATAORBIT SPACE ACADEMY. ALL METRICS ALIGNED.
      </footer>
    </div>
  );
};

export default App;
