"""
TimeBars Timer Module
Handles async timer countdown logic and state management.
"""

import asyncio
import uuid
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class TimerState(Enum):
    """Timer states."""
    WAITING = "waiting"
    RUNNING = "running"
    PAUSED = "paused"
    ALARM = "alarm"
    COMPLETE = "complete"


@dataclass
class Timer:
    """Represents a single timer."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    label: str = "Timer"
    duration_seconds: int = 60
    remaining_seconds: int = 0
    alarm_enabled: bool = True
    state: TimerState = TimerState.WAITING
    
    def __post_init__(self):
        if self.remaining_seconds == 0:
            self.remaining_seconds = self.duration_seconds
    
    @property
    def progress(self) -> float:
        """Get progress as a value from 0.0 to 1.0."""
        if self.duration_seconds == 0:
            return 1.0
        return 1.0 - (self.remaining_seconds / self.duration_seconds)
    
    @property
    def time_display(self) -> str:
        """Format remaining time as HH:MM:SS."""
        hours = self.remaining_seconds // 3600
        minutes = (self.remaining_seconds % 3600) // 60
        seconds = self.remaining_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    @property
    def duration_display(self) -> str:
        """Format total duration as HH:MM:SS."""
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def reset(self) -> None:
        """Reset timer to initial state."""
        self.remaining_seconds = self.duration_seconds
        self.state = TimerState.WAITING


class TimerManager:
    """Manages a queue of timers with async countdown."""
    
    def __init__(self):
        self._timers: List[Timer] = []
        self._running = False
        self._paused = False
        self._task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.on_tick: Optional[Callable[[Timer], None]] = None
        self.on_timer_complete: Optional[Callable[[Timer], None]] = None
        self.on_alarm_start: Optional[Callable[[Timer], None]] = None
        self.on_alarm_end: Optional[Callable[[Timer], None]] = None
        self.on_queue_complete: Optional[Callable[[], None]] = None
        self.on_state_change: Optional[Callable[[], None]] = None
    
    @property
    def timers(self) -> List[Timer]:
        """Get list of all timers."""
        return self._timers.copy()
    
    @property
    def current_timer(self) -> Optional[Timer]:
        """Get the currently active timer."""
        if len(self._timers) > 0:
            return self._timers[0]
        return None
    
    @property
    def is_running(self) -> bool:
        return self._running and not self._paused
    
    @property
    def is_paused(self) -> bool:
        return self._running and self._paused
    
    @property
    def is_idle(self) -> bool:
        return not self._running
    
    def add_timer(self, label: str, duration_seconds: int, alarm_enabled: bool = True) -> Timer:
        """Add a new timer to the queue."""
        timer = Timer(
            label=label,
            duration_seconds=duration_seconds,
            remaining_seconds=duration_seconds,
            alarm_enabled=alarm_enabled,
            state=TimerState.WAITING
        )
        self._timers.append(timer)
        logger.info(f"Added timer: {label} ({timer.duration_display})")
        self._notify_state_change()
        return timer
    
    def add_timer_from_data(self, id: str, label: str, duration_seconds: int, alarm_enabled: bool = True) -> Timer:
        """Add a timer with a specific ID (for loading from persistence)."""
        timer = Timer(
            id=id,
            label=label,
            duration_seconds=duration_seconds,
            remaining_seconds=duration_seconds,
            alarm_enabled=alarm_enabled,
            state=TimerState.WAITING
        )
        self._timers.append(timer)
        return timer
    
    def remove_timer(self, timer_id: str) -> bool:
        """Remove a timer from the queue."""
        for i, timer in enumerate(self._timers):
            if timer.id == timer_id:
                self._timers.pop(i)
                logger.info(f"Removed timer: {timer.label}")
                self._notify_state_change()
                return True
        return False
    
    def clear_all(self) -> None:
        """Clear all timers and stop."""
        self.stop()
        self._timers.clear()
        logger.info("Cleared all timers")
        self._notify_state_change()
    
    def start(self) -> bool:
        """Start the timer queue."""
        if not self._timers:
            logger.warning("Cannot start: no timers in queue")
            return False
        
        if self._paused:
            # Resume from pause
            self._paused = False
            logger.info("Resumed timers")
            self._notify_state_change()
            return True
        
        if self._running:
            logger.warning("Timers already running")
            return False
        
        self._running = True
        self._paused = False
        
        # Start the async task
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Started timer queue")
        self._notify_state_change()
        return True
    
    def pause(self) -> bool:
        """Pause the current timer."""
        if not self._running or self._paused:
            return False
        
        self._paused = True
        if self.current_timer:
            self.current_timer.state = TimerState.PAUSED
        logger.info("Paused timers")
        self._notify_state_change()
        return True
    
    def stop(self) -> None:
        """Stop and reset all timers."""
        self._running = False
        self._paused = False
        
        if self._task:
            self._task.cancel()
            self._task = None
        
        # Reset all timers
        for timer in self._timers:
            timer.reset()
        
        logger.info("Stopped timers")
        self._notify_state_change()
    
    async def _run_loop(self) -> None:
        """Main async loop for running timers."""
        try:
            while self._running and len(self._timers) > 0:
                timer = self._timers[0]  # Always process first timer
                
                # Set timer as running
                timer.state = TimerState.RUNNING
                self._notify_state_change()
                
                # Countdown loop
                while timer.remaining_seconds > 0 and self._running:
                    if self._paused:
                        await asyncio.sleep(0.1)
                        continue
                    
                    await asyncio.sleep(1)
                    
                    if not self._paused and self._running:
                        timer.remaining_seconds -= 1
                        
                        # Call tick callback
                        if self.on_tick:
                            self.on_tick(timer)
                
                if not self._running:
                    break
                
                # Timer complete
                timer.state = TimerState.COMPLETE
                logger.info(f"Timer complete: {timer.label}")
                
                if self.on_timer_complete:
                    self.on_timer_complete(timer)
                
                # Alarm phase
                if timer.alarm_enabled:
                    timer.state = TimerState.ALARM
                    self._notify_state_change()
                    
                    if self.on_alarm_start:
                        self.on_alarm_start(timer)
                    
                    # Wait for alarm duration (5 seconds)
                    await asyncio.sleep(5)
                    
                    if self.on_alarm_end:
                        self.on_alarm_end(timer)
                
                # Remove completed timer from list
                if len(self._timers) > 0 and self._timers[0].id == timer.id:
                    self._timers.pop(0)
                    logger.info(f"Removed completed timer: {timer.label}")
                
                self._notify_state_change()
            
            # Queue complete
            self._running = False
            logger.info("Timer queue complete")
            
            if self.on_queue_complete:
                self.on_queue_complete()
            
            self._notify_state_change()
            
        except asyncio.CancelledError:
            logger.debug("Timer loop cancelled")
        except Exception as e:
            logger.error(f"Error in timer loop: {e}")
            self._running = False
            self._notify_state_change()
    
    def _notify_state_change(self) -> None:
        """Notify listeners of state change."""
        if self.on_state_change:
            self.on_state_change()