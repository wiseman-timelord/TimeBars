"""
TimeBars Interface Module
NiceGUI-based user interface for the timer application.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from nicegui import ui

from .config import PersistenceManager, TimerData
from .utility import AudioManager
from .timers import TimerManager, Timer, TimerState

logger = logging.getLogger(__name__)


class TimeBarsApp:
    """Main application class for TimeBars."""
    
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.persistence = PersistenceManager(data_path)
        self.audio = AudioManager(data_path)
        self.timer_manager = TimerManager()
        
        # UI state
        self._timer_cards: dict[str, ui.card] = {}
        self._timer_progress: dict[str, ui.linear_progress] = {}
        self._timer_labels: dict[str, ui.label] = {}
        self._flash_active = False
        self._container: Optional[ui.column] = None
        self._status_label: Optional[ui.label] = None
        
        # Bind callbacks
        self.timer_manager.on_tick = self._on_tick
        self.timer_manager.on_timer_complete = self._on_timer_complete
        self.timer_manager.on_alarm_start = self._on_alarm_start
        self.timer_manager.on_alarm_end = self._on_alarm_end
        self.timer_manager.on_queue_complete = self._on_queue_complete
        self.timer_manager.on_state_change = self._on_state_change
    
    def load_data(self) -> None:
        """Load saved data and populate timer manager."""
        self.persistence.load()
        
        # Add saved timers to manager
        for timer_data in self.persistence.timer_queue:
            self.timer_manager.add_timer_from_data(
                id=timer_data.id,
                label=timer_data.label,
                duration_seconds=timer_data.duration_seconds,
                alarm_enabled=timer_data.alarm_enabled
            )
        
        logger.info(f"Loaded {len(self.timer_manager.timers)} timers")
    
    def save_data(self) -> None:
        """Save current timer queue to persistence (only non-complete timers)."""
        timer_data_list = [
            TimerData(
                id=t.id,
                label=t.label,
                duration_seconds=t.duration_seconds,
                alarm_enabled=t.alarm_enabled
            )
            for t in self.timer_manager.timers
            if t.state != TimerState.COMPLETE
        ]
        self.persistence.update_queue(timer_data_list)
    
    def _parse_time_input(self, time_str: str) -> int:
        """Parse HH:MM or HHMM input to seconds."""
        try:
            time_str = time_str.strip()
            
            # Handle HH:MM format
            if ':' in time_str:
                parts = time_str.split(':')
                if len(parts) == 2:
                    hours, minutes = map(int, parts)
                elif len(parts) == 1:
                    hours = 0
                    minutes = int(parts[0])
                else:
                    return 0
            # Handle HHMM format (4 digits) or MM format (1-2 digits)
            elif time_str.isdigit():
                if len(time_str) <= 2:
                    hours = 0
                    minutes = int(time_str)
                elif len(time_str) == 3:
                    hours = int(time_str[0])
                    minutes = int(time_str[1:])
                elif len(time_str) == 4:
                    hours = int(time_str[:2])
                    minutes = int(time_str[2:])
                else:
                    return 0
            else:
                return 0
            
            return hours * 3600 + minutes * 60
        except ValueError:
            return 0
    
    def _add_timer_clicked(self, label_input: ui.input, duration_input: ui.input, alarm_checkbox: ui.checkbox) -> None:
        """Handle add timer button click."""
        label = label_input.value.strip() or "Timer"
        duration = self._parse_time_input(duration_input.value)
        alarm_enabled = alarm_checkbox.value
        
        if duration <= 0:
            ui.notify("Please enter a valid duration (HH:MM or HHMM)", type="warning")
            return
        
        # Add to manager
        timer = self.timer_manager.add_timer(label, duration, alarm_enabled)
        
        # Create UI card
        self._create_timer_card(timer)
        
        # Clear inputs
        label_input.value = ""
        duration_input.value = ""
        
        ui.notify(f"Added: {label}", type="positive")
    
    def _create_timer_card(self, timer: Timer) -> None:
        """Create a UI card for a timer."""
        if self._container is None:
            return
        
        with self._container:
            with ui.card().classes('w-full timer-card') as card:
                self._timer_cards[timer.id] = card
                card.props('flat bordered')
                
                with ui.row().classes('w-full items-center justify-between'):
                    # Timer info
                    with ui.column().classes('gap-0'):
                        with ui.row().classes('items-center gap-2'):
                            # State indicator
                            ui.icon('schedule').classes('text-gray-500')
                            ui.label(timer.label).classes('text-lg font-bold')
                            ui.label(f"({timer.duration_display})").classes('text-gray-500')
                            if timer.alarm_enabled:
                                ui.icon('notifications_active').classes('text-amber-500').tooltip('Alarm enabled')
                        
                        # Time remaining label
                        time_label = ui.label(timer.time_display).classes('text-2xl font-mono')
                        self._timer_labels[timer.id] = time_label
                    
                    # Remove button
                    ui.button(icon='delete', on_click=lambda t=timer: self._remove_timer(t.id)).props('flat round color=negative')
                
                # Progress bar
                progress = ui.linear_progress(value=0, show_value=False).classes('w-full')
                self._timer_progress[timer.id] = progress
    
    def _remove_timer(self, timer_id: str) -> None:
        """Remove a timer from the queue."""
        # Remove from manager
        self.timer_manager.remove_timer(timer_id)
        
        # Remove UI elements
        if timer_id in self._timer_cards:
            self._timer_cards[timer_id].delete()
            del self._timer_cards[timer_id]
        if timer_id in self._timer_progress:
            del self._timer_progress[timer_id]
        if timer_id in self._timer_labels:
            del self._timer_labels[timer_id]
        
        ui.notify("Timer removed", type="info")
    
    def _clear_all_clicked(self) -> None:
        """Clear all timers."""
        # Clear from manager
        self.timer_manager.clear_all()
        
        # Remove all UI cards
        for card in self._timer_cards.values():
            card.delete()
        self._timer_cards.clear()
        self._timer_progress.clear()
        self._timer_labels.clear()
        
        ui.notify("All timers cleared", type="info")
    
    def _start_clicked(self) -> None:
        """Start button clicked."""
        if self.timer_manager.start():
            ui.notify("Started", type="positive")
    
    def _pause_clicked(self) -> None:
        """Pause button clicked."""
        if self.timer_manager.pause():
            ui.notify("Paused", type="warning")
    
    def _stop_clicked(self) -> None:
        """Stop button clicked."""
        self.timer_manager.stop()
        self._flash_active = False
        
        # Update all progress bars and labels
        for timer in self.timer_manager.timers:
            if timer.id in self._timer_progress:
                self._timer_progress[timer.id].value = 0
            if timer.id in self._timer_labels:
                self._timer_labels[timer.id].text = timer.time_display
        
        ui.notify("Stopped", type="negative")
    
    def _on_tick(self, timer: Timer) -> None:
        """Called every second during countdown."""
        if timer.id in self._timer_progress:
            self._timer_progress[timer.id].value = timer.progress
        if timer.id in self._timer_labels:
            self._timer_labels[timer.id].text = timer.time_display
    
    def _on_timer_complete(self, timer: Timer) -> None:
        """Called when a timer reaches zero."""
        logger.info(f"Timer complete callback: {timer.label}")
    
    def _on_alarm_start(self, timer: Timer) -> None:
        """Called when alarm phase starts."""
        logger.info(f"Alarm start: {timer.label}")
        
        # Play audio alarm once
        self.audio.play_alarm_async()
        
        # Start flash effect (will flash 5 times over 5 seconds)
        settings = self.persistence.settings
        if settings.flash_on_alarm:
            asyncio.create_task(self._flash_sequence(timer.id, 5))
    
    def _on_alarm_end(self, timer: Timer) -> None:
        """Called when alarm phase ends."""
        logger.info(f"Alarm end: {timer.label}")
        
        # Ensure flash is stopped
        self._stop_flash(timer.id)
        
        # Remove the completed timer card from UI
        if timer.id in self._timer_cards:
            self._timer_cards[timer.id].delete()
            del self._timer_cards[timer.id]
        if timer.id in self._timer_progress:
            del self._timer_progress[timer.id]
        if timer.id in self._timer_labels:
            del self._timer_labels[timer.id]
    
    def _on_queue_complete(self) -> None:
        """Called when all timers are done."""
        logger.info("Queue complete")
        ui.notify("All timers complete!", type="positive")
        self._update_status()
    
    def _on_state_change(self) -> None:
        """Called when timer manager state changes."""
        self._update_status()
    
    def _update_status(self) -> None:
        """Update the status display."""
        if self._status_label is None:
            return
        
        if self.timer_manager.is_running:
            current = self.timer_manager.current_timer
            if current:
                self._status_label.text = f"Running: {current.label}"
                self._status_label.classes(replace='text-green-500')
            else:
                self._status_label.text = "Running"
                self._status_label.classes(replace='text-green-500')
        elif self.timer_manager.is_paused:
            self._status_label.text = "Paused"
            self._status_label.classes(replace='text-amber-500')
        else:
            self._status_label.text = "Idle"
            self._status_label.classes(replace='text-gray-500')
    
    def _start_flash(self, timer_id: str) -> None:
        """Start flash effect on timer card."""
        if timer_id in self._timer_cards:
            self._timer_cards[timer_id].classes(add='flash-alarm')
    
    def _stop_flash(self, timer_id: str) -> None:
        """Stop flash effect on timer card."""
        if timer_id in self._timer_cards:
            self._timer_cards[timer_id].classes(remove='flash-alarm')
    
    async def _flash_sequence(self, timer_id: str, count: int = 5) -> None:
        """Flash the timer card on/off for count times (once per second)."""
        for i in range(count):
            self._start_flash(timer_id)
            await asyncio.sleep(0.5)
            self._stop_flash(timer_id)
            await asyncio.sleep(0.5)
    
    def build_ui(self) -> None:
        """Build the main user interface."""
        # Add custom CSS and zoom script
        ui.add_head_html('''
        <style>
            .timer-card {
                transition: all 0.3s ease;
            }
            .flash-alarm {
                animation: flash 0.5s ease-in-out infinite alternate;
            }
            @keyframes flash {
                from {
                    background-color: #1a1a2e;
                    border-color: #ff4444;
                }
                to {
                    background-color: #ff4444;
                    border-color: #ff4444;
                }
            }
            body {
                background-color: #0a0a0f;
            }
            .nicegui-content {
                padding: 0 !important;
            }
        </style>
        <script>
            // Ctrl+MouseWheel zoom
            let currentZoom = 100;
            document.addEventListener('wheel', function(e) {
                if (e.ctrlKey) {
                    e.preventDefault();
                    if (e.deltaY < 0) {
                        currentZoom = Math.min(200, currentZoom + 10);
                    } else {
                        currentZoom = Math.max(50, currentZoom - 10);
                    }
                    document.body.style.zoom = currentZoom + '%';
                }
            }, { passive: false });
        </script>
        ''')
        
        # Main container
        with ui.column().classes('w-full min-h-screen bg-slate-900 p-4'):
            # Header
            with ui.row().classes('w-full items-center justify-between mb-4'):
                ui.label('TimeBars').classes('text-3xl font-bold text-white')
                self._status_label = ui.label('Idle').classes('text-gray-500 text-lg')
            
            # Add Timer Section
            with ui.card().classes('w-full bg-slate-800'):
                ui.label('Add New Timer').classes('text-xl font-bold text-white mb-2')
                
                with ui.row().classes('w-full items-end gap-4 flex-wrap'):
                    label_input = ui.input(
                        label='Label',
                        placeholder='Timer name'
                    ).classes('flex-1 min-w-48')
                    
                    duration_input = ui.input(
                        label='Duration',
                        placeholder='HH:MM or HHMM'
                    ).classes('w-36')
                    
                    alarm_checkbox = ui.checkbox('Enable Alarm', value=True).classes('text-white')
                    
                    ui.button(
                        'Add Timer',
                        icon='add',
                        on_click=lambda: self._add_timer_clicked(label_input, duration_input, alarm_checkbox)
                    ).props('color=primary')
            
            # Timer Queue Section
            ui.label('Timer Queue').classes('text-xl font-bold text-white mt-4 mb-2')
            
            # Container for timer cards
            self._container = ui.column().classes('w-full gap-2')
            
            # Load existing timers into UI
            for timer in self.timer_manager.timers:
                self._create_timer_card(timer)
            
            # Control Buttons
            with ui.row().classes('w-full justify-center gap-4 mt-4 sticky bottom-4'):
                ui.button('Start', icon='play_arrow', on_click=self._start_clicked).props('color=positive size=lg')
                ui.button('Pause', icon='pause', on_click=self._pause_clicked).props('color=warning size=lg')
                ui.button('Stop', icon='stop', on_click=self._stop_clicked).props('color=negative size=lg')
                ui.button('Clear All', icon='delete_sweep', on_click=self._clear_all_clicked).props('color=grey size=lg')


def run_app(data_path: Path, native: bool = True, port: int = 8080) -> None:
    """Run the TimeBars application."""
    from nicegui import app
    
    # Store app instance at module level for shutdown access
    app_instance_holder = {'instance': None}
    
    # Define the main page - all UI must be inside this function
    @ui.page('/')
    def main_page():
        # Set dark mode inside page context
        ui.dark_mode(True)
        
        app_instance = TimeBarsApp(data_path)
        app_instance.load_data()
        app_instance.build_ui()
        
        # Store reference for shutdown
        app_instance_holder['instance'] = app_instance
    
    # Save data on shutdown
    @app.on_shutdown
    def shutdown():
        if app_instance_holder['instance']:
            logger.info("Saving data on shutdown...")
            app_instance_holder['instance'].save_data()
    
    # Run NiceGUI with native mode (uses Edge WebView2 on Windows)
    ui.run(
        title='TimeBars',
        native=native,
        window_size=(800, 700) if native else None,
        reload=False,
        port=port,
        show=True,
    )