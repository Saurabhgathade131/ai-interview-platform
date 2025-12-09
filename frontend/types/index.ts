/**
 * TypeScript type definitions for the AI Interview Platform
 */

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  is_hint?: boolean;
}

export interface ExecutionResult {
  stdout?: string;
  stderr?: string;
  compile_output?: string;
  status: string;
  test_passed: boolean;
  test_total: number;
  time?: number;
  memory?: number;
}

export interface SessionData {
  session_id: string;
  problem_title: string;
  initial_code: string;
  chat_history: ChatMessage[];
  status: 'waiting' | 'in_progress' | 'completed';
}

export interface ProctoringEvent {
  type: 'tab_switch' | 'paste_detected' | 'copy_detected';
  metadata?: Record<string, any>;
}

export interface Tab {
  id: string;
  name: string;
  content: string;
  readOnly: boolean;
}
