import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.path import Path

class TreeVisualizer:
    def __init__(self):
        self.fig = None
        self.ax = None
        self.block_colors = {
            'event': '#FFBF00',    # yellow/gold
            'control': '#FFAB19',  # orange
            'motion': '#4C97FF',   # blue
            'default': '#A0A0A0',  # gray
        }
    
    def visualize(self, codeorama_data, root_event='flag_clicked', show_message_names=True):
        """Create a hierarchical tree visualization starting from a root event"""
        # Create figure
        self.fig, self.ax = plt.subplots(figsize=(14, 10))
        
        # Find all scripts triggered by the root event
        root_scripts = []
        for (sprite, event), script_list in codeorama_data['scripts'].items():
            if event.startswith(root_event):
                for i, script in enumerate(script_list):
                    root_scripts.append((sprite, event, i, script))
        
        if not root_scripts:
            self.ax.text(0.5, 0.5, f"No scripts found for event '{root_event}'", 
                       ha='center', va='center', fontsize=14)
            self.ax.set_xlim(0, 1)
            self.ax.set_ylim(0, 1)
            self.ax.axis('off')
            return self.fig
        
        # Calculate tree layout
        tree_layout = self._calculate_tree_layout(codeorama_data, root_scripts)
        
        # Draw the tree
        self._draw_tree(tree_layout, codeorama_data, show_message_names)
        
        # Adjust display
        self.ax.axis('off')
        plt.tight_layout()
        
        return self.fig
    
    def _calculate_tree_layout(self, codeorama_data, root_scripts):
        """Calculate positions for each node in the tree"""
        # This is a simplified layout calculation
        # For a real implementation, you'd want a more sophisticated algorithm
        
        # Start with root scripts at the top
        layout = {}
        layer_width = len(root_scripts)
        spacing = 1.0
        
        # Position root scripts horizontally
        for i, (sprite, event, script_idx, script) in enumerate(root_scripts):
            key = (sprite, event, script_idx)
            x = (i + 0.5) * spacing
            y = 9.0  # Start at top
            layout[key] = (x, y)
        
        # Simple BFS to layout child nodes
        visited = set([key for key in layout.keys()])
        queue = list(visited)
        layer = 1
        
        while queue and layer < 5:  # Limit depth to prevent infinite loops
            new_queue = []
            nodes_in_layer = 0
            
            # Count how many nodes will be in this layer
            for sprite, event, script_idx in queue:
                # Find any broadcasts from this script
                script = codeorama_data['scripts'][(sprite, event)][script_idx]
                broadcasts = self._find_broadcasts(sprite, event, script, codeorama_data)
                nodes_in_layer += len(broadcasts)
            
            if nodes_in_layer == 0:
                break
                
            # Position nodes in this layer
            current_pos = 0
            for sprite, event, script_idx in queue:
                # Find any broadcasts from this script
                script = codeorama_data['scripts'][(sprite, event)][script_idx]
                broadcasts = self._find_broadcasts(sprite, event, script, codeorama_data)
                
                # Place each child node
                for target_sprite, target_event, target_idx in broadcasts:
                    if (target_sprite, target_event, target_idx) not in visited:
                        key = (target_sprite, target_event, target_idx)
                        x = (current_pos + 0.5) * spacing
                        y = 9.0 - (layer * 2.0)  # Move down for each layer
                        layout[key] = (x, y)
                        visited.add(key)
                        new_queue.append(key)
                        current_pos += 1
            
            queue = new_queue
            layer += 1
        
        return layout
    
    def _find_broadcasts(self, sprite, event, script, codeorama_data):
        """Find all scripts that are triggered by broadcasts from this script"""
        result = []
        
        # Check connections to find broadcasts
        for source_sprite, source_event, _, target_event in codeorama_data['connections']:
            if source_sprite == sprite and source_event == event:
                # This script broadcasts a message
                # Find all scripts that receive this message
                for target_sprite in codeorama_data['sprites']:
                    if (target_sprite, target_event) in codeorama_data['scripts']:
                        for i, _ in enumerate(codeorama_data['scripts'][(target_sprite, target_event)]):
                            result.append((target_sprite, target_event, i))
        
        return result
    
    def _draw_tree(self, layout, codeorama_data, show_message_names):
        """Draw the tree with scripts as nodes and messages as edges"""
        # Set the axis limits based on layout
        if not layout:
            self.ax.set_xlim(0, 1)
            self.ax.set_ylim(0, 1)
            return
        
        xs = [x for x, y in layout.values()]
        ys = [y for x, y in layout.values()]
        
        margin = 1.0
        self.ax.set_xlim(min(xs) - margin, max(xs) + margin)
        self.ax.set_ylim(min(ys) - margin, max(ys) + margin)
        
        # Draw nodes
        for (sprite, event, script_idx), (x, y) in layout.items():
            script = codeorama_data['scripts'][(sprite, event)][script_idx]
            if not script:
                continue
            
            # Get color based on event type
            if event.startswith('flag_clicked'):
                color = self.block_colors['event']
            elif event.startswith('receive_'):
                color = self.block_colors['control']
            else:
                color = self.block_colors['default']
            
            # Create a node for this script
            self._draw_script_node(x, y, sprite, event, script, color)
        
        # Draw edges
        for (sprite, event, script_idx), (x1, y1) in layout.items():
            script = codeorama_data['scripts'][(sprite, event)][script_idx]
            broadcasts = self._find_broadcasts(sprite, event, script, codeorama_data)
            
            for target_sprite, target_event, target_idx in broadcasts:
                if (target_sprite, target_event, target_idx) in layout:
                    x2, y2 = layout[(target_sprite, target_event, target_idx)]
                    
                    # Draw edge from source to target
                    self._draw_edge(x1, y1, x2, y2, target_event, show_message_names)
    
    def _draw_script_node(self, x, y, sprite, event, script, color):
        """Draw a node representing a script"""
        width, height = 2.0, 1.0
        
        # Create rounded rectangle for the script
        rect = patches.FancyBboxPatch(
            (x - width/2, y - height/2), width, height,
            boxstyle=patches.BoxStyle("Round", pad=0.02, rounding_size=0.1),
            linewidth=1.5, edgecolor='black', facecolor=color, alpha=0.8
        )
        self.ax.add_patch(rect)
        
        # Add sprite name
        self.ax.text(x, y + 0.2, sprite, 
                    ha='center', va='center', fontsize=8, 
                    color='black', fontweight='bold')
        
        # Add event name
        formatted_event = event.replace('_', ' ').title()
        if formatted_event.startswith('Receive '):
            formatted_event = 'Receive: ' + formatted_event[8:]
        self.ax.text(x, y - 0.1, formatted_event,
                    ha='center', va='center', fontsize=7,
                    color='black')
        
        # Add first block opcode
        if script and len(script) > 0:
            first_block = script[0]
            opcode = first_block.get('opcode', 'Unknown')
            # Format opcode for display
            opcode = opcode.split('_')[-1].replace('_', ' ').title()
            self.ax.text(x, y - 0.3, f"({opcode})",
                        ha='center', va='center', fontsize=6,
                        color='gray', style='italic')
    
    def _draw_edge(self, x1, y1, x2, y2, target_event, show_message_names):
        """Draw an edge between scripts"""
        # Create curved path
        dx = x2 - x1
        dy = y2 - y1
        dist = np.sqrt(dx**2 + dy**2)
        
        # More curve for longer distances
        rad = min(0.3, dist / 10)
        
        # Create path points for a smoother curve
        path_points = []
        path_points.append((x1, y1 - 0.5))  # Start at bottom of source
        
        # Midpoint
        mid_x = (x1 + x2) / 2
        mid_y = y1 - abs(dy) / 2
        
        path_points.append((mid_x, mid_y))
        path_points.append((x2, y2 + 0.5))  # End at top of target
        
        # Draw the path
        codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
        path = Path(path_points, codes)
        patch = patches.PathPatch(path, facecolor='none', 
                                 edgecolor='red', lw=1.5, alpha=0.8)
        self.ax.add_patch(patch)
        
        # Add arrow at the end
        end_x, end_y = path_points[-1]
        arrow_dx = 0
        arrow_dy = -0.2
        self.ax.arrow(end_x, end_y + 0.2, arrow_dx, arrow_dy,
                     head_width=0.1, head_length=0.1, fc='red', ec='red')
        
        # Add message name if enabled
        if show_message_names and target_event.startswith('receive_'):
            message = target_event.replace('receive_', '')
            # Place the text at the midpoint of the curved arrow
            self.ax.text(mid_x, mid_y, message, fontsize=7,
                       ha='center', va='center', 
                       bbox=dict(boxstyle="round,pad=0.3", 
                                fc="white", ec="gray", alpha=0.7))