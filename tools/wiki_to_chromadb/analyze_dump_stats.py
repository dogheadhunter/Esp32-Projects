"""
Analyze MediaWiki XML Dump Statistics

Streams through a MediaWiki XML dump and categorizes pages by content type.
Provides statistical breakdown of page types without performing chunking or embedding.
"""

import argparse
import re
from pathlib import Path
from typing import Dict

from wiki_parser_v2 import extract_pages
from logging_config import get_logger

logger = get_logger(__name__)


def is_redirect(wikitext: str) -> bool:
    """Check if wikitext is a redirect page."""
    if not wikitext:
        return False
    return bool(re.match(r'^\s*#REDIRECT', wikitext, re.IGNORECASE))


def is_empty(wikitext: str) -> bool:
    """Check if wikitext is empty or only whitespace."""
    return not wikitext or not wikitext.strip()


def analyze_dump(xml_path: str, max_pages: int = 5000) -> Dict[str, int]:
    """
    Analyze wiki dump and categorize pages.
    
    Args:
        xml_path: Path to MediaWiki XML dump file
        max_pages: Maximum number of pages to analyze (default: 5000)
    
    Returns:
        Dictionary with counts for each category
    """
    stats = {
        'total': 0,
        'redirects': 0,
        'empty': 0,
        'valid_content': 0,
        'errors': 0
    }
    
    logger.info(f"Starting analysis of {xml_path}")
    logger.info(f"Processing up to {max_pages:,} pages")
    
    try:
        for page in extract_pages(xml_path):
            if stats['total'] >= max_pages:
                logger.info(f"Reached maximum page limit ({max_pages:,})")
                break
            
            stats['total'] += 1
            
            try:
                wikitext = page.get('wikitext', '')
                
                # Categorize the page
                if is_redirect(wikitext):
                    stats['redirects'] += 1
                elif is_empty(wikitext):
                    stats['empty'] += 1
                else:
                    stats['valid_content'] += 1
                
                # Progress update every 500 pages
                if stats['total'] % 500 == 0:
                    logger.info(f"Processed {stats['total']:,} pages...")
                    
            except Exception as e:
                stats['errors'] += 1
                logger.error(f"Error processing page {stats['total']}: {e}")
                
    except Exception as e:
        logger.error(f"Fatal error during dump analysis: {e}")
        stats['errors'] += 1
    
    return stats


def print_summary(stats: Dict[str, int]) -> None:
    """Print formatted summary table with statistics."""
    total = stats['total']
    
    if total == 0:
        print("\n❌ No pages were processed!")
        return
    
    print("\n" + "=" * 60)
    print("WIKI DUMP ANALYSIS SUMMARY")
    print("=" * 60)
    print()
    print(f"{'Category':<20} {'Count':>10} {'Percentage':>15}")
    print("-" * 60)
    
    # Total
    print(f"{'Total Pages':<20} {total:>10,} {100.0:>14.2f}%")
    print("-" * 60)
    
    # Redirects
    redirects = stats['redirects']
    redirect_pct = (redirects / total * 100) if total > 0 else 0
    print(f"{'Redirects':<20} {redirects:>10,} {redirect_pct:>14.2f}%")
    
    # Empty
    empty = stats['empty']
    empty_pct = (empty / total * 100) if total > 0 else 0
    print(f"{'Empty Pages':<20} {empty:>10,} {empty_pct:>14.2f}%")
    
    # Valid Content
    valid = stats['valid_content']
    valid_pct = (valid / total * 100) if total > 0 else 0
    print(f"{'Valid Content':<20} {valid:>10,} {valid_pct:>14.2f}%")
    
    # Errors
    errors = stats['errors']
    error_pct = (errors / total * 100) if total > 0 else 0
    print(f"{'Errors':<20} {errors:>10,} {error_pct:>14.2f}%")
    
    print("=" * 60)
    print()
    
    # Quality assessment
    if valid_pct > 80:
        print("✅ High quality dump - most pages have valid content")
    elif valid_pct > 50:
        print("⚠️  Moderate quality dump - significant redirects/empty pages")
    else:
        print("❌ Low quality dump - consider filtering or preprocessing")
    
    if error_pct > 5:
        print("⚠️  High error rate - check logs for issues")
    
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze MediaWiki XML dump statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze first 5000 pages (default)
  python analyze_dump_stats.py
  
  # Analyze first 1000 pages
  python analyze_dump_stats.py --max-pages 1000
  
  # Analyze all pages
  python analyze_dump_stats.py --max-pages 0
  
  # Specify custom XML file
  python analyze_dump_stats.py --xml-file path/to/dump.xml
        """
    )
    
    parser.add_argument(
        '--xml-file',
        type=str,
        default='lore/fallout_wiki_complete.xml',
        help='Path to MediaWiki XML dump file (default: lore/fallout_wiki_complete.xml)'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        default=5000,
        help='Maximum number of pages to analyze (0 = unlimited, default: 5000)'
    )
    
    args = parser.parse_args()
    
    # Validate XML file exists
    xml_path = Path(args.xml_file)
    if not xml_path.exists():
        print(f"❌ Error: XML file not found: {xml_path}")
        return 1
    
    # Set max pages (0 means unlimited)
    max_pages = args.max_pages if args.max_pages > 0 else float('inf')
    
    # Run analysis
    stats = analyze_dump(str(xml_path), max_pages)
    
    # Print results
    print_summary(stats)
    
    return 0


if __name__ == '__main__':
    exit(main())
