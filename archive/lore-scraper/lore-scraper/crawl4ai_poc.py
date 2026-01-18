"""
Crawl4AI Proof-of-Concept for Fallout 76 Wiki Scraping
Demonstrates superior data quality and classification accuracy
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy
import time

# Test URLs - known entities with classification challenges
TEST_CASES = [
    {
        "url": "https://fallout.fandom.com/wiki/Buttercup_(character)",
        "expected_type": "character",
        "expected_name": "Buttercup"
    },
    {
        "url": "https://fallout.fandom.com/wiki/Rose_(Fallout_76)",
        "expected_type": "character",
        "expected_name": "Rose"
    },
    {
        "url": "https://fallout.fandom.com/wiki/The_Rose_Room",
        "expected_type": "location",
        "expected_name": "The Rose Room"
    },
    {
        "url": "https://fallout.fandom.com/wiki/Rose_(Gone_Fission)",
        "expected_type": "character",
        "expected_name": "Rose (Gone Fission)"
    },
    {
        "url": "https://fallout.fandom.com/wiki/Vault_76",
        "expected_type": "location",
        "expected_name": "Vault 76"
    },
    {
        "url": "https://fallout.fandom.com/wiki/The_Crater",
        "expected_type": "location",
        "expected_name": "The Crater"
    },
    {
        "url": "https://fallout.fandom.com/wiki/Top_of_the_World_(location)",
        "expected_type": "location",
        "expected_name": "Top of the World"
    },
    {
        "url": "https://fallout.fandom.com/wiki/Scorched_plague",
        "expected_type": "disease",
        "expected_name": "Scorched plague"
    },
    {
        "url": "https://fallout.fandom.com/wiki/Reclamation_Day",
        "expected_type": "event",
        "expected_name": "Reclamation Day"
    },
    {
        "url": "https://fallout.fandom.com/wiki/Responders",
        "expected_type": "faction",
        "expected_name": "Responders"
    }
]

# Enhanced extraction schema leveraging MediaWiki structure
# Note: Extraction happens AFTER JS execution, so we get structured data directly
EXTRACTION_SCHEMA = {
    "name": "Fallout76WikiEntity",
    "baseSelector": "body",
    "fields": [
        # Primary identifiers
        {"name": "page_title", "selector": "h1.page-header__title, h1#firstHeading", "type": "text"},
        {"name": "canonical_url", "selector": "link[rel='canonical']", "type": "attribute", "attribute": "href"},
        
        # Main content for fallback analysis
        {"name": "first_paragraph", "selector": ".mw-parser-output > p:first-of-type", "type": "text"},
        {"name": "description", "selector": ".mw-parser-output", "type": "text"},
        
        # Categories (visible at bottom of page)
        {"name": "categories_visible", "selector": "#mw-normal-catlinks ul li a", "type": "text", "multiple": True},
    ]
}

# JavaScript to extract MediaWiki metadata AND portable infobox data
MW_METADATA_JS = """
(async () => {
    const metadata = {
        wgCategories: mw.config.get('wgCategories') || [],
        wgPageName: mw.config.get('wgPageName') || '',
        wgTitle: mw.config.get('wgTitle') || '',
        wgNamespaceNumber: mw.config.get('wgNamespaceNumber') || 0,
        wgArticleId: mw.config.get('wgArticleId') || 0,
        infoboxData: {},
        infoboxType: null
    };
    
    // Extract ALL infobox data using Fandom's portable infobox structure
    const infobox = document.querySelector('.portable-infobox, aside[role="region"]');
    if (infobox) {
        // Get infobox type from classes
        const classes = infobox.className;
        if (classes.includes('pi-theme-character')) metadata.infoboxType = 'character';
        else if (classes.includes('pi-theme-location')) metadata.infoboxType = 'location';
        else if (classes.includes('pi-theme-faction')) metadata.infoboxType = 'faction';
        else if (classes.includes('pi-theme-quest')) metadata.infoboxType = 'quest';
        else if (classes.includes('pi-theme-disease')) metadata.infoboxType = 'disease';
        
        // Extract all data-source fields
        const dataElements = infobox.querySelectorAll('[data-source]');
        dataElements.forEach(elem => {
            const source = elem.getAttribute('data-source');
            const valueElem = elem.querySelector('.pi-data-value, .pi-font');
            if (source && valueElem) {
                metadata.infoboxData[source] = valueElem.textContent.trim();
            }
        });
        
        // Also grab the title
        const titleElem = infobox.querySelector('.pi-title, .pi-item-spacing');
        if (titleElem) {
            metadata.infoboxData['_title'] = titleElem.textContent.trim();
        }
    }
    
    return JSON.stringify(metadata);
})();
"""

def classify_entity(extracted: Dict[str, Any], mw_metadata: Dict[str, Any]) -> str:
    """
    Intelligent classification using multiple signals
    Priority: Infobox theme > Infobox data > Categories > Content analysis
    """
    
    # Signal 1: Infobox type from CSS classes (STRONGEST)
    infobox_type = mw_metadata.get('infoboxType')
    if infobox_type:
        return infobox_type
    
    # Signal 2: Infobox data fields (character indicators)
    infobox_data = mw_metadata.get('infoboxData', {})
    if infobox_data.get('race') or infobox_data.get('voice') or infobox_data.get('actor'):
        return 'character'
    
    # Signal 3: Categories from MediaWiki
    categories = mw_metadata.get('wgCategories', [])
    if categories:
        categories_text = ' '.join(categories).lower()
        
        # Check for specific category patterns
        if any(word in categories_text for word in ['fallout 76 characters', 'characters in fallout', 'npcs', 'human characters']):
            return 'character'
        elif any(word in categories_text for word in ['fallout 76 locations', 'locations in', 'settlements']):
            return 'location'
        elif any(word in categories_text for word in ['fallout 76 factions', 'factions in', 'organizations']):
            return 'faction'
        elif any(word in categories_text for word in ['fallout 76 quests', 'quests in']):
            return 'quest'
        elif any(word in categories_text for word in ['diseases', 'afflictions', 'medical conditions']):
            return 'disease'
        elif any(word in categories_text for word in ['events', 'occurrences']):
            return 'event'
        elif any(word in categories_text for word in ['creatures', 'enemies', 'wildlife']):
            return 'creature'
        elif any(word in categories_text for word in ['documents', 'notes', 'holotapes']):
            return 'document'
    
    # Signal 4: First paragraph analysis
    first_para = extracted.get('first_paragraph', '').lower()
    if first_para:
        # Look for defining phrases in first 300 chars
        snippet = first_para[:300]
        if any(phrase in snippet for phrase in ['is a character', 'is an npc', 'is a person', 'is a raider']):
            return 'character'
        elif any(phrase in snippet for phrase in ['is a location', 'is a settlement', 'is a place', 'is a building']):
            return 'location'
        elif any(phrase in snippet for phrase in ['is a faction', 'is an organization', 'is a group']):
            return 'faction'
        elif any(phrase in snippet for phrase in ['is a quest', 'is a mission']):
            return 'quest'
        elif any(phrase in snippet for phrase in ['is a disease', 'is an affliction', 'is a plague']):
            return 'disease'
        elif any(phrase in snippet for phrase in ['is an event', 'was an event', 'occurred on']):
            return 'event'
    
    return 'unknown'


async def scrape_entity(url: str) -> Dict[str, Any]:
    """Scrape a single wiki page with enhanced extraction"""
    
    browser_config = BrowserConfig(
        headless=True,
        java_script_enabled=True,
        verbose=False
    )
    
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(EXTRACTION_SCHEMA),
        js_code=[MW_METADATA_JS],  # Extract MediaWiki metadata
        wait_for="css:.mw-parser-output",  # Wait for content
        page_timeout=30000,
        mean_delay=0.5,  # Respect rate limits
        max_range=1.0
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=crawl_config)
        
        if not result.success:
            return {
                "url": url,
                "success": False,
                "error": result.error_message
            }
        
        # Parse extracted data
        extracted = json.loads(result.extracted_content)[0] if result.extracted_content else {}
        
        # Parse MediaWiki metadata from JS execution
        mw_metadata = {}
        if result.js_execution_result:
            try:
                mw_metadata = json.loads(result.js_execution_result[0])
            except:
                pass
        
        # Classify entity
        entity_type = classify_entity(extracted, mw_metadata)
        
        return {
            "url": url,
            "success": True,
            "classified_type": entity_type,
            "page_title": extracted.get('page_title', ''),
            "categories": mw_metadata.get('wgCategories', []),
            "infobox_type": mw_metadata.get('infoboxType'),
            "infobox_data": mw_metadata.get('infoboxData', {}),
            "has_infobox": bool(mw_metadata.get('infoboxType') or mw_metadata.get('infoboxData')),
            "extraction_signals": {
                "infobox_type": mw_metadata.get('infoboxType'),
                "infobox_fields": list(mw_metadata.get('infoboxData', {}).keys()),
                "category_count": len(mw_metadata.get('wgCategories', [])),
                "categories_sample": mw_metadata.get('wgCategories', [])[:3]
            },
            "markdown_length": len(result.markdown.raw_markdown) if result.markdown else 0,
            "fit_markdown_length": len(result.markdown.fit_markdown) if result.markdown and result.markdown.fit_markdown else 0
        }

async def run_poc():
    """Run proof-of-concept on test cases"""
    
    print("=" * 80)
    print("CRAWL4AI PROOF-OF-CONCEPT: Fallout 76 Wiki Scraping")
    print("=" * 80)
    print(f"\nTesting {len(TEST_CASES)} wiki pages with known classification challenges...\n")
    
    results = []
    correct = 0
    total = len(TEST_CASES)
    
    start_time = time.time()
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"[{i}/{total}] Scraping: {test_case['expected_name']}")
        print(f"  URL: {test_case['url']}")
        
        result = await scrape_entity(test_case['url'])
        
        if result['success']:
            is_correct = result['classified_type'] == test_case['expected_type']
            if is_correct:
                correct += 1
                status = "✓ CORRECT"
            else:
                status = "✗ INCORRECT"
            
            print(f"  Expected: {test_case['expected_type']}")
            print(f"  Got:      {result['classified_type']} {status}")
            print(f"  Signals:  {result['extraction_signals']}")
            print(f"  Markdown: {result['markdown_length']:,} chars (raw), {result['fit_markdown_length']:,} chars (filtered)")
            
            results.append({
                **test_case,
                **result,
                "is_correct": is_correct
            })
        else:
            print(f"  ✗ FAILED: {result.get('error', 'Unknown error')}")
            results.append({
                **test_case,
                **result,
                "is_correct": False
            })
        
        print()
        await asyncio.sleep(1.5)  # Respectful rate limiting
    
    elapsed = time.time() - start_time
    
    # Summary
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(f"Total Tests:       {total}")
    print(f"Correct:           {correct}")
    print(f"Incorrect:         {total - correct}")
    print(f"Accuracy:          {(correct/total)*100:.1f}%")
    print(f"Time Elapsed:      {elapsed:.1f}s")
    print(f"Avg Time/Page:     {elapsed/total:.2f}s")
    print()
    
    # Save detailed results
    output_file = Path(__file__).parent / "crawl4ai_poc_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total": total,
                "correct": correct,
                "accuracy": (correct/total)*100,
                "elapsed_seconds": elapsed
            },
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Detailed results saved to: {output_file}")
    
    # Failures breakdown
    failures = [r for r in results if not r['is_correct']]
    if failures:
        print("\nFAILURES:")
        for fail in failures:
            print(f"  - {fail['expected_name']}: Expected '{fail['expected_type']}', got '{fail.get('classified_type', 'unknown')}'")
    
    print("\n" + "=" * 80)
    
    return results

if __name__ == "__main__":
    asyncio.run(run_poc())
