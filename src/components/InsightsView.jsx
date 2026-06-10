import React from 'react';
import { useApp } from '../context/AppContext';
import { 
  Users, 
  Trophy, 
  AlertTriangle, 
  Activity, 
  ShieldCheck, 
  TrendingUp, 
  Award, 
  Brain, 
  Layers, 
  ArrowLeft, 
  MessageSquare,
  Sparkles,
  Percent,
  GraduationCap
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  Cell 
} from 'recharts';

const IconHelper = ({ name }) => {
  const sizeClass = "w-6 h-6";
  switch (name) {
    case 'alert-triangle':
      return <AlertTriangle className={`${sizeClass} text-[#ff5252] text-glow-red`} />;
    case 'shield-check':
      return <ShieldCheck className={`${sizeClass} text-mintGreen text-glow-mint`} />;
    case 'trending-up':
      return <TrendingUp className={`${sizeClass} text-electricBlue text-glow-blue`} />;
    case 'award':
      return <Award className={`${sizeClass} text-accentViolet text-glow-violet`} />;
    case 'brain':
      return <Brain className={`${sizeClass} text-accentViolet text-glow-violet`} />;
    default:
      return <Activity className={`${sizeClass} text-electricBlue`} />;
  }
};

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#0a0c16]/95 border border-electricBlue/20 p-3 rounded-lg shadow-xl backdrop-blur-md text-xs">
        <p className="font-semibold text-white mb-1 uppercase tracking-wider">{payload[0].payload.name}</p>
        <p className="text-electricBlue">
          Correlation Weight: <strong className="text-glow-blue">{payload[0].value}%</strong>
        </p>
      </div>
    );
  }
  return null;
};

