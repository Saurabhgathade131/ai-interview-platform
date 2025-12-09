/**
 * Socket.io client for real-time communication with backend
 */
import { io, Socket } from 'socket.io-client';

const SOCKET_URL = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000';

class SocketClient {
    private socket: Socket | null = null;

    connect(): Socket {
        if (!this.socket) {
            this.socket = io(SOCKET_URL, {
                transports: ['polling', 'websocket'],
                autoConnect: true,
                withCredentials: false,
            });

            this.socket.on('connect', () => {
                console.log('✅ Connected to server:', this.socket?.id);
            });

            this.socket.on('disconnect', () => {
                console.log('❌ Disconnected from server');
            });

            this.socket.on('connect_error', (error) => {
                console.error('Connection error:', error);
            });
        }

        return this.socket;
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
    }

    getSocket(): Socket | null {
        return this.socket;
    }
}

// Singleton instance
export const socketClient = new SocketClient();

// Helper functions for common events
export const joinSession = (socket: Socket, sessionId: string, candidateName?: string) => {
    socket.emit('join_session', { session_id: sessionId, candidate_name: candidateName });
};

export const sendCodeUpdate = (socket: Socket, code: string) => {
    socket.emit('code_update', { code });
};

export const runCode = (socket: Socket, code: string) => {
    socket.emit('run_code', { code });
};

export const sendChatMessage = (socket: Socket, message: string) => {
    socket.emit('chat_message', { message });
};

export const sendProctoringEvent = (socket: Socket, type: string, metadata?: Record<string, any>) => {
    socket.emit('proctoring_event', { type, metadata });
};
