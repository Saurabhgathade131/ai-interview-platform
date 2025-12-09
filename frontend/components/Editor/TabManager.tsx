/**
 * Tab Manager Component
 * Manages fixed tabs for solution.js and tests.js
 */
'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { FileCode, Lock } from 'lucide-react';
import { Tab } from '@/types';

interface TabManagerProps {
    tabs: Tab[];
    activeTab: string;
    onTabChange: (tabId: string) => void;
}

export default function TabManager({ tabs, activeTab, onTabChange }: TabManagerProps) {
    return (
        <div className="flex items-center gap-1 bg-gray-900 border-b border-gray-700 px-2">
            {tabs.map((tab) => (
                <button
                    key={tab.id}
                    onClick={() => onTabChange(tab.id)}
                    className={cn(
                        'flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors',
                        'border-b-2 hover:bg-gray-800',
                        activeTab === tab.id
                            ? 'border-blue-500 text-blue-400 bg-gray-800'
                            : 'border-transparent text-gray-400'
                    )}
                >
                    <FileCode className="w-4 h-4" />
                    {tab.name}
                    {tab.readOnly && <Lock className="w-3 h-3 text-gray-500" />}
                </button>
            ))}
        </div>
    );
}