const InsightsView = () => {
  const { insights, resetApp, setIsChatOpen, fileInfo } = useApp();

  if (!insights) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 py-16">
        <Activity className="w-16 h-16 text-electricBlue animate-spin mb-4" />
        <p className="text-gray-400">Syncing telemetry data orbits...</p>
      </div>
    );
  }

  const { kpis, factors, distributions, insight_cards } = insights;

  // Chart gradient variables
  const colors = ['#4fc3f7', '#64b5f6', '#9575cd', '#b388ff', '#ea80fc'];

  return (
    <div className="flex-1 w-full max-w-6xl mx-auto px-4 py-8 flex flex-col space-y-8 animate-card-entrance">
      
      {/* Top Navbar Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-electricBlue/15 pb-5">
        <div>
          <span className="text-xs font-semibold uppercase tracking-widest text-electricBlue px-2.5 py-1 bg-electricBlue/10 border border-electricBlue/25 rounded-full">
            Platform Telemetry
          </span>
          <h2 className="text-2xl font-bold tracking-tight text-white mt-2">
            Academy Intelligence Report
          </h2>
          <p className="text-gray-400 text-xs mt-0.5 font-medium truncate max-w-md">
            Source: {fileInfo?.filename || 'Mock Space Cohort Telemetry'}
          </p>
        </div>

        <div className="flex space-x-3 w-full sm:w-auto">
          <button
            onClick={resetApp}
            className="flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-semibold rounded-xl bg-white/[0.04] border border-electricBlue/15 hover:bg-white/[0.08] hover:border-electricBlue/30 text-white transition-all w-1/2 sm:w-auto"
          >
            <ArrowLeft className="w-4 h-4" />
            Upload New
          </button>
          <button
            onClick={() => setIsChatOpen(true)}
            className="flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-semibold rounded-xl bg-gradient-to-r from-electricBlue to-accentViolet text-spaceBg hover:brightness-110 active:scale-95 shadow-[0_0_15px_rgba(79,195,247,0.2)] transition-all w-1/2 sm:w-auto"
          >
            <MessageSquare className="w-4 h-4" />
            Query AI Agent
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        
        {/* KPI 1: Total Students */}
        <div className="glass-card p-5 relative overflow-hidden group">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2">Total Students</p>
              <h3 className="text-3xl font-bold text-glow-mint text-mintGreen">{kpis.total_students}</h3>
            </div>
            <div className="p-2.5 bg-mintGreen/10 border border-mintGreen/25 rounded-xl">
              <Users className="w-5 h-5 text-mintGreen" />
            </div>
          </div>
          <p className="text-[10px] text-gray-500 mt-4 tracking-wider uppercase font-medium">Active Academy Cohorts</p>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-mintGreen/5 to-mintGreen/30 opacity-50" />
        </div>

        {/* KPI 2: Avg Score */}
        <div className="glass-card p-5 relative overflow-hidden group">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2">Average Score</p>
              <h3 className="text-3xl font-bold text-glow-blue text-electricBlue">{kpis.avg_score}%</h3>
            </div>
            <div className="p-2.5 bg-electricBlue/10 border border-electricBlue/25 rounded-xl">
              <Trophy className="w-5 h-5 text-electricBlue" />
            </div>
          </div>
          <p className="text-[10px] text-gray-500 mt-4 tracking-wider uppercase font-medium">Exam Performance Telemetry</p>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-electricBlue/5 to-electricBlue/30 opacity-50" />
        </div>

        {/* KPI 3: At-Risk Count */}
        <div className="glass-card p-5 relative overflow-hidden group">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2">At-Risk Count</p>
              <h3 className="text-3xl font-bold text-glow-red text-[#ff5252]">{kpis.at_risk_count}</h3>
            </div>
            <div className="p-2.5 bg-red-500/10 border border-red-500/25 rounded-xl">
              <AlertTriangle className="w-5 h-5 text-[#ff5252]" />
            </div>
          </div>
          <p className="text-[10px] text-gray-500 mt-4 tracking-wider uppercase font-medium">Warning: GPA &lt; 5.0 or Att. &lt; 40%</p>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-red-500/5 to-[#ff5252]/30 opacity-50" />
        </div>

        {/* KPI 4: Top Factor */}
        <div className="glass-card p-5 relative overflow-hidden group">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2">Top Factor</p>
              <h3 className="text-lg font-bold text-glow-violet text-accentViolet leading-tight truncate max-w-[150px] mt-1.5">{kpis.top_factor}</h3>
            </div>
            <div className="p-2.5 bg-accentViolet/10 border border-accentViolet/25 rounded-xl">
              <Activity className="w-5 h-5 text-accentViolet" />
            </div>
          </div>
          <p className="text-[10px] text-gray-500 mt-4 tracking-wider uppercase font-medium">Primary Correlation Vector</p>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-accentViolet/5 to-accentViolet/30 opacity-50" />
        </div>
      </div>

      {/* Analytics 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Recharts Horizontal Bar Chart */}
        <div className="glass-card p-6 lg:col-span-7 flex flex-col space-y-4">
          <div>
            <h4 className="text-base font-semibold uppercase tracking-widest text-electricBlue">
              Top Factors Affecting Marks
            </h4>
            <p className="text-xs text-gray-400 mt-1">
              Percentage coefficient indicating factor correlation weights against student grades.
            </p>
          </div>

          <div className="h-72 w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={factors}
                layout="vertical"
                margin={{ top: 10, right: 20, left: 10, bottom: 5 }}
              >
                <defs>
                  <linearGradient id="barGrad" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#b388ff" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="#4fc3f7" stopOpacity={0.95} />
                  </linearGradient>
                </defs>
                <XAxis 
                  type="number" 
                  domain={[0, 100]} 
                  stroke="rgba(255,255,255,0.3)"
                  tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 10, fontFamily: 'Space Grotesk' }}
                  gridArea=""
                />
                <YAxis 
                  type="category" 
                  dataKey="name" 
                  stroke="rgba(255,255,255,0.3)"
                  tick={{ fill: 'rgba(255,255,255,0.85)', fontSize: 10, fontFamily: 'Space Grotesk' }}
                  width={110}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255, 255, 255, 0.02)' }} />
                <Bar 
                  dataKey="value" 
                  radius={[0, 8, 8, 0]}
                  barSize={18}
                >
                  {factors.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill="url(#barGrad)"
                      stroke="rgba(100, 160, 255, 0.3)"
                      strokeWidth={1}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right Column: Column Distribution Summary List */}
        <div className="glass-card p-6 lg:col-span-5 flex flex-col space-y-4">
          <div>
            <h4 className="text-base font-semibold uppercase tracking-widest text-accentViolet">
              Department Telemetry
            </h4>
            <p className="text-xs text-gray-400 mt-1">
              Active student cohort distribution, GPA, and attendance averages.
            </p>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 pr-1 mt-2 max-h-[280px]">
            {distributions && distributions.map((item, idx) => (
              <div 
                key={idx}
                className="bg-[#0b0c16] border border-electricBlue/10 p-3.5 rounded-xl hover:border-electricBlue/30 transition-all flex flex-col space-y-2.5"
              >
                {/* Header */}
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-sm text-glow-blue text-electricBlue truncate max-w-[180px]">{item.category}</span>
                  <span className="text-[10px] text-gray-400 bg-white/[0.04] px-2 py-0.5 rounded border border-white/5 font-medium">
                    {item.student_count} Students
                  </span>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="flex flex-col space-y-1">
                    <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">GPA Mean</span>
                    <span className="font-semibold text-white flex items-center gap-1">
                      <GraduationCap className="w-3.5 h-3.5 text-accentViolet" />
                      {item.avg_gpa} / 10.0
                    </span>
                    {/* Visual Bar */}
                    <div className="w-full h-1 bg-white/[0.05] rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-accentViolet rounded-full" 
                        style={{ width: `${(item.avg_gpa / 10.0) * 100}%` }}
                      />
                    </div>
                  </div>

                  <div className="flex flex-col space-y-1">
                    <span className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Attendance</span>
                    <span className="font-semibold text-white flex items-center gap-1">
                      <Percent className="w-3.5 h-3.5 text-mintGreen" />
                      {item.avg_attendance}%
                    </span>
                    {/* Visual Bar */}
                    <div className="w-full h-1 bg-white/[0.05] rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-mintGreen rounded-full" 
                        style={{ width: `${item.avg_attendance}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Auto Insights Console */}
      <div className="flex flex-col space-y-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-mintGreen text-glow-mint" />
          <h4 className="text-lg font-bold tracking-tight uppercase text-white font-space">
            Auto Insights Console
          </h4>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {insight_cards && insight_cards.map((card, idx) => (
            <div 
              key={idx}
              className="glass-card p-5 flex flex-col space-y-3 hover:border-mintGreen/30 relative overflow-hidden group"
            >
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-white/[0.04] border border-white/10 rounded-lg group-hover:border-electricBlue/20 transition-all">
                  <IconHelper name={card.icon} />
                </div>
                <h5 className="font-bold text-sm text-white tracking-wide leading-snug truncate">
                  {card.headline}
                </h5>
              </div>
              <p className="text-xs text-gray-400 leading-relaxed font-medium">
                {card.explanation}
              </p>
              
              {/* Corner accent glow indicator */}
              <div className="absolute top-0 right-0 w-8 h-8 bg-gradient-to-bl from-white/[0.02] to-transparent pointer-events-none" />
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};

export default InsightsView;
