import React from 'react';
import { useApp } from './context/AppContext';
import StarField from './components/StarField';
import InsightsView from './components/InsightsView';
import { 
  Orbit, 
  BarChart3, 
  Radio 
} from 'lucide-react';

const App = () => {
  const { fileInfo } = useApp();

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
        </div>
      </header>

      {/* 3. Main Operational Deck */}
      <main className="flex-1 flex flex-col justify-start relative z-10 w-full">
        <InsightsView />
      </main>

      {/* 6. Footer Copyright */}
      <footer className="py-5 border-t border-white/[0.04] bg-[#050710]/50 text-center text-[10px] text-gray-500 font-mono tracking-widest relative z-20">
        &copy; {new Date().getFullYear()} DATAORBIT SPACE ACADEMY. ALL METRICS ALIGNED.
      </footer>
    </div>
  );
};

export default App;
