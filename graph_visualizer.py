import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

class GraphVisualizer:
    def __init__(self):
        self.fig = None
        self.ax = None
        self.block_colors = {
            'event': '#FFBF00',    # yellow/gold
            'control': '#FFAB19',  # orange
            'motion': '#4C97FF',   # blue
            'looks': '#9966FF',    # purple
            'sound': '#CF63CF',    # magenta
            'sensing': '#5CB1D6',  # light blue
            'operator': '#59C059', # green
            'default': '#A0A0A0',  # gray
        }
    
    def visualize(self, codeorama_data, layout_type='spring', show_message_names=True):
        """Create a force-directed graph visualization of the CodeOrama data"""
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add sprites as larger nodes
        sprite_colors = {}
        for i, sprite in enumerate(codeorama_data['sprites']):
            sprite_id = f"sprite_{sprite}"
            G.add_node(sprite_id, 
                      type='sprite', 
                      label=sprite, 
                      size=1500,
                      color='#4C97FF')
            sprite_colors[sprite] = plt.cm.tab10(i % 10)
        
        # Add scripts as nodes
        script_positions = {}
        for (sprite, event), script_list in codeorama_data['scripts'].items():
            for i, script in enumerate(script_list):
                if not script:
                    continue
                
                # Create a unique ID for this script
                script_id = f"script_{sprite}_{event}_{i}"
                
                # Get color based on event type
                if event.startswith('flag_clicked'):
                    color = self.block_colors['event']
                elif event.startswith('receive_'):
                    color = self.block_colors['control']
                else:
                    color = self.block_colors['default']
                
                # Get script label (first block opcode)
                first_block = script[0]
                label = first_block.get('opcode', 'Unknown').split('_')[-1]
                
                # Add the script node
                G.add_node(script_id, 
                          type='script', 
                          sprite=sprite,
                          event=event,
                          label=label,
                          size=500,
                          color=color)
                
                # Connect this script to its sprite
                sprite_id = f"sprite_{sprite}"
                G.add_edge(sprite_id, script_id, type='contains', weight=0.5)
        
        # Add message connections
        for source_sprite, source_event, _, target_event in codeorama_data['connections']:
            if source_sprite and source_event and target_event:
                # For each script that broadcasts this message
                for i, script in enumerate(codeorama_data['scripts'].get((source_sprite, source_event), [])):
                    source_id = f"script_{source_sprite}_{source_event}_{i}"
                    
                    # For each sprite that has a script receiving this message
                    for target_sprite in codeorama_data['sprites']:
                        if (target_sprite, target_event) in codeorama_data['scripts']:
                            for j, target_script in enumerate(codeorama_data['scripts'][(target_sprite, target_event)]):
                                target_id = f"script_{target_sprite}_{target_event}_{j}"
                                
                                # Get message name
                                message = target_event.replace('receive_', '')
                                
                                # Add edge from source to target
                                G.add_edge(source_id, target_id, 
                                          type='message', 
                                          message=message,
                                          weight=2.0)
        
        # Create figure
        plt.figure(figsize=(14, 10))
        
        # Choose layout algorithm
        if layout_type == 'spring':
            pos = nx.spring_layout(G, k=0.3, iterations=50)
        elif layout_type == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(G)
        elif layout_type == 'spectral':
            pos = nx.spectral_layout(G)
        else:
            pos = nx.spring_layout(G)
        
        # Draw sprites (larger nodes)
        sprite_nodes = [n for n, attr in G.nodes(data=True) if attr['type'] == 'sprite']
        sprite_colors_list = [sprite_colors[G.nodes[n]['label']] for n in sprite_nodes]
        nx.draw_networkx_nodes(G, pos, 
                              nodelist=sprite_nodes,
                              node_size=[G.nodes[n]['size'] for n in sprite_nodes],
                              node_color=sprite_colors_list,
                              alpha=0.8)
        
        # Draw scripts (smaller nodes)
        script_nodes = [n for n, attr in G.nodes(data=True) if attr['type'] == 'script']
        script_colors = [G.nodes[n]['color'] for n in script_nodes]
        nx.draw_networkx_nodes(G, pos, 
                              nodelist=script_nodes,
                              node_size=[G.nodes[n]['size'] for n in script_nodes],
                              node_color=script_colors,
                              alpha=0.8)
        
        # Draw contains edges (sprite to script)
        contains_edges = [(u, v) for u, v, attr in G.edges(data=True) if attr['type'] == 'contains']
        nx.draw_networkx_edges(G, pos, 
                              edgelist=contains_edges,
                              width=1, alpha=0.5, 
                              edge_color='gray',
                              style='dashed')
        
        # Draw message edges
        message_edges = [(u, v) for u, v, attr in G.edges(data=True) if attr['type'] == 'message']
        nx.draw_networkx_edges(G, pos, 
                              edgelist=message_edges,
                              width=2, alpha=0.8, 
                              edge_color='red',
                              arrows=True,
                              arrowsize=15)
        
        # Add labels
        sprite_labels = {n: G.nodes[n]['label'] for n in sprite_nodes}
        nx.draw_networkx_labels(G, pos, 
                               labels=sprite_labels,
                               font_size=10, 
                               font_weight='bold')
        
        script_labels = {n: G.nodes[n]['label'] for n in script_nodes}
        nx.draw_networkx_labels(G, pos, 
                               labels=script_labels,
                               font_size=8)
        
        # Add message labels if requested
        if show_message_names:
            edge_labels = {(u, v): G.edges[u, v]['message'] 
                          for u, v, attr in G.edges(data=True) 
                          if attr['type'] == 'message'}
            nx.draw_networkx_edge_labels(G, pos, 
                                        edge_labels=edge_labels,
                                        font_size=8,
                                        font_color='black',
                                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
        
        plt.axis('off')
        plt.tight_layout()
        
        return plt.gcf()