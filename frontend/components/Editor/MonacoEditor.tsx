/**
 * Monaco Editor Component with TypeScript support
 * Handles code editing with syntax highlighting and auto-completion
 */
'use client';

import React, { useRef, useEffect } from 'react';
import Editor, { OnMount } from '@monaco-editor/react';
import { debounce } from '@/lib/utils';

interface MonacoEditorProps {
    value: string;
    onChange: (value: string) => void;
    onCodeUpdate?: (value: string) => void;
    readOnly?: boolean;
    language?: string;
}

export default function MonacoEditor({
    value,
    onChange,
    onCodeUpdate,
    readOnly = false,
    language = 'typescript',
}: MonacoEditorProps) {
    const editorRef = useRef<any>(null);

    // Debounced code update (500ms delay)
    const debouncedUpdate = useRef(
        debounce((code: string) => {
            if (onCodeUpdate) {
                onCodeUpdate(code);
            }
        }, 500)
    ).current;

    const handleEditorDidMount: OnMount = (editor, monaco) => {
        editorRef.current = editor;

        // Configure TypeScript compiler options
        monaco.languages.typescript.typescriptDefaults.setCompilerOptions({
            target: monaco.languages.typescript.ScriptTarget.ES2020,
            allowNonTsExtensions: true,
            moduleResolution: monaco.languages.typescript.ModuleResolutionKind.NodeJs,
            module: monaco.languages.typescript.ModuleKind.CommonJS,
            noEmit: true,
            esModuleInterop: true,
            jsx: monaco.languages.typescript.JsxEmit.React,
            allowJs: true,
            typeRoots: ['node_modules/@types'],
        });

        // Set up paste detection
        editor.onDidPaste((e) => {
            const pastedText = editor.getModel()?.getValueInRange(e.range) || '';

            if (pastedText.length > 50) {
                console.log('📋 Large paste detected:', pastedText.length, 'characters');

                // Emit proctoring event (will be handled by parent component)
                window.dispatchEvent(
                    new CustomEvent('paste-detected', {
                        detail: { length: pastedText.length, content: pastedText },
                    })
                );
            }
        });
    };

    const handleEditorChange = (value: string | undefined) => {
        const newValue = value || '';
        onChange(newValue);
        debouncedUpdate(newValue);
    };

    return (
        <div className="h-full w-full border border-gray-700 rounded-lg overflow-hidden">
            <Editor
                height="100%"
                language={language}
                value={value}
                onChange={handleEditorChange}
                onMount={handleEditorDidMount}
                theme="vs-dark"
                options={{
                    readOnly,
                    minimap: { enabled: true },
                    fontSize: 14,
                    lineNumbers: 'on',
                    roundedSelection: false,
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    tabSize: 2,
                    wordWrap: 'on',
                    formatOnPaste: true,
                    formatOnType: true,
                    suggestOnTriggerCharacters: true,
                    quickSuggestions: true,
                    padding: { top: 16, bottom: 16 },
                }}
            />
        </div>
    );
}
