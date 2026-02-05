"""
TimeBars Utility Module
Handles audio playback and other utility functions.
"""

import threading
import logging
import wave
import io
import array
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import winsound (Windows only)
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False
    logger.warning("winsound not available (non-Windows platform)")


class AudioManager:
    """Manages audio playback for alarms."""
    
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.base_path = data_path.parent
        
        # Check sounds directory first (packaged), then data directory
        sounds_path = self.base_path / "sounds" / "alarm-bleep.wav"
        data_path_wav = data_path / "alarm-bleep.wav"
        
        if sounds_path.exists():
            self.alarm_path = sounds_path
        elif data_path_wav.exists():
            self.alarm_path = data_path_wav
        else:
            self.alarm_path = sounds_path  # Will fail gracefully in playback
            
        self._stop_event = threading.Event()
        self._playback_thread: Optional[threading.Thread] = None
        
    def _check_alarm_file(self) -> bool:
        """Check if alarm file exists."""
        if self.alarm_path.exists():
            return True
        logger.warning(f"Alarm file not found: {self.alarm_path}")
        return False
    
    def _convert_stereo_to_mono(self, input_path: Path) -> bytes:
        """
        Convert stereo 44.1kHz WAV to mono format that winsound handles correctly.
        Returns bytes of converted WAV data.
        """
        try:
            with wave.open(str(input_path), 'rb') as wav_in:
                # Get input parameters
                n_channels = wav_in.getnchannels()
                sample_width = wav_in.getsampwidth()
                framerate = wav_in.getframerate()
                n_frames = wav_in.getnframes()
                
                # Read all frames
                frames = wav_in.readframes(n_frames)
                
                # If already mono, return original file bytes
                if n_channels == 1:
                    with open(input_path, 'rb') as f:
                        return f.read()
                
                # Convert stereo to mono by averaging channels
                # For 16-bit samples, each sample is 2 bytes
                if sample_width == 2:
                    # Convert bytes to array of signed shorts
                    stereo_data = array.array('h', frames)
                    mono_data = array.array('h')
                    
                    # Average left and right channels (stereo interleaved: L,R,L,R...)
                    for i in range(0, len(stereo_data), 2):
                        left = stereo_data[i]
                        right = stereo_data[i + 1]
                        mono_data.append((left + right) // 2)
                    
                    # Create output WAV in memory
                    output = io.BytesIO()
                    with wave.open(output, 'wb') as wav_out:
                        wav_out.setnchannels(1)  # Mono
                        wav_out.setsampwidth(sample_width)
                        wav_out.setframerate(framerate)
                        wav_out.writeframes(mono_data.tobytes())
                    
                    return output.getvalue()
                else:
                    # For other bit depths, just return original
                    with open(input_path, 'rb') as f:
                        return f.read()
                    
        except Exception as e:
            logger.error(f"Failed to convert audio: {e}")
            # Return original file content as fallback
            with open(input_path, 'rb') as f:
                return f.read()
    
    def play_alarm_sync(self) -> None:
        """Play the alarm sound synchronously (blocking)."""
        if not HAS_WINSOUND:
            logger.warning("Cannot play sound: winsound not available")
            return
            
        if self._check_alarm_file():
            try:
                # Convert stereo to mono for proper playback speed
                mono_data = self._convert_stereo_to_mono(self.alarm_path)
                
                # Play from memory buffer
                winsound.PlaySound(
                    mono_data,
                    winsound.SND_MEMORY | winsound.SND_NODEFAULT
                )
            except Exception as e:
                logger.error(f"Failed to play alarm: {e}")
                self._fallback_beep()
        else:
            self._fallback_beep()
    
    def _fallback_beep(self) -> None:
        """Play a fallback system beep."""
        if HAS_WINSOUND:
            try:
                winsound.Beep(880, 150)
                winsound.Beep(880, 150)
                winsound.Beep(880, 150)
            except Exception as e:
                logger.error(f"Failed to play fallback beep: {e}")
    
    def play_alarm_async(self) -> None:
        """Play the alarm sound in a background thread (non-blocking)."""
        def _play():
            self.play_alarm_sync()
        
        thread = threading.Thread(target=_play, daemon=True)
        thread.start()
    
    def stop_alarm(self) -> None:
        """Stop any playing alarm loop."""
        self._stop_event.set()
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=1.0)
        self._playback_thread = None
    
    def is_playing(self) -> bool:
        """Check if alarm is currently playing."""
        return self._playback_thread is not None and self._playback_thread.is_alive()