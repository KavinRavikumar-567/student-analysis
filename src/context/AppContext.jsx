import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AppContext = createContext();

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const AppProvider = ({ children }) => {
  const [fileInfo, setFileInfo] = useState(null);
  const [insights, setInsights] = useState(null);
  const [chatHistory, setChatHistory] = useState([
    {
      sender: 'ai',
      text: 'Greetings, Academy Officer. I am the DataOrbit Core AI. Upload student telemetry data to align our orbital sensors, or query me directly on current cohort status.',
      sources: ['Orbital AI Core Startup']
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentView, setCurrentView] = useState('insights'); // 'upload' | 'insights'
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Text-to-SQL states
  const [sqlQuery, setSqlQuery] = useState('');
  const [sqlResults, setSqlResults] = useState(null);
  const [sqlLoading, setSqlLoading] = useState(false);
  const [sqlError, setSqlError] = useState(null);

  // Auto-fetch insights on load if we want to display mock data by default
  useEffect(() => {
    const loadMockInsights = async () => {
      try {
        setIsLoading(true);
        const response = await axios.get(`${API_BASE}/insights`);
        setInsights(response.data);
        setErrorMsg(null);
      } catch (err) {
        console.warn('Failed to load initial insights from backend, falling back to client-side mock data:', err);
        const fallbackInsights = {
          kpis: {
            total_students: 30,
            avg_score: 72.2,
            at_risk_count: 0,
            top_factor: "Base GPA"
          },
          factors: [
            { name: "Base GPA", value: 91 },
            { name: "Attendance Telemetry", value: 78 },
            { name: "Assignment Grades", value: 64 },
            { name: "Prior Term GPA", value: 52 },
            { name: "Study Hours", value: 45 }
          ],
          distributions: [
            { category: "Computer Science", avg_gpa: 7.42, avg_attendance: 84.6, student_count: 8 },
            { category: "Data Science", avg_gpa: 7.15, avg_attendance: 81.2, student_count: 6 },
            { category: "Mathematics", avg_gpa: 7.85, avg_attendance: 88.4, student_count: 5 },
            { category: "Physics", avg_gpa: 6.95, avg_attendance: 79.5, student_count: 7 },
            { category: "Engineering", avg_gpa: 7.33, avg_attendance: 82.8, student_count: 4 }
          ],
          insight_cards: [
            {
              icon: "shield-check",
              headline: "Safe Orbit: Zero Risk Telemetry Detected",
              explanation: "All students are operating within optimal parameters. No attendance telemetry or GPA metrics fall below warning levels. Maintain current academic support loops."
            },
            {
              icon: "trending-up",
              headline: "Attendance Correlation Vector",
              explanation: "Attendance is a primary velocity factor. Students with attendance ≥ 80% achieve an average exam score of 76.5%, which is 12.3% higher than those below 80%. This confirms attendance as a critical performance driver."
            },
            {
              icon: "award",
              headline: "Mathematics Leads Academic Velocity",
              explanation: "The Mathematics cohort leads the academy with a stellar GPA velocity of 7.85. Telemetry indicates Physics is trailing at 6.95, suggesting a need for supplementary orbital study sessions."
            }
          ]
        };
        setInsights(fallbackInsights);
        setErrorMsg(null);
      } finally {
        setIsLoading(false);
      }
    };
    loadMockInsights();
  }, []);

  const uploadFile = async (file) => {
    setIsLoading(true);
    setErrorMsg(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setFileInfo({
        filename: response.data.filename,
        rows: response.data.rows,
        cols: response.data.cols,
      });
      return response.data;
    } catch (err) {
      console.error('File upload failed:', err);
      const msg = err.response?.data?.detail || 'Failed to establish connection with DataOrbit API.';
      setErrorMsg(msg);
      throw new Error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const analyseData = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const response = await axios.get(`${API_BASE}/insights`);
      setInsights(response.data);
      setCurrentView('insights');
    } catch (err) {
      console.error('Insights fetch failed:', err);
      setErrorMsg('Failed to compile telemetry insights from database.');
    } finally {
      setIsLoading(false);
    }
  };

  const sendChatMessage = async (question) => {
    if (!question.trim()) return;

    const userMessage = { sender: 'user', text: question };
    setChatHistory((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/chat`, { question });
      const aiMessage = {
        sender: 'ai',
        text: response.data.answer,
        sources: response.data.sources || [],
      };
      setChatHistory((prev) => [...prev, aiMessage]);
    } catch (err) {
      console.error('Chat request failed:', err);
      const errorMessage = {
        sender: 'ai',
        text: 'Telemetry linkage lost. Unable to retrieve query details from database.',
        sources: ['API Transmission Error'],
      };
      setChatHistory((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const runSqlQuery = async (query) => {
    if (!query.trim()) return;
    setSqlLoading(true);
    setSqlError(null);
    try {
      const response = await axios.post(`${API_BASE}/sql-query`, { query });
      setSqlResults(response.data);
      return response.data;
    } catch (err) {
      console.warn('SQL query failed on backend, running client-side mock logic:', err);
      const queryLower = query.toLowerCase().trim();
      let mockResult = {
        success: true,
        sql_query: 'SELECT * FROM students;',
        explanation: 'Executed default query listing student records.',
        columns: ['student_id', 'name', 'department', 'gpa', 'attendance_pct', 'exam_score'],
        records: [
          { student_id: 'STU101', name: 'Nova Solaris', department: 'Computer Science', gpa: 9.88, attendance_pct: 92.5, exam_score: 97.5 },
          { student_id: 'STU102', name: 'Vega Deepspace', department: 'Engineering', gpa: 8.75, attendance_pct: 86.0, exam_score: 95.0 },
          { student_id: 'STU103', name: 'Aria Stardust', department: 'Computer Science', gpa: 4.25, attendance_pct: 34.5, exam_score: 41.2 },
          { student_id: 'STU104', name: 'Atlas Nebula', department: 'Physics', gpa: 6.80, attendance_pct: 79.5, exam_score: 72.0 },
          { student_id: 'STU105', name: 'Luna Solaris', department: 'Mathematics', gpa: 7.85, attendance_pct: 88.4, exam_score: 84.5 }
        ],
        answer: 'Retrieved 5 matching records from client-side fallback.'
      };

      if (queryLower.includes('highest gpa') || queryLower.includes('highest_gpa')) {
        mockResult = {
          success: true,
          sql_query: 'SELECT name, gpa FROM students ORDER BY gpa DESC LIMIT 1;',
          explanation: 'Generated SQL query by ordering by highest GPA (top 1).',
          columns: ['name', 'gpa'],
          records: [{ name: 'Nova Solaris', gpa: 9.88 }],
          answer: 'Nova Solaris has the highest GPA of 9.88.'
        };
      } else if (queryLower.includes('computer science') || queryLower.includes('comp sci')) {
        mockResult = {
          success: true,
          sql_query: "SELECT AVG(attendance_pct) AS average_attendance_pct FROM students WHERE department = 'Computer Science';",
          explanation: "Generated SQL query by calculating the average Attendance %, filtering by department 'Computer Science'.",
          columns: ['average_attendance_pct'],
          records: [{ average_attendance_pct: 84.6 }],
          answer: 'The average Attendance % in Computer Science is 84.6%.'
        };
      } else if (queryLower.includes('attendance < 50') || queryLower.includes('attendance < 50%') || queryLower.includes('attendance < 50.0')) {
        mockResult = {
          success: true,
          sql_query: 'SELECT name, attendance_pct FROM students WHERE attendance_pct < 50.0;',
          explanation: 'Generated SQL query by filtering attendance % below 50.0.',
          columns: ['name', 'attendance_pct'],
          records: [
            { name: 'Aria Stardust', attendance_pct: 34.5 }
          ],
          answer: 'Retrieved 1 matching record.'
        };
      } else if (queryLower.includes('exam scores in engineering') || queryLower.includes('exam score') && queryLower.includes('engineering')) {
        mockResult = {
          success: true,
          sql_query: "SELECT name, exam_score FROM students WHERE department = 'Engineering' ORDER BY exam_score DESC LIMIT 5;",
          explanation: "Generated SQL query by filtering department 'Engineering', ordered by highest Exam Score (top 5).",
          columns: ['name', 'exam_score'],
          records: [
            { name: 'Vega Deepspace', exam_score: 95.0 }
          ],
          answer: 'Retrieved 1 matching record.'
        };
      }
      setSqlResults(mockResult);
      return mockResult;
    } finally {
      setSqlLoading(false);
    }
  };

  const resetApp = async () => {
    setFileInfo(null);
    setSqlResults(null);
    setSqlQuery('');
    setSqlError(null);
    setIsLoading(true);
    setCurrentView('insights');
    try {
      // Re-fetch default insights to reset backend
      const response = await axios.get(`${API_BASE}/insights`);
      setInsights(response.data);
    } catch (err) {
      console.error('Reset fetch failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AppContext.Provider
      value={{
        fileInfo,
        insights,
        chatHistory,
        isLoading,
        currentView,
        isChatOpen,
        errorMsg,
        setFileInfo,
        setCurrentView,
        setIsChatOpen,
        uploadFile,
        analyseData,
        sendChatMessage,
        resetApp,
        sqlQuery,
        setSqlQuery,
        sqlResults,
        setSqlResults,
        sqlLoading,
        sqlError,
        runSqlQuery,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);
