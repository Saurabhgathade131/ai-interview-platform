/**
 * Output Console Component
 * Displays execution results with stdout/stderr separation
 */
'use client';

import React, { useEffect, useRef } from 'react';
import { Terminal, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConsoleOutput {
    type: 'stdout' | 'stderr' | 'system';
    text: string;
    timestamp: Date;
}

interface OutputConsoleProps {
    outputs: ConsoleOutput[];
    onClear: () => void;
}

export default function OutputConsole({ outputs, onClear }: OutputConsoleProps) {
    const consoleEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when new output arrives
    useEffect(() => {
        consoleEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [outputs]);

    return (
        <div className="h-full flex flex-col bg-gray-950 border border-gray-700 rounded-lg overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-700">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-300">
                    <Terminal className="w-4 h-4" />
                    Output Console
                </div>
                <button
                    onClick={onClear}
                    className="p-1 hover:bg-gray-800 rounded transition-colors"
                    title="Clear console"
                >
                    <Trash2 className="w-4 h-4 text-gray-400" />
                </button>
            </div>

            {/* Console Output */}
            <div className="flex-1 overflow-y-auto p-4 font-mono text-sm">
                {outputs.length === 0 ? (
                    <div className="text-gray-500 italic">
                        No output yet. Run your code to see results here.
                    </div>
                ) : (
                    outputs.map((output, index) => (
                        <div
                            key={index}
                            className={cn(
                                'mb-1 whitespace-pre-wrap break-words',
                                output.type === 'stderr' && 'text-red-400',
                                output.type === 'stdout' && 'text-green-300',
                                output.type === 'system' && 'text-blue-300'
                            )}
                        >
                            {output.text}
                        </div>
                    ))
                )}
                <div ref={consoleEndRef} />
            </div>
        </div>
    );
}
