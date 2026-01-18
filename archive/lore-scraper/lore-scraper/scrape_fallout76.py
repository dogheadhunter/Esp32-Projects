"""
Fallout 76 Lore Scraper
Targeted scraper for canonical Fallout 76 wiki content
Rebuilt from scratch - clean, thread-safe, production-ready
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import re
import argparse
import shutil
import logging
from urllib.parse import urlparse, unquote, quote
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Base URLs for Fallout Wiki (Independent Wiki - 91K articles, ad-free, better API)
WIKI_BASE = "https://fallout.wiki/wiki/"
API_BASE = "https://fallout.wiki/api.php"


class MediaWikiAPI:
    """MediaWiki API client for structured metadata retrieval"""
    
    @staticmethod
    def fetch_page_metadata(page_title: str, session: requests.Session) -> Dict:
        """Fetch categories and wikitext from MediaWiki API"""
        params = {
            "action": "query",
            "titles": page_title,
            "prop": "categories|revisions",
            "rvprop": "content",
            "rvslots": "main",
            "cllimit": "max",
            "format": "json",
            "formatversion": 2
        }
        
        try:
            response = session.get(API_BASE, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "query" not in data or "pages" not in data["query"]:
                return {"categories": [], "wikitext": ""}
            
            page = data["query"]["pages"][0]
            
            if page.get("missing"):
                return {"categories": [], "wikitext": ""}
            
            # Extract categories
            categories = []
            if "categories" in page:
                categories = [cat["title"].replace("Category:", "") for cat in page["categories"]]
            
            # Extract wikitext for infobox type detection
            wikitext = ""
            if "revisions" in page and len(page["revisions"]) > 0:
                wikitext = page["revisions"][0]["slots"]["main"]["content"]
            
            return {
                "categories": categories,
                "wikitext": wikitext
            }
        except Exception as e:
            logging.warning(f"API metadata fetch failed for {page_title}: {e}")
            return {"categories": [], "wikitext": ""}
    
    @staticmethod
    def parse_infobox_type(wikitext: str) -> Optional[str]:
        """Extract infobox type from wikitext (e.g., {{Infobox character}} -> 'character')"""
        infobox_match = re.search(r'\{\{Infobox\s+(\w+)', wikitext, re.IGNORECASE)
        if infobox_match:
            return infobox_match.group(1).lower()
        return None


class FalloutWikiSession:
    """Rate-limited session for Fallout Wiki requests with thread-safe operation"""
    
    def __init__(self, rate_limit_seconds: float = 2.0):
        self.rate_limit = rate_limit_seconds
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ESP32-AI-Radio-Lore-Scraper/2.0 (Educational Project)'
        })
        self.lock = threading.Lock()  # Thread-safe rate limiting
        
    def get(self, url: str, retries: int = 3) -> Optional[requests.Response]:
        """Get URL with rate limiting and retry logic (thread-safe)"""
        # Enforce rate limit (thread-safe)
        with self.lock:
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.rate_limit:
                time.sleep(self.rate_limit - time_since_last)
            self.last_request_time = time.time()
        
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                # 404 is not retryable
                if response.status_code == 404:
                    return response
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt < retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logging.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Failed to fetch {url} after {retries} attempts: {e}")
                    return None
        return None


class PageParser:
    """Parse Fallout Wiki pages for structured data with HTML cleaning"""
    
    def __init__(self):
        self.fo76_indicators = [
            "Fallout 76",
            "Appalachia",
            "Reclamation Day",
            "Vault 76",
            "2102",
            "2103"
        ]
        
        # Blacklist only technical wiki terms (keep content-related links)
        self.relationship_blacklist = {
            'form_id', 'formid', 'editor_id', 'editorid', 'voice_type', 'voicetype',
            'appearances', 'references', 'gallery', 'behind_the_scenes', 'bugs', 'notes'
        }
        
    def is_fallout76_content(self, soup: BeautifulSoup) -> bool:
        """Check if page contains Fallout 76 content (strict check)"""
        # 1. Check Infobox 'appearances' or 'mentioned_in'
        # We need to extract it temporarily here as we haven't run extract_infobox yet
        infobox = soup.find('aside', class_='portable-infobox')
        if infobox:
            text = infobox.get_text().lower()
            if 'fallout 76' in text or 'wastelanders' in text or 'steel dawn' in text:
                return True

        # 2. Check content div only (exclude footer/sidebar/nav)
        content = soup.find('div', class_='mw-parser-output')
        if content:
            text = content.get_text()
            return any(indicator in text for indicator in self.fo76_indicators)
            
        return False
    
    def extract_infobox(self, soup: BeautifulSoup) -> Dict:
        """Extract infobox data with cleaning"""
        infobox = soup.find('aside', class_='portable-infobox')
        if not infobox:
            return {}
        
        data = {}
        for section in infobox.find_all('section'):
            for row in section.find_all(['div']):
                # Extract label-value pairs
                label = row.find('h3', class_='pi-data-label')
                value = row.find('div', class_='pi-data-value')
                if label and value:
                    key = label.get_text(strip=True).lower().replace(' ', '_')
                    # Clean value text (remove extra whitespace)
                    clean_value = ' '.join(value.get_text(separator=' ', strip=True).split())
                    data[key] = clean_value
        
        return data
    
    def extract_dates(self, text: str) -> List[str]:
        """Extract year dates from text (Fallout-relevant range only)"""
        # Match 4-digit years in constrained range (2050-2103)
        # Avoids false positives like "Pip-Boy 2000"
        dates = re.findall(r'\b(20[5-9]\d|210[0-3])\b', text)
        return sorted(set(dates))
    
    def extract_description(self, soup: BeautifulSoup) -> str:
        """Extract main description/summary with HTML cleaning"""
        content = soup.find('div', class_='mw-parser-output')
        if not content:
            return ""
        
        # Remove infobox and navigation elements that create concatenated text
        for element in content.find_all(['aside', 'div', 'sup'], class_=['portable-infobox', 'navbox', 'toc', 'infobox-header', 'reference']):
            element.decompose()
        
        # Get first few paragraphs
        paragraphs = []
        for p in content.find_all('p', limit=5):
            text = p.get_text(separator=' ', strip=True)
            # Clean whitespace and skip very short paragraphs
            text = ' '.join(text.split())
            if len(text) > 50:
                paragraphs.append(text)
        
        description = ' '.join(paragraphs)

        # Cleanup wiki artifacts
        description = description.replace(' }', '').replace('{ ', '')
        if description.endswith('}'):
            description = description[:-1]
        
        # Remove common wiki section headers
        description = re.sub(r'\b(Overview|Stats|Technical|Lore|Race|Gameplay|Location|Quests|Other|Dialogue|Voice actor|Appearances|Background|Characteristics|Inventory|Interactions)\b', '', description)
        
        # Split camelCase/concatenated words (e.g., "MainframeAssaultronAI" -> "Mainframe Assaultron AI")
        description = re.sub(r'([a-z])([A-Z])', r'\1 \2', description)
        
        # Final whitespace normalization
        description = ' '.join(description.split())
        
        return description[:2000]  # Increased limit for better context
    
    def extract_relationships(self, soup: BeautifulSoup) -> List[str]:
        """Extract internal wiki links as relationships (filtered)"""
        content = soup.find('div', class_='mw-parser-output')
        if not content:
            return []
        
        links = []
        for link in content.find_all('a', href=True, limit=100):
            href = link['href']
            if '/wiki/' in href and ':' not in href:  # Wiki article, not special page
                page_name = href.split('/wiki/')[-1].split('#')[0]  # Remove anchors
                page_name_clean = unquote(page_name)
                
                # Convert to normalized ID for blacklist check
                normalized = re.sub(r'[^\w\s-]', '', page_name_clean.lower())
                normalized = re.sub(r'[-\s]+', '_', normalized)
                
                # Filter out blacklisted meta-terms (check both original and normalized)
                if normalized not in self.relationship_blacklist and page_name_clean.lower().replace('_', ' ') not in self.relationship_blacklist:
                    links.append(page_name_clean)
        
        # Deduplicate while preserving order, limit to 30
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
                if len(unique_links) >= 30:
                    break
        
        return unique_links


class EntityFactory:
    """Convert parsed data to entity JSON with enhanced type detection"""
    
    SOURCE_CONFIDENCE = {
        'quest_dialogue': 0.95,
        'holotape': 0.90,
        'terminal': 0.85,
        'environmental': 0.80,
        'item_description': 0.75,
        'wiki_interpretation': 0.60
    }
    
    def __init__(self):
        self.review_queue = []
    
    def create_entity(self, page_name: str, infobox: Dict, description: str, 
                     dates: List[str], relationships: List[str], 
                     api_metadata: Optional[Dict] = None) -> Dict:
        """Create standardized entity JSON with API metadata support"""
        
        # Determine entity type (API-enhanced detection)
        entity_type = self._determine_type(page_name, infobox, description, api_metadata)
        
        # Generate ID
        entity_id = self._generate_id(page_name, entity_type)
        
        # Extract temporal data
        temporal = self._extract_temporal(infobox, dates)
        
        # Determine confidence
        confidence = self.SOURCE_CONFIDENCE['wiki_interpretation']
        needs_review = confidence < 0.70
        
        # Clean Name
        clean_name = page_name.replace('_', ' ')
        # Remove common disambiguation suffixes
        clean_name = re.sub(r' \(Fallout 76\)$', '', clean_name)
        clean_name = re.sub(r' \(Wastelanders\)$', '', clean_name)
        clean_name = re.sub(r' \(Wild Appalachia\)$', '', clean_name)
        clean_name = re.sub(r' \(Nuclear Winter\)$', '', clean_name)
        clean_name = re.sub(r' \(Steel Dawn\)$', '', clean_name)
        clean_name = re.sub(r' \(Steel Reign\)$', '', clean_name)

        # Build entity
        entity = {
            "id": entity_id,
            "name": clean_name,
            "type": entity_type,
            "canonical_source": ["wiki_interpretation"],
            "verification": {
                "confidence": confidence,
                "last_verified": datetime.now().strftime("%Y-%m-%d"),
                "needs_review": needs_review
            },
            "temporal": temporal,
            "geography": {
                "region": "Appalachia",
                "specific_location": infobox.get('location', 'Unknown')
            },
            "description": description,
            "related_entities": [
                {"id": self._normalize_id(rel), "relationship": "referenced_in"}
                for rel in relationships
            ],
            "knowledge_accessibility": {
                "julie_2102": self._determine_knowledge_level(temporal, page_name)
            },
            "tags": self._extract_tags(entity_type, infobox),
            "raw_data": {
                "infobox": infobox,
                "wiki_url": f"{WIKI_BASE}{quote(page_name)}"
            }
        }
        
        if needs_review:
            self.review_queue.append(entity_id)
        
        return entity
    
    def _determine_type(self, page_name: str, infobox: Dict, description: str, 
                       api_metadata: Optional[Dict] = None) -> str:
        """
        Determine entity type with API metadata priority
        Priority: API categories > Infobox type (from wikitext) > Infobox fields > Description heuristics
        """
        name_lower = page_name.lower()
        desc_lower = description.lower()
        
        # PRIORITY 1: MediaWiki API Categories (most reliable)
        if api_metadata:
            categories = api_metadata.get("categories", [])
            if categories:
                cat_text = " ".join(categories).lower()
                
                # Specific Fallout 76 category patterns
                if any(cat in cat_text for cat in ["fallout 76 characters", "characters in fallout 76"]):
                    return "character"
                elif any(cat in cat_text for cat in ["fallout 76 locations", "locations in fallout 76"]):
                    return "location"
                elif any(cat in cat_text for cat in ["fallout 76 factions", "factions in fallout 76"]):
                    return "faction"
                elif any(cat in cat_text for cat in ["fallout 76 quests", "quests in fallout 76"]):
                    return "quest"
                elif "diseases" in cat_text or "afflictions" in cat_text:
                    return "disease"
                elif "events" in cat_text:
                    return "event"
                elif "creatures" in cat_text or "enemies" in cat_text:
                    return "creature"
                
                # Generic patterns (less specific)
                elif "characters" in cat_text or "npcs" in cat_text:
                    return "character"
                elif "locations" in cat_text or "places" in cat_text:
                    return "location"
                elif "factions" in cat_text or "organizations" in cat_text:
                    return "faction"
            
            # PRIORITY 2: Infobox type from wikitext (also very reliable)
            infobox_type = MediaWikiAPI.parse_infobox_type(api_metadata.get("wikitext", ""))
            if infobox_type:
                if infobox_type in ["character", "person", "npc"]:
                    return "character"
                elif infobox_type in ["location", "place", "settlement"]:
                    return "location"
                elif infobox_type in ["faction", "organization", "group"]:
                    return "faction"
                elif infobox_type in ["quest", "mission"]:
                    return "quest"
                elif infobox_type in ["disease", "affliction"]:
                    return "disease"
                elif infobox_type in ["event", "occurrence"]:
                    return "event"
                elif infobox_type in ["creature", "enemy"]:
                    return "creature"
        
        # FALLBACK: Original infobox field + description heuristics
        infobox_type = infobox.get('type', '').lower()
        
        # 0. Priority Infobox Checks (Strong indicators override text heuristics)
        
        # Character strong indicators
        if infobox.get('race') in ['Human', 'HumanRace', 'Ghoul', 'Super Mutant']:
             return 'character'
        if 'voice_actor' in infobox and infobox['voice_actor']:
             return 'character'
        if 'gender' in infobox and ('Male' in infobox['gender'] or 'Female' in infobox['gender']):
             return 'character'
             
        # Creature strong indicators
        if 'creature_name' in infobox:
            return 'creature'
            
        # Quest strong indicators
        if 'quest_xp' in infobox or 'quest_rewards' in infobox:
            return 'quest'
        
        # 1. Quests and Events
        if 'quest' in infobox_type or 'quest' in name_lower.split('_')[-1]: 
             return 'quest'
        if 'quest' in infobox.values(): 
             return 'quest'
        if 'quest' in desc_lower[:50]:
             return 'quest'
             
        if 'event' in infobox_type or 'public event' in name_lower:
            return 'event'
        if 'event' in desc_lower[:50]: # "This event..." "When the event..."
            return 'event'

        # 2. Key Items / Notes / Holotapes (ENHANCED DETECTION)
        if 'holotape' in name_lower or 'holotape' in desc_lower:
            return 'document'
        if 'game tape' in desc_lower or 'pip-boy game' in desc_lower:
             return 'technology'
        if 'note' in name_lower or 'letter' in name_lower or 'memo' in name_lower or 'postcard' in name_lower:
            return 'document'
        if 'report' in name_lower or 'journal' in name_lower or 'log' in name_lower or 'entry' in name_lower:
             return 'document'
        # Enhanced note detection patterns
        if any(pattern in desc_lower[:100] for pattern in ['this note', 'the note', 'is a note', 'paper note', 'note can be found']):
            return 'document'
        if 'the tape can be found' in desc_lower or 'listening to the tape' in desc_lower:
             return 'document'
        if 'terminal' in name_lower or 'terminal entry' in desc_lower:
            return 'document'
        if 'plan:' in name_lower or 'recipe:' in name_lower:
            return 'technology'

        # 3. Mutations, Diseases, Perks, Effects
        if 'mutation' in infobox_type or 'mutation' in desc_lower or 'mutation' in name_lower:
             # Check for "Mutations" category or similar
             return 'mutation'
        if 'positive_effects' in infobox or 'negative_effects' in infobox:
             return 'mutation' # or status_effect
        if 'perk' in infobox_type or 'perk' in desc_lower[:50]:
             return 'perk'
        if 'disease' in infobox_type or 'disease' in desc_lower:
             return 'disease'

        # 4. Factions / Organizations
        if 'faction' in infobox_type or 'organization' in infobox_type or 'group' in infobox_type:
            return 'faction'
        if 'faction' in desc_lower or 'organization' in desc_lower:
            return 'faction'

        # 4. Locations
        if 'location' in infobox_type or 'settlement' in infobox_type or 'landmark' in infobox_type:
            return 'location'
        if 'region' in infobox_type:
            return 'location'
        if 'location' in infobox.get('keywords', '').lower():
            return 'location'
        if 'location' in desc_lower.split()[:10]: # "X is a location..."
            return 'location'
        if 'settlement' in desc_lower or 'building' in desc_lower:
             return 'location'

        # 5. Characters / Robots
        if 'character' in infobox_type or 'npc' in infobox_type or 'person' in infobox_type:
            return 'character'
        
        robot_keywords = ['robot', 'assaultron', 'protectron', 'mister handy', 'eyebot', 'sentry bot', 'robobrain', 'liberator', 'vertibot', 'cargobot']
        if any(k in desc_lower for k in robot_keywords) or any(k in infobox_type for k in robot_keywords):
            return 'character' # Or creature? Usually characters in lore database.

        # Human detection in description
        human_roles = ['survivor', 'resident', 'raider', 'settler', 'soldier', 'officer', 'employee', 'member', 'leader', 'man', 'woman', 'donor', 'student', 'scientist', 'doctor', 'technician', 'dweller', 'engineer', 'merchant', 'trader', 'guard']
        
        # Check "X was a [role]" or "X is a [role]"
        # Simple heuristic: if description starts with Name...
        if any(f"was a {role}" in desc_lower for role in human_roles) or any(f"is a {role}" in desc_lower for role in human_roles):
             return 'character'

        # 6. Creatures
        race = infobox.get('race', '').lower()
        creature_keywords = ['mirelurk', 'deathclaw', 'scorchbeast', 'yau guai', 'radroach', 'mongrel', 'wolf', 'super mutant', 'beast', 'creature', 'cryptid', 'ghoul', 'scorched', 'wendigo', 'snallygaster', 'grafton monster', 'mothman', 'flatwoods monster']
        
        if any(k in race for k in creature_keywords):
            return 'creature'
            
        # Description check - Be careful of references
        # Check first 100 chars for "is a [creature]" or similar
        early_desc = desc_lower[:100]
        if any(k in early_desc for k in creature_keywords):
           return 'creature'
        
        # 7. Technology / Items
        if 'weapon' in infobox_type or 'armor' in infobox_type or 'item' in infobox_type or 'apparel' in infobox_type:
            return 'technology'
        if 'consumable' in infobox_type or 'food' in infobox_type or 'chem' in infobox_type:
            return 'item'

        # Default
        return 'unknown'
    
    def _generate_id(self, page_name: str, entity_type: str) -> str:
        """Generate entity ID"""
        clean_name = re.sub(r'[^\w\s-]', '', page_name.lower())
        clean_name = re.sub(r'[-\s]+', '_', clean_name)
        return f"{entity_type}_{clean_name}"
    
    def _normalize_id(self, page_name: str) -> str:
        """Normalize page name to ID format"""
        clean_name = re.sub(r'[^\w\s-]', '', page_name.lower())
        return re.sub(r'[-\s]+', '_', clean_name)
    
    def _extract_temporal(self, infobox: Dict, dates: List[str]) -> Dict:
        """Extract temporal information"""
        temporal = {
            "active_during": dates if dates else ["2077-2103"]
        }
        
        # Try to extract founded/defunct from infobox
        if 'founded' in infobox:
            temporal['founded'] = infobox['founded']
        if 'defunct' in infobox:
            temporal['defunct'] = infobox['defunct']
        
        return temporal
    
    def _determine_knowledge_level(self, temporal: Dict, page_name: str) -> str:
        """Determine Julie's knowledge accessibility"""
        # Check for 2103+ content (Wastelanders expansion - Julie can't know)
        name_lower = page_name.lower()
        if 'wastelanders' in name_lower or 'foundation' in name_lower or 'crater' in name_lower:
            return 'cannot_know'
        
        # If active during 2102-2103, Julie can know firsthand
        active = temporal.get('active_during', [])
        if any('2102' in str(d) or '2103' in str(d) for d in active):
            return 'firsthand'
        
        # If before 2102, historical knowledge
        if temporal.get('defunct'):
            try:
                if int(temporal['defunct']) < 2102:
                    return 'historical'
            except (ValueError, TypeError):
                pass
        
        return 'historical'
    
    def _extract_tags(self, entity_type: str, infobox: Dict) -> List[str]:
        """Extract relevant tags"""
        tags = [entity_type]
        
        # Add tags from infobox
        if 'type' in infobox:
            tags.append(infobox['type'].lower())
        if 'affiliation' in infobox:
            tags.append('affiliated')
        
        return tags


