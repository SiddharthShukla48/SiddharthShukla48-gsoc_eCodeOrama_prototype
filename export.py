import os
import io
import csv
import json
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

class CodeOramaExporter:
    """Handles export of CodeOrama visualizations to different formats"""
    
    def __init__(self, codeorama_data, config=None):
        self.sprites = codeorama_data['sprites']
        self.events = codeorama_data['events']
        self.scripts = codeorama_data['scripts']
        self.connections = codeorama_data['connections']
        self.config = config or {}
        
        # Apply custom ordering if provided
        if self.config and 'sprite_order' in self.config:
            # Use only sprites that exist in the data
            sprite_order = [s for s in self.config['sprite_order'] if s in self.sprites]
            # Add any sprites not in the order
            sprite_order.extend([s for s in self.sprites if s not in sprite_order])
            self.sprites = sprite_order
        
        if self.config and 'event_order' in self.config:
            # Use only events that exist in the data
            event_order = [e for e in self.config['event_order'] if e in self.events]
            # Add any events not in the order
            event_order.extend([e for e in self.events if e not in event_order])
            self.events = event_order
    
    def export_to_pdf(self, output_path):
        """Export CodeOrama to a formatted PDF document"""
        # Create a PDF document
        doc = SimpleDocTemplate(output_path, pagesize=landscape(A3))
        elements = []
        
        # Get styles for text
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        header_style = styles['Heading2']
        
        # Add title
        elements.append(Paragraph("CodeOrama Visualization", title_style))
        elements.append(Spacer(1, 0.5*inch))
        
        # Create table data
        table_data = []
        
        # Header row with sprite names
        header_row = ['Events / Sprites']
        header_row.extend(self.sprites)
        table_data.append(header_row)
        
        # Add rows for each event
        for event in self.events:
            row = [self._format_event_name(event)]
            
            # Add cells for each sprite
            for sprite in self.sprites:
                if (sprite, event) in self.scripts:
                    # Get scripts for this cell
                    scripts_text = self._format_scripts_for_cell(sprite, event)
                    row.append(scripts_text)
                else:
                    row.append("")
            
            table_data.append(row)
        
        # Create table
        table = Table(table_data, repeatRows=1)
        
        # Apply table style
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 0), (0, -1), 12),
            ('FONTSIZE', (1, 1), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])
        
        # Add broadcast connection indicators
        for source_sprite, source_event, _, target_event in self.connections:
            if source_sprite and source_event and target_event:
                # Find source cell position
                source_col = self.sprites.index(source_sprite) + 1  # +1 for header column
                source_row = self.events.index(source_event) + 1  # +1 for header row
                
                # Find all receiving sprites
                for sprite_idx, sprite in enumerate(self.sprites):
                    if (sprite, target_event) in self.scripts:
                        target_col = sprite_idx + 1  # +1 for header column
                        target_row = self.events.index(target_event) + 1  # +1 for header row
                        
                        # Highlight cells with broadcasts/receives
                        style.add('BACKGROUND', (source_col, source_row), (source_col, source_row), colors.lightblue)
                        style.add('BACKGROUND', (target_col, target_row), (target_col, target_row), colors.lightyellow)
        
        table.setStyle(style)
        elements.append(table)
        
        # Add connection information
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("Message Connections:", header_style))
        
        for source_sprite, source_event, _, target_event in self.connections:
            if source_sprite and source_event and target_event and target_event.startswith('receive_'):
                message = target_event.replace('receive_', '')
                
                # Find all receiving sprites
                receivers = []
                for sprite in self.sprites:
                    if (sprite, target_event) in self.scripts:
                        receivers.append(sprite)
                
                if receivers:
                    connection_text = f"From '{source_sprite}' (event '{self._format_event_name(source_event)}') "
                    connection_text += f"broadcasts '{message}' to: " + ", ".join(receivers)
                    elements.append(Paragraph(connection_text, styles['Normal']))
        
        # Build the PDF
        doc.build(elements)
        return True
    
    def export_to_text(self, output_path):
        """Export CodeOrama to a text-based layout"""
        with open(output_path, 'w') as f:
            # Title
            f.write("CODEORAMA TEXT LAYOUT\n")
            f.write("=====================\n\n")
            
            # Create a simple text-based table
            # Header row
            header = "Events / Sprites | "
            header += " | ".join(self.sprites)
            f.write(header + "\n")
            f.write("-" * len(header) + "\n")
            
            # Event rows
            for event in self.events:
                row = f"{self._format_event_name(event)} | "
                
                # Sprite cells
                cells = []
                for sprite in self.sprites:
                    if (sprite, event) in self.scripts:
                        script_count = len(self.scripts[(sprite, event)])
                        cells.append(f"{script_count} script(s)")
                    else:
                        cells.append("-")
                
                row += " | ".join(cells)
                f.write(row + "\n")
            
            f.write("\n\n")
            
            # Detailed script listing
            f.write("DETAILED SCRIPT LISTING\n")
            f.write("======================\n\n")
            
            for sprite in self.sprites:
                f.write(f"SPRITE: {sprite}\n")
                f.write("=" * (len(sprite) + 8) + "\n\n")
                
                # Get all scripts for this sprite
                sprite_scripts = {event: scripts for (s, event), scripts in self.scripts.items() if s == sprite}
                
                for event in self.events:
                    if event in sprite_scripts:
                        f.write(f"EVENT: {self._format_event_name(event)}\n")
                        f.write("-" * (len(event) + 7) + "\n")
                        
                        # For each script in this event
                        for script_idx, script in enumerate(sprite_scripts[event]):
                            f.write(f"Script #{script_idx + 1}:\n")
                            
                            # Print blocks with special handling for broadcasts
                            for block in script:
                                block_text = f"  {block['opcode']}"
                                
                                # Add special annotations for broadcasts and receives
                                if block['opcode'] == 'event_broadcast' or block['opcode'] == 'event_broadcastandwait':
                                    # Find the message by looking for connections from this sprite/event
                                    matching_connections = [conn for conn in self.connections 
                                                          if conn[0] == sprite and conn[1] == event]
                                    
                                    for conn in matching_connections:
                                        if conn[3] and conn[3].startswith('receive_'):
                                            msg = conn[3].replace('receive_', '')
                                            block_text += f" '{msg}'"
                                            
                                            # Add receivers
                                            receivers = []
                                            for s in self.sprites:
                                                if (s, conn[3]) in self.scripts:
                                                    receivers.append(s)
                                            
                                            if receivers:
                                                block_text += " → " + ", ".join(receivers)
                                
                                f.write(block_text + "\n")
                            
                            f.write("\n")
                
                f.write("\n\n")
            
            # Message connections summary
            f.write("MESSAGE CONNECTIONS\n")
            f.write("==================\n\n")
            
            for source_sprite, source_event, _, target_event in self.connections:
                if source_sprite and source_event and target_event and target_event.startswith('receive_'):
                    message = target_event.replace('receive_', '')
                    
                    # Find all receiving sprites
                    receivers = []
                    for sprite in self.sprites:
                        if (sprite, target_event) in self.scripts:
                            receivers.append(sprite)
                    
                    if receivers:
                        connection_text = f"From '{source_sprite}' (event '{self._format_event_name(source_event)}') "
                        connection_text += f"broadcasts '{message}' to: " + ", ".join(receivers)
                        f.write(connection_text + "\n")
            
        return True
    
    def export_edge_list(self, output_path):
        """Export a simple list of all connections (edges)"""
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(['Source Sprite', 'Source Event', 'Message', 'Target Sprite', 'Target Event'])
            
            # Write edges
            for source_sprite, source_event, _, target_event in self.connections:
                if source_sprite and source_event and target_event and target_event.startswith('receive_'):
                    message = target_event.replace('receive_', '')
                    
                    # For each receiving sprite, write an edge
                    for sprite in self.sprites:
                        if (sprite, target_event) in self.scripts:
                            writer.writerow([
                                source_sprite, 
                                self._format_event_name(source_event),
                                message,
                                sprite,
                                self._format_event_name(target_event)
                            ])
        
        return True
    
    def export_to_excel(self, output_path):
        """Export CodeOrama to Excel/LibreCalc format"""
        # Create a pandas Excel writer
        writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
        
        # Create the CodeOrama grid data
        grid_data = []
        
        # Header row
        header_row = ['Events / Sprites']
        header_row.extend(self.sprites)
        grid_data.append(header_row)
        
        # Add rows for each event
        for event in self.events:
            row = [self._format_event_name(event)]
            
            # Add cells for each sprite
            for sprite in self.sprites:
                if (sprite, event) in self.scripts:
                    # Count scripts for this cell
                    script_count = len(self.scripts[(sprite, event)])
                    row.append(f"{script_count} script(s)")
                else:
                    row.append("")
            
            grid_data.append(row)
        
        # Convert to DataFrame and write to Excel
        df_grid = pd.DataFrame(grid_data[1:], columns=grid_data[0])
        df_grid.to_excel(writer, sheet_name='CodeOrama Grid', index=False)
        
        # Create the connections data
        connections_data = []
        
        # Header row
        connections_data.append(['Source Sprite', 'Source Event', 'Message', 'Target Sprite'])
        
        # Add rows for each connection
        for source_sprite, source_event, _, target_event in self.connections:
            if source_sprite and source_event and target_event and target_event.startswith('receive_'):
                message = target_event.replace('receive_', '')
                
                # For each receiving sprite, add a row
                for sprite in self.sprites:
                    if (sprite, target_event) in self.scripts:
                        connections_data.append([
                            source_sprite,
                            self._format_event_name(source_event),
                            message,
                            sprite
                        ])
        
        # Convert to DataFrame and write to Excel
        df_connections = pd.DataFrame(connections_data[1:], columns=connections_data[0])
        df_connections.to_excel(writer, sheet_name='Connections', index=False)
        
        # Create the scripts data
        scripts_data = []
        
        # Header row
        scripts_data.append(['Sprite', 'Event', 'Script Index', 'Block Count', 'First Block Opcode'])
        
        # Add rows for each script
        for (sprite, event), script_list in self.scripts.items():
            for i, script in enumerate(script_list):
                scripts_data.append([
                    sprite,
                    self._format_event_name(event),
                    i + 1,
                    len(script),
                    script[0]['opcode'] if script else 'Empty Script'
                ])
        
        # Convert to DataFrame and write to Excel
        df_scripts = pd.DataFrame(scripts_data[1:], columns=scripts_data[0])
        df_scripts.to_excel(writer, sheet_name='Scripts', index=False)
        
        # Save the Excel file
        writer.save()
        return True
    
    def export_to_json(self, output_path):
        """Export CodeOrama to JSON format for use with other tools"""
        export_data = {
            'sprites': self.sprites,
            'events': self.events,
            'grid': {},
            'connections': []
        }
        
        # Build grid data
        for (sprite, event), script_list in self.scripts.items():
            if sprite not in export_data['grid']:
                export_data['grid'][sprite] = {}
            
            export_data['grid'][sprite][event] = {
                'script_count': len(script_list),
                'scripts': []
            }
            
            # Add script details
            for script in script_list:
                script_details = {
                    'block_count': len(script),
                    'first_block': script[0]['opcode'] if script else 'Empty Script',
                    'blocks': [block['opcode'] for block in script]
                }
                export_data['grid'][sprite][event]['scripts'].append(script_details)
        
        # Add connection data
        for source_sprite, source_event, _, target_event in self.connections:
            if source_sprite and source_event and target_event and target_event.startswith('receive_'):
                message = target_event.replace('receive_', '')
                
                # Find all receiving sprites
                for sprite in self.sprites:
                    if (sprite, target_event) in self.scripts:
                        export_data['connections'].append({
                            'source_sprite': source_sprite,
                            'source_event': source_event,
                            'message': message,
                            'target_sprite': sprite,
                            'target_event': target_event
                        })
        
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return True
    
    def _format_event_name(self, event):
        """Format event name for display"""
        formatted = event.replace('_', ' ').title()
        if formatted.startswith('Receive '):
            formatted = 'Receive: ' + formatted[8:]
        return formatted
    
    def _format_scripts_for_cell(self, sprite, event):
        """Format scripts for display in a cell"""
        script_list = self.scripts.get((sprite, event), [])
        if not script_list:
            return ""
        
        text = ""
        for i, script in enumerate(script_list):
            if i > 0:
                text += "\n---\n"
                
            # Add first few blocks of the script
            for j, block in enumerate(script[:3]):  # Show only first 3 blocks
                if j > 0:
                    text += "\n"
                text += block['opcode'].split('_')[-1]
            
            # If there are more blocks, add an indicator
            if len(script) > 3:
                text += f"\n... +{len(script)-3} more blocks"
        
        return text