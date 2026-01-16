"""
Log Analyzer for Wiki Ingestion Pipeline

Parses ingestion log files to extract:
- Errors and warnings
- Missing sections
- Failed pages
- Processing statistics
- Performance metrics
"""

import re
import argparse
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
from datetime import datetime


class LogAnalyzer:
    """Analyzes ingestion log files for errors, warnings, and statistics"""
    
    def __init__(self, log_file: str):
        self.log_file = Path(log_file)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.missing_sections: List[Tuple[str, str]] = []  # (page, section)
        self.failed_pages: List[str] = []
        self.stats: Dict[str, any] = {}
        self.error_types: Counter = Counter()
        
    def parse_log(self):
        """Parse the log file and extract key information"""
        if not self.log_file.exists():
            print(f"Error: Log file not found: {self.log_file}")
            return False
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_page = None
        
        for line in lines:
            line = line.strip()
            
            # Extract current page being processed
            if 'Processing page:' in line:
                match = re.search(r"Processing page: (.+)", line)
                if match:
                    current_page = match.group(1)
            
            # Extract errors
            if '| ERROR' in line:
                self.errors.append(line)
                # Categorize error types
                if 'Could not find section' in line:
                    match = re.search(r'Could not find section "(.+?)" in page "(.+?)"', line)
                    if match:
                        self.missing_sections.append((match.group(2), match.group(1)))
                        self.error_types['missing_section'] += 1
                elif 'Failed to process page' in line:
                    if current_page:
                        self.failed_pages.append(current_page)
                    self.error_types['page_processing_failed'] += 1
                elif 'UnicodeEncodeError' in line or 'charmap' in line:
                    self.error_types['unicode_error'] += 1
                elif 'Failed to ingest' in line:
                    self.error_types['ingestion_failed'] += 1
                else:
                    self.error_types['other_error'] += 1
            
            # Extract warnings
            if '| WARNING' in line or '| WARN' in line:
                self.warnings.append(line)
            
            # Extract statistics
            if 'Pages processed:' in line:
                match = re.search(r'Pages processed: (\d+)', line)
                if match:
                    self.stats['pages_processed'] = int(match.group(1))
            
            if 'Skipped (Redirects):' in line or 'Pages skipped (redirect):' in line:
                match = re.search(r'(\d+)', line)
                if match:
                    self.stats['redirects_skipped'] = int(match.group(1))
            
            if 'Skipped (Empty):' in line or 'Pages skipped (empty):' in line:
                match = re.search(r'(\d+)', line)
                if match:
                    self.stats['empty_skipped'] = int(match.group(1))
            
            if 'Pages Failed:' in line or 'Pages failed:' in line:
                match = re.search(r'(\d+)', line)
                if match:
                    self.stats['pages_failed'] = int(match.group(1))
            
            if 'Chunks Created:' in line or 'Chunks created:' in line:
                match = re.search(r'(\d+[,\d]*)', line)
                if match:
                    self.stats['chunks_created'] = int(match.group(1).replace(',', ''))
            
            if 'Chunks Ingested:' in line or 'Chunks ingested:' in line:
                match = re.search(r'(\d+[,\d]*)', line)
                if match:
                    self.stats['chunks_ingested'] = int(match.group(1).replace(',', ''))
            
            if 'Elapsed Time:' in line or 'Elapsed time:' in line:
                match = re.search(r'([\d.]+) minutes', line)
                if match:
                    self.stats['elapsed_minutes'] = float(match.group(1))
            
            if 'Processing rate:' in line:
                match = re.search(r'([\d.]+) pages/min', line)
                if match:
                    self.stats['pages_per_min'] = float(match.group(1))
            
            if 'Total Chunks in DB:' in line:
                match = re.search(r'(\d+[,\d]*)', line)
                if match:
                    self.stats['total_chunks_in_db'] = int(match.group(1).replace(',', ''))
        
        return True
    
    def print_summary(self, verbose: bool = False):
        """Print analysis summary"""
        print("=" * 80)
        print("INGESTION LOG ANALYSIS")
        print("=" * 80)
        print(f"Log File: {self.log_file.name}")
        print(f"Full Path: {self.log_file.absolute()}")
        print("=" * 80)
        
        # Statistics
        if self.stats:
            print("\n--- PROCESSING STATISTICS ---")
            if 'pages_processed' in self.stats:
                print(f"Pages Processed:     {self.stats['pages_processed']:,}")
            if 'redirects_skipped' in self.stats:
                print(f"Redirects Skipped:   {self.stats['redirects_skipped']:,}")
            if 'empty_skipped' in self.stats:
                print(f"Empty Pages Skipped: {self.stats['empty_skipped']:,}")
            if 'pages_failed' in self.stats:
                print(f"Pages Failed:        {self.stats['pages_failed']:,}")
            if 'chunks_created' in self.stats:
                print(f"Chunks Created:      {self.stats['chunks_created']:,}")
            if 'chunks_ingested' in self.stats:
                print(f"Chunks Ingested:     {self.stats['chunks_ingested']:,}")
            if 'total_chunks_in_db' in self.stats:
                print(f"Total in Database:   {self.stats['total_chunks_in_db']:,}")
            if 'elapsed_minutes' in self.stats:
                hours = self.stats['elapsed_minutes'] / 60
                print(f"Elapsed Time:        {self.stats['elapsed_minutes']:.1f} min ({hours:.2f} hours)")
            if 'pages_per_min' in self.stats:
                print(f"Processing Rate:     {self.stats['pages_per_min']:.1f} pages/min")
        
        # Error Summary
        print("\n--- ERROR SUMMARY ---")
        if self.error_types:
            for error_type, count in self.error_types.most_common():
                print(f"{error_type.replace('_', ' ').title()}: {count:,}")
        else:
            print("No errors detected!")
        
        print(f"\nTotal Errors:   {len(self.errors):,}")
        print(f"Total Warnings: {len(self.warnings):,}")
        
        # Missing Sections
        if self.missing_sections:
            print(f"\n--- MISSING SECTIONS ({len(self.missing_sections)}) ---")
            if verbose:
                # Show all missing sections
                for page, section in self.missing_sections[:50]:  # Limit to 50
                    print(f"  Page: {page}")
                    print(f"    Missing: {section}")
                if len(self.missing_sections) > 50:
                    print(f"  ... and {len(self.missing_sections) - 50} more")
            else:
                # Show summary by page
                page_counts = Counter([page for page, _ in self.missing_sections])
                print(f"Top pages with missing sections:")
                for page, count in page_counts.most_common(10):
                    print(f"  {page}: {count} missing sections")
                if len(page_counts) > 10:
                    print(f"  ... and {len(page_counts) - 10} more pages")
        
        # Failed Pages
        if self.failed_pages:
            print(f"\n--- FAILED PAGES ({len(self.failed_pages)}) ---")
            for page in self.failed_pages[:20]:
                print(f"  - {page}")
            if len(self.failed_pages) > 20:
                print(f"  ... and {len(self.failed_pages) - 20} more")
        
        # Recent Errors (last 10)
        if self.errors and verbose:
            print(f"\n--- RECENT ERRORS (Last 10) ---")
            for error in self.errors[-10:]:
                # Extract just the error message part
                match = re.search(r'\| ERROR\s+\| (.+)', error)
                if match:
                    print(f"  {match.group(1)}")
                else:
                    print(f"  {error}")
        
        print("\n" + "=" * 80)
        
        # Final verdict
        if not self.errors and not self.warnings:
            print("[SUCCESS] No errors or warnings detected!")
        elif not self.errors:
            print(f"[WARNING] {len(self.warnings)} warnings detected (no errors)")
        else:
            print(f"[ERROR] {len(self.errors)} errors and {len(self.warnings)} warnings detected")
        
        print("=" * 80)
    
    def export_errors(self, output_file: str):
        """Export all errors to a separate file"""
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("INGESTION ERROR REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Source Log: {self.log_file.name}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            if self.errors:
                f.write(f"ERRORS ({len(self.errors)})\n")
                f.write("-" * 80 + "\n")
                for error in self.errors:
                    f.write(error + "\n")
            
            if self.warnings:
                f.write(f"\n\nWARNINGS ({len(self.warnings)})\n")
                f.write("-" * 80 + "\n")
                for warning in self.warnings:
                    f.write(warning + "\n")
            
            if self.missing_sections:
                f.write(f"\n\nMISSING SECTIONS ({len(self.missing_sections)})\n")
                f.write("-" * 80 + "\n")
                for page, section in self.missing_sections:
                    f.write(f"Page: {page}\n")
                    f.write(f"  Missing: {section}\n")
            
            if self.failed_pages:
                f.write(f"\n\nFAILED PAGES ({len(self.failed_pages)})\n")
                f.write("-" * 80 + "\n")
                for page in self.failed_pages:
                    f.write(f"  - {page}\n")
        
        print(f"\nError report exported to: {output_path.absolute()}")


def find_latest_log() -> Path:
    """Find the most recent ingestion log file"""
    log_files = list(Path('.').glob('ingestion_*.log'))
    if not log_files:
        raise FileNotFoundError("No ingestion log files found in current directory")
    return max(log_files, key=lambda p: p.stat().st_mtime)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze wiki ingestion log files for errors and statistics"
    )
    
    parser.add_argument(
        'log_file',
        nargs='?',
        type=str,
        help='Path to ingestion log file (default: latest ingestion_*.log)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed error listings'
    )
    
    parser.add_argument(
        '--export', '-e',
        type=str,
        help='Export errors to specified file'
    )
    
    args = parser.parse_args()
    
    # Find log file
    if args.log_file:
        log_file = args.log_file
    else:
        try:
            log_file = str(find_latest_log())
            print(f"Using latest log file: {log_file}\n")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return 1
    
    # Analyze log
    analyzer = LogAnalyzer(log_file)
    
    if not analyzer.parse_log():
        return 1
    
    analyzer.print_summary(verbose=args.verbose)
    
    # Export if requested
    if args.export:
        analyzer.export_errors(args.export)
    
    return 0


if __name__ == "__main__":
    exit(main())
