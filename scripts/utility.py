"""
TimeBars Utility Module
Handles audio playback and other utility functions.
"""

import threading
import logging
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
        self.alarm_path = data_path / "alarm-bleep.wav"
        self._stop_event = threading.Event()
        self._playback_thread: Optional[threading.Thread] = None
        
    def _check_alarm_file(self) -> bool:
        """Check if alarm file exists."""
        if self.alarm_path.exists():
            return True
        logger.warning(f"Alarm file not found: {self.alarm_path}")
        return False
    
    def play_alarm_sync(self) -> None:
        """Play the alarm sound synchronously (blocking)."""
        if not HAS_WINSOUND:
            logger.warning("Cannot play sound: winsound not available")
            return
            
        if self._check_alarm_file():
            try:
                winsound.PlaySound(
                    str(self.alarm_path),
                    winsound.SND_FILENAME | winsound.SND_NODEFAULT
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