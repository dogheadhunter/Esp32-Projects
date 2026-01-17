"""
Structural Metadata Extractor

Consolidated extraction of all MediaWiki structural elements.
Replaces separate functions from template_parser.py and chunker.py.
"""

import re
from typing import List, Tuple, Dict
import mwparserfromhell

from tools.wiki_to_chromadb.models import (
    WikiLink, SectionInfo, Template, Infobox, StructuralMetadata
)
from tools.wiki_to_chromadb.constants import GAME_ABBREVIATIONS
from tools.wiki_to_chromadb.logging_config import get_logger

logger = get_logger(__name__)


class StructuralExtractor:
    """
    Extracts structural metadata from raw MediaWiki markup.
    
    MUST be called BEFORE strip_code() to preserve markup.
    """
    
    @staticmethod
    def extract_categories(wikitext: str) -> List[str]:
        """
        Extract all [[Category:...]] tags from raw wikitext.
        
        Args:
            wikitext: Raw MediaWiki markup
        
        Returns:
            List of category names (e.g., ["Vaults", "Fallout 3 locations"])
        """
        category_pattern = r'\[\[Category:([^\]]+)\]\]'
        categories = re.findall(category_pattern, wikitext, re.IGNORECASE)
        return [cat.strip() for cat in categories]
    
    @staticmethod
    def extract_wikilinks(wikitext: str) -> List[WikiLink]:
        """
        Extract [[Link|Display Text]] markup from raw wikitext.
        
        Args:
            wikitext: Raw MediaWiki markup
        
        Returns:
            List of WikiLink objects
        """
        # [[Page Name|Display Text]]
        piped_link = r'\[\[([^\]|]+)\|([^\]]+)\]\]'
        # [[Page Name]]
        simple_link = r'\[\[([^\]|]+)\]\]'
        
        links = []
        
        # Find piped links first
        for match in re.finditer(piped_link, wikitext):
            target = match.group(1).strip()
            display = match.group(2).strip()
            
            links.append(WikiLink(
                target=target,
                display=display,
                type=StructuralExtractor._classify_link_type(target)
            ))
        
        # Find simple links
        for match in re.finditer(simple_link, wikitext):
            target = match.group(1).strip()
            
            # Skip if already captured as piped link
            if not any(link.target == target for link in links):
                links.append(WikiLink(
                    target=target,
                    display=target,
                    type=StructuralExtractor._classify_link_type(target)
                ))
        
        return links
    
    @staticmethod
    def _classify_link_type(target: str) -> str:
        """Classify wiki link types"""
        if target.startswith('Category:'):
            return 'category'
        elif target.startswith('File:') or target.startswith('Image:'):
            return 'media'
        else:
            return 'internal'
    
    @staticmethod
    def extract_section_tree(wikitext: str) -> List[SectionInfo]:
        """
        Parse MediaWiki section headers into hierarchical structure.
        
        MediaWiki syntax:
        = Level 1 =
        == Level 2 ==
        === Level 3 ===
        
        Args:
            wikitext: Raw MediaWiki markup
        
        Returns:
            List of SectionInfo objects
        """
        section_pattern = r'^(={1,6})\s*(.+?)\s*\1\s*$'
        sections = []
        
        for line_num, line in enumerate(wikitext.split('\n'), 1):
            match = re.match(section_pattern, line.strip())
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                
                # Filter out decorative separator lines (just equals signs)
                # e.g., "======================================"
                if not title or all(c == '=' for c in title):
                    continue
                
                sections.append(SectionInfo(
                    level=level,
                    title=title,
                    line_number=line_num
                ))
        
        return sections
    
    @staticmethod
    def build_section_path(sections: List[SectionInfo], current_index: int) -> str:
        """
        Build breadcrumb path for current section.
        
        Args:
            sections: List of SectionInfo objects
            current_index: Index of current section
        
        Returns:
            Breadcrumb path (e.g., "Background > Pre-War Era > Vault Construction")
        """
        if not sections or current_index >= len(sections):
            return ""
        
        current_level = sections[current_index].level
        path_parts = [sections[current_index].title]
        
        # Walk backwards to find parent sections
        for i in range(current_index - 1, -1, -1):
            if sections[i].level < current_level:
                path_parts.insert(0, sections[i].title)
                current_level = sections[i].level
        
        return ' > '.join(path_parts)
    
    @staticmethod
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
        except Exception as e:
            logger.warning(f"Failed to extract template safely: {e}")
            return str(template.name).strip(), {}
    
    @staticmethod
    def extract_infoboxes(wikitext: str) -> List[Infobox]:
        """
        Parse {{Infobox ...}} templates into structured objects.
        
        Args:
            wikitext: Raw MediaWiki markup
        
        Returns:
            List of Infobox objects
        """
        parsed = mwparserfromhell.parse(wikitext)
        infoboxes = []
        
        for template in parsed.filter_templates():
            template_name = str(template.name).strip()
            
            # Detect infobox templates
            if template_name.lower().startswith('infobox'):
                name, params = StructuralExtractor.extract_template_safely(template)
                
                # Remove positional params for infoboxes (usually not used)
                params.pop('_positional', None)
                
                infoboxes.append(Infobox(
                    type=name,
                    parameters=params
                ))
        
        return infoboxes
    
    @staticmethod
    def extract_templates(wikitext: str) -> List[Template]:
        """
        Extract ALL templates from wikitext, excluding infoboxes.
        
        Args:
            wikitext: Raw MediaWiki markup
        
        Returns:
            List of Template objects
        """
        parsed = mwparserfromhell.parse(wikitext)
        templates = []
        
        for template in parsed.filter_templates():
            name, params = StructuralExtractor.extract_template_safely(template)
            
            # Skip infoboxes (handled separately)
            if name.lower().startswith('infobox'):
                continue
            
            # Separate positional and named parameters
            positional = params.pop('_positional', None)
            
            templates.append(Template(
                name=name,
                positional=positional,
                params=params if params else None
            ))
        
        return templates
    
    @staticmethod
    def extract_game_references(wikitext: str) -> List[str]:
        """
        Extract game references from templates like {{Game|FO3|FO4}}.
        
        Args:
            wikitext: Raw MediaWiki markup
        
        Returns:
            List of full game names (e.g., ["Fallout 3", "Fallout 4"])
        """
        parsed = mwparserfromhell.parse(wikitext)
        games = []
        
        for template in parsed.filter_templates():
            name, params = StructuralExtractor.extract_template_safely(template)
            
            # Check if it's a Game template
            if name.lower() in ['game', 'games']:
                # Extract positional parameters (game abbreviations)
                positional = params.get('_positional', [])
                for game_code in positional:
                    game_code = game_code.strip().upper()
                    if game_code in GAME_ABBREVIATIONS:
                        games.append(GAME_ABBREVIATIONS[game_code])
                
                # Also check named parameters
                for key, value in params.items():
                    if key != '_positional':
                        game_code = value.strip().upper()
                        if game_code in GAME_ABBREVIATIONS:
                            games.append(GAME_ABBREVIATIONS[game_code])
        
        return list(set(games))  # Remove duplicates
    
    @staticmethod
    def extract_all(wikitext: str) -> StructuralMetadata:
        """
        Extract all structural metadata from wikitext.
        
        This is a convenience method that calls all extraction functions.
        
        Args:
            wikitext: Raw MediaWiki markup
        
        Returns:
            StructuralMetadata object with all extracted data
        """
        return StructuralMetadata(
            raw_categories=StructuralExtractor.extract_categories(wikitext),
            wikilinks=StructuralExtractor.extract_wikilinks(wikitext),
            sections=StructuralExtractor.extract_section_tree(wikitext),
            infoboxes=StructuralExtractor.extract_infoboxes(wikitext),
            templates=StructuralExtractor.extract_templates(wikitext),
            game_source=StructuralExtractor.extract_game_references(wikitext)
        )
