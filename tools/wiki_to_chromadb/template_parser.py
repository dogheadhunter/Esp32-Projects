"""
Template Parser - Extract ALL MediaWiki Templates

Extracts and structures template data from wikitext, including:
- Infoboxes (structured as JSON)
- Game references
- Quotes
- Icons
- Other templates

MUST be called with raw wikitext BEFORE strip_code().
"""

import re
from typing import List, Dict, Any, Tuple
import mwparserfromhell


def extract_template_safely(template) -> Tuple[str, Dict]:
    """
    Safely extract template data with fallback for complex nested templates.
    
    Args:
        template: mwparserfromhell Template object
    
    Returns:
        (template_name, parameters_dict)
    """
    try:
        name = template.name.strip_code().strip()
        params = {}
        positional = []
        
        for p in template.params:
            try:
                if p.showkey:
                    # Named parameter
                    param_name = p.name.strip_code().strip()
                    param_value = p.value.strip_code().strip()
                    params[param_name] = param_value
                else:
                    # Positional parameter
                    param_value = p.value.strip_code().strip()
                    positional.append(param_value)
            except Exception:
                continue
        
        # Add positional params to dict if they exist
        if positional:
            params['_positional'] = positional
        
        return name, params
    except Exception:
        # Fallback: just get template name
        return str(template.name).strip(), {}


def extract_infobox_data(wikitext: str) -> List[Dict]:
    """
    Parse {{Infobox ...}} templates into structured JSON.
    WITHOUT flattening or interpreting fields.
    
    Args:
        wikitext: Raw MediaWiki markup
    
    Returns:
        List of infobox dicts with keys: type, parameters
        
    Example:
        [
            {
                'type': 'Infobox character',
                'parameters': {
                    'name': 'Overseer Barstow',
                    'location': 'Vault-Tec University',
                    'affiliation': 'Vault-Tec Corporation'
                }
            }
        ]
    """
    parsed = mwparserfromhell.parse(wikitext)
    infoboxes = []
    
    for template in parsed.filter_templates():
        template_name = str(template.name).strip()
        
        # Detect infobox templates
        if template_name.lower().startswith('infobox'):
            name, params = extract_template_safely(template)
            
            # Remove positional params for infoboxes (usually not used)
            params.pop('_positional', None)
            
            infoboxes.append({
                'type': name,
                'parameters': params
            })
    
    return infoboxes


def extract_all_templates(wikitext: str) -> List[Dict]:
    """
    Extract ALL templates from wikitext, not just infoboxes.
    
    Examples:
    - {{Game|FO3|FO4}} -> Game references
    - {{Icon|gun}} -> UI elements
    - {{Quote|...}} -> Dialogue/quotes
    
    Args:
        wikitext: Raw MediaWiki markup
    
    Returns:
        List of template dicts with keys: name, params (dict), positional (list)
        
    Example:
        [
            {
                'name': 'Game',
                'positional': ['FO3', 'FO4']
            },
            {
                'name': 'Quote',
                'params': {
                    'text': 'War. War never changes.',
                    'speaker': 'Ron Perlman'
                }
            }
        ]
    """
    parsed = mwparserfromhell.parse(wikitext)
    templates = []
    
    for template in parsed.filter_templates():
        name, params = extract_template_safely(template)
        
        # Skip infoboxes (handled separately)
        if name.lower().startswith('infobox'):
            continue
        
        template_data = {'name': name}
        
        # Separate positional and named parameters
        positional = params.pop('_positional', None)
        
        if positional:
            template_data['positional'] = positional
        
        if params:
            template_data['params'] = params
        
        templates.append(template_data)
    
    return templates


def extract_game_references(wikitext: str) -> List[str]:
    """
    Extract game references from templates like {{Game|FO3|FO4}}.
    
    Args:
        wikitext: Raw MediaWiki markup
    
    Returns:
        List of full game names (e.g., ["Fallout 3", "Fallout 4"])
    """
    game_abbrev_map = {
        'FO1': 'Fallout',
        'FO2': 'Fallout 2',
        'FO3': 'Fallout 3',
        'FNV': 'Fallout: New Vegas',
        'FONV': 'Fallout: New Vegas',
        'FO4': 'Fallout 4',
        'FO76': 'Fallout 76',
        'FOT': 'Fallout Tactics',
        'FOBOS': 'Fallout: Brotherhood of Steel',
    }
    
    parsed = mwparserfromhell.parse(wikitext)
    games = []
    
    for template in parsed.filter_templates():
        name, params = extract_template_safely(template)
        
        # Check if it's a Game template
        if name.lower() in ['game', 'games']:
            # Extract positional parameters (game abbreviations)
            positional = params.get('_positional', [])
            for game_code in positional:
                game_code = game_code.strip().upper()
                if game_code in game_abbrev_map:
                    games.append(game_abbrev_map[game_code])
            
            # Also check named parameters
            for key, value in params.items():
                if key != '_positional':
                    game_code = value.strip().upper()
                    if game_code in game_abbrev_map:
                        games.append(game_abbrev_map[game_code])
    
    return list(set(games))  # Remove duplicates


def extract_all_template_metadata(wikitext: str) -> Dict[str, Any]:
    """
    Extract all template-related metadata from wikitext.
    
    This is a convenience function that calls all template extraction functions.
    
    Args:
        wikitext: Raw MediaWiki markup
    
    Returns:
        Dict with keys: infoboxes, templates, game_source
    """
    return {
        'infoboxes': extract_infobox_data(wikitext),
        'templates': extract_all_templates(wikitext),
        'game_source': extract_game_references(wikitext)
    }


if __name__ == "__main__":
    # Test with example wikitext
    test_wikitext = """
{{Infobox character
|name = Overseer Barstow
|location = Vault-Tec University
|affiliation = Vault-Tec Corporation
|appears = Fallout 76
}}

{{Game|FO3|FO4|FO76}}

The '''Overseer''' was a key figure in {{Icon|vault}} Vault-Tec operations.

{{Quote|War never changes.|Ron Perlman}}
"""
    
    print("Testing Template Parser")
    print("=" * 60)
    
    # Test infobox extraction
    infoboxes = extract_infobox_data(test_wikitext)
    print(f"\nInfoboxes found: {len(infoboxes)}")
    for ib in infoboxes:
        print(f"  Type: {ib['type']}")
        print(f"  Parameters: {ib['parameters']}")
    
    # Test all templates
    templates = extract_all_templates(test_wikitext)
    print(f"\nTemplates found: {len(templates)}")
    for t in templates:
        print(f"  {t}")
    
    # Test game references
    games = extract_game_references(test_wikitext)
    print(f"\nGame references: {games}")
    
    # Test combined extraction
    print("\nCombined metadata:")
    metadata = extract_all_template_metadata(test_wikitext)
    import json
    print(json.dumps(metadata, indent=2))
