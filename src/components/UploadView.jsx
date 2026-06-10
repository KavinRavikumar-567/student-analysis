import React, { useState, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { Upload, FileSpreadsheet, CheckCircle, Database, AlertCircle, RefreshCw } from 'lucide-react';

const UploadView = () => {
  const { uploadFile, fileInfo, analyseData, isLoading, errorMsg } = useApp();
  const [isDragActive, setIsDragActive] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [localFile, setLocalFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  };

  const processFile = async (file) => {
    if (!file) return;
    const extension = file.name.split('.').pop().toLowerCase();
    if (extension !== 'csv' && extension !== 'xlsx' && extension !== 'xls') {
      alert('DataOrbit only accepts .csv or .xlsx telemetry files.');
      return;
    }
    setLocalFile(file);
    try {
      await uploadFile(file);
      setUploadSuccess(true);
    } catch (err) {
      setUploadSuccess(false);
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e) => {
    if (e.target.files && e.target.files[0]) {
      await processFile(e.target.files[0]);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current.click();
  };

  return (
    <div className="flex flex-col items-center justify-center flex-1 px-4 py-12 max-w-4xl mx-auto w-full animate-card-entrance">
      {/* Title Area */}
      <div className="text-center mb-8">
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-3 bg-gradient-to-r from-electricBlue via-accentViolet to-mintGreen bg-clip-text text-transparent">
          DataOrbit
        </h1>
        <p className="text-gray-400 text-lg max-w-xl">
          Deploy student telemetry matrices into our zero-gravity analytics core. 
          Auto-compile KPIs, cohort metrics, and interactive predictive factors.
        </p>
      </div>

      {/* Drag & Drop Main Zone */}
      <div
        className={`w-full max-w-2xl h-80 glass-card p-8 flex flex-col items-center justify-center cursor-pointer transition-all duration-300 relative ${
          isDragActive 
            ? 'border-accentViolet bg-white/[0.08] shadow-[0_0_30px_rgba(179,136,255,0.25)]' 
            : 'border-electricBlue/20 hover:border-electricBlue/50'
        } ${uploadSuccess ? 'border-mintGreen/45 shadow-[0_0_20px_rgba(105,240,174,0.15)]' : ''}`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={triggerFileInput}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".csv, .xlsx, .xls"
          onChange={handleFileChange}
        />

        {isLoading && !fileInfo ? (
          <div className="flex flex-col items-center space-y-4">
            <RefreshCw className="w-16 h-16 text-electricBlue animate-spin" />
            <p className="text-electricBlue font-medium tracking-widest text-sm text-glow-blue uppercase">
              Establishing Data Linkage...
            </p>
          </div>
        ) : uploadSuccess && fileInfo ? (
          <div className="flex flex-col items-center text-center space-y-4">
            <div className="p-4 bg-mintGreen/10 rounded-full border border-mintGreen/30 shadow-[0_0_15px_rgba(105,240,174,0.15)]">
              <CheckCircle className="w-12 h-12 text-mintGreen" />
            </div>
            <div>
              <p className="text-mintGreen font-semibold text-xl tracking-wide text-glow-mint mb-1">
                Telemetry Link Operational
              </p>
              <p className="text-gray-300 font-medium truncate max-w-md text-sm">
                {fileInfo.filename}
              </p>
            </div>
            
            {/* Dimensions Badge */}
            <div className="flex space-x-6 text-sm text-gray-400 bg-[#0a0c16] px-5 py-2.5 rounded-full border border-electricBlue/10">
              <span className="flex items-center gap-1.5">
                <Database className="w-4 h-4 text-electricBlue" />
                Rows: <strong className="text-white">{fileInfo.rows}</strong>
              </span>
              <span className="flex items-center gap-1.5">
                <FileSpreadsheet className="w-4 h-4 text-accentViolet" />
                Columns: <strong className="text-white">{fileInfo.cols}</strong>
              </span>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center text-center space-y-4">
            <div className="p-4 bg-electricBlue/10 rounded-full border border-electricBlue/20 shadow-[0_0_15px_rgba(79,195,247,0.1)]">
              <Upload className="w-12 h-12 text-electricBlue animate-bounce" />
            </div>
            <div>
              <p className="text-white font-semibold text-xl tracking-wide mb-1">
                Upload Telemetry Vector
              </p>
              <p className="text-gray-400 text-sm">
                Drag and drop your <span className="text-electricBlue font-medium">.csv</span> or <span className="text-accentViolet font-medium">.xlsx</span> spreadsheet here, or click to browse
              </p>
            </div>
            <p className="text-xs text-gray-500 max-w-sm">
              Standard formats will auto-map Roll IDs, Names, GPAs, attendance ratios, and departments dynamically.
            </p>
          </div>
        )}

        {/* Glowing dashed border effect overlay */}
        <div 
          className={`absolute inset-3 border-2 border-dashed rounded-[15px] pointer-events-none transition-all duration-300 ${
            isDragActive 
              ? 'border-accentViolet/50' 
              : uploadSuccess 
                ? 'border-mintGreen/40' 
                : 'border-electricBlue/15'
          }`}
        />
      </div>

      {/* Error Output */}
      {errorMsg && (
        <div className="w-full max-w-2xl mt-4 p-4 rounded-xl border border-red-500/20 bg-red-500/5 flex items-start space-x-3 text-red-400 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-glow-red">Orbital Linkage Failure</p>
            <p className="text-red-300/80">{errorMsg}</p>
          </div>
        </div>
      )}

      {/* Bottom Action Button */}
      {uploadSuccess && fileInfo && (
        <div className="mt-8 flex flex-col items-center w-full max-w-2xl">
          <button
            onClick={analyseData}
            disabled={isLoading}
            className="w-full py-4 bg-gradient-to-r from-electricBlue via-accentViolet to-mintGreen hover:brightness-110 active:scale-[0.98] transition-all duration-200 text-spaceBg font-bold text-lg tracking-widest rounded-xl shadow-[0_0_25px_rgba(79,195,247,0.35)] pulse-glow"
          >
            {isLoading ? 'ANALYSING TELEMETRY...' : 'ANALYSE DATA'}
          </button>
          <button
            onClick={() => {
              setUploadSuccess(false);
              setLocalFile(null);
            }}
            className="mt-3 text-gray-500 hover:text-gray-300 text-xs transition-colors"
          >
            Upload a different file
          </button>
        </div>
      )}

      {/* Quick Telemetry Info for Trial */}
      {!uploadSuccess && (
        <div className="mt-8 text-center text-xs text-gray-500">
          <p>
            No dataset? Feel free to view the active space academy mock database. 
          </p>
          <button 
            onClick={analyseData}
            className="mt-2 text-electricBlue hover:text-accentViolet transition-colors underline underline-offset-4 font-semibold"
          >
            Load Active Mock Telemetry Dashboard &rarr;
          </button>
        </div>
      )}
    </div>
  );
};

export default UploadView;
