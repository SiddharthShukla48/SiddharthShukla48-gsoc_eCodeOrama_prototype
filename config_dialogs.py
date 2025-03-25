from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                            QPushButton, QDialogButtonBox, QLabel, QGroupBox,
                            QAbstractItemView, QListWidgetItem)
from PyQt5.QtCore import Qt
import json

class OrderConfigDialog(QDialog):
    """Dialog for configuring the order of sprites, events, and scripts"""
    
    def __init__(self, parent=None, sprites=None, events=None, current_config=None):
        super(OrderConfigDialog, self).__init__(parent)
        
        self.setWindowTitle("Configure Element Order")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.sprites = sprites or []
        self.events = events or []
        self.current_config = current_config or {}
        
        # Initialize the sprites and events order with current values or defaults
        self.sprite_order = self.current_config.get('sprite_order', self.sprites.copy())
        self.event_order = self.current_config.get('event_order', self.events.copy())
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI with configuration options"""
        layout = QVBoxLayout(self)
        
        # Sprites order group
        sprite_group = QGroupBox("Sprite Order (Columns)")
        sprite_layout = QVBoxLayout(sprite_group)
        
        sprite_layout.addWidget(QLabel("Drag to reorder sprites:"))
        
        self.sprite_list = QListWidget()
        self.sprite_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.sprite_list.setSelectionMode(QAbstractItemView.SingleSelection)
        sprite_layout.addWidget(self.sprite_list)
        
        # Add sprites to the list
        for sprite in self.sprite_order:
            item = QListWidgetItem(sprite)
            self.sprite_list.addItem(item)
        
        sprite_button_layout = QHBoxLayout()
        self.sprite_up_button = QPushButton("Move Up")
        self.sprite_up_button.clicked.connect(self._move_sprite_up)
        self.sprite_down_button = QPushButton("Move Down")
        self.sprite_down_button.clicked.connect(self._move_sprite_down)
        sprite_button_layout.addWidget(self.sprite_up_button)
        sprite_button_layout.addWidget(self.sprite_down_button)
        sprite_layout.addLayout(sprite_button_layout)
        
        layout.addWidget(sprite_group)
        
        # Events order group
        event_group = QGroupBox("Event Order (Rows)")
        event_layout = QVBoxLayout(event_group)
        
        event_layout.addWidget(QLabel("Drag to reorder events:"))
        
        self.event_list = QListWidget()
        self.event_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.event_list.setSelectionMode(QAbstractItemView.SingleSelection)
        event_layout.addWidget(self.event_list)
        
        # Add events to the list with friendly names
        for event in self.event_order:
            friendly_name = event.replace('_', ' ').title()
            if friendly_name.startswith('Receive '):
                friendly_name = 'Receive: ' + friendly_name[8:]
            item = QListWidgetItem(friendly_name)
            item.setData(Qt.UserRole, event)  # Store original event name
            self.event_list.addItem(item)
        
        event_button_layout = QHBoxLayout()
        self.event_up_button = QPushButton("Move Up")
        self.event_up_button.clicked.connect(self._move_event_up)
        self.event_down_button = QPushButton("Move Down")
        self.event_down_button.clicked.connect(self._move_event_down)
        event_button_layout.addWidget(self.event_up_button)
        event_button_layout.addWidget(self.event_down_button)
        event_layout.addLayout(event_button_layout)
        
        layout.addWidget(event_group)
        
        # Automatic ordering options
        order_group = QGroupBox("Automatic Ordering")
        order_layout = QHBoxLayout(order_group)
        
        self.topological_order_button = QPushButton("Topological Order (Events)")
        self.topological_order_button.clicked.connect(self._apply_topological_order)
        order_layout.addWidget(self.topological_order_button)
        
        self.connectivity_order_button = QPushButton("Connectivity Order (Sprites)")
        self.connectivity_order_button.clicked.connect(self._apply_connectivity_order)
        order_layout.addWidget(self.connectivity_order_button)
        
        layout.addWidget(order_group)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _move_sprite_up(self):
        """Move the selected sprite up in the list"""
        current_row = self.sprite_list.currentRow()
        if current_row > 0:
            item = self.sprite_list.takeItem(current_row)
            self.sprite_list.insertItem(current_row - 1, item)
            self.sprite_list.setCurrentRow(current_row - 1)
    
    def _move_sprite_down(self):
        """Move the selected sprite down in the list"""
        current_row = self.sprite_list.currentRow()
        if current_row < self.sprite_list.count() - 1:
            item = self.sprite_list.takeItem(current_row)
            self.sprite_list.insertItem(current_row + 1, item)
            self.sprite_list.setCurrentRow(current_row + 1)
    
    def _move_event_up(self):
        """Move the selected event up in the list"""
        current_row = self.event_list.currentRow()
        if current_row > 0:
            item = self.event_list.takeItem(current_row)
            self.event_list.insertItem(current_row - 1, item)
            self.event_list.setCurrentRow(current_row - 1)
    
    def _move_event_down(self):
        """Move the selected event down in the list"""
        current_row = self.event_list.currentRow()
        if current_row < self.event_list.count() - 1:
            item = self.event_list.takeItem(current_row)
            self.event_list.insertItem(current_row + 1, item)
            self.event_list.setCurrentRow(current_row + 1)
    
    def _apply_topological_order(self):
        """Apply a topological ordering to events based on dependencies"""
        # This would be implemented with actual topological sorting algorithm
        # For now, we'll just sort by type with a simple heuristic
        
        # Get current event names (original values)
        events = []
        for i in range(self.event_list.count()):
            item = self.event_list.item(i)
            events.append(item.data(Qt.UserRole))
        
        # Clear the list
        self.event_list.clear()
        
        # Sort events by type (flags first, then keys, then receives)
        ordered_events = []
        
        # First add flag_clicked events
        flag_events = [e for e in events if e.startswith('flag_clicked')]
        ordered_events.extend(flag_events)
        
        # Then add key events
        key_events = [e for e in events if e.startswith('key_pressed')]
        ordered_events.extend(key_events)
        
        # Then add sprite/stage clicked events
        click_events = [e for e in events if e.endswith('_clicked') and not e.startswith('flag_')]
        ordered_events.extend(click_events)
        
        # Then add receive events
        receive_events = [e for e in events if e.startswith('receive_')]
        ordered_events.extend(sorted(receive_events))
        
        # Add any remaining events
        remaining = [e for e in events if e not in ordered_events]
        ordered_events.extend(remaining)
        
        # Add back to list with friendly names
        for event in ordered_events:
            friendly_name = event.replace('_', ' ').title()
            if friendly_name.startswith('Receive '):
                friendly_name = 'Receive: ' + friendly_name[8:]
            item = QListWidgetItem(friendly_name)
            item.setData(Qt.UserRole, event)
            self.event_list.addItem(item)
    
    def _apply_connectivity_order(self):
        """Order sprites based on message connectivity to minimize edge crossings"""
        # This would be implemented with an actual layout algorithm
        # For now, we'll just keep the current order
        pass
    
    def get_configuration(self):
        """Get the configured order of sprites and events"""
        # Get sprite order
        sprite_order = []
        for i in range(self.sprite_list.count()):
            sprite_order.append(self.sprite_list.item(i).text())
        
        # Get event order (original values, not display names)
        event_order = []
        for i in range(self.event_list.count()):
            event_order.append(self.event_list.item(i).data(Qt.UserRole))
        
        return {
            'sprite_order': sprite_order,
            'event_order': event_order
        }

class StyleConfigDialog(QDialog):
    """Dialog for configuring visualization styles"""
    
    def __init__(self, parent=None, current_config=None):
        super(StyleConfigDialog, self).__init__(parent)
        
        self.setWindowTitle("Configure Visualization Style")
        self.setMinimumWidth(500)
        
        self.current_config = current_config or {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI with style configuration options"""
        # Implement style configuration UI here
        pass