class DatabaseWriter:
    """Write entities to lore database structure (thread-safe)"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.manifest = {
            "scrape_date": datetime.now().isoformat(),
            "total_pages": 0,
            "successful": 0,
            "failed": 0,
            "entities_created": 0,
            "skipped_existing": 0
        }
        self.lock = threading.Lock()  # Thread-safe writing
    
    def setup_directories(self):
        """Create lore database directory structure"""
        dirs = [
            self.base_path / "entities" / "factions",
            self.base_path / "entities" / "locations",
            self.base_path / "entities" / "characters",
            self.base_path / "entities" / "technology",
            self.base_path / "entities" / "creatures",
            self.base_path / "entities" / "documents",
            self.base_path / "entities" / "unknown",
            self.base_path / "events",
            self.base_path / "relationships",
            self.base_path / "metadata",
            self.base_path / "indices"
        ]
        
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
        
        logging.info(f"Created database structure at {self.base_path}")
    
    def entity_exists(self, entity_type: str, entity_id: str) -> bool:
        """Check if entity file already exists"""
        file_path = self._get_entity_path(entity_type, entity_id)
        return file_path.exists()
    
    def _get_entity_path(self, entity_type: str, entity_id: str) -> Path:
        """Get file path for entity"""
        type_to_dir = {
            'faction': 'factions',
            'location': 'locations',
            'character': 'characters',
            'technology': 'technology',
            'creature': 'creatures',
            'document': 'documents',
            'mutation': 'mutations',
            'perk': 'perks',
            'disease': 'diseases',
            'quest': 'quests',
            'event': 'events',
            'item': 'items',
            'unknown': 'unknown'
        }
        
        dir_name = type_to_dir.get(entity_type, 'unknown')
        dir_path = self.base_path / "entities" / dir_name
        dir_path.mkdir(parents=True, exist_ok=True) # Ensure subdir exists
        
        return dir_path / f"{entity_id}.json"
    
    def write_entity(self, entity: Dict):
        """Write entity to appropriate directory (thread-safe)"""
        entity_type = entity['type']
        entity_id = entity['id']
        file_path = self._get_entity_path(entity_type, entity_id)
        
        # Write JSON (thread-safe)
        with self.lock:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(entity, f, indent=2, ensure_ascii=False)
            self.manifest['entities_created'] += 1
    
    def increment_counter(self, counter_name: str):
        """Increment manifest counter (thread-safe)"""
        with self.lock:
            self.manifest[counter_name] += 1
    
    def write_manifest(self, review_queue: List[str]):
        """Write scrape manifest"""
        manifest_path = self.base_path / "metadata" / "scrape_manifest.json"
        self.manifest['review_queue'] = review_queue
        self.manifest['review_queue_count'] = len(review_queue)
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2)
        
        print(f"\nOK: Manifest written: {self.manifest['entities_created']} entities created")
        print(f"  {self.manifest['skipped_existing']} skipped (already exist)")
        print(f"  {len(review_queue)} entities flagged for manual review")


def setup_logging(log_file: Path, level: str) -> None:
    """Configure logging to file and console"""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def resolve_title_via_api(session: requests.Session, title: str) -> Optional[str]:
    """Resolve redirects and detect missing pages via MediaWiki API"""
    try:
        resp = session.get(
            API_BASE,
            params={
                "action": "query",
                "titles": title,
                "redirects": 1,
                "converttitles": 1,
                "prop": "info",
                "format": "json",
                "formatversion": 2,
            },
            timeout=30,
        )
        resp.raise_for_status()
        pages = (resp.json().get("query") or {}).get("pages") or []
        if not pages:
            return None
        page = pages[0]
        if page.get("missing"):
            return None
        return page.get("title")
    except Exception as e:
        logging.warning(f"API resolution failed for '{title}': {e}")
        return None


def parse_selection_file(path: Path) -> List[str]:
    """Read selection file with one title per line"""
    titles: List[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        
        # Allow full URLs
        if line.startswith("http://") or line.startswith("https://"):
            parsed = urlparse(line)
            if parsed.netloc.endswith("fallout.wiki") and parsed.path.startswith("/wiki/"):
                title = unquote(parsed.path.split("/wiki/")[-1])
                titles.append(title)
                continue
        
        titles.append(line)
    
    # Deduplicate while preserving order
    seen = set()
    out: List[str] = []
    for t in titles:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    
    return out


def scrape_single_page(page_name: str, session: FalloutWikiSession, parser: PageParser,
                       factory: EntityFactory, writer: DatabaseWriter, 
                       skip_existing: bool) -> Dict[str, any]:
    """Scrape a single page (used for both sequential and concurrent execution)"""
    result = {"page_name": page_name, "status": "unknown", "entity_id": None}
    
    # Resolve via API first
    resolved = resolve_title_via_api(session.session, page_name)
    if not resolved:
        logging.warning(f"Missing/unknown title (skipping): {page_name}")
        result["status"] = "missing"
        return result
    
    resolved_wiki_title = resolved.replace(' ', '_')
    
    # Check if already exists (skip-existing mode)
    if skip_existing:
        # Generate entity ID to check existence
        temp_type = factory._determine_type(resolved_wiki_title, {}, "")
        temp_id = factory._generate_id(resolved_wiki_title, temp_type)
        
        if writer.entity_exists(temp_type, temp_id):
            result["status"] = "skipped"
            result["entity_id"] = temp_id
            return result
    
    # Encode title for URL (handles ?, &, etc)
    safe_title = quote(resolved_wiki_title)
    url = f"{WIKI_BASE}{safe_title}"
    logging.info(f"Fetching: {url}")
    
    # Fetch page
    response = session.get(url)
    if not response:
        result["status"] = "failed"
        return result
    
    if response.status_code == 404:
        logging.warning(f"404: {url}")
        result["status"] = "404"
        return result
    
    # Parse HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Verify FO76 content
    if not parser.is_fallout76_content(soup):
        logging.warning(f"Not FO76 content: {url}")
        result["status"] = "not_fo76"
        return result
    
    # Extract data
    infobox = parser.extract_infobox(soup)
    description = parser.extract_description(soup)
    dates = parser.extract_dates(soup.get_text())
    relationships = parser.extract_relationships(soup)
    
    # Fetch API metadata for enhanced classification
    api_metadata = MediaWikiAPI.fetch_page_metadata(resolved_wiki_title, session.session)
    
    # Create entity with API metadata
    entity = factory.create_entity(
        page_name=resolved_wiki_title,
        infobox=infobox,
        description=description,
        dates=dates,
        relationships=relationships,
        api_metadata=api_metadata
    )
    
    # Write to database
    writer.write_entity(entity)
    
    result["status"] = "success"
    result["entity_id"] = entity["id"]
    return result


def main():
    """Main scraper execution"""
    argp = argparse.ArgumentParser(
        description="Fallout 76 wiki scraper - clean rebuild with concurrent support"
    )
    argp.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory (default: <repo>/lore/fallout76_canon)",
    )
    argp.add_argument(
        "--reset",
        action="store_true",
        help="Delete output directory before scraping (creates zip backup unless --no-backup)",
    )
    argp.add_argument(
        "--yes",
        action="store_true",
        help="Do not prompt for confirmation when using --reset",
    )
    argp.add_argument(
        "--no-backup",
        action="store_true",
        help="When using --reset, skip creating a zip backup",
    )
    argp.add_argument(
        "--rate-limit",
        type=float,
        default=2.0,
        help="Seconds to wait between requests (default: 2.0, min 0.5 recommended)",
    )
    argp.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of concurrent workers (default: 1, recommended 3-5 for speed)",
    )
    argp.add_argument(
        "--no-fixups",
        action="store_true",
        help="Do not run canon fixups after scraping",
    )
    argp.add_argument(
        "--selection",
        type=Path,
        default=None,
        help="Selection file (titles/URLs, one per line). Default: lore/julie_lore_selection.txt",
    )
    argp.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Log level (DEBUG, INFO, WARNING, ERROR)",
    )
    argp.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip pages that already have entity files (resume interrupted scrapes)",
    )
    args = argp.parse_args()

    print("=" * 60)
    print("FALLOUT 76 LORE SCRAPER (v2.0 - Clean Rebuild)")
    print("=" * 60)
    
    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    lore_path = args.output if args.output is not None else (project_root / "lore" / "fallout76_canon")
    
    # Default selection file
    if args.selection is None:
        selection_path = project_root / "lore" / "julie_lore_selection.txt"
    else:
        selection_path = args.selection if args.selection.is_absolute() else (project_root / args.selection).resolve()
    
    # Handle reset
    if args.reset and lore_path.exists():
        if not args.yes:
            resp = input(f"Reset requested. This will delete '{lore_path}'. Continue? [y/N]: ").strip().lower()
            if resp not in {"y", "yes"}:
                print("Aborted.")
                return

        if not args.no_backup:
            backup_root = (project_root / "lore" / "_backups")
            backup_root.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_base = backup_root / f"fallout76_canon_{stamp}"
            print(f"Creating backup zip: {archive_base}.zip")
            shutil.make_archive(str(archive_base), "zip", root_dir=str(lore_path))

        print(f"Deleting output directory: {lore_path}")
        shutil.rmtree(lore_path)
    
    # Setup logging
    log_path = lore_path / "metadata" / "scrape.log"
    setup_logging(log_path, args.log_level)
    
    # Initialize components
    session = FalloutWikiSession(rate_limit_seconds=float(args.rate_limit))
    parser = PageParser()
    factory = EntityFactory()
    writer = DatabaseWriter(lore_path)
    
    writer.setup_directories()
    
    # Load page list
    if not selection_path.exists():
        logging.error(f"Selection file not found: {selection_path}")
        print(f"ERROR: Selection file not found: {selection_path}")
        return
    
    page_list = parse_selection_file(selection_path)
    total_pages = len(page_list)
    writer.manifest['total_pages'] = total_pages
    
    logging.info(f"Using selection file: {selection_path} ({total_pages} pages)")
    
    # Estimate time
    est_time_minutes = (total_pages * args.rate_limit) / (60 * args.workers)
    print(f"\nScraping {total_pages} pages:")
    print(f"  Selection: {selection_path.name}")
    print(f"  Rate limit: {args.rate_limit}s/request")
    print(f"  Workers: {args.workers}")
    print(f"  Skip existing: {args.skip_existing}")
    print(f"  Estimated time: ~{est_time_minutes:.1f} minutes")
    print(f"  Output: {lore_path}\n")
    
    # Scrape pages
    if args.workers == 1:
        # Sequential execution
        print("Starting sequential scrape...\n")
        for idx, page_name in enumerate(page_list, 1):
            print(f"[{idx}/{total_pages}] {page_name}...", end=' ', flush=True)
            
            result = scrape_single_page(page_name, session, parser, factory, writer, args.skip_existing)
            
            if result["status"] == "success":
                writer.increment_counter("successful")
                print("OK")
            elif result["status"] == "skipped":
                writer.increment_counter("skipped_existing")
                print("SKIP (exists)")
            elif result["status"] == "missing":
                writer.increment_counter("failed")
                print("FAIL (missing)")
            elif result["status"] == "404":
                writer.increment_counter("failed")
                print("FAIL (404)")
            elif result["status"] == "not_fo76":
                writer.increment_counter("failed")
                print("WARN (not FO76)")
            else:
                writer.increment_counter("failed")
                print("FAIL")
    else:
        # Concurrent execution
        print(f"Starting concurrent scrape with {args.workers} workers...\n")
        
        completed_count = 0
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            # Submit all tasks
            future_to_page = {
                executor.submit(scrape_single_page, page_name, session, parser, factory, writer, args.skip_existing): page_name
                for page_name in page_list
            }
            
            # Process results as they complete
            for future in as_completed(future_to_page):
                page_name = future_to_page[future]
                completed_count += 1
                
                try:
                    result = future.result()
                    
                    status_symbol = "?"
                    if result["status"] == "success":
                        writer.increment_counter("successful")
                        status_symbol = "OK"
                    elif result["status"] == "skipped":
                        writer.increment_counter("skipped_existing")
                        status_symbol = "SKIP"
                    elif result["status"] in ["missing", "404", "failed"]:
                        writer.increment_counter("failed")
                        status_symbol = "FAIL"
                    elif result["status"] == "not_fo76":
                        writer.increment_counter("failed")
                        status_symbol = "WARN"
                    
                    print(f"[{completed_count}/{total_pages}] {page_name} {status_symbol}")
                    
                except Exception as e:
                    writer.increment_counter("failed")
                    logging.error(f"Exception processing {page_name}: {e}")
                    print(f"[{completed_count}/{total_pages}] {page_name} FAIL (exception)")
    
    # Write manifest
    writer.write_manifest(factory.review_queue)
    
    # Run canon fixups
    if not args.no_fixups:
        try:
            from canon_fixups import main as fixups_main
            print("\nApplying canon fixups...")
            fixups_main()
        except Exception as e:
            logging.error(f"Fixups failed: {e}")
            print(f"\nWARNING: Canon fixups failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SCRAPE COMPLETE")
    print("=" * 60)
    print(f"Total pages: {total_pages}")
    print(f"Successful: {writer.manifest['successful']}")
    print(f"Skipped (existing): {writer.manifest['skipped_existing']}")
    print(f"Failed: {writer.manifest['failed']}")
    print(f"Entities created: {writer.manifest['entities_created']}")
    print(f"Manual review needed: {len(factory.review_queue)}")
    print(f"\nDatabase location: {lore_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
