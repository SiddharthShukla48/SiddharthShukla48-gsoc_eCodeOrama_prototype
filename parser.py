import json
import zipfile
from collections import defaultdict

class ScratchParser:
    def __init__(self):
        self.sprites = []
        self.events = set()
        self.scripts = defaultdict(list)  # {(sprite_name, event_name): [scripts]}
        self.connections = []  # [(source_sprite, source_script, target_sprite, target_event)]
        
    def parse_sb3(self, file_path):
        """Parse a Scratch .sb3 file and extract sprites, events, scripts and connections"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                if 'project.json' in zip_ref.namelist():
                    with zip_ref.open('project.json') as f:
                        project_data = json.load(f)
                        self._parse_project_data(project_data)
                        return True
                else:
                    print("Invalid Scratch file: project.json not found")
                    return False
        except Exception as e:
            print(f"Error parsing Scratch file: {e}")
            return False
    
    def _parse_project_data(self, data):
        """Extract information from the project JSON data"""
        # Extract stage (background) as a sprite
        if 'targets' in data:
            for target in data['targets']:
                sprite_name = target['name']
                self.sprites.append(sprite_name)
                
                # Process scripts for this sprite
                if 'blocks' in target:
                    self._process_blocks(sprite_name, target['blocks'])
    
    def _process_blocks(self, sprite_name, blocks):
        """Process block definitions to identify scripts, events, and broadcasts"""
        # Find all script entry points (hat blocks)
        script_blocks = {}
        
        # First pass: identify script entry points
        for block_id, block in blocks.items():
            if block['topLevel'] and block['opcode'].startswith('event_'):
                event_name = self._get_event_name(block)
                if event_name:
                    self.events.add(event_name)
                    script_blocks[block_id] = (event_name, [])
        
        # Second pass: follow each script and collect blocks
        for block_id, (event_name, script_blocks_list) in script_blocks.items():
            current_id = block_id
            while current_id:
                block = blocks.get(current_id)
                if not block:
                    break
                
                script_blocks_list.append(block)
                
                # Check for broadcast blocks
                if block['opcode'] == 'event_broadcast' or block['opcode'] == 'event_broadcastandwait':
                    broadcast_message = self._get_broadcast_message(block, blocks)
                    if broadcast_message:
                        # Record this connection
                        self.connections.append((
                            sprite_name,
                            event_name,
                            None,  # Target sprite (all that listen to this message)
                            f"receive_{broadcast_message}"  # Target event
                        ))
                
                # Move to next block in script
                current_id = block.get('next')
            
            # Add complete script to our collection
            self.scripts[(sprite_name, event_name)].append(script_blocks_list)
    
    def _get_event_name(self, block):
        """Extract the event name from a hat block"""
        if block['opcode'] == 'event_whenflagclicked':
            return 'flag_clicked'
        elif block['opcode'] == 'event_whenkeypressed':
            key = self._get_input_value(block, 'KEY_OPTION')
            return f'key_pressed_{key}'
        elif block['opcode'] == 'event_whenbroadcastreceived':
            message = self._get_input_value(block, 'BROADCAST_OPTION')
            return f'receive_{message}'
        elif block['opcode'] == 'event_whenstageclicked':
            return 'stage_clicked'
        elif block['opcode'] == 'event_whenthisspriteclicked':
            return 'sprite_clicked'
        return None
    
    def _get_broadcast_message(self, block, all_blocks):
        """Extract the broadcast message from a broadcast block"""
        if 'inputs' in block and 'BROADCAST_INPUT' in block['inputs']:
            input_block_id = block['inputs']['BROADCAST_INPUT'][1]
            if isinstance(input_block_id, str) and input_block_id in all_blocks:
                input_block = all_blocks[input_block_id]
                if 'fields' in input_block and 'BROADCAST_OPTION' in input_block['fields']:
                    return input_block['fields']['BROADCAST_OPTION'][0]
        return None
    
    def _get_input_value(self, block, input_name):
        """Get the value of an input field"""
        if 'fields' in block and input_name in block['fields']:
            return block['fields'][input_name][0]
        return None
    
    def get_codeorama_data(self):
        """Return data structured for the CodeOrama visualization"""
        return {
            'sprites': self.sprites,
            'events': sorted(list(self.events)),
            'scripts': dict(self.scripts),
            'connections': self.connections
        }