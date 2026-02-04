"""
TimeBars Configuration Module
Handles loading and saving timer data and settings to JSON.
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    """Application settings."""
    default_alarm_enabled: bool = True
    alarm_duration_seconds: int = 5
    flash_on_alarm: bool = True
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Settings':
        return cls(
            default_alarm_enabled=data.get('default_alarm_enabled', True),
            alarm_duration_seconds=data.get('alarm_duration_seconds', 5),
            flash_on_alarm=data.get('flash_on_alarm', True)
        )


@dataclass 
class TimerData:
    """Serializable timer data for persistence."""
    id: str
    label: str
    duration_seconds: int
    alarm_enabled: bool
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TimerData':
        return cls(
            id=data.get('id', ''),
            label=data.get('label', 'Timer'),
            duration_seconds=data.get('duration_seconds', 60),
            alarm_enabled=data.get('alarm_enabled', True)
        )


class PersistenceManager:
    """Manages loading and saving application state to JSON."""
    
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.json_path = data_path / "persistent.json"
        self._settings: Settings = Settings()
        self._timer_queue: list[TimerData] = []
        
    def load(self) -> bool:
        """Load data from persistent.json."""
        try:
            if not self.json_path.exists():
                logger.warning(f"persistent.json not found at {self.json_path}, using defaults")
                self._create_default()
                return True
            
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load settings
            if 'settings' in data:
                self._settings = Settings.from_dict(data['settings'])
            
            # Load timer queue
            self._timer_queue = []
            if 'timer_queue' in data:
                for timer_data in data['timer_queue']:
                    self._timer_queue.append(TimerData.from_dict(timer_data))
            
            logger.info(f"Loaded {len(self._timer_queue)} timers from persistence")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse persistent.json: {e}")
            self._create_default()
            return False
        except Exception as e:
            logger.error(f"Failed to load persistent.json: {e}")
            return False
    
    def save(self) -> bool:
        """Save current state to persistent.json."""
        try:
            data = {
                "settings": asdict(self._settings),
                "timer_queue": [asdict(t) for t in self._timer_queue]
            }
            
            # Ensure directory exists
            self.json_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self._timer_queue)} timers to persistence")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save persistent.json: {e}")
            return False
    
    def _create_default(self) -> None:
        """Create default data structure."""
        self._settings = Settings()
        self._timer_queue = []
        self.save()
    
    @property
    def settings(self) -> Settings:
        return self._settings
    
    @settings.setter
    def settings(self, value: Settings) -> None:
        self._settings = value
        self.save()
    
    @property
    def timer_queue(self) -> list[TimerData]:
        return self._timer_queue.copy()
    
    def add_timer(self, timer: TimerData) -> None:
        """Add a timer to the queue and save."""
        self._timer_queue.append(timer)
        self.save()
    
    def remove_timer(self, timer_id: str) -> bool:
        """Remove a timer by ID and save."""
        original_len = len(self._timer_queue)
        self._timer_queue = [t for t in self._timer_queue if t.id != timer_id]
        if len(self._timer_queue) < original_len:
            self.save()
            return True
        return False
    
    def clear_timers(self) -> None:
        """Clear all timers and save."""
        self._timer_queue = []
        self.save()
    
    def update_queue(self, timers: list[TimerData]) -> None:
        """Replace the entire timer queue."""
        self._timer_queue = timers
        self.save()