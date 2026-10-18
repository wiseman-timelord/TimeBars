"""
TimeBars Interface Module
NiceGUI-based user interface for the timer application.
"""

import os
import threading
import time
import socket
import webview
import asyncio
import logging
from pathlib import Path
from typing import Optional

from nicegui import ui, app

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
        self._timer_title_labels: dict[str, ui.label] = {}
        self._timer_duration_labels: dict[str, ui.label] = {}
        self._flash_active = False
        self._container: Optional[ui.column] = None
        self._status_label: Optional[ui.label] = None
        self._btn_start: Optional[ui.button] = None
        self._btn_pause: Optional[ui.button] = None
        self._btn_stop: Optional[ui.button] = None
        self._volume_slider: Optional[ui.slider] = None
        
        # Bind callbacks
        self.timer_manager.on_tick = self._on_tick
        self.timer_manager.on_timer_complete = self._on_timer_complete
        self.timer_manager.on_alarm_start = self._on_alarm_start
        self.timer_manager.on_alarm_end = self._on_alarm_end
        self.timer_manager.on_queue_complete = self._on_queue_complete
        self.timer_manager.on_state_change = self._on_state_change
    
    def load_data(self) -> None:
        """Load saved settings and ensure timer queue starts empty."""
        self.persistence.load()
        # Apply persisted volume to audio manager
        self.audio.volume = self.persistence.settings.alarm_volume
        # ------------------------------------------------------------------
        # UPDATE 1: Always start with a blank queue — do not carry timers
        # over from the previous session.  (Equivalent to clicking Clear.)
        # ------------------------------------------------------------------
        self.persistence.clear_timers()
        logger.info("Timer queue cleared for fresh session")
    
    def save_data(self) -> None:
        """Save current timer queue and settings to persistence."""
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
        # Ensure volume (and other settings) are written
        self.persistence.save()
    
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
        """Create a UI card for a timer (supports drag-reorder + inline edit)."""
        if self._container is None:
            return
        
        with self._container:
            with ui.card().classes('w-full timer-card cursor-grab') as card:
                self._timer_cards[timer.id] = card
                card.props(f'flat bordered data-timer-id="{timer.id}"')
                # Make the whole card a drag handle for SortableJS
                card.style('touch-action: none;')
                
                with ui.row().classes('w-full items-center justify-between'):
                    # Timer info
                    with ui.column().classes('gap-0 flex-1'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('drag_indicator').classes('text-gray-500 drag-handle')
                            title_lbl = ui.label(timer.label).classes('text-lg font-bold')
                            self._timer_title_labels[timer.id] = title_lbl
                            # Edit icon for title
                            ui.button(
                                icon='edit',
                                on_click=lambda t=timer: self._edit_timer_clicked(t)
                            ).props('flat dense round size=sm color=grey').classes('opacity-70 hover:opacity-100').tooltip('Edit title & duration')
                            dur_lbl = ui.label(f"({timer.duration_display})").classes('text-gray-500')
                            self._timer_duration_labels[timer.id] = dur_lbl
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
        # Store notification message before deleting UI
        notify_msg = "Timer removed"
        notify_type = "info"
        
        # Remove from manager first
        self.timer_manager.remove_timer(timer_id)
        
        # Remove UI elements
        if timer_id in self._timer_cards:
            self._timer_cards[timer_id].delete()
            del self._timer_cards[timer_id]
        if timer_id in self._timer_progress:
            del self._timer_progress[timer_id]
        if timer_id in self._timer_labels:
            del self._timer_labels[timer_id]
        if timer_id in self._timer_title_labels:
            del self._timer_title_labels[timer_id]
        if timer_id in self._timer_duration_labels:
            del self._timer_duration_labels[timer_id]
        
        # Notify after cleanup, wrapped in try-except to prevent crashes
        try:
            ui.notify(notify_msg, type=notify_type)
        except RuntimeError:
            # Context may be lost, notification is non-critical
            pass
    
    def _clear_all_clicked(self) -> None:
        """Clear all timers."""
        # Clear from manager
        self.timer_manager.clear_all()
        
        # Remove all UI cards safely
        for timer_id in list(self._timer_cards.keys()):
            try:
                self._timer_cards[timer_id].delete()
            except RuntimeError:
                pass  # Already deleted
        
        self._timer_cards.clear()
        self._timer_progress.clear()
        self._timer_labels.clear()
        self._timer_title_labels.clear()
        self._timer_duration_labels.clear()
        
        try:
            ui.notify("All timers cleared", type="info")
        except RuntimeError:
            pass

    def _edit_timer_clicked(self, timer: Timer) -> None:
        """Open a dialog to edit label and duration of an existing timer."""
        with ui.dialog() as dialog, ui.card().classes('w-96'):
            ui.label('Edit Timer').classes('text-xl font-bold mb-2')
            label_in = ui.input('Label', value=timer.label).classes('w-full')
            # Show duration as HH:MM for convenience
            hours = timer.duration_seconds // 3600
            minutes = (timer.duration_seconds % 3600) // 60
            duration_in = ui.input(
                'Duration (HH:MM or HHMM)',
                value=f"{hours:02d}:{minutes:02d}"
            ).classes('w-full')

            def apply_edit():
                new_label = label_in.value.strip() or "Timer"
                new_dur = self._parse_time_input(duration_in.value)
                if new_dur <= 0:
                    ui.notify("Please enter a valid duration", type="warning")
                    return
                self.timer_manager.update_timer(timer.id, label=new_label, duration_seconds=new_dur)
                # Refresh visible labels
                if timer.id in self._timer_title_labels:
                    self._timer_title_labels[timer.id].text = new_label
                if timer.id in self._timer_duration_labels:
                    self._timer_duration_labels[timer.id].text = f"({timer.duration_display})"
                if timer.id in self._timer_labels:
                    self._timer_labels[timer.id].text = timer.time_display
                if timer.id in self._timer_progress:
                    self._timer_progress[timer.id].value = timer.progress
                dialog.close()
                ui.notify("Timer updated", type="positive")

            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button('Save', on_click=apply_edit).props('color=primary')
        dialog.open()

    def _on_reorder(self, ordered_ids) -> None:
        """Called from JS when user finishes dragging a timer card."""
        if isinstance(ordered_ids, str):
            ordered_ids = [x for x in ordered_ids.split('|') if x]
        if not ordered_ids:
            return
        # Filter to known timer IDs only
        known = {t.id for t in self.timer_manager.timers}
        ordered_ids = [tid for tid in ordered_ids if tid in known]
        if ordered_ids:
            self.timer_manager.reorder(ordered_ids)
            logger.info(f"Queue reordered via drag: {ordered_ids}")

    def _volume_changed(self, e) -> None:
        """Slider moved – update live volume and persist setting."""
        vol = float(e.value) if hasattr(e, 'value') else float(e)
        vol = max(0.0, min(1.0, vol))
        self.audio.volume = vol
        self.persistence.settings.alarm_volume = vol
        # settings setter already calls save(), but be explicit
        self.persistence.save()

    # ------------------------------------------------------------------
    # UPDATE 2: Save / Load preset buttons
    # ------------------------------------------------------------------
    def _save_preset_clicked(self) -> None:
        """Save the current timer queue as the single preset."""
        if not self.timer_manager.timers:
            ui.notify("No timers to save", type="warning")
            return

        timer_data_list = [
            TimerData(
                id=t.id,
                label=t.label,
                duration_seconds=t.duration_seconds,
                alarm_enabled=t.alarm_enabled
            )
            for t in self.timer_manager.timers
        ]

        if self.persistence.save_preset(timer_data_list):
            ui.notify("Preset saved", type="positive")
        else:
            ui.notify("Failed to save preset", type="negative")

    def _load_preset_clicked(self) -> None:
        """Load the single preset and replace the current queue."""
        preset_timers = self.persistence.load_preset()

        if not preset_timers:
            ui.notify("No preset found", type="warning")
            return

        # Stop anything currently running
        self.timer_manager.stop()
        self._flash_active = False

        # Tear down existing UI cards
        for timer_id in list(self._timer_cards.keys()):
            try:
                self._timer_cards[timer_id].delete()
            except RuntimeError:
                pass

        self._timer_cards.clear()
        self._timer_progress.clear()
        self._timer_labels.clear()
        self._timer_title_labels.clear()
        self._timer_duration_labels.clear()

        # Replace manager queue
        self.timer_manager.clear_all()
        for timer_data in preset_timers:
            timer = self.timer_manager.add_timer_from_data(
                id=timer_data.id,
                label=timer_data.label,
                duration_seconds=timer_data.duration_seconds,
                alarm_enabled=timer_data.alarm_enabled
            )
            self._create_timer_card(timer)

        self._update_status()
        ui.notify(f"Loaded {len(preset_timers)} timers from preset", type="positive")
    # ------------------------------------------------------------------

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
        if timer.id in self._timer_title_labels:
            del self._timer_title_labels[timer.id]
        if timer.id in self._timer_duration_labels:
            del self._timer_duration_labels[timer.id]
    
    def _on_queue_complete(self) -> None:
        """Called when all timers are done."""
        logger.info("Queue complete")
        # Use run_javascript for notifications from background tasks
        # or schedule on the main thread
        try:
            ui.notify("All timers complete!", type="positive")
        except RuntimeError:
            # If context is not available, log only
            logger.info("Queue complete notification skipped (no UI context)")
        self._update_status()
    
    def _on_state_change(self) -> None:
        """Called when timer manager state changes."""
        self._update_status()
    
    def _update_status(self) -> None:
        """Update the status display and dynamic control-button visibility."""
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

        # Dynamic button visibility:
        #   Play  → only when Paused or Stopped (idle)
        #   Pause → only when Playing
        #   Stop  → only when Playing or Paused
        try:
            if self._btn_start is not None:
                if self.timer_manager.is_running:
                    self._btn_start.set_visibility(False)
                else:
                    self._btn_start.set_visibility(True)
            if self._btn_pause is not None:
                if self.timer_manager.is_running:
                    self._btn_pause.set_visibility(True)
                else:
                    self._btn_pause.set_visibility(False)
            if self._btn_stop is not None:
                if self.timer_manager.is_running or self.timer_manager.is_paused:
                    self._btn_stop.set_visibility(True)
                else:
                    self._btn_stop.set_visibility(False)
        except Exception:
            pass  # UI may not be fully built yet
    
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
                cursor: grab;
            }
            .timer-card:active {
                cursor: grabbing;
            }
            .sortable-ghost {
                opacity: 0.4;
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
            html, body {
                background-color: #0a0a0f;
                min-height: 100vh;
                margin: 0;
            }
            .nicegui-content {
                padding: 0 !important;
                min-height: 100vh;
                background-color: #0a0a0f;
            }
            .main-container {
                min-height: 100vh;
                background-color: #0a0a0f;
                padding-bottom: 100px;
            }
            .control-bar {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background-color: rgba(15, 23, 42, 0.95);
                backdrop-filter: blur(10px);
                padding: 16px;
                z-index: 1000;
                border-top: 1px solid #334155;
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
        
        # Main container - full height background that scales with content
        with ui.column().classes('w-full bg-slate-900 p-4 main-container'):
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
            
            # Container for timer cards - expands to fill content
            self._container = ui.column().classes('w-full gap-2')
            
            # Load existing timers into UI
            for timer in self.timer_manager.timers:
                self._create_timer_card(timer)
            
            # Spacer to ensure content doesn't get hidden behind fixed controls
            ui.element('div').classes('h-20')
        
        # Control Buttons - Fixed at bottom, outside main scrollable area
        with ui.element('div').classes('control-bar'):
            with ui.row().classes('w-full justify-center items-center gap-4 flex-wrap'):
                self._btn_start = ui.button('Start', icon='play_arrow', on_click=self._start_clicked).props('color=positive size=lg')
                self._btn_pause = ui.button('Pause', icon='pause', on_click=self._pause_clicked).props('color=warning size=lg')
                self._btn_stop = ui.button('Stop', icon='stop', on_click=self._stop_clicked).props('color=negative size=lg')
                ui.button('Clear', icon='delete_sweep', on_click=self._clear_all_clicked).props('color=grey size=lg')
                # ------------------------------------------------------------------
                # UPDATE 2: Save & Load preset buttons
                # ------------------------------------------------------------------
                ui.button('Save', icon='save', on_click=self._save_preset_clicked).props('color=info size=lg')
                ui.button('Load', icon='folder_open', on_click=self._load_preset_clicked).props('color=info size=lg')
                # ------------------------------------------------------------------
                # Volume slider (short) at end of button row – persists to persistent.json
                # ------------------------------------------------------------------
                with ui.row().classes('items-center gap-1 ml-2'):
                    ui.icon('volume_up').classes('text-gray-400')
                    self._volume_slider = ui.slider(
                        min=0.0, max=1.0, step=0.05,
                        value=self.persistence.settings.alarm_volume,
                        on_change=self._volume_changed
                    ).props('dense').classes('w-24').tooltip('Alarm volume')
                # ------------------------------------------------------------------

        # Apply initial button visibility
        self._update_status()

        # ------------------------------------------------------------------
        # Drag-and-drop reordering via SortableJS (CDN)
        # ------------------------------------------------------------------
        ui.add_body_html('''
        <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.2/Sortable.min.js"></script>
        <script>
        (function() {
            function initSortable() {
                const container = document.querySelector('.main-container .nicegui-column, .main-container > .q-column, [class*="gap-2"]');
                // Prefer the timer-queue column that holds .timer-card elements
                let el = null;
                document.querySelectorAll('.timer-card').forEach(card => {
                    if (!el) el = card.parentElement;
                });
                if (!el || el._sortable) return;
                el._sortable = new Sortable(el, {
                    animation: 150,
                    handle: '.timer-card',
                    ghostClass: 'opacity-50',
                    onEnd: function(evt) {
                        const ids = Array.from(el.querySelectorAll('[data-timer-id]'))
                            .map(n => n.getAttribute('data-timer-id'))
                            .filter(Boolean);
                        // Emit custom event that NiceGUI can listen to
                        window.dispatchEvent(new CustomEvent('timebars-reorder', { detail: ids }));
                    }
                });
            }
            // Retry a few times while the UI builds
            let attempts = 0;
            const t = setInterval(() => {
                initSortable();
                attempts++;
                if (attempts > 20) clearInterval(t);
            }, 300);
            // Also re-init when new cards appear
            const obs = new MutationObserver(() => initSortable());
            setTimeout(() => {
                const root = document.querySelector('.main-container') || document.body;
                obs.observe(root, { childList: true, subtree: true });
            }, 500);
        })();
        </script>
        ''')

        # Hidden input used as a JS→Python bridge for reorder events
        self._reorder_bridge = ui.input(value='').props('id=timebars-reorder-bridge').classes('hidden').style('display:none')
        self._reorder_bridge.on_value_change(lambda e: self._on_reorder(
            (e.value or '').split('|') if e.value else []
        ))

        # Patch the Sortable onEnd to write into the hidden input
        ui.run_javascript('''
        (function waitForSortable() {
            const tryPatch = () => {
                document.querySelectorAll('.timer-card').forEach(card => {
                    const parent = card.parentElement;
                    if (parent && parent._sortable && !parent._sortable._patched) {
                        parent._sortable.option('onEnd', function(evt) {
                            const ids = Array.from(parent.querySelectorAll('[data-timer-id]'))
                                .map(n => n.getAttribute('data-timer-id'))
                                .filter(Boolean);
                            const inp = document.getElementById('timebars-reorder-bridge');
                            if (inp) {
                                const setter = Object.getOwnPropertyDescriptor(
                                    window.HTMLInputElement.prototype, 'value').set;
                                setter.call(inp, ids.join('|'));
                                inp.dispatchEvent(new Event('input', { bubbles: true }));
                                inp.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        });
                        parent._sortable._patched = true;
                    }
                });
            };
            setInterval(tryPatch, 400);
        })();
        ''')


def run_app(data_path: Path, native: bool = True, port: int = 8080) -> None:
    """Run the TimeBars application."""
    
    # Compute path to custom icon
    icon_path = Path(__file__).parent.parent / "media" / "application_icon.ico"
    icon_path_str = str(icon_path.resolve()) if icon_path.exists() else None
    
    # Holder for app instance so shutdown can save data
    app_instance_holder = {'instance': None}
    
    @ui.page('/')
    def main_page():
        ui.dark_mode(True)
        
        app_instance = TimeBarsApp(data_path)
        app_instance.load_data()
        app_instance.build_ui()
        
        app_instance_holder['instance'] = app_instance
    
    # Save data on server shutdown (works in standard NiceGUI mode)
    @app.on_shutdown
    def shutdown():
        if app_instance_holder['instance']:
            logger.info("Saving data on server shutdown...")
            app_instance_holder['instance'].save_data()
    
    # Custom native mode with manual icon setting on Windows
    if native and icon_path_str:
        def start_server():
            ui.run(
                title='TimeBars',
                native=False,
                host='127.0.0.1',
                port=port,
                reload=False,
                show=False,
            )
        
        server_thread = threading.Thread(target=start_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Wait for server to be ready
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                with socket.create_connection(('127.0.0.1', port)):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            raise TimeoutError("Failed to start NiceGUI server within 10 seconds")
        
        # Create the native window (no 'icon' parameter)
        window = webview.create_window(
            title='TimeBars',
            url=f'http://127.0.0.1:{port}',
            width=800,
            height=700,
            resizable=True,
        )
        
        # Save data when window is closed
        def on_closed():
            if app_instance_holder['instance']:
                logger.info("Saving data on window close...")
                app_instance_holder['instance'].save_data()
        
        window.events.closed += on_closed
        
        # --- Custom icon setting on Windows only ---
        if os.name == 'nt':
            import ctypes
            
            user32 = ctypes.windll.user32
            
            def apply_custom_icon():
                time.sleep(2.0)  # Wait for window to fully appear
                
                hwnd = None
                title_p = ctypes.c_wchar_p("TimeBars")
                
                for _ in range(40):  # Try for up to 20 seconds
                    hwnd = user32.FindWindowW(None, title_p)
                    if hwnd:
                        break
                    time.sleep(0.5)
                
                if not hwnd:
                    logger.warning("Could not find TimeBars window to apply custom icon")
                    return
                
                # Constants
                IMAGE_ICON = 1
                LR_LOADFROMFILE = 0x00000010
                WM_SETICON = 0x0080
                ICON_SMALL = 0
                ICON_BIG = 1
                
                path_p = ctypes.c_wchar_p(icon_path_str)
                
                # Large icon (taskbar / alt-tab)
                cx = user32.GetSystemMetrics(11)  # SM_CXICON
                cy = user32.GetSystemMetrics(12)  # SM_CYICON
                hbig = user32.LoadImageW(None, path_p, IMAGE_ICON, cx, cy, LR_LOADFROMFILE)
                if hbig:
                    user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hbig)
                
                # Small icon (title bar)
                cx_small = user32.GetSystemMetrics(49)  # SM_CXSMICON
                cy_small = user32.GetSystemMetrics(50)  # SM_CYSMICON
                hsmall = user32.LoadImageW(None, path_p, IMAGE_ICON, cx_small, cy_small, LR_LOADFROMFILE)
                if hsmall:
                    user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hsmall)
                
                logger.info("Custom application icon applied to window and taskbar")
            
            threading.Thread(target=apply_custom_icon, daemon=True).start()
        # ------------------------------------------------
        
        webview.start()
    
    else:
        # Standard NiceGUI behavior (fallback)
        ui.run(
            title='TimeBars',
            native=native,
            window_size=(800, 700) if native else None,
            reload=False,
            port=port,
            show=True,
            favicon=icon_path_str,  # Sets browser tab icon if running in browser mode
        )