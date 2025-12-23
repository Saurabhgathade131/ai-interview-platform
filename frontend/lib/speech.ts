/**
 * Azure Speech Service Client
 * Uses Microsoft Azure Cognitive Services for high-quality TTS/STT
 * NO browser fallback - Azure only
 */

const API_BASE = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000';

// Audio player instance for managing playback
let currentAudio: HTMLAudioElement | null = null;

/**
 * Convert text to speech using Microsoft Azure Speech Services
 * Returns audio as base64 or plays directly
 */
export async function textToSpeech(text: string, autoPlay: boolean = true): Promise<string | null> {
    try {
        // Stop any currently playing audio
        stopSpeech();

        const response = await fetch(`${API_BASE}/api/tts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text }),
        });

        if (!response.ok) {
            console.error('Azure TTS API error:', response.statusText);
            return null;
        }

        const data = await response.json();

        if (data.success && data.audio) {
            if (autoPlay) {
                await playBase64Audio(data.audio);
            }
            return data.audio;
        }

        console.error('Azure TTS returned no audio');
        return null;
    } catch (error) {
        console.error('Azure TTS error:', error);
        return null;
    }
}

/**
 * Play base64 encoded audio from Azure TTS
 */
export async function playBase64Audio(base64Audio: string): Promise<void> {
    try {
        // Stop any currently playing audio first
        stopSpeech();

        const audioBlob = base64ToBlob(base64Audio, 'audio/mpeg');
        const audioUrl = URL.createObjectURL(audioBlob);
        currentAudio = new Audio(audioUrl);

        return new Promise((resolve, reject) => {
            if (!currentAudio) {
                reject(new Error('Audio not initialized'));
                return;
            }

            currentAudio.onended = () => {
                URL.revokeObjectURL(audioUrl);
                currentAudio = null;
                resolve();
            };

            currentAudio.onerror = (e) => {
                URL.revokeObjectURL(audioUrl);
                currentAudio = null;
                reject(e);
            };

            currentAudio.play().catch(reject);
        });
    } catch (error) {
        console.error('Audio playback error:', error);
        throw error;
    }
}

/**
 * Convert base64 string to Blob
 */
function base64ToBlob(base64: string, mimeType: string): Blob {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);

    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }

    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
}

/**
 * Stop any ongoing speech playback
 */
export function stopSpeech(): void {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        currentAudio = null;
    }
}

/**
 * Check if TTS is currently speaking
 */
export function isSpeaking(): boolean {
    return currentAudio !== null && !currentAudio.paused;
}

/**
 * Speech-to-Text using Azure Speech Services
 * Records audio and sends to backend for transcription
 */
export async function speechToText(): Promise<string | null> {
    try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        const audioChunks: Blob[] = [];

        return new Promise((resolve, reject) => {
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());

                // Create audio blob
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

                // Convert to base64 and send to backend
                const reader = new FileReader();
                reader.onloadend = async () => {
                    const base64Audio = (reader.result as string).split(',')[1];

                    try {
                        const response = await fetch(`${API_BASE}/api/stt`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ audio: base64Audio }),
                        });

                        if (response.ok) {
                            const data = await response.json();
                            resolve(data.text || null);
                        } else {
                            resolve(null);
                        }
                    } catch (error) {
                        console.error('STT error:', error);
                        resolve(null);
                    }
                };
                reader.readAsDataURL(audioBlob);
            };

            // Start recording
            mediaRecorder.start();

            // Stop after 5 seconds (or you can make this configurable)
            setTimeout(() => {
                if (mediaRecorder.state === 'recording') {
                    mediaRecorder.stop();
                }
            }, 5000);
        });
    } catch (error) {
        console.error('Microphone access error:', error);
        return null;
    }
}
