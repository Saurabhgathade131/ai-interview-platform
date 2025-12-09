/**
 * Chat Panel Component
 * Displays conversation with AI interviewer
 */
'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Bot, User, Send, Lightbulb, Mic, MicOff, Volume2, AlertCircle } from 'lucide-react';
import { ChatMessage } from '@/types';
import { formatTime, cn } from '@/lib/utils';

interface ChatPanelProps {
    messages: ChatMessage[];
    onSendMessage: (message: string) => void;
    isLoading?: boolean;
}

export default function ChatPanel({ messages, onSendMessage, isLoading = false }: ChatPanelProps) {
    const [inputValue, setInputValue] = React.useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Voice State
    const [isVoiceMode, setIsVoiceMode] = React.useState(false);
    const [isListening, setIsListening] = React.useState(false);
    const [isSpeaking, setIsSpeaking] = React.useState(false);
    const [selectedVoice, setSelectedVoice] = React.useState<SpeechSynthesisVoice | null>(null);
    const [highlightIndex, setHighlightIndex] = useState<number>(0);

    // Refs for persistence across renders
    const recognitionRef = useRef<any>(null);
    const synthesisRef = useRef<SpeechSynthesis | null>(null);
    const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);

    // Initialize Speech Services & Load Voices
    useEffect(() => {
        if (typeof window !== 'undefined') {
            synthesisRef.current = window.speechSynthesis;

            // Load voices
            const loadVoices = () => {
                const voices = window.speechSynthesis.getVoices();
                // Prefer Google US English or a female voice for better clarity
                const preferredVoice = voices.find(v =>
                    v.name.includes('Google US English') ||
                    v.name.includes('Samantha') ||
                    v.lang === 'en-US'
                );
                if (preferredVoice) setSelectedVoice(preferredVoice);
            };

            loadVoices();
            window.speechSynthesis.onvoiceschanged = loadVoices;

            // Setup Speech Recognition
            const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
            if (SpeechRecognition) {
                const recognition = new SpeechRecognition();
                recognition.continuous = true; // Keep listening 
                recognition.interimResults = true; // Required for faster interruption detection
                recognition.lang = 'en-US';

                recognition.onstart = () => setIsListening(true);

                recognition.onend = () => {
                    setIsListening(false);
                    // Auto-restart if in voice mode AND AI is NOT speaking
                    // This prevents the loop where recognition restarts during AI speech
                    if (isVoiceMode && !window.speechSynthesis.speaking) {
                        try {
                            recognition.start();
                        } catch (e) { /* Already started */ }
                    }
                };

                // Detect speech
                recognition.onresult = (event: any) => {
                    // 1. Handle Interruption: Stop AI if it's speaking
                    if (window.speechSynthesis.speaking) {
                        window.speechSynthesis.cancel();
                        setIsSpeaking(false);
                        setHighlightIndex(0);
                    }

                    // 2. Process Result
                    const result = event.results[event.results.length - 1];
                    const transcript = result[0].transcript;

                    // REAL-TIME INPUT UPDATE
                    setInputValue(transcript);

                    // Reset silence timer on every new word
                    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);

                    if (result.isFinal) {
                        // Send immediately if final
                        if (transcript.trim()) {
                            onSendMessage(transcript.trim());
                            setInputValue(''); // Clear after sending
                        }
                    } else {
                        // VAD: If 1.2s silence during interim results, assume finished (Reduced from 1.5s for better responsiveness)
                        silenceTimerRef.current = setTimeout(() => {
                            recognition.stop();
                            if (transcript.trim()) {
                                onSendMessage(transcript.trim());
                                setInputValue(''); // Clear after sending
                            }
                        }, 1200);
                    }
                };

                recognitionRef.current = recognition;
            }
        }
    }, [isVoiceMode, onSendMessage]);

    // Handle Voice Mode Toggling
    const toggleVoiceMode = () => {
        if (isVoiceMode) {
            setIsVoiceMode(false);
            synthesisRef.current?.cancel();
            recognitionRef.current?.stop();
            setIsSpeaking(false);
            setHighlightIndex(0);
        } else {
            setIsVoiceMode(true);
            try {
                recognitionRef.current?.start();
            } catch (e) {
                console.error("Failed to start recognition", e);
            }
        }
    };

    // Speak incoming AI messages
    useEffect(() => {
        const lastMessage = messages[messages.length - 1];

        // Ensure strictly only the AI speaks and we are in voice mode
        if (isVoiceMode && lastMessage?.role === 'assistant' && synthesisRef.current) {
            // Cancel previous speech
            synthesisRef.current.cancel();

            // Prepare text
            const textToSpeak = lastMessage.content
                .replace(/```[\s\S]*?```/g, " I've written some code for you to check. ") // Friendly replacement
                .replace(/[*_`]/g, "");

            const utterance = new SpeechSynthesisUtterance(textToSpeak);

            if (selectedVoice) {
                utterance.voice = selectedVoice;
            }

            utterance.rate = 1.1; // Slightly faster for natural feel
            utterance.pitch = 1.0;

            utterance.onstart = () => {
                setIsSpeaking(true);
                setHighlightIndex(0);
                // CRITICAL: Stop listening while AI speaks to prevent self-loop
                if (isListening && recognitionRef.current) {
                    recognitionRef.current.stop();
                }
            };

            utterance.onend = () => {
                setIsSpeaking(false);
                setHighlightIndex(0);
                // Resume listening only if we are still in voice mode
                if (isVoiceMode && recognitionRef.current) {
                    try {
                        recognitionRef.current.start();
                    } catch (e) { /* Already started */ }
                }
            };

            // Karaoke Effect: Track word boundaries
            utterance.onboundary = (event) => {
                if (event.name === 'word') {
                    setHighlightIndex(event.charIndex);
                }
            };

            synthesisRef.current.speak(utterance);
        }
    }, [messages, isVoiceMode, selectedVoice, isListening]); // Added isListening to deps

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, highlightIndex]); // Also scroll on highlight update

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (inputValue.trim() && !isLoading) {
            onSendMessage(inputValue.trim());
            setInputValue('');
        }
    };

    // Helper to render text with highlights
    const renderMessageContent = (content: string, isSpeakingThis: boolean) => {
        if (!isSpeakingThis || !isVoiceMode) return <div className="text-sm whitespace-pre-wrap">{content}</div>;

        // Simple approach: Split string into spoken (past) and current/future
        // Note: charIndex from onboundary is start of current word
        const before = content.slice(0, highlightIndex);
        const after = content.slice(highlightIndex);

        return (
            <div className="text-sm whitespace-pre-wrap">
                <span className="opacity-60 transition-opacity duration-300">{before}</span>
                <span className="font-bold text-white transition-all duration-300 bg-blue-500/20 box-decoration-clone px-0.5 rounded shadow-[0_0_10px_rgba(59,130,246,0.5)]">
                    {after.split(' ')[0]}
                </span>
                <span className="text-gray-300">{after.slice(after.split(' ')[0].length)}</span>
            </div>
        );
    };

    return (
        <div className="h-full flex flex-col bg-gray-900">
            {/* Header */}
            <div className="px-4 py-3 bg-gray-900/95 backdrop-blur border-b border-gray-800 flex justify-between items-center z-10">
                <div>
                    <div className="flex items-center gap-2">
                        <Bot className="w-5 h-5 text-blue-400" />
                        <h3 className="font-semibold text-white tracking-wide">AI Interviewer</h3>
                    </div>
                    <div className="flex items-center gap-1.5 mt-1">
                        <div className={`w-1.5 h-1.5 rounded-full ${isVoiceMode ? 'bg-green-500 animate-pulse' : 'bg-gray-600'}`} />
                        <p className="text-xs text-gray-400">
                            {isVoiceMode ? (isListening ? "Listening..." : isSpeaking ? "Speaking..." : "Voice Active") : "Text Mode"}
                        </p>
                    </div>
                </div>

                <button
                    onClick={toggleVoiceMode}
                    className={cn(
                        "p-2.5 rounded-full transition-all duration-300 shadow-lg",
                        isVoiceMode
                            ? "bg-red-500/10 text-red-400 hover:bg-red-500/20 ring-1 ring-red-500/50"
                            : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white"
                    )}
                    title={isVoiceMode ? "Stop Voice Mode" : "Start Voice Mode"}
                >
                    {isVoiceMode ? (
                        isListening ? (
                            <div className="relative">
                                <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full animate-ping" />
                                <Mic className="w-5 h-5" />
                            </div>
                        ) : <Volume2 className="w-5 h-5 animate-pulse" />
                    ) : (
                        <MicOff className="w-5 h-5" />
                    )}
                </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin scrollbar-thumb-gray-800 scrollbar-track-transparent">
                {messages.map((message, index) => {
                    const isLast = index === messages.length - 1;
                    const isAssistant = message.role === 'assistant';
                    const isError = message.content.includes("Error:") || message.content.includes("trouble connecting");

                    return (
                        <div
                            key={index}
                            className={cn(
                                'flex gap-4 group',
                                message.role === 'user' ? 'justify-end' : 'justify-start'
                            )}
                        >
                            {isAssistant && (
                                <div className="flex-shrink-0 mt-1">
                                    {message.is_hint ? (
                                        <div className="w-8 h-8 rounded-full bg-yellow-500/20 border border-yellow-500/30 flex items-center justify-center shadow-lg shadow-yellow-900/20">
                                            <Lightbulb className="w-4 h-4 text-yellow-400" />
                                        </div>
                                    ) : (
                                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-900/20">
                                            {isSpeaking && isLast && isVoiceMode ? (
                                                <Volume2 className="w-4 h-4 text-white animate-pulse" />
                                            ) : (
                                                <Bot className="w-4 h-4 text-white" />
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}

                            <div
                                className={cn(
                                    'max-w-[85%] rounded-2xl px-5 py-3 shadow-md transition-all duration-300',
                                    message.role === 'user'
                                        ? 'bg-blue-600 text-white rounded-br-none hover:bg-blue-500'
                                        : isError
                                            ? 'bg-red-900/20 border border-red-500/30 text-red-200 rounded-bl-none'
                                            : message.is_hint
                                                ? 'bg-yellow-900/20 border border-yellow-500/30 text-yellow-100 rounded-bl-none'
                                                : 'bg-gray-800/80 border border-gray-700/50 text-gray-100 rounded-bl-none hover:border-gray-600/50 backdrop-blur-sm'
                                )}
                            >
                                {isError && <div className="flex items-center gap-2 mb-2 text-red-400 font-bold text-xs uppercase tracking-wider"><AlertCircle className="w-3 h-3" /> Error</div>}

                                {renderMessageContent(message.content, isAssistant && isSpeaking && isLast)}

                                <div className="text-[10px] opacity-40 mt-1.5 flex justify-end font-medium tracking-wide">{formatTime(message.timestamp)}</div>
                            </div>

                            {message.role === 'user' && (
                                <div className="flex-shrink-0 mt-1">
                                    <div className="w-8 h-8 rounded-full bg-gray-700 border border-gray-600 flex items-center justify-center">
                                        <User className="w-4 h-4 text-gray-300" />
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}

                {isLoading && (
                    <div className="flex gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500/20 to-purple-500/20 flex items-center justify-center border border-white/10 shadow-lg">
                            <Bot className="w-4 h-4 text-blue-400 animate-pulse" />
                        </div>
                        <div className="bg-gray-800/80 backdrop-blur-md rounded-2xl rounded-bl-none px-6 py-4 border border-white/5 shadow-xl">
                            <div className="flex gap-2 items-center">
                                <div className="w-2 h-2 bg-gradient-to-r from-blue-400 to-cyan-400 rounded-full animate-[bounce_1s_infinite_0ms]" />
                                <div className="w-2 h-2 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full animate-[bounce_1s_infinite_200ms]" />
                                <div className="w-2 h-2 bg-gradient-to-r from-teal-400 to-green-400 rounded-full animate-[bounce_1s_infinite_400ms]" />
                                <span className="text-xs text-gray-400 ml-2 font-medium tracking-wide animate-pulse">Thinking...</span>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSubmit} className="p-4 bg-gray-900/95 border-t border-gray-800 backdrop-blur">
                <div className="flex gap-3 items-center">
                    <div className="relative">
                        <button
                            type="button"
                            onClick={toggleVoiceMode}
                            className={cn(
                                "p-3 rounded-xl transition-all duration-300 flex-shrink-0 z-10 relative",
                                isVoiceMode
                                    ? "bg-red-500/10 text-red-400 ring-1 ring-red-500/50"
                                    : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white"
                            )}
                            title={isVoiceMode ? "Stop Voice Mode" : "Start Voice Mode"}
                        >
                            {isListening ? (
                                <Mic className="w-5 h-5 animate-pulse" />
                            ) : (
                                <MicOff className="w-5 h-5" />
                            )}
                        </button>
                        {isListening && (
                            <div className="absolute -inset-1 rounded-xl bg-red-500/20 blur-sm animate-pulse z-0" />
                        )}
                    </div>

                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder={isVoiceMode ? (isListening ? "Listening... (Speak now)" : "Voice Active (Waiting...)") : "Type your message..."}
                        className={cn(
                            "flex-1 bg-gray-950 border border-gray-800 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all",
                            isListening && "border-blue-500/30 ring-1 ring-blue-500/20"
                        )}
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={!inputValue.trim() || isLoading}
                        className="px-4 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed rounded-xl transition-all shadow-lg shadow-blue-900/20 hover:shadow-blue-900/40 flex-shrink-0"
                    >
                        <Send className="w-5 h-5 text-white" />
                    </button>
                </div>
            </form>
        </div>
    );
}
