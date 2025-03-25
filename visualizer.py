import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.path import Path
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D

class CodeOramaVisualizer:
    def __init__(self):
        self.fig = None
        self.ax = None
        self.sprite_positions = {}
        self.event_positions = {}
        self.cell_contents = {}
        
        # Color scheme for different script types
        self.block_colors = {
            'event_whenflagclicked': '#FFBF00',
            'event_whenkeypressed': '#FF8E00',
            'event_whenbroadcastreceived': '#FFD500',
            'event_whenstageclicked': '#FFBF00',
            'event_whenthisspriteclicked': '#FFBF00',
            'event_broadcast': '#FF661A',
            'event_broadcastandwait': '#FF661A',
            'default': '#4C97FF'
        }
        
    def visualize(self, codeorama_data, edge_style='improved', show_message_names=True, 
                 config=None, script_folding=None):
        """Create a visualization of the CodeOrama data
        
        Args:
            codeorama_data: The parsed data containing sprites, events, scripts, connections
            edge_style: 'straight', 'curved', or 'improved'
            show_message_names: Whether to show message names on the edges
            config: Optional configuration dict with ordering preferences
            script_folding: Dict specifying which scripts are folded/unfolded
        """
        sprites = codeorama_data['sprites']
        events = codeorama_data['events']
        scripts = codeorama_data['scripts']
        connections = codeorama_data['connections']
        
        # Apply custom ordering if provided
        if config and 'sprite_order' in config:
            # Use only sprites that exist in the data
            sprite_order = [s for s in config['sprite_order'] if s in sprites]
            # Add any sprites not in the order
            sprite_order.extend([s for s in sprites if s not in sprite_order])
            sprites = sprite_order
        
        if config and 'event_order' in config:
            # Use only events that exist in the data
            event_order = [e for e in config['event_order'] if e in events]
            # Add any events not in the order
            event_order.extend([e for e in events if e not in event_order])
            events = event_order
        
        # Set up the figure and axis
        fig_width = max(10, 2 * len(sprites))
        fig_height = max(8, 1.5 * len(events))
        self.fig, self.ax = plt.subplots(figsize=(fig_width, fig_height))
        
        # Create the grid
        self._create_grid(sprites, events)
        
        # Add script blocks to cells
        script_folding = script_folding or {}
        self._add_scripts(scripts, script_folding)
        
        # Add connection arrows with the selected style
        if edge_style == 'straight':
            self._add_straight_connections(connections, show_message_names)
        elif edge_style == 'curved':
            self._add_curved_connections(connections, show_message_names)
        else:
            self._add_improved_connections(connections, show_message_names)
        
        # Show the plot
        plt.tight_layout()
        return self.fig
    
    def _create_grid(self, sprites, events):
        """Create the grid with sprite columns and event rows"""
        # Set up axes
        self.ax.set_xlim(0, len(sprites) + 1)
        self.ax.set_ylim(0, len(events) + 1)
        
        # Remove axis ticks
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        
        # Add sprite headers (columns) with Scratch-like styling
        for i, sprite in enumerate(sprites):
            x = i + 1
            y = len(events) + 0.5
            
            # Add a background for sprite name - using FancyBboxPatch for rounded corners
            sprite_bg = patches.FancyBboxPatch(
                (x - 0.4, y - 0.3), 0.8, 0.6, 
                boxstyle=patches.BoxStyle("Round", pad=0.02, rounding_size=0.1),
                linewidth=1, edgecolor='black', facecolor='#4C97FF', alpha=0.7,
                zorder=3
            )
            self.ax.add_patch(sprite_bg)
            
            # Add sprite name
            self.ax.text(x, y, sprite, ha='center', va='center', fontsize=10, 
                        color='white', fontweight='bold', zorder=4)
            self.sprite_positions[sprite] = x
            
            # Draw vertical grid line
            self.ax.axvline(x - 0.5, color='gray', linestyle='-', alpha=0.3)
        
        # Add event headers (rows) with Scratch-like styling
        for i, event in enumerate(events):
            x = 0.5
            y = len(events) - i
            
            # Format event name for display
            formatted_event = event.replace('_', ' ').title()
            if formatted_event.startswith('Receive '):
                formatted_event = 'Receive: ' + formatted_event[8:]
            
            # Add a background for event name - using FancyBboxPatch for rounded corners
            event_color = self._get_event_color(event)
            event_bg = patches.FancyBboxPatch(
                (x - 0.4, y - 0.3), 0.8, 0.6, 
                boxstyle=patches.BoxStyle("Round", pad=0.02, rounding_size=0.1),
                linewidth=1, edgecolor='black', facecolor=event_color, alpha=0.7,
                zorder=3
            )
            self.ax.add_patch(event_bg)
            
            # Add event name
            self.ax.text(x, y, formatted_event, ha='center', va='center', 
                        fontsize=8, color='black', zorder=4)
            self.event_positions[event] = y
            
            # Draw horizontal grid line
            self.ax.axhline(y + 0.5, color='gray', linestyle='-', alpha=0.3)
            
        # Draw final grid lines
        self.ax.axvline(len(sprites) + 0.5, color='gray', linestyle='-', alpha=0.3)
        self.ax.axhline(0.5, color='gray', linestyle='-', alpha=0.3)
    
    def _add_scripts(self, scripts, script_folding=None):
        """Add script blocks to the grid cells using Scratch-like styling
        
        Args:
            scripts: Dictionary of scripts indexed by (sprite, event)
            script_folding: Dictionary indicating folding state {(sprite, event, script_idx): is_folded}
        """
        script_folding = script_folding or {}
        
        for (sprite, event), script_list in scripts.items():
            if sprite in self.sprite_positions and event in self.event_positions:
                x = self.sprite_positions[sprite]
                y = self.event_positions[event]
                
                # For each script in this cell
                for i, script in enumerate(script_list):
                    # Multiple scripts in a cell are stacked with a slight offset
                    offset = i * 0.1
                    
                    # Get the color for this event type
                    color = self._get_event_color(event)
                    
                    # Check if this script should be folded
                    is_folded = script_folding.get((sprite, event, i), False)
                    
                    if is_folded:
                        # Create a small folded block
                        self._add_folded_script(x + offset, y + offset, color, script)
                    else:
                        # Create a more detailed script block
                        self._add_detailed_script(x + offset, y + offset, color, script)
                    
                    # Store the cell for connection drawing with offset to account for multiple scripts
                    self.cell_contents[(sprite, event, i)] = (x + offset, y + offset)

    def _add_folded_script(self, x, y, color, script):
        """Add a folded script block (minimal representation)"""
        width, height = 0.8, 0.4
        
        # Create a rounded rectangle for the script
        rect = patches.FancyBboxPatch(
            (x - width/2, y - height/2), width, height,
            boxstyle=patches.BoxStyle("Round", pad=0.02, rounding_size=0.1),
            linewidth=1.5, edgecolor='black', facecolor=color, alpha=0.8
        )
        self.ax.add_patch(rect)
        
        # Add script label (first opcode or event type)
        if script and len(script) > 0:
            first_block = script[0]
            label = first_block.get('opcode', 'Unknown').split('_')[-1]
            # Simplify label
            label = label.replace('whenflagclicked', 'Flag')
            label = label.replace('whenbroadcastreceived', 'Receive')
            label = label.replace('whenkeypressed', 'Key')
            
            self.ax.text(x, y, f"{label} (+{len(script)-1} blocks)", 
                        ha='center', va='center', fontsize=7, 
                        color='black', fontweight='bold')

    def _add_detailed_script(self, x, y, color, script):
        """Add a more detailed script block with multiple blocks shown"""
        if not script:
            return
        
        base_width = 0.8
        block_height = 0.25
        
        # Determine how many blocks to show (up to 4 for clarity)
        visible_blocks = min(4, len(script))
        total_height = visible_blocks * block_height
        
        # Create a background for the entire script
        for i in range(visible_blocks):
            # Each block in the script
            block_y = y - (i * block_height)
            block_color = color if i == 0 else self._get_block_color(script[i])
            
            # Determine shape based on position in script
            if i == 0:  # First block (hat/event)
                # Hat block shape
                hat_points = [
                    (x - base_width/2, block_y - block_height/2),  # Bottom left
                    (x - base_width/2, block_y - block_height/10),  # Middle left
                    (x - base_width/2 + base_width/10, block_y + block_height/3),  # Top left curve
                    (x + base_width/2 - base_width/10, block_y + block_height/3),  # Top right curve
                    (x + base_width/2, block_y - block_height/10),  # Middle right
                    (x + base_width/2, block_y - block_height/2),  # Bottom right
                ]
                hat_polygon = patches.Polygon(
                    hat_points, closed=True, 
                    facecolor=block_color, edgecolor='black', linewidth=1
                )
                self.ax.add_patch(hat_polygon)
            else:  # Regular block
                block_rect = patches.FancyBboxPatch(
                    (x - base_width/2, block_y - block_height/2), base_width, block_height,
                    boxstyle=patches.BoxStyle("Round", pad=0.02, rounding_size=0.05),
                    linewidth=1, edgecolor='black', facecolor=block_color, alpha=0.8
                )
                self.ax.add_patch(block_rect)
            
            # Add block label
            if i < len(script):
                block = script[i]
                opcode = block.get('opcode', 'Unknown')
                # Format opcode for display
                label = self._format_opcode_for_display(opcode)
                
                self.ax.text(x, block_y, label, 
                            ha='center', va='center', fontsize=6, 
                            color='black', fontweight='bold')
        
        # If there are more blocks not shown, add an indicator
        if len(script) > visible_blocks:
            more_y = y - (visible_blocks * block_height)
            self.ax.text(x, more_y, f"+ {len(script) - visible_blocks} more blocks", 
                        ha='center', va='top', fontsize=6, 
                        color='gray', style='italic')

    def _format_opcode_for_display(self, opcode):
        """Format an opcode for display in a script block"""
        # Remove the prefix (e.g., 'event_', 'motion_', etc.)
        if '_' in opcode:
            parts = opcode.split('_', 1)
            if len(parts) > 1:
                opcode = parts[1]
        
        # Replace underscores with spaces and capitalize words
        opcode = opcode.replace('_', ' ').title()
        
        # Special case replacements for common opcodes
        replacements = {
            'When Flag Clicked': 'When ⚑ Clicked',
            'When Broadcast Received': 'When I Receive',
            'When Key Pressed': 'When Key Pressed',
            'When This Sprite Clicked': 'When Sprite Clicked',
            'Broadcast': 'Broadcast',
            'Broadcastandwait': 'Broadcast and Wait',
            'Move Steps': 'Move',
            'Turn Right': 'Turn Right',
            'Turn Left': 'Turn Left',
            'Go To': 'Go to',
            'Change X By': '+ X',
            'Change Y By': '+ Y',
        }
        
        # Apply replacements
        for old, new in replacements.items():
            if opcode.startswith(old):
                return new
        
        return opcode

    def _get_block_color(self, block):
        """Get color for a specific block based on its category"""
        opcode = block.get('opcode', 'unknown')
        category = opcode.split('_')[0] if '_' in opcode else 'unknown'
        
        # Expanded color scheme for different block categories
        category_colors = {
            'event': '#FFBF00',    # yellow/gold
            'control': '#FFAB19',  # orange
            'motion': '#4C97FF',   # blue
            'looks': '#9966FF',    # purple
            'sound': '#CF63CF',    # magenta
            'sensing': '#5CB1D6',  # light blue
            'operator': '#59C059', # green
            'data': '#FF8C1A',     # orange-red
            'procedures': '#FF6680', # pink
            'unknown': '#A0A0A0',  # gray
        }
        
        return category_colors.get(category, self.block_colors['default'])
    
    def _add_straight_connections(self, connections, show_message_names=True):
        """Add straight line arrows between scripts that broadcast and receive messages"""
        for source_sprite, source_event, target_sprite, target_event in connections:
            if source_sprite and source_event and target_event:
                # Find the source cell - use first script in the cell
                source_key = next((k for k in self.cell_contents.keys() 
                                  if k[0] == source_sprite and k[1] == source_event), None)
                
                if source_key:
                    source_x, source_y = self.cell_contents[source_key]
                    
                    # For broadcast messages, draw arrows to all receiving scripts
                    receivers_found = False
                    for sprite in self.sprite_positions:
                        # Find all scripts that receive this message
                        receive_keys = [k for k in self.cell_contents.keys() 
                                      if k[0] == sprite and k[1] == target_event]
                        
                        for receive_key in receive_keys:
                            receivers_found = True
                            target_x, target_y = self.cell_contents[receive_key]
                            
                            # Draw arrow from source to target
                            arrow = self.ax.annotate(
                                "", xy=(target_x, target_y), xytext=(source_x, source_y),
                                arrowprops=dict(arrowstyle="->", color="red", lw=1.5)
                            )
                            
                            # Add message name if enabled
                            if show_message_names and target_event.startswith('receive_'):
                                message = target_event.replace('receive_', '')
                                # Place the text at the midpoint of the arrow
                                mid_x = (source_x + target_x) / 2
                                mid_y = (source_y + target_y) / 2
                                self.ax.text(mid_x, mid_y, message, fontsize=7,
                                           ha='center', va='center', 
                                           bbox=dict(boxstyle="round,pad=0.3", 
                                                    fc="white", ec="gray", alpha=0.7))
                    
                    # If no receivers for this message, add a note
                    if not receivers_found:
                        self.ax.text(
                            source_x + 0.1, source_y - 0.1,
                            f"Broadcasts: {target_event.replace('receive_', '')}",
                            fontsize=8, color='red', ha='left', va='top',
                            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="red", alpha=0.7)
                        )
    
    def _add_curved_connections(self, connections, show_message_names=True):
        """Add curved arrows between scripts that broadcast and receive messages"""
        for source_sprite, source_event, target_sprite, target_event in connections:
            if source_sprite and source_event and target_event:
                # Find the source cell - use first script in the cell
                source_key = next((k for k in self.cell_contents.keys() 
                                  if k[0] == source_sprite and k[1] == source_event), None)
                
                if source_key:
                    source_x, source_y = self.cell_contents[source_key]
                    
                    # For broadcast messages, draw arrows to all receiving scripts
                    receivers_found = False
                    for sprite in self.sprite_positions:
                        # Find all scripts that receive this message
                        receive_keys = [k for k in self.cell_contents.keys() 
                                      if k[0] == sprite and k[1] == target_event]
                        
                        for receive_key in receive_keys:
                            receivers_found = True
                            target_x, target_y = self.cell_contents[receive_key]
                            
                            # Calculate curvature based on distance
                            dx = target_x - source_x
                            dy = target_y - source_y
                            dist = np.sqrt(dx**2 + dy**2)
                            
                            # More curve for longer distances
                            rad = min(0.3, dist / 10)
                            
                            # Draw curved arrow from source to target
                            arrow = self.ax.annotate(
                                "", xy=(target_x, target_y), xytext=(source_x, source_y),
                                arrowprops=dict(arrowstyle="->", color="red", lw=1.5,
                                             connectionstyle=f"arc3,rad={rad}")
                            )
                            
                            # Add message name if enabled
                            if show_message_names and target_event.startswith('receive_'):
                                message = target_event.replace('receive_', '')
                                # Place the text at the midpoint of the curved arrow
                                theta = np.arctan2(dy, dx)
                                mid_x = (source_x + target_x) / 2 + rad * dist * np.cos(theta + np.pi/2)
                                mid_y = (source_y + target_y) / 2 + rad * dist * np.sin(theta + np.pi/2)
                                self.ax.text(mid_x, mid_y, message, fontsize=7,
                                           ha='center', va='center', 
                                           bbox=dict(boxstyle="round,pad=0.3", 
                                                    fc="white", ec="gray", alpha=0.7))
                    
                    # If no receivers for this message, add a note
                    if not receivers_found:
                        self.ax.text(
                            source_x + 0.1, source_y - 0.1,
                            f"Broadcasts: {target_event.replace('receive_', '')}",
                            fontsize=8, color='red', ha='left', va='top',
                            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="red", alpha=0.7)
                        )
    
    def _add_improved_connections(self, connections, show_message_names=True):
        """Add improved arrows that route around nodes between scripts"""
        for source_sprite, source_event, target_sprite, target_event in connections:
            if source_sprite and source_event and target_event:
                # Find the source cell - use first script in the cell
                source_key = next((k for k in self.cell_contents.keys() 
                                  if k[0] == source_sprite and k[1] == source_event), None)
                
                if source_key:
                    source_x, source_y = self.cell_contents[source_key]
                    
                    # For broadcast messages, draw arrows to all receiving scripts
                    receivers_found = False
                    for sprite in self.sprite_positions:
                        # Find all scripts that receive this message
                        receive_keys = [k for k in self.cell_contents.keys() 
                                      if k[0] == sprite and k[1] == target_event]
                        
                        for receive_key in receive_keys:
                            receivers_found = True
                            target_x, target_y = self.cell_contents[receive_key]
                            
                            # Calculate positions in the grid
                            source_col = self.sprite_positions[source_sprite]
                            target_col = self.sprite_positions[sprite]
                            
                            # Create path points for routing around nodes
                            path_points = []
                            path_points.append((source_x, source_y))  # Start
                            
                            # If source and target are in different columns
                            if source_col != target_col:
                                # Route down from source
                                path_points.append((source_x, source_y - 0.4))
                                
                                # Route horizontally at the bottom
                                path_points.append((source_x, 0.8))  # Go to bottom area
                                path_points.append((target_x, 0.8))  # Move horizontally
                                
                                # Route up to target
                                path_points.append((target_x, target_y - 0.4))
                            else:
                                # Same column - use a simple curved path
                                # Determine if going up or down
                                if source_y > target_y:  # Going down
                                    mid_y = (source_y + target_y) / 2
                                    # Right curve
                                    path_points.append((source_x, mid_y))
                                    path_points.append((source_x + 0.5, mid_y))
                                    path_points.append((source_x + 0.5, target_y))
                                else:  # Going up
                                    mid_y = (source_y + target_y) / 2
                                    # Left curve
                                    path_points.append((source_x, mid_y))
                                    path_points.append((source_x - 0.5, mid_y))
                                    path_points.append((source_x - 0.5, target_y))
                            
                            path_points.append((target_x, target_y))  # End
                            
                            # Create a smooth path
                            codes = [Path.MOVETO]
                            for _ in range(len(path_points) - 2):
                                codes.append(Path.CURVE4)
                            codes.append(Path.LINETO)
                            
                            # Draw the path
                            path = Path(path_points, codes)
                            patch = patches.PathPatch(path, facecolor='none', 
                                                     edgecolor='red', lw=1.5, alpha=0.8)
                            self.ax.add_patch(patch)
                            
                            # Add arrow at the end
                            end_x, end_y = path_points[-1]
                            prev_x, prev_y = path_points[-2]
                            dx, dy = end_x - prev_x, end_y - prev_y
                            self.ax.arrow(end_x - 0.1*dx, end_y - 0.1*dy, 0.07*dx, 0.07*dy,
                                         head_width=0.1, head_length=0.1, fc='red', ec='red')
                            
                            # Add message name if enabled
                            if show_message_names and target_event.startswith('receive_'):
                                message = target_event.replace('receive_', '')
                                # Place the text at a good point along the path
                                if len(path_points) > 3:
                                    text_point = path_points[len(path_points) // 2]
                                    self.ax.text(text_point[0], text_point[1], message, fontsize=7,
                                               ha='center', va='center', 
                                               bbox=dict(boxstyle="round,pad=0.3", 
                                                        fc="white", ec="gray", alpha=0.7))
                    
                    # If no receivers for this message, add a note
                    if not receivers_found:
                        self.ax.text(
                            source_x + 0.1, source_y - 0.1,
                            f"Broadcasts: {target_event.replace('receive_', '')}",
                            fontsize=8, color='red', ha='left', va='top',
                            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="red", alpha=0.7)
                        )
    
    def _get_event_color(self, event):
        """Get appropriate color for an event type"""
        if event.startswith('flag_clicked'):
            return self.block_colors['event_whenflagclicked']
        elif event.startswith('key_pressed'):
            return self.block_colors['event_whenkeypressed']
        elif event.startswith('receive_'):
            return self.block_colors['event_whenbroadcastreceived']
        elif event.startswith('stage_clicked'):
            return self.block_colors['event_whenstageclicked']
        elif event.startswith('sprite_clicked'):
            return self.block_colors['event_whenthisspriteclicked']
        else:
            return self.block_colors['default']