/**
 * Main Interview Page
 * Integrates editor, console, chat, and WebSocket communication
 */
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { Socket } from 'socket.io-client';
import { Play, Clock } from 'lucide-react';

import MonacoEditor from '@/components/Editor/MonacoEditor';
import TabManager from '@/components/Editor/TabManager';
import OutputConsole from '@/components/Console/OutputConsole';
import ChatPanel from '@/components/Chat/ChatPanel';
import AgentStatus, { AgentState } from '@/components/Agent/AgentStatus';

import { socketClient, joinSession, sendCodeUpdate, sendChatMessage, sendProctoringEvent } from '@/lib/socket';
import { textToSpeech, stopSpeech } from '@/lib/speech';
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
        { id: 'tests', name: 'tests.js', content: '// Test cases will appear here after first run\n// You can edit and add your own test cases', readOnly: false },
    ]);
    const [activeTab, setActiveTab] = useState('solution');

    const [consoleOutputs, setConsoleOutputs] = useState<Array<{ type: 'stdout' | 'stderr' | 'system'; text: string; timestamp: Date }>>([]);
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [isExecuting, setIsExecuting] = useState(false);
    const [isChatLoading, setIsChatLoading] = useState(false);
    const [agentState, setAgentState] = useState<AgentState>('idle');

    // Interview phase: 'waiting' = waiting for user to click start, 'started' = interview in progress
    const [interviewPhase, setInterviewPhase] = useState<'waiting' | 'started'>('waiting');
    const [isAISpeaking, setIsAISpeaking] = useState(false);

    // Proctoring state
    const [tabSwitchCount, setTabSwitchCount] = useState(0);
    const [pasteCount, setPasteCount] = useState(0);
    const [showWarningModal, setShowWarningModal] = useState(false);
    const [warningMessage, setWarningMessage] = useState('');
    const [isFullscreen, setIsFullscreen] = useState(false);

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

        newSocket.on('session_joined', (data: SessionData & { speak_welcome?: boolean }) => {
            console.log('Session joined:', data);
            setSessionData(data);
            setTabs((prev) =>
                prev.map((tab) =>
                    tab.id === 'solution' ? { ...tab, content: data.initial_code } : tab
                )
            );
            setChatMessages(data.chat_history);
            // TTS will be triggered when user clicks "Start Interview" button
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

            // Update tests.js tab with actual test code if available
            if (result.stdout) {
                const testCases = `// Two Sum Test Cases
const { twoSum } = require('./solution.js');

const testCases = [
    { nums: [2, 7, 11, 15], target: 9, expected: [0, 1] },
    { nums: [3, 2, 4], target: 6, expected: [1, 2] },
    { nums: [3, 3], target: 6, expected: [0, 1] },
    { nums: [1, 5, 3, 7, 9], target: 12, expected: [2, 4] },
    { nums: [-1, -2, -3, -4, -5], target: -8, expected: [2, 4] }
];

let passed = 0;
let failed = 0;

testCases.forEach((test, i) => {
    try {
        const result = twoSum(test.nums, test.target);
        const isCorrect = (
            result.length === 2 &&
            test.nums[result[0]] + test.nums[result[1]] === test.target &&
            result[0] !== result[1]
        );
        
        if (isCorrect) {
            console.log(\`✓ Test \${i + 1} passed\`);
            passed++;
        } else {
            console.error(\`✗ Test \${i + 1} failed\`);
            failed++;
        }
    } catch (error) {
        console.error(\`✗ Test \${i + 1} failed: \${error.message}\`);
        failed++;
    }
});

console.log(\`\\n\${passed}/\${testCases.length} tests passed\`);
if (failed > 0) process.exit(1);`;

                setTabs((prev) =>
                    prev.map((tab) =>
                        tab.id === 'tests' ? { ...tab, content: testCases } : tab
                    )
                );
            }
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
            setAgentState('idle');  // Reset agent state after response

            // Auto-speak AI responses using Azure TTS
            if (message.speak && message.role === 'assistant' && message.content) {
                // Use Azure TTS (falls back to browser TTS if unavailable)
                textToSpeech(message.content, true).catch(error => {
                    console.warn('TTS failed:', error);
                });
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

    // Proctoring: Tab visibility - show warning when tab is switched
    useEffect(() => {
        const handleVisibilityChange = () => {
            if (document.hidden && interviewPhase === 'started') {
                const newCount = tabSwitchCount + 1;
                setTabSwitchCount(newCount);

                if (socket) {
                    sendProctoringEvent(socket, 'tab_switch', {
                        timestamp: Date.now(),
                        count: newCount
                    });
                }

                // Show warning modal
                if (newCount >= 3) {
                    setWarningMessage(`⚠️ FINAL WARNING: You have switched tabs ${newCount} times. One more violation and you will be DISQUALIFIED from this interview.`);
                } else {
                    setWarningMessage(`⚠️ WARNING: Tab switch detected (${newCount}/3). Switching tabs during the interview is not allowed and may result in disqualification.`);
                }
                setShowWarningModal(true);
            }
        };

        const handleFullscreenChange = () => {
            if (!document.fullscreenElement && interviewPhase === 'started') {
                // User exited fullscreen during interview - show warning
                setWarningMessage('⚠️ WARNING: Fullscreen mode is required during the interview. Please remain in fullscreen mode to avoid disqualification.');
                setShowWarningModal(true);
                setIsFullscreen(false);
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);
        document.addEventListener('fullscreenchange', handleFullscreenChange);

        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
            document.removeEventListener('fullscreenchange', handleFullscreenChange);
        };
    }, [socket, interviewPhase, tabSwitchCount]);

    // Proctoring: Paste detection with warning
    useEffect(() => {
        const handlePaste = (e: ClipboardEvent) => {
            if (interviewPhase === 'started') {
                const pastedText = e.clipboardData?.getData('text') || '';
                const newCount = pasteCount + 1;
                setPasteCount(newCount);

                if (socket) {
                    sendProctoringEvent(socket, 'paste_detected', {
                        length: pastedText.length,
                        timestamp: Date.now(),
                        count: newCount
                    });
                }

                // Show warning for paste
                if (pastedText.length > 50) {
                    setWarningMessage(`⚠️ WARNING: Large paste detected (${pastedText.length} characters). Pasting code from external sources is being monitored. Paste count: ${newCount}`);
                    setShowWarningModal(true);
                }
            }
        };

        document.addEventListener('paste', handlePaste);
        return () => document.removeEventListener('paste', handlePaste);
    }, [socket, interviewPhase, pasteCount]);

    // Start Interview - triggers AI greeting with TTS
    // Enter fullscreen mode
    const enterFullscreen = async () => {
        try {
            await document.documentElement.requestFullscreen();
            setIsFullscreen(true);
        } catch (error) {
            console.warn('Fullscreen request failed:', error);
        }
    };

    // Exit fullscreen
    const exitFullscreen = () => {
        if (document.fullscreenElement) {
            document.exitFullscreen();
            setIsFullscreen(false);
        }
    };

    const startInterview = async () => {
        // Enter fullscreen mode first
        await enterFullscreen();

        setInterviewPhase('started');
        setIsAISpeaking(true);

        // AI Introduction greeting
        const voiceGreeting = `Hello and welcome to your technical interview! I'm your AI Interviewer today, powered by advanced artificial intelligence technology. Before we begin with the coding problem, I'd love to hear a bit about yourself. Please take a moment to introduce yourself - tell me about your background, your experience, and what excites you most about software development. You can speak or type your response.`;

        // Wait 500ms then play TTS
        setTimeout(async () => {
            try {
                console.log('Starting AI introduction TTS...');
                await textToSpeech(voiceGreeting, true);
                console.log('AI introduction TTS completed');
                setIsAISpeaking(false);
            } catch (error) {
                console.warn('AI introduction TTS failed:', error);
                setIsAISpeaking(false);
            }
        }, 500);
    };

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

            // Proactive AI when stuck (2 minutes idle with code)
            if (idleTime > 120000 && hasCode && !hasHintedRef.current && socket && connected) {
                hasHintedRef.current = true;

                // AI proactively asks/suggests
                const aiMessages = [
                    "I notice you've been working on this for a while. Would you like a hint about the algorithm approach?",
                    "I see you're taking some time here. Would it help if I explained the optimal time complexity for this problem?",
                    "You've been quiet for a bit. Are you stuck on a specific part? I can help with hints!",
                    "I'm here to help! Would you like me to suggest a data structure that might work well for this problem?"
                ];

                const randomMessage = aiMessages[Math.floor(Math.random() * aiMessages.length)];

                setChatMessages(prev => [...prev, {
                    role: 'assistant',
                    content: randomMessage,
                    timestamp: new Date().toISOString()
                }]);

                // Speak the AI message using Azure TTS
                textToSpeech(randomMessage, true).catch(error => {
                    console.warn('Azure TTS failed:', error);
                });
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

        // Stop any AI speech when user runs code (user interrupt)
        stopSpeech();

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
            setAgentState('thinking');  // Show agent is processing
            sendChatMessage(socket, message);
        }
    };

    const handleClearConsole = () => setConsoleOutputs([]);
    const currentTab = tabs.find((t) => t.id === activeTab);

    return (
        <div className="h-[100dvh] flex flex-col bg-gray-950 text-white overflow-hidden">
            {/* Start Interview Overlay */}
            {interviewPhase === 'waiting' && sessionData && (
                <div className="absolute inset-0 z-50 bg-gray-950/95 backdrop-blur-sm flex items-center justify-center">
                    <div className="bg-gray-900 border border-gray-700 rounded-2xl p-8 max-w-lg mx-4 text-center shadow-2xl">
                        <div className="w-20 h-20 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
                            <span className="text-4xl">🎙️</span>
                        </div>
                        <h2 className="text-2xl font-bold mb-4">Ready to Start Your Interview?</h2>
                        <p className="text-gray-400 mb-6">
                            Your AI Interviewer will introduce themselves and ask you to share a bit about your background before presenting the coding challenge.
                        </p>
                        <p className="text-sm text-gray-500 mb-6">
                            <strong>Problem:</strong> {sessionData.problem_title} • <strong>Duration:</strong> 45 minutes
                        </p>
                        <button
                            onClick={startInterview}
                            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-4 px-8 rounded-xl transition-all transform hover:scale-105 flex items-center justify-center gap-3 text-lg"
                        >
                            <Play className="w-6 h-6" />
                            Start Interview
                        </button>
                        <p className="text-xs text-gray-500 mt-4">
                            🔊 Audio will play - ensure your speakers are on
                        </p>
                    </div>
                </div>
            )}

            {/* AI Speaking Indicator */}
            {isAISpeaking && (
                <div className="absolute top-20 left-1/2 transform -translate-x-1/2 z-40 bg-blue-600/90 text-white px-4 py-2 rounded-full flex items-center gap-2 shadow-lg">
                    <div className="w-3 h-3 bg-white rounded-full animate-pulse"></div>
                    <span className="text-sm font-medium">AI Interviewer is speaking...</span>
                </div>
            )}

            {/* Proctoring Warning Modal */}
            {showWarningModal && (
                <div className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
                    <div className="bg-gray-900 border-2 border-red-500 rounded-2xl p-8 max-w-md text-center shadow-2xl animate-in zoom-in-95 duration-200">
                        <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                            <span className="text-4xl">⚠️</span>
                        </div>
                        <h2 className="text-xl font-bold text-red-400 mb-4">Proctoring Alert</h2>
                        <p className="text-gray-300 mb-6 leading-relaxed">
                            {warningMessage}
                        </p>
                        <div className="space-y-3">
                            <button
                                onClick={() => {
                                    setShowWarningModal(false);
                                    enterFullscreen();
                                }}
                                className="w-full bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-6 rounded-xl transition-all"
                            >
                                I Understand - Return to Interview
                            </button>
                            <div className="text-xs text-gray-500">
                                Tab Switches: {tabSwitchCount}/3 • Pastes: {pasteCount}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Proctoring Status Bar */}
            {interviewPhase === 'started' && (
                <div className="absolute top-0 right-0 m-2 z-30 flex items-center gap-2 bg-gray-900/90 px-3 py-1.5 rounded-full border border-gray-700 text-xs">
                    <div className={`w-2 h-2 rounded-full ${isFullscreen ? 'bg-green-500' : 'bg-yellow-500 animate-pulse'}`}></div>
                    <span className="text-gray-400">
                        {isFullscreen ? 'Proctored' : 'Not Fullscreen'}
                    </span>
                    {tabSwitchCount > 0 && (
                        <span className="text-red-400 font-medium">• {tabSwitchCount} warnings</span>
                    )}
                </div>
            )}

            {/* Header */}
            <header className="h-16 flex-shrink-0 bg-gray-900 border-b border-gray-700 flex items-center justify-between px-4 lg:px-6 z-10">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-lg">AI</div>
                    <div className="hidden sm:block">
                        <h1 className="text-base font-bold text-white leading-tight">{sessionData?.problem_title || 'Loading...'}</h1>
                        <p className="text-xs text-gray-400">Session: {sessionId.slice(0, 8)}...</p>
                    </div>
                </div>

                <div className="flex items-center gap-3 sm:gap-4">
                    <div className="hidden md:flex items-center gap-2 text-sm text-gray-400 bg-gray-800/50 px-3 py-1.5 rounded-full border border-gray-700">
                        <Clock className="w-4 h-4" />
                        <span>45:00</span>
                    </div>

                    {/* Agent Status Indicator */}
                    <AgentStatus state={agentState} className="hidden md:flex" />

                    <div className="flex items-center gap-2">
                        {connected ? (
                            <div className="flex items-center gap-1.5 bg-green-500/10 px-2.5 py-1 rounded-full border border-green-500/20">
                                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                <span className="text-xs font-medium text-green-400 hidden sm:inline">Connected</span>
                            </div>
                        ) : (
                            <div className="flex items-center gap-1.5 bg-red-500/10 px-2.5 py-1 rounded-full border border-red-500/20">
                                <span className="w-2 h-2 rounded-full bg-red-500" />
                                <span className="text-xs font-medium text-red-400 hidden sm:inline">Disconnected</span>
                            </div>
                        )}
                    </div>

                    <button
                        onClick={handleRunCode}
                        disabled={isExecuting || !connected}
                        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 disabled:from-gray-700 disabled:to-gray-800 disabled:cursor-not-allowed rounded-lg font-medium text-sm transition-all shadow-lg shadow-green-900/20"
                    >
                        {isExecuting ? (
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <Play className="w-4 h-4 fill-current" />
                        )}
                        <span className="hidden sm:inline">{isExecuting ? 'Running...' : 'Run Code'}</span>
                    </button>
                </div>
            </header>

            {/* Main Layout - Responsive Grid/Flex */}
            <div className="flex-1 flex flex-col md:flex-row overflow-hidden relative">

                {/* Left Panel: Editor & Console */}
                <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
                    {/* Top: Editor */}
                    <div className="flex-1 flex flex-col min-h-0 bg-gray-900/50 relative">
                        <div className="absolute inset-0 flex flex-col p-2 sm:p-4 gap-2 sm:gap-4">
                            <div className="flex-1 flex flex-col bg-gray-900 rounded-xl overflow-hidden border border-gray-800 shadow-xl">
                                <TabManager tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
                                <div className="flex-1 relative" key={activeTab}>
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
                        </div>
                    </div>

                    {/* Bottom: Console (Resizable idea, but fixed for now) */}
                    <div className="h-48 sm:h-64 md:h-72 flex-shrink-0 bg-gray-950 border-t border-gray-800 p-2 sm:p-4 z-10">
                        <OutputConsole outputs={consoleOutputs} onClear={handleClearConsole} />
                    </div>
                </div>

                {/* Right Panel: Chat - Collapsible on mobile or stacked? Stacked logic here. */}
                <div className="w-full md:w-80 lg:w-96 flex-shrink-0 border-t md:border-t-0 md:border-l border-gray-800 bg-gray-900 flex flex-col h-[40vh] md:h-full z-20 shadow-2xl">
                    <div className="flex-1 flex flex-col min-h-0">
                        <ChatPanel messages={chatMessages} onSendMessage={handleSendMessage} isLoading={isChatLoading} />
                    </div>
                </div>
            </div>
        </div>
    );
}
