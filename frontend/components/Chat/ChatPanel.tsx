/**
 * Chat Panel Component
 * Displays conversation with AI interviewer
 * TTS: Azure Jenny Neural (high quality)
 * STT: Browser Web Speech API (fast, no network call)
 */
'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Bot, User, Send, Lightbulb, Mic, MicOff, AlertCircle } from 'lucide-react';
import { ChatMessage } from '@/types';
import { formatTime, cn } from '@/lib/utils';
import { stopSpeech } from '@/lib/speech';

interface ChatPanelProps {
    messages: ChatMessage[];
    onSendMessage: (message: string) => void;
    isLoading?: boolean;
}

export default function ChatPanel({ messages, onSendMessage, isLoading = false }: ChatPanelProps) {
    const [inputValue, setInputValue] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Voice State - using browser Web Speech API for STT
    const [isListening, setIsListening] = useState(false);
    const [speechSupported, setSpeechSupported] = useState(false);

    // Speech recognition ref
    const recognitionRef = useRef<any>(null);
    const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);

    // Initialize browser Speech Recognition
    useEffect(() => {
        if (typeof window !== 'undefined') {
            const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

            if (SpeechRecognition) {
                setSpeechSupported(true);
                const recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = true;
                recognition.lang = 'en-US';

                recognition.onstart = () => {
                    setIsListening(true);
                    // Stop any AI speech when user starts speaking
                    stopSpeech();
                };

                recognition.onend = () => {
                    setIsListening(false);
                };

                recognition.onresult = (event: any) => {
                    const result = event.results[event.results.length - 1];
                    const transcript = result[0].transcript;

                    // Update input in real-time
                    setInputValue(transcript);

                    // Clear any existing silence timer
                    if (silenceTimerRef.current) {
                        clearTimeout(silenceTimerRef.current);
                    }

                    if (result.isFinal) {
                        // Auto-send after 1.5 second delay when speech is final
                        silenceTimerRef.current = setTimeout(() => {
                            if (transcript.trim()) {
                                onSendMessage(transcript.trim());
                                setInputValue('');
                            }
                        }, 1500);
                    }
                };

                recognition.onerror = (event: any) => {
                    console.warn('Speech recognition error:', event.error);
                    setIsListening(false);
                };

                recognitionRef.current = recognition;
            }
        }

        return () => {
            if (silenceTimerRef.current) {
                clearTimeout(silenceTimerRef.current);
            }
        };
    }, [onSendMessage]);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Toggle speech recognition
    const toggleListening = () => {
        if (!recognitionRef.current) return;

        if (isListening) {
            recognitionRef.current.stop();
        } else {
            try {
                recognitionRef.current.start();
            } catch (e) {
                console.warn('Recognition already started');
            }
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (inputValue.trim() && !isLoading) {
            // Stop any AI speech when user sends a message
            stopSpeech();
            onSendMessage(inputValue.trim());
            setInputValue('');
        }
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
                        <div className={`w-1.5 h-1.5 rounded-full ${isListening ? 'bg-red-500 animate-pulse' : 'bg-green-500'}`} />
                        <p className="text-xs text-gray-400">
                            {isListening ? "🎙️ Listening..." : "Azure TTS • Browser STT"}
                        </p>
                    </div>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin scrollbar-thumb-gray-800 scrollbar-track-transparent">
                {messages.map((message, index) => {
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
                                            <Bot className="w-4 h-4 text-white" />
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

                                <div className="text-sm whitespace-pre-wrap">{message.content}</div>

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
                    {/* Speak Button - Browser Speech Recognition */}
                    {speechSupported && (
                        <div className="relative">
                            <button
                                type="button"
                                onClick={toggleListening}
                                disabled={isLoading}
                                className={cn(
                                    "p-3 rounded-xl transition-all duration-300 flex-shrink-0 z-10 relative",
                                    isListening
                                        ? "bg-red-500 text-white ring-2 ring-red-400"
                                        : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white"
                                )}
                                title={isListening ? "Stop Listening" : "Click to Speak (auto-sends after you stop)"}
                            >
                                {isListening ? (
                                    <Mic className="w-5 h-5 animate-pulse" />
                                ) : (
                                    <Mic className="w-5 h-5" />
                                )}
                            </button>
                            {isListening && (
                                <div className="absolute -inset-1 rounded-xl bg-red-500/20 blur-sm animate-pulse z-0" />
                            )}
                        </div>
                    )}

                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder={isListening ? "Listening... speak now" : "Type or click mic to speak..."}
                        className={cn(
                            "flex-1 bg-gray-950 border border-gray-800 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all",
                            isListening && "border-red-500/30 ring-1 ring-red-500/20"
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

                {/* Listening indicator */}
                {isListening && (
                    <div className="mt-2 text-center text-sm text-red-400 animate-pulse">
                        🎙️ Listening... (auto-sends 1.5s after you stop speaking)
                    </div>
                )}
            </form>
        </div>
    );
}
