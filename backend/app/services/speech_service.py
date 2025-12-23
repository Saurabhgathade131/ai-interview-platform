"""
Azure Speech Service Integration
High-quality TTS and STT using Azure Cognitive Services Speech SDK
"""
import asyncio
import base64
import io
from typing import Optional, AsyncGenerator
import azure.cognitiveservices.speech as speechsdk
from app.config import settings


class AzureSpeechService:
    """
    Azure Speech Service for Text-to-Speech and Speech-to-Text.
    Uses Azure Cognitive Services for high-quality voice synthesis and recognition.
    """
    
    def __init__(self):
        """Initialize Azure Speech Service with credentials from settings"""
        self.speech_key = settings.AZURE_SPEECH_KEY
        self.speech_region = settings.AZURE_SPEECH_REGION
        
        if not self.speech_key or not self.speech_region:
            raise ValueError("Azure Speech credentials not configured. Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION.")
        
        # Configure speech synthesis
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )
        
        # Use a natural-sounding neural voice
        self.speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
        
        # Configure output format for web streaming
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )
    
    async def text_to_speech(self, text: str) -> Optional[bytes]:
        """
        Convert text to speech audio bytes.
        Returns MP3 audio data suitable for web playback.
        """
        try:
            # Create synthesizer with audio output to memory stream
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=None  # No audio output, we'll get the bytes
            )
            
            # Clean text for speech (remove markdown formatting)
            clean_text = self._clean_for_speech(text)
            
            # Synthesize speech
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: synthesizer.speak_text_async(clean_text).get()
            )
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return result.audio_data
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                print(f"TTS canceled: {cancellation.reason}")
                if cancellation.error_details:
                    print(f"TTS error: {cancellation.error_details}")
                return None
                
        except Exception as e:
            print(f"TTS error: {e}")
            return None
    
    async def text_to_speech_base64(self, text: str) -> Optional[str]:
        """
        Convert text to speech and return as base64 encoded string.
        Useful for sending audio data via WebSocket/JSON.
        """
        audio_data = await self.text_to_speech(text)
        if audio_data:
            return base64.b64encode(audio_data).decode('utf-8')
        return None
    
    async def text_to_speech_ssml(self, text: str, voice: str = "en-US-JennyNeural", 
                                   rate: str = "1.0", pitch: str = "default") -> Optional[bytes]:
        """
        Advanced TTS with SSML for finer control over voice synthesis.
        """
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="{voice}">
                <prosody rate="{rate}" pitch="{pitch}">
                    {self._escape_ssml(text)}
                </prosody>
            </voice>
        </speak>
        """
        
        try:
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=None
            )
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: synthesizer.speak_ssml_async(ssml).get()
            )
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return result.audio_data
            return None
            
        except Exception as e:
            print(f"TTS SSML error: {e}")
            return None
    
    def create_speech_recognizer(self) -> speechsdk.SpeechRecognizer:
        """
        Create a speech recognizer for real-time STT.
        Returns a recognizer that can be used for continuous recognition.
        """
        # Configure for microphone input (for real-time scenarios)
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )
        
        return recognizer
    
    async def speech_to_text_from_audio(self, audio_data: bytes) -> Optional[str]:
        """
        Convert audio bytes to text.
        Accepts WAV or MP3 audio data.
        """
        try:
            # Create audio stream from bytes
            stream = speechsdk.audio.PushAudioInputStream()
            audio_config = speechsdk.audio.AudioConfig(stream=stream)
            
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Push audio data
            stream.write(audio_data)
            stream.close()
            
            # Recognize
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: recognizer.recognize_once_async().get()
            )
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                print("STT: No speech recognized")
                return None
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                print(f"STT canceled: {cancellation.reason}")
                return None
                
        except Exception as e:
            print(f"STT error: {e}")
            return None
    
    def _clean_for_speech(self, text: str) -> str:
        """Remove markdown and other formatting that shouldn't be spoken"""
        import re
        
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', ' code block ', text)
        text = re.sub(r'`[^`]+`', '', text)
        
        # Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Italic
        text = re.sub(r'#+\s*', '', text)  # Headers
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Links
        
        # Remove bullet points
        text = re.sub(r'^[-*]\s*', '', text, flags=re.MULTILINE)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _escape_ssml(self, text: str) -> str:
        """Escape special characters for SSML"""
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        return self._clean_for_speech(text)


# Singleton instance
_speech_service: Optional[AzureSpeechService] = None

def get_speech_service() -> AzureSpeechService:
    """Get or create the Azure Speech Service singleton"""
    global _speech_service
    if _speech_service is None:
        _speech_service = AzureSpeechService()
    return _speech_service
