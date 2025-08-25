#!/usr/bin/env python3
"""
Quick test script to demonstrate OpenDKP conversion functionality
"""

import re

def convert_to_opendkp_format(who_content):
    """Convert /who result content to OpenDKP tab-separated format"""
    lines = who_content.split('\n')
    opendkp_lines = []
    
    # Class name mapping for consistency (including EQ class titles)
    class_mappings = {
        # Standard classes
        'warrior': 'Warrior',
        'paladin': 'Paladin',
        'ranger': 'Ranger',
        'shadow knight': 'Shadow Knight',
        'monk': 'Monk',
        'bard': 'Bard',
        'rogue': 'Rogue',
        'shaman': 'Shaman',
        'necromancer': 'Necromancer',
        'wizard': 'Wizard',
        'magician': 'Magician',
        'enchanter': 'Enchanter',
        'druid': 'Druid',
        'cleric': 'Cleric',
        'beastlord': 'Beastlord',
        'berserker': 'Berserker',
        
        # Enchanter titles
        'phantasmist': 'Enchanter',
        'illusionist': 'Enchanter',
        'beguiler': 'Enchanter',
        'arch convoker': 'Enchanter',
        'coercer': 'Enchanter',
        
        # Magician titles
        'conjurer': 'Magician',
        'elementalist': 'Magician',
        'arch mage': 'Magician',
        
        # Wizard titles
        'warlock': 'Wizard',
        'sorcerer': 'Wizard',
        'arcanist': 'Wizard',
        
        # Warrior titles
        'myrmidon': 'Warrior',
        'champion': 'Warrior',
        'overlord': 'Warrior',
        'warlord': 'Warrior',
        
        # Monk titles
        'master': 'Monk',
        'grandmaster': 'Monk',
        'transcendent': 'Monk',
        
        # Cleric/Paladin titles
        'templar': 'Paladin',
        'crusader': 'Paladin',
        'knight': 'Paladin',
        'cavalier': 'Paladin',
        
        # Shadow Knight titles
        'heretic': 'Shadow Knight',
        'reaver': 'Shadow Knight',
        'blackguard': 'Shadow Knight',
        
        # Common alternatives
        'sk': 'Shadow Knight',
        'shadowknight': 'Shadow Knight',
        'enc': 'Enchanter',
        'mag': 'Magician',
        'wiz': 'Wizard',
        'nec': 'Necromancer',
        'war': 'Warrior',
        'pal': 'Paladin',
        'ran': 'Ranger',
        'rog': 'Rogue',
        'mnk': 'Monk',
        'shm': 'Shaman',
        'dru': 'Druid',
        'cle': 'Cleric',
        'bst': 'Beastlord',
        'ber': 'Berserker',
        
        # Alternative names
        'minstrel': 'Bard',
        'troubadour': 'Bard',
        'unknown': 'Unknown',
    }
    
    for line in lines:
        line = line.strip()
        
        if not line or 'Players on EverQuest' in line or line.startswith('---') or line.startswith('There are'):
            continue
        
        # Remove timestamp from beginning if present
        if line.startswith('[') and '] [' in line:
            # Extract everything after the timestamp
            parts = line.split('] ', 1)
            if len(parts) > 1:
                line = parts[1]
        
        # Parse player lines - look for [Level ClassTitle] Name or [ANONYMOUS] Name
        player_match = None
        
        # Try to match [Level ClassTitle] PlayerName (Race) <Guild> pattern first
        player_match = re.match(r'^\[(\d+)\s+([A-Za-z ]+)\]\s+([A-Za-z0-9_]+)', line)
        if player_match:
            level = player_match.group(1)
            class_name = player_match.group(2).strip()
            player_name = player_match.group(3).strip()
        else:
            # Try to match [ANONYMOUS] PlayerName pattern
            anon_match = re.match(r'^\[ANONYMOUS\]\s+([A-Za-z0-9_]+)', line)
            if anon_match:
                level = "0"  # Unknown level for anonymous
                class_name = "Unknown"  # No class info for anonymous
                player_name = anon_match.group(1).strip()
            else:
                continue  # Skip lines we can't parse
        
        # Normalize class name
        class_name_lower = class_name.lower()
        normalized_class = class_mappings.get(class_name_lower, class_name)
        
        # Create OpenDKP format: 0\tPlayerName\tLevel\tClass
        opendkp_line = f"0\t{player_name}\t{level}\t{normalized_class}"
        opendkp_lines.append(opendkp_line)
    
    return '\n'.join(opendkp_lines)

# Test with actual EQ data format
test_who_content = """[Tue Jul 01 22:08:30 2025] Players on EverQuest:
[Tue Jul 01 22:08:30 2025] ---------------------------
[Tue Jul 01 22:08:30 2025] [60 Phantasmist] Accosted (Dark Elf) <Denial>
[Tue Jul 01 22:08:30 2025] [51 Illusionist] Drokoth (High Elf) <Denial> LFG
[Tue Jul 01 22:08:30 2025] [57 Conjurer] Kilowattz (Gnome) <Denial>
[Tue Jul 01 22:08:30 2025] [ANONYMOUS] Toad 
[Tue Jul 01 22:08:30 2025] [ANONYMOUS] Akuppee  <Denial>
[Tue Jul 01 22:08:30 2025] [52 Heretic] Luciferianism (Skeleton) <Denial>
[Tue Jul 01 22:08:30 2025] [60 Arch Mage] Hakaresh (Erudite) <Denial>
[Tue Jul 01 22:08:30 2025] [55 Myrmidon] Kawaiinomu (Gnome) <CUTE>
[Tue Jul 01 22:08:30 2025] There are 24 players in Kael Drakkal."""

print("Original /who data:")
print("=" * 50)
print(test_who_content)
print("\n\nConverted OpenDKP format:")
print("=" * 50)
converted = convert_to_opendkp_format(test_who_content)
print(converted)
print("\n\nFormat explanation:")
print("Each line is: 0\\tPlayerName\\tLevel\\tClass")
print("- First column: Always '0' (placeholder)")
print("- Second column: Character name")
print("- Third column: Character level (0 for ANONYMOUS)")
print("- Fourth column: Normalized class name")