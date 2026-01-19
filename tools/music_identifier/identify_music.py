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
    from .batch_stats import BatchStatistics
    from .config import get_config
    from .file_organizer import FileOrganizer
    from .identifier import MusicIdentifier
    from .metadata_tagger import MetadataTagger
except ImportError:
    # Add parent directory to path for standalone execution
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from tools.music_identifier.batch_stats import BatchStatistics
    from tools.music_identifier.config import get_config
    from tools.music_identifier.file_organizer import FileOrganizer
    from tools.music_identifier.identifier import MusicIdentifier
    from tools.music_identifier.metadata_tagger import MetadataTagger

# Import tqdm for progress bar
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


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
    stats: BatchStatistics,
    dry_run: bool = False,
    skip_tagged: bool = False,
    verbose: bool = False
) -> str:
    """Process a single MP3 file.
    
    Args:
        filepath: Path to MP3 file
        identifier: MusicIdentifier instance
        tagger: MetadataTagger instance
        organizer: FileOrganizer instance
        stats: BatchStatistics instance for tracking
        dry_run: If True, don't modify files
        skip_tagged: If True, skip files that already have complete tags
        verbose: If True, print detailed logs
        
    Returns:
        Status string: 'identified', 'unidentified', 'error', or 'skipped'
    """
    logger = logging.getLogger(__name__)
    
    if verbose:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {filepath.name}")
        logger.info(f"{'='*60}")
    
    # Check existing tags
    if skip_tagged and tagger.has_complete_tags(filepath):
        if verbose:
            logger.info("✓ File already has complete tags - skipping")
        stats.record_skipped(filepath.name)
        return 'skipped'
    
    try:
        # Identify file
        result = identifier.identify_file(filepath)
        
        if result.identified:
            if verbose:
                logger.info(f"✓ Identified: {result}")
            
            # Check if fingerprint was from cache
            from_cache = (identifier.use_cache and 
                         identifier.cache and 
                         identifier.cache.get(filepath) is not None)
            
            # Record stats
            stats.record_identified(filepath.name, result.confidence, from_cache)
            
            # Update tags
            if not dry_run:
                tagger.update_tags(filepath, result, force=True)
            elif verbose:
                logger.info("[DRY RUN] Would update tags")
            
            # Organize file
            new_path = organizer.organize_file(result, dry_run=dry_run, rename=True)
            
            if new_path and verbose:
                logger.info(f"✓ Success: {new_path.name}")
            
            return 'identified'
        else:
            if verbose:
                logger.warning(f"✗ Failed to identify: {result.error}")
            
            # Record stats
            stats.record_unidentified(filepath.name)
            
            # Move to unidentified folder
            organizer.organize_file(result, dry_run=dry_run, rename=False)
            
            return 'unidentified'
            
    except Exception as e:
        logger.error(f"Error processing {filepath.name}: {e}")
        stats.record_error(filepath.name)
        return 'error'


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
    
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable fingerprint caching"
    )
    
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar"
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
    use_cache = not args.no_cache
    identifier = MusicIdentifier(config, use_cache=use_cache)
    tagger = MetadataTagger()
    organizer = FileOrganizer(config.identified_dir, config.unidentified_dir)
    
    # Initialize batch statistics
    stats = BatchStatistics()
    stats.total_files = len(mp3_files)
    
    # Process files
    use_progress = TQDM_AVAILABLE and not args.no_progress and not args.verbose
    
    if use_progress:
        # Use progress bar
        pbar = tqdm(
            mp3_files,
            desc="Processing MP3s",
            unit="file",
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
        )
        file_iterator = pbar
    else:
        file_iterator = mp3_files
    
    try:
        for filepath in file_iterator:
            status = process_file(
                filepath,
                identifier,
                tagger,
                organizer,
                stats,
                dry_run=args.dry_run,
                skip_tagged=args.skip_tagged,
                verbose=args.verbose
            )
            
            # Update progress bar description
            if use_progress:
                pbar.set_postfix({
                    'identified': stats.identified,
                    'unidentified': stats.unidentified,
                    'cached': stats.cached_fingerprints
                })
    
    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user")
        if use_progress:
            pbar.close()
    
    finally:
        if use_progress:
            pbar.close()
    
    # Finish statistics
    stats.finish()
    
    # Print summary
    if not args.verbose:
        print()  # Add spacing
    stats.print_summary()
    
    # Print file organization stats
    if not args.dry_run:
        org_stats = organizer.get_stats()
        print(f"\nCurrent organization:")
        print(f"  Identified folder:   {org_stats['identified_count']} files")
        print(f"  Unidentified folder: {org_stats['unidentified_count']} files")
    
    logger.info("="*60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
