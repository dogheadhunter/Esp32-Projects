#!/usr/bin/env python3
"""
Music Identifier - CLI tool for batch music identification and organization.

This tool processes MP3 files in the input directory, identifies them using
AcoustID/MusicBrainz, updates their metadata, and organizes them into
identified/unidentified folders.

Usage:
    python tools/music_identifier/identify_music.py
    python tools/music_identifier/identify_music.py --dry-run
    python tools/music_identifier/identify_music.py --verbose
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List

# Fix imports for both package and standalone usage
try:
    from .config import get_config
    from .file_organizer import FileOrganizer
    from .identifier import MusicIdentifier
    from .metadata_tagger import MetadataTagger
except ImportError:
    # Add parent directory to path for standalone execution
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from tools.music_identifier.config import get_config
    from tools.music_identifier.file_organizer import FileOrganizer
    from tools.music_identifier.identifier import MusicIdentifier
    from tools.music_identifier.metadata_tagger import MetadataTagger


def setup_logging(verbose: bool = False) -> None:
    """Configure logging.
    
    Args:
        verbose: If True, set DEBUG level. Otherwise INFO level.
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    
    # Reduce noise from libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def find_mp3_files(directory: Path) -> List[Path]:
    """Find all MP3 files in a directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of MP3 file paths
    """
    mp3_files = list(directory.glob("*.mp3"))
    mp3_files.sort()  # Process in alphabetical order
    return mp3_files


def process_file(
    filepath: Path,
    identifier: MusicIdentifier,
    tagger: MetadataTagger,
    organizer: FileOrganizer,
    dry_run: bool = False,
    skip_tagged: bool = False
) -> bool:
    """Process a single MP3 file.
    
    Args:
        filepath: Path to MP3 file
        identifier: MusicIdentifier instance
        tagger: MetadataTagger instance
        organizer: FileOrganizer instance
        dry_run: If True, don't modify files
        skip_tagged: If True, skip files that already have complete tags
        
    Returns:
        True if file was successfully identified, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing: {filepath.name}")
    logger.info(f"{'='*60}")
    
    # Check existing tags
    if skip_tagged and tagger.has_complete_tags(filepath):
        logger.info("✓ File already has complete tags - skipping")
        return True
    
    # Identify file
    result = identifier.identify_file(filepath)
    
    if result.identified:
        logger.info(f"✓ Identified: {result}")
        
        # Update tags
        if not dry_run:
            tagger.update_tags(filepath, result, force=True)
        else:
            logger.info("[DRY RUN] Would update tags")
        
        # Organize file
        new_path = organizer.organize_file(result, dry_run=dry_run, rename=True)
        
        if new_path:
            logger.info(f"✓ Success: {new_path.name}")
        
        return True
    else:
        logger.warning(f"✗ Failed to identify: {result.error}")
        
        # Move to unidentified folder
        organizer.organize_file(result, dry_run=dry_run, rename=False)
        
        return False


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(
        description="Identify and organize MP3 files using AcoustID/MusicBrainz",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Process all files in music/input/
  %(prog)s --dry-run                # Show what would happen without modifying files
  %(prog)s --verbose                # Show detailed debug information
  %(prog)s --skip-tagged            # Skip files that already have tags
  %(prog)s --input /path/to/files   # Process files from custom directory
        """
    )
    
    parser.add_argument(
        "--input",
        type=Path,
        help="Input directory (default: music/input/)"
    )
    
    parser.add_argument(
        "--identified",
        type=Path,
        help="Output directory for identified files (default: music/identified/)"
    )
    
    parser.add_argument(
        "--unidentified",
        type=Path,
        help="Output directory for unidentified files (default: music/unidentified/)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without modifying files"
    )
    
    parser.add_argument(
        "--skip-tagged",
        action="store_true",
        help="Skip files that already have complete tags"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose debug output"
    )
    
    parser.add_argument(
        "--api-key",
        help="AcoustID API key (or set ACOUSTID_API_KEY environment variable)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("Music Identifier - Batch Processing Tool")
    logger.info("="*60)
    
    # Load configuration
    config_overrides = {}
    if args.input:
        config_overrides["input_dir"] = args.input
    if args.identified:
        config_overrides["identified_dir"] = args.identified
    if args.unidentified:
        config_overrides["unidentified_dir"] = args.unidentified
    if args.api_key:
        config_overrides["acoustid_api_key"] = args.api_key
    
    config = get_config(**config_overrides)
    
    # Validate API key
    if not config.validate_api_key():
        logger.error(
            "AcoustID API key not configured!\n"
            "Get a free key from: https://acoustid.org/new-application\n"
            "Then set ACOUSTID_API_KEY environment variable or use --api-key"
        )
        return 1
    
    # Ensure directories exist
    config.ensure_directories()
    
    # Find MP3 files
    mp3_files = find_mp3_files(config.input_dir)
    
    if not mp3_files:
        logger.warning(f"No MP3 files found in {config.input_dir}")
        logger.info(f"Place MP3 files in {config.input_dir} and run again")
        return 0
    
    logger.info(f"Found {len(mp3_files)} MP3 file(s) to process")
    logger.info(f"Input directory: {config.input_dir}")
    logger.info(f"Identified directory: {config.identified_dir}")
    logger.info(f"Unidentified directory: {config.unidentified_dir}")
    
    if args.dry_run:
        logger.info("\n⚠️  DRY RUN MODE - No files will be modified ⚠️\n")
    
    # Initialize components
    identifier = MusicIdentifier(config)
    tagger = MetadataTagger()
    organizer = FileOrganizer(config.identified_dir, config.unidentified_dir)
    
    # Process files
    results = {
        "total": len(mp3_files),
        "identified": 0,
        "unidentified": 0,
        "errors": 0
    }
    
    for filepath in mp3_files:
        try:
            success = process_file(
                filepath,
                identifier,
                tagger,
                organizer,
                dry_run=args.dry_run,
                skip_tagged=args.skip_tagged
            )
            
            if success:
                results["identified"] += 1
            else:
                results["unidentified"] += 1
                
        except KeyboardInterrupt:
            logger.info("\n\nInterrupted by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error processing {filepath.name}: {e}", exc_info=args.verbose)
            results["errors"] += 1
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"Total files:       {results['total']}")
    logger.info(f"✓ Identified:      {results['identified']}")
    logger.info(f"✗ Unidentified:    {results['unidentified']}")
    if results['errors']:
        logger.info(f"⚠ Errors:          {results['errors']}")
    
    if args.dry_run:
        logger.info("\n(Dry run - no files were actually modified)")
    else:
        stats = organizer.get_stats()
        logger.info(f"\nFiles in identified folder:   {stats['identified_count']}")
        logger.info(f"Files in unidentified folder: {stats['unidentified_count']}")
    
    logger.info("="*60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
