/**
 * Agent Status Component
 * Displays the current state of the AI interviewer agent
 */
'use client';

import React from 'react';
import { Bot, Brain, Lightbulb, Code, CheckCircle, Loader2 } from 'lucide-react';

export type AgentState = 'idle' | 'thinking' | 'analyzing' | 'responding' | 'evaluating';

interface AgentStatusProps {
    state: AgentState;
    activePlugin?: string;
    className?: string;
}

const stateConfig: Record<AgentState, { icon: React.ElementType; label: string; color: string; animation: boolean }> = {
    idle: {
        icon: Bot,
        label: 'Ready',
        color: 'text-gray-400',
        animation: false
    },
    thinking: {
        icon: Brain,
        label: 'Thinking...',
        color: 'text-blue-400',
        animation: true
    },
    analyzing: {
        icon: Code,
        label: 'Analyzing Code...',
        color: 'text-purple-400',
        animation: true
    },
    responding: {
        icon: Lightbulb,
        label: 'Responding...',
        color: 'text-yellow-400',
        animation: true
    },
    evaluating: {
        icon: CheckCircle,
        label: 'Evaluating...',
        color: 'text-green-400',
        animation: true
    }
};

export default function AgentStatus({ state, activePlugin, className = '' }: AgentStatusProps) {
    const config = stateConfig[state] || stateConfig.idle;
    const Icon = config.icon;

    return (
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-800/50 border border-gray-700 ${className}`}>
            {/* Animated icon */}
            <div className={`relative ${config.animation ? 'animate-pulse' : ''}`}>
                <Icon className={`w-4 h-4 ${config.color}`} />
                {config.animation && (
                    <div className="absolute inset-0 rounded-full bg-current opacity-20 animate-ping"></div>
                )}
            </div>

            {/* State label */}
            <span className={`text-sm font-medium ${config.color}`}>
                {config.label}
            </span>

            {/* Active plugin badge */}
            {activePlugin && state !== 'idle' && (
                <span className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-300">
                    {activePlugin}
                </span>
            )}

            {/* Loading indicator */}
            {config.animation && (
                <Loader2 className="w-3 h-3 text-gray-500 animate-spin" />
            )}
        </div>
    );
}

/**
 * Compact version for smaller spaces
 */
export function AgentStatusCompact({ state }: { state: AgentState }) {
    const config = stateConfig[state] || stateConfig.idle;
    const Icon = config.icon;

    return (
        <div className={`relative ${config.animation ? 'animate-pulse' : ''}`} title={config.label}>
            <Icon className={`w-5 h-5 ${config.color}`} />
            {config.animation && (
                <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-blue-500 animate-ping"></span>
            )}
        </div>
    );
}
