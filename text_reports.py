class TextReportGenerator:
    def __init__(self, codeorama_data):
        self.sprites = codeorama_data['sprites']
        self.events = codeorama_data['events']
        self.scripts = codeorama_data['scripts']
        self.connections = codeorama_data['connections']
        
    def generate_broadcast_report(self):
        """Generate a report of broadcast messages and their receivers"""
        report = "BROADCAST REPORT\n===============\n\n"
        
        # Create a dictionary of broadcasts: {(sprite, message): [receiving_sprites]}
        broadcasts = {}
        for source_sprite, source_event, _, target_event in self.connections:
            if target_event and target_event.startswith('receive_'):
                message = target_event.replace('receive_', '')
                key = (source_sprite, message)
                if key not in broadcasts:
                    broadcasts[key] = []
                
                # Find all sprites that receive this message
                for sprite in self.sprites:
                    if (sprite, f'receive_{message}') in self.scripts:
                        if sprite not in broadcasts[key]:
                            broadcasts[key].append(sprite)
        
        # Format the report
        for (sprite, message), receivers in sorted(broadcasts.items()):
            report += f"Sprite '{sprite}' broadcasts '{message}' to:\n"
            if receivers:
                for receiver in receivers:
                    report += f"  - {receiver}\n"
            else:
                report += "  (No receivers)\n"
            report += "\n"
            
        return report
    
    def generate_receive_report(self):
        """Generate a report of received messages and their broadcasters"""
        report = "RECEIVE REPORT\n==============\n\n"
        
        # Create a dictionary of receives: {(sprite, message): [broadcasting_sprites]}
        receives = {}
        for source_sprite, source_event, _, target_event in self.connections:
            if target_event and target_event.startswith('receive_'):
                message = target_event.replace('receive_', '')
                
                # Find all sprites that receive this message
                for sprite in self.sprites:
                    if (sprite, f'receive_{message}') in self.scripts:
                        key = (sprite, message)
                        if key not in receives:
                            receives[key] = []
                        if source_sprite not in receives[key]:
                            receives[key].append(source_sprite)
        
        # Format the report
        for (sprite, message), broadcasters in sorted(receives.items()):
            report += f"Sprite '{sprite}' receives '{message}' from:\n"
            if broadcasters:
                for broadcaster in broadcasters:
                    report += f"  - {broadcaster}\n"
            else:
                report += "  (No broadcasters found)\n"
            report += "\n"
            
        return report
    
    def generate_script_layout(self):
        """Generate a text-based layout of scripts with connections"""
        report = "SCRIPT LAYOUT\n=============\n\n"
        
        for sprite in self.sprites:
            report += f"SPRITE: {sprite}\n"
            report += "=" * (len(sprite) + 8) + "\n\n"
            
            # Get all scripts for this sprite
            sprite_scripts = {event: scripts for (s, event), scripts in self.scripts.items() if s == sprite}
            
            for event in self.events:
                if event in sprite_scripts:
                    report += f"EVENT: {event}\n"
                    report += "-" * (len(event) + 7) + "\n"
                    
                    # For each script in this event
                    for script_idx, script in enumerate(sprite_scripts[event]):
                        report += f"Script #{script_idx + 1}:\n"
                        
                        # Print blocks with special handling for broadcasts
                        for block in script:
                            block_text = f"  {block['opcode']}"
                            
                            # Add special annotations for broadcasts and receives
                            if block['opcode'] == 'event_broadcast' or block['opcode'] == 'event_broadcastandwait':
                                msg = self._get_broadcast_message(block)
                                if msg:
                                    block_text += f" '{msg}'"
                                    # Add receivers
                                    receivers = self._get_receivers(sprite, msg)
                                    if receivers:
                                        block_text += " → " + ", ".join(receivers)
                            
                            report += block_text + "\n"
                        
                        report += "\n"
            
            report += "\n\n"
            
        return report
    
    def _get_broadcast_message(self, block):
        """Try to extract message from a broadcast block"""
        # This is a simplified version - actual implementation would be more complex
        if 'inputs' in block and 'BROADCAST_INPUT' in block['inputs']:
            # This is just a placeholder - actual implementation would extract from inputs
            return "message_placeholder"
        return None
    
    def _get_receivers(self, source_sprite, message):
        """Get list of sprites that receive a specific message"""
        receivers = []
        for sprite in self.sprites:
            if (sprite, f'receive_{message}') in self.scripts:
                receivers.append(sprite)
        return receivers