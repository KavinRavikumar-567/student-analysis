import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AppContext = createContext();

const API_BASE = 'http://localhost:8000';

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
  const [currentView, setCurrentView] = useState('upload'); // 'upload' | 'insights'
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Auto-fetch insights on load if we want to display mock data by default
  useEffect(() => {
    const loadMockInsights = async () => {
      try {
        setIsLoading(true);
        const response = await axios.get(`${API_BASE}/insights`);
        setInsights(response.data);
        setErrorMsg(null);
      } catch (err) {
        console.error('Failed to load initial insights:', err);
        setErrorMsg('Unable to connect to the orbital API backend. Ensure FastAPI server is running on http://localhost:8000');
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

  const resetApp = async () => {
    setFileInfo(null);
    setIsLoading(true);
    setCurrentView('upload');
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
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);
