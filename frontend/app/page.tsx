/**
 * Landing Page
 * Entry point for starting an interview session
 */
'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Code2, Sparkles, MessageSquare, Shield } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();
  const [candidateName, setCandidateName] = useState('');

  const handleStartInterview = () => {
    // Generate a random session ID
    const sessionId = `session-${Date.now()}-${Math.random().toString(36).substring(7)}`;
    router.push(`/interview/${sessionId}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Code2 className="w-12 h-12 text-blue-500" />
            <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              AI Interview Platform
            </h1>
          </div>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Experience the future of technical interviews with AI-powered assistance,
            real-time code execution, and intelligent feedback
          </p>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="bg-gray-800/50 backdrop-blur border border-gray-700 rounded-xl p-6 hover:border-blue-500 transition-colors">
            <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center mb-4">
              <Sparkles className="w-6 h-6 text-blue-400" />
            </div>
            <h3 className="text-xl font-semibold mb-2">AI Interviewer</h3>
            <p className="text-gray-400">
              Get real-time help from an intelligent AI interviewer that provides hints
              and guidance without giving away solutions
            </p>
          </div>

          <div className="bg-gray-800/50 backdrop-blur border border-gray-700 rounded-xl p-6 hover:border-green-500 transition-colors">
            <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center mb-4">
              <Code2 className="w-6 h-6 text-green-400" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Live Code Execution</h3>
            <p className="text-gray-400">
              Write TypeScript code in a professional IDE and run it instantly with
              automated test cases and detailed feedback
            </p>
          </div>

          <div className="bg-gray-800/50 backdrop-blur border border-gray-700 rounded-xl p-6 hover:border-purple-500 transition-colors">
            <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center mb-4">
              <Shield className="w-6 h-6 text-purple-400" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Proctoring Features</h3>
            <p className="text-gray-400">
              Built-in integrity monitoring with paste detection and tab-switch tracking
              for fair assessment
            </p>
          </div>
        </div>

        {/* Start Interview */}
        <div className="max-w-md mx-auto bg-gray-800/50 backdrop-blur border border-gray-700 rounded-xl p-8">
          <h2 className="text-2xl font-bold mb-6 text-center">Start Your Interview</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Your Name (Optional)
              </label>
              <input
                type="text"
                value={candidateName}
                onChange={(e) => setCandidateName(e.target.value)}
                placeholder="Enter your name"
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              onClick={handleStartInterview}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-all transform hover:scale-105 flex items-center justify-center gap-2"
            >
              <MessageSquare className="w-5 h-5" />
              Start Interview
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-16 text-center text-gray-500 text-sm">
          <p>Built with Next.js, FastAPI, Azure OpenAI, and Judge0</p>
        </div>
      </div>
    </div>
  );
}
