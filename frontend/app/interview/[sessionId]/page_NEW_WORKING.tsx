/**
 * Main Interview Page
 * Integrates editor, console, chat, and WebSocket communication
 */
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { Socket } from 'socket.io-client';
import { Play, Clock, CheckCircle } from 'lucide-react';

import MonacoEditor from '@/components/Editor/MonacoEditor';
import TabManager from '@/components/Editor/TabManager';
import OutputConsole from '@/components/Console/OutputConsole';
import ChatPanel from '@/components/Chat/ChatPanel';

import { socketClient, joinSession, sendCodeUpdate, runCode, sendChatMessage, sendProctoringEvent } from '@/lib/socket';
import { ChatMessage, ExecutionResult, SessionData, Tab } from '@/types';

export default function InterviewPage() {
    const params = useParams();
    const sessionId = params?.sessionId as string || 'demo-session';

    // State
    const [socket, setSocket] = useState<Socket | null>(null);
    const [connected, setConnected] = useState(false);
    const [sessionData, setSessionData] = useState<SessionData | null>(null);

    const [tabs, setTabs] = useState<Tab[]>([
        { id: 'solution', name: 'solution.js', content: '', readOnly: false },
        { id: 'tests', name: 'tests.js', content: '// Test cases will appear here after first run', readOnly: true },
    ]);
    const [activeTab, setActiveTab] = useState('solution');

    const [consoleOutputs, setConsoleOutputs] = useState<Array<{ type: 'stdout' | 'stderr' | 'system'; text: string; timestamp: Date }>>([]);
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [isExecuting, setIsExecuting] = useState(false);
    const [isChatLoading, setIsChatLoading] = useState(false);

    // Initialize WebSocket connection
    useEffect(() => {
        const newSocket = socketClient.connect();
        setSocket(newSocket);

        newSocket.on('connect', () => {
            setConnected(true);
            joinSession(newSocket, sessionId, 'Candidate');
        });

        newSocket.on('disconnect', () => {
            setConnected(false);
        });

        newSocket.on('session_joined', (data: SessionData) => {
            console.log('Session joined:', data);
            setSessionData(data);
            setTabs((prev) =>
                prev.map((tab) =>
                    tab.id === 'solution' ? { ...tab, content: data.initial_code } : tab
                )
            );
            setChatMessages(data.chat_history);
        });

        newSocket.on('execution_started', () => {
            setIsExecuting(true);
            setConsoleOutputs((prev) => [
                ...prev,
                { type: 'system', text: '⏳ Running code...', timestamp: new Date() },
            ]);
        });

        newSocket.on('execution_complete', (result: ExecutionResult) => {
            setIsExecuting(false);
            const outputs: Array<{ type: 'stdout' | 'stderr' | 'system'; text: string; timestamp: Date }> = [];

            if (result.stdout) {
                outputs.push({ type: 'stdout', text: result.stdout, timestamp: new Date() });
            }
            if (result.stderr) {
                outputs.push({ type: 'stderr', text: result.stderr, timestamp: new Date() });
            }

            const statusText = result.test_passed
                ? `✅ All tests passed! (${result.time?.toFixed(2)}s)`
                : `❌ Tests failed`;

            outputs.push({ type: 'system', text: statusText, timestamp: new Date() });
            setConsoleOutputs((prev) => [...prev, ...outputs]);
        });

        newSocket.on('execution_error', (data: { error: string }) => {
            setIsExecuting(false);
            setConsoleOutputs((prev) => [
                ...prev,
                { type: 'stderr', text: `Error: ${data.error}`, timestamp: new Date() },
            ]);
        });

        // Chat response handler with voice support
        newSocket.on('chat_response', (message: ChatMessage & { speak?: boolean }) => {
            setChatMessages((prev) => [...prev, message]);
            setIsChatLoading(false);

            // Auto-speak AI responses if voice flag is set
            if (message.speak && message.role === 'assistant' && message.content) {
                try {
                    const utterance = new SpeechSynthesisUtterance(message.content);
                    utterance.rate = 1.0;
                    utterance.pitch = 1.0;
                    utterance.volume = 1.0;
                    window.speechSynthesis.speak(utterance);
                } catch (error) {
                    console.warn('Text-to-speech not supported:', error);
                }
            }
        });

        newSocket.on('chat_error', (data: { error: string }) => {
            setIsChatLoading(false);
            setChatMessages((prev) => [
                ...prev,
                { role: 'assistant', content: `⚠️ Error: ${data.error}`, timestamp: new Date().toISOString() }
            ]);
        });

        return () => {
            newSocket.off('connect');
            newSocket.off('disconnect');
            newSocket.off('session_joined');
            newSocket.off('execution_started');
            newSocket.off('execution_complete');
            newSocket.off('execution_error');
            newSocket.off('chat_response');
            newSocket.off('chat_error');
        };
    }, [sessionId]);

    // Proctoring: Tab visibility
    useEffect(() => {
        const handleVisibilityChange = () => {
            if (document.hidden && socket) {
                sendProctoringEvent(socket, 'tab_switch', { timestamp: Date.now() });
            }
        };
        document.addEventListener('visibilitychange', handleVisibilityChange);
        return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
    }, [socket]);

    // Proctoring: Paste detection
    useEffect(() => {
        const handlePaste = (e: Event) => {
            const customEvent = e as CustomEvent;
            if (socket && customEvent.detail) {
                sendProctoringEvent(socket, 'paste_detected', {
                    length: customEvent.detail.length,
                    timestamp: Date.now(),
                });
            }
        };
        window.addEventListener('paste-detected', handlePaste);
        return () => window.removeEventListener('paste-detected', handlePaste);
    }, [socket]);

    const handleCodeChange = (code: string) => {
        setTabs((prev) =>
            prev.map((tab) => (tab.id === activeTab ? { ...tab, content: code } : tab))
        );
    };

    const debounceRef = React.useRef<NodeJS.Timeout | null>(null);
    const lastInteractionRef = React.useRef<number>(Date.now());
    const hasHintedRef = React.useRef<boolean>(false);

    useEffect(() => {
        const interval = setInterval(() => {
            const now = Date.now();
            const idleTime = now - lastInteractionRef.current;
            const hasCode = tabs.find(t => t.id === 'solution')?.content.length || 0 > 50;

            if (idleTime > 120000 && hasCode && !hasHintedRef.current && socket && connected) {
                hasHintedRef.current = true;
                sendChatMessage(socket, "I seem to be stuck. Can you give me a subtle hint?");
                setChatMessages(prev => [...prev, {
                    role: 'user',
                    content: "I seem to be stuck. Can you give me a subtle hint?",
                    timestamp: new Date().toISOString()
                }]);
                setIsChatLoading(true);
            }
        }, 10000);
        return () => clearInterval(interval);
    }, [socket, connected, tabs]);

    const handleCodeUpdate = useCallback((code: string) => {
        lastInteractionRef.current = Date.now();
        hasHintedRef.current = false;
        if (debounceRef.current) clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => {
            if (socket && connected) sendCodeUpdate(socket, code);
        }, 3000);
    }, [socket, connected]);

    const handleRunCode = async () => {
        if (!connected || isExecuting) return;
        setIsExecuting(true);
        setConsoleOutputs((prev) => [...prev, { type: 'system', text: '⏳ Running code (via Secure API)...', timestamp: new Date() }]);
        const solutionCode = tabs.find((t) => t.id === 'solution')?.content || '';

        try {
            const response = await fetch('http://localhost:8000/api/run_code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    code: solutionCode,
                    problem_id: sessionData?.problem_title?.toLowerCase().replace(/\s+/g, '-') || 'two-sum'
                })
            });

            if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
            const result: ExecutionResult = await response.json();
            setIsExecuting(false);
            const outputs: Array<{ type: 'stdout' | 'stderr' | 'system'; text: string; timestamp: Date }> = [];

            if (result.stdout) outputs.push({ type: 'stdout', text: result.stdout, timestamp: new Date() });
            if (result.stderr) outputs.push({ type: 'stderr', text: result.stderr, timestamp: new Date() });
            if (result.compile_output) outputs.push({ type: 'stderr', text: `Compile Error:\n${result.compile_output}`, timestamp: new Date() });

            const statusText = result.test_passed ? `✅ All tests passed! (${result.time?.toFixed(2)}s)` : `❌ Tests failed`;
            outputs.push({ type: 'system', text: statusText, timestamp: new Date() });
            setConsoleOutputs((prev) => [...prev, ...outputs]);
        } catch (error) {
            setIsExecuting(false);
            setConsoleOutputs((prev) => [...prev, { type: 'stderr', text: `Execution failed: ${error}`, timestamp: new Date() }]);
        }
    };

    const handleSendMessage = (message: string) => {
        if (socket && connected) {
            const userMessage: ChatMessage = { role: 'user', content: message, timestamp: new Date().toISOString() };
            setChatMessages((prev) => [...prev, userMessage]);
            setIsChatLoading(true);
            sendChatMessage(socket, message);
        }
    };

    const handleClearConsole = () => setConsoleOutputs([]);
    const currentTab = tabs.find((t) => t.id === activeTab);

    return (
        <div className="h-screen flex flex-col bg-gray-950 text-white">
            <header className="h-16 bg-gray-900 border-b border-gray-700 flex items-center justify-between px-6">
                <div>
                    <h1 className="text-xl font-bold text-white">{sessionData?.problem_title || 'Loading...'}</h1>
                    <p className="text-sm text-gray-400">Session: {sessionId}</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 text-sm text-gray-400">
                        <Clock className="w-4 h-4" />
                        <span>45:00</span>
                    </div>
                    <div className="flex items-center gap-2">
                        {connected ? (
                            <>
                                <CheckCircle className="w-4 h-4 text-green-500" />
                                <span className="text-sm text-green-500">Connected</span>
                            </>
                        ) : (
                            <>
                                <div className="w-4 h-4 rounded-full bg-red-500 animate-pulse" />
                                <span className="text-sm text-red-500">Disconnected</span>
                            </>
                        )}
                    </div>
                    <button onClick={handleRunCode} disabled={isExecuting || !connected} className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg font-medium transition-colors">
                        <Play className="w-4 h-4" />
                        {isExecuting ? 'Running...' : 'Run Code'}
                    </button>
                </div>
            </header>
            <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
                <div className="flex-1 flex flex-col p-4 gap-4 overflow-y-auto lg:overflow-hidden min-h-[500px]">
                    <div className="flex-1 flex flex-col bg-gray-900 rounded-lg overflow-hidden border border-gray-700">
                        <TabManager tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
                        <div className="flex-1">
                            <MonacoEditor
                                value={currentTab?.content || ''}
                                language="javascript"
                                onChange={(value) => {
                                    handleCodeChange(value || '');
                                    handleCodeUpdate(value || '');
                                }}
                                readOnly={currentTab?.readOnly || false}
                            />
                        </div>
                    </div>
                    <div className="h-64 lg:h-80 flex-shrink-0">
                        <OutputConsole outputs={consoleOutputs} onClear={handleClearConsole} />
                    </div>
                </div>
                <div className="w-full lg:w-96 flex-shrink-0 border-l border-gray-700">
                    <ChatPanel messages={chatMessages} onSendMessage={handleSendMessage} isLoading={isChatLoading} />
                </div>
            </div>
        </div>
    );
}
