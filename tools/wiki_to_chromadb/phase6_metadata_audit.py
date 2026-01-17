"""
Phase 6, Task 1: Metadata Bug Analysis & Audit

Audits ChromaDB metadata for:
- Year extraction errors (character IDs, vault numbers, invalid ranges)
- Location classification errors (Vault-Tec, generic assignments)
- Content type misclassifications (factions, locations)
- Missing knowledge tier fields

Generates audit reports in output/ directory.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("Warning: ChromaDB not available. Running in dry-run mode.")

from tools.wiki_to_chromadb.logging_config import get_logger

logger = get_logger(__name__)


class MetadataAuditor:
    """Audits ChromaDB metadata for Phase 6 enhancement"""
    
    def __init__(self, chroma_db_path: str = "chroma_db"):
        """
        Initialize the metadata auditor.
        
        Args:
            chroma_db_path: Path to ChromaDB directory
        """
        self.chroma_db_path = chroma_db_path
        self.client = None
        self.collection = None
        
        if CHROMADB_AVAILABLE:
            try:
                self.client = chromadb.PersistentClient(path=chroma_db_path)
                self.collection = self.client.get_collection("fallout_wiki")
                logger.info(f"Connected to ChromaDB at {chroma_db_path}")
            except Exception as e:
                logger.warning(f"Could not connect to ChromaDB: {e}")
                self.client = None
                self.collection = None
        
        # Audit results
        self.year_issues = []
        self.location_issues = []
        self.content_type_issues = []
        self.knowledge_tier_issues = []
        self.stats = defaultdict(int)
    
    def audit_year_extraction(self) -> Dict[str, Any]:
        """
        Audit year extraction for common issues:
        - Invalid ranges (< 1950 or > 2290)
        - Character ID patterns (A-2018, B5-92)
        - Vault number patterns (Vault 2018)
        - Developer statement dates (2020, 2021, 2024)
        
        Returns:
            Dictionary with audit results
        """
        logger.info("Starting year extraction audit...")
        
        if not self.collection:
            logger.warning("No database connection, skipping audit")
            return self._create_sample_year_audit()
        
        issues = {
            "invalid_range": [],
            "character_id_pattern": [],
            "vault_number_pattern": [],
            "developer_dates": [],
            "missing_year_data": []
        }
        
        # Character ID patterns: A-2018, B5-92, etc.
        char_id_pattern = re.compile(r'\b[A-Z]-?\d{2,4}\b')
        
        # Vault number patterns in context
        vault_pattern = re.compile(r'vault\s*-?\s*\d{2,4}', re.IGNORECASE)
        
        # Developer dates (real-world years after 2010)
        dev_dates = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 
                     2019, 2020, 2021, 2022, 2023, 2024, 2025]
        
        try:
            # Get all chunks (in batches to avoid memory issues)
            batch_size = 1000
            offset = 0
            total_checked = 0
            
            while True:
                results = self.collection.get(
                    limit=batch_size,
                    offset=offset,
                    include=["metadatas", "documents"]
                )
                
                if not results['ids']:
                    break
                
                for i, chunk_id in enumerate(results['ids']):
                    metadata = results['metadatas'][i]
                    document = results['documents'][i]
                    total_checked += 1
                    
                    year_min = metadata.get('year_min')
                    year_max = metadata.get('year_max')
                    title = metadata.get('title', 'Unknown')
                    
                    # Check for missing year data
                    if year_min is None and year_max is None:
                        self.stats['missing_year_data'] += 1
                        continue
                    
                    # Check invalid ranges
                    if year_min is not None and (year_min < 1950 or year_min > 2290):
                        issues['invalid_range'].append({
                            'chunk_id': chunk_id,
                            'title': title,
                            'year_min': year_min,
                            'year_max': year_max,
                            'reason': f'year_min {year_min} outside valid range (1950-2290)'
                        })
                        self.stats['invalid_range'] += 1
                    
                    if year_max is not None and (year_max < 1950 or year_max > 2290):
                        issues['invalid_range'].append({
                            'chunk_id': chunk_id,
                            'title': title,
                            'year_min': year_min,
                            'year_max': year_max,
                            'reason': f'year_max {year_max} outside valid range (1950-2290)'
                        })
                        self.stats['invalid_range'] += 1
                    
                    # Check for character ID patterns in document text
                    if document and char_id_pattern.search(document[:500]):
                        # Could be a character ID mistaken for year
                        char_ids = char_id_pattern.findall(document[:500])
                        issues['character_id_pattern'].append({
                            'chunk_id': chunk_id,
                            'title': title,
                            'year_min': year_min,
                            'year_max': year_max,
                            'char_ids_found': char_ids
                        })
                        self.stats['character_id_pattern'] += 1
                    
                    # Check for vault numbers
                    if document and vault_pattern.search(document[:500]):
                        vault_nums = vault_pattern.findall(document[:500])
                        issues['vault_number_pattern'].append({
                            'chunk_id': chunk_id,
                            'title': title,
                            'year_min': year_min,
                            'year_max': year_max,
                            'vault_refs_found': vault_nums
                        })
                        self.stats['vault_number_pattern'] += 1
                    
                    # Check for developer dates
                    if year_min in dev_dates or year_max in dev_dates:
                        issues['developer_dates'].append({
                            'chunk_id': chunk_id,
                            'title': title,
                            'year_min': year_min,
                            'year_max': year_max,
                            'reason': 'Contains real-world development dates'
                        })
                        self.stats['developer_dates'] += 1
                
                offset += batch_size
                logger.info(f"Checked {total_checked} chunks...")
            
            self.stats['total_checked'] = total_checked
            logger.info(f"Year extraction audit complete. Checked {total_checked} chunks.")
            
        except Exception as e:
            logger.error(f"Error during year audit: {e}")
            import traceback
            traceback.print_exc()
        
        return issues
    
    def audit_location_classification(self) -> Dict[str, Any]:
        """
        Audit location classification for:
        - Vault-Tec misclassified as location (should be info_source)
        - Overly generic "general" assignments
        - Missing location data for major regions
        
        Returns:
            Dictionary with audit results
        """
        logger.info("Starting location classification audit...")
        
        if not self.collection:
            logger.warning("No database connection, skipping audit")
            return self._create_sample_location_audit()
        
        issues = {
            "vault_tec_location": [],
            "generic_assignments": [],
            "missing_location": []
        }
        
        try:
            batch_size = 1000
            offset = 0
            total_checked = 0
            
            major_regions = ['appalachia', 'mojave', 'commonwealth', 'capital wasteland', 
                           'west virginia', 'nevada', 'boston', 'washington']
            
            while True:
                results = self.collection.get(
                    limit=batch_size,
                    offset=offset,
                    include=["metadatas", "documents"]
                )
                
                if not results['ids']:
                    break
                
                for i, chunk_id in enumerate(results['ids']):
                    metadata = results['metadatas'][i]
                    document = results['documents'][i]
                    title = metadata.get('title', 'Unknown')
                    location = metadata.get('location')
                    total_checked += 1
                    
                    # Check for Vault-Tec as location
                    if location and 'vault-tec' in location.lower():
                        issues['vault_tec_location'].append({
                            'chunk_id': chunk_id,
                            'title': title,
                            'location': location,
                            'reason': 'Vault-Tec should be info_source, not location'
                        })
                        self.stats['vault_tec_location'] += 1
                    
                    # Check for generic assignments
                    if location == 'general':
                        # Verify if it's truly generic by checking for region mentions
                        doc_lower = document.lower() if document else ''
                        has_region = any(region in doc_lower for region in major_regions)
                        if has_region:
                            issues['generic_assignments'].append({
                                'chunk_id': chunk_id,
                                'title': title,
                                'location': location,
                                'reason': 'Marked as general but contains specific region references'
                            })
                            self.stats['generic_assignments'] += 1
                    
                    # Check for missing location in major region articles
                    if not location or location == 'unknown':
                        doc_lower = document.lower() if document else ''
                        title_lower = title.lower()
                        if any(region in doc_lower or region in title_lower 
                              for region in major_regions):
                            issues['missing_location'].append({
                                'chunk_id': chunk_id,
                                'title': title,
                                'location': location,
                                'reason': 'Major region article missing location classification'
                            })
                            self.stats['missing_location'] += 1
                
                offset += batch_size
                logger.info(f"Checked {total_checked} chunks...")
            
            self.stats['total_checked_location'] = total_checked
            logger.info(f"Location audit complete. Checked {total_checked} chunks.")
            
        except Exception as e:
            logger.error(f"Error during location audit: {e}")
        
        return issues
    
    def audit_content_type(self) -> Dict[str, Any]:
        """
        Audit content type classification for:
        - Faction misclassifications (Brotherhood, Enclave as non-faction)
        - Infobox normalization coverage
        
        Returns:
            Dictionary with audit results
        """
        logger.info("Starting content type audit...")
        
        if not self.collection:
            logger.warning("No database connection, skipping audit")
            return self._create_sample_content_type_audit()
        
        issues = {
            "faction_misclass": [],
            "missing_infobox": [],
            "unknown_content_type": []
        }
        
        major_factions = ['brotherhood of steel', 'enclave', 'ncr', 'legion', 
                         'institute', 'minutemen', 'railroad']
        
        try:
            batch_size = 1000
            offset = 0
            total_checked = 0
            
            while True:
                results = self.collection.get(
                    limit=batch_size,
                    offset=offset,
                    include=["metadatas", "documents"]
                )
                
                if not results['ids']:
                    break
                
                for i, chunk_id in enumerate(results['ids']):
                    metadata = results['metadatas'][i]
                    document = results['documents'][i]
                    title = metadata.get('title', 'Unknown')
                    content_type = metadata.get('content_type')
                    total_checked += 1
                    
                    # Check faction misclassification
                    title_lower = title.lower()
                    doc_lower = document.lower() if document else ''
                    
                    for faction in major_factions:
                        if faction in title_lower or faction in doc_lower[:200]:
                            if content_type != 'faction':
                                issues['faction_misclass'].append({
                                    'chunk_id': chunk_id,
                                    'title': title,
                                    'content_type': content_type,
                                    'faction_found': faction,
                                    'reason': f'Contains {faction} but not classified as faction'
                                })
                                self.stats['faction_misclass'] += 1
                                break
                    
                    # Check for missing or unknown content type
                    if not content_type or content_type == 'unknown':
                        issues['unknown_content_type'].append({
                            'chunk_id': chunk_id,
                            'title': title,
                            'content_type': content_type
                        })
                        self.stats['unknown_content_type'] += 1
                
                offset += batch_size
                logger.info(f"Checked {total_checked} chunks...")
            
            self.stats['total_checked_content'] = total_checked
            logger.info(f"Content type audit complete. Checked {total_checked} chunks.")
            
        except Exception as e:
            logger.error(f"Error during content type audit: {e}")
        
        return issues
    
    def audit_knowledge_tier(self) -> Dict[str, Any]:
        """
        Audit knowledge tier assignments for:
        - Missing knowledge_tier field
        - None or empty values
        
        Returns:
            Dictionary with audit results
        """
        logger.info("Starting knowledge tier audit...")
        
        if not self.collection:
            logger.warning("No database connection, skipping audit")
            return {"missing_tier": [], "none_values": []}
        
        issues = {
            "missing_tier": [],
            "none_values": []
        }
        
        try:
            batch_size = 1000
            offset = 0
            total_checked = 0
            
            while True:
                results = self.collection.get(
                    limit=batch_size,
                    offset=offset,
                    include=["metadatas"]
                )
                
                if not results['ids']:
                    break
                
                for i, chunk_id in enumerate(results['ids']):
                    metadata = results['metadatas'][i]
                    title = metadata.get('title', 'Unknown')
                    knowledge_tier = metadata.get('knowledge_tier')
                    total_checked += 1
                    
                    if knowledge_tier is None:
                        issues['none_values'].append({
                            'chunk_id': chunk_id,
                            'title': title
                        })
                        self.stats['none_values'] += 1
                    elif 'knowledge_tier' not in metadata:
                        issues['missing_tier'].append({
                            'chunk_id': chunk_id,
                            'title': title
                        })
                        self.stats['missing_tier'] += 1
                
                offset += batch_size
                logger.info(f"Checked {total_checked} chunks...")
            
            self.stats['total_checked_tier'] = total_checked
            logger.info(f"Knowledge tier audit complete. Checked {total_checked} chunks.")
            
        except Exception as e:
            logger.error(f"Error during knowledge tier audit: {e}")
        
        return issues
    
    def generate_audit_reports(self, output_dir: str = "output") -> None:
        """
        Generate audit reports in JSON format.
        
        Args:
            output_dir: Directory to save reports
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Run all audits
        logger.info("Running comprehensive metadata audit...")
        
        year_issues = self.audit_year_extraction()
        location_issues = self.audit_location_classification()
        content_type_issues = self.audit_content_type()
        knowledge_tier_issues = self.audit_knowledge_tier()
        
        # Save individual reports
        reports = {
            'year_audit': year_issues,
            'location_audit': location_issues,
            'content_type_audit': content_type_issues,
            'knowledge_tier_audit': knowledge_tier_issues
        }
        
        for report_name, report_data in reports.items():
            report_file = output_path / f"phase6_{report_name}_{timestamp}.json"
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            logger.info(f"Saved {report_name} to {report_file}")
        
        # Generate summary statistics
        summary = self._generate_summary_stats()
        summary_file = output_path / f"phase6_audit_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Saved audit summary to {summary_file}")
        
        # Generate markdown report
        self._generate_markdown_report(output_path, timestamp, summary)
    
    def _generate_summary_stats(self) -> Dict[str, Any]:
        """Generate summary statistics from audit"""
        total = self.stats.get('total_checked', 0)
        
        summary = {
            "audit_timestamp": datetime.now().isoformat(),
            "total_chunks_audited": total,
            "year_extraction": {
                "invalid_range": self.stats.get('invalid_range', 0),
                "character_id_pattern": self.stats.get('character_id_pattern', 0),
                "vault_number_pattern": self.stats.get('vault_number_pattern', 0),
                "developer_dates": self.stats.get('developer_dates', 0),
                "missing_year_data": self.stats.get('missing_year_data', 0),
                "error_rate_pct": round((self.stats.get('invalid_range', 0) / total * 100) 
                                       if total > 0 else 0, 2)
            },
            "location_classification": {
                "vault_tec_location": self.stats.get('vault_tec_location', 0),
                "generic_assignments": self.stats.get('generic_assignments', 0),
                "missing_location": self.stats.get('missing_location', 0),
                "error_rate_pct": round((self.stats.get('vault_tec_location', 0) / total * 100) 
                                       if total > 0 else 0, 2)
            },
            "content_type": {
                "faction_misclass": self.stats.get('faction_misclass', 0),
                "unknown_content_type": self.stats.get('unknown_content_type', 0),
                "error_rate_pct": round((self.stats.get('faction_misclass', 0) / total * 100) 
                                       if total > 0 else 0, 2)
            },
            "knowledge_tier": {
                "missing_tier": self.stats.get('missing_tier', 0),
                "none_values": self.stats.get('none_values', 0),
                "error_rate_pct": round((self.stats.get('none_values', 0) / total * 100) 
                                       if total > 0 else 0, 2)
            }
        }
        
        return summary
    
    def _generate_markdown_report(self, output_dir: Path, timestamp: str, 
                                  summary: Dict[str, Any]) -> None:
        """Generate human-readable markdown report"""
        report_file = output_dir / f"PHASE_6_AUDIT_REPORT_{timestamp}.md"
        
        total = summary['total_chunks_audited']
        year_errors = sum(summary['year_extraction'].values()) - summary['year_extraction'].get('missing_year_data', 0)
        loc_errors = sum(summary['location_classification'].values())
        content_errors = sum(summary['content_type'].values())
        tier_errors = sum(summary['knowledge_tier'].values())
        
        report = f"""# Phase 6: Metadata Audit Report

**Date**: {summary['audit_timestamp']}  
**Chunks Audited**: {total:,}  
**Database**: {self.chroma_db_path}

---

## Executive Summary

Total metadata issues identified: **{year_errors + loc_errors + content_errors + tier_errors:,}**

### Issue Breakdown

| Category | Issues Found | Error Rate |
|----------|--------------|------------|
| Year Extraction | {year_errors:,} | {summary['year_extraction']['error_rate_pct']}% |
| Location Classification | {loc_errors:,} | {summary['location_classification']['error_rate_pct']}% |
| Content Type | {content_errors:,} | {summary['content_type']['error_rate_pct']}% |
| Knowledge Tier | {tier_errors:,} | {summary['knowledge_tier']['error_rate_pct']}% |

---

## Year Extraction Issues

### Invalid Range: {summary['year_extraction']['invalid_range']:,}
Chunks with years outside valid Fallout timeline (1950-2290)

### Character ID Pattern: {summary['year_extraction']['character_id_pattern']:,}
Chunks containing character ID patterns (e.g., A-2018, B5-92) that may be mistaken for years

### Vault Number Pattern: {summary['year_extraction']['vault_number_pattern']:,}
Chunks containing vault numbers (e.g., Vault 2018) that may be mistaken for years

### Developer Dates: {summary['year_extraction']['developer_dates']:,}
Chunks with real-world development dates (2010-2025)

### Missing Year Data: {summary['year_extraction']['missing_year_data']:,}
Chunks with no year information

---

## Location Classification Issues

### Vault-Tec Misclassified: {summary['location_classification']['vault_tec_location']:,}
Chunks where Vault-Tec is classified as location (should be info_source)

### Generic Assignments: {summary['location_classification']['generic_assignments']:,}
Chunks marked as "general" but contain specific region references

### Missing Location: {summary['location_classification']['missing_location']:,}
Major region articles missing location classification

---

## Content Type Issues

### Faction Misclassification: {summary['content_type']['faction_misclass']:,}
Chunks about major factions not classified as "faction" content type

### Unknown Content Type: {summary['content_type']['unknown_content_type']:,}
Chunks with missing or unknown content type

---

## Knowledge Tier Issues

### Missing Tier Field: {summary['knowledge_tier']['missing_tier']:,}
Chunks missing the knowledge_tier field entirely

### None Values: {summary['knowledge_tier']['none_values']:,}
Chunks with knowledge_tier = None

---

## Recommendations

Based on error rates:

"""
        
        total_error_rate = ((year_errors + loc_errors + content_errors + tier_errors) / total * 100) if total > 0 else 0
        
        if total_error_rate > 50:
            report += "- ⚠️ **High error rate (>50%)**: Consider full re-ingestion\n"
        elif total_error_rate > 30:
            report += "- ⚠️ **Moderate error rate (30-50%)**: In-place updates with caution\n"
        else:
            report += "- ✅ **Low error rate (<30%)**: Proceed with in-place metadata updates\n"
        
        report += f"""
**Next Steps:**
1. Review detailed JSON reports in {output_dir}/
2. Implement metadata bug fixes (Phase 6, Task 2)
3. Test fixes on sample dataset
4. Re-enrich database with corrected metadata

---

**Detailed Reports:**
- `phase6_year_audit_{timestamp}.json`
- `phase6_location_audit_{timestamp}.json`
- `phase6_content_type_audit_{timestamp}.json`
- `phase6_knowledge_tier_audit_{timestamp}.json`
- `phase6_audit_summary_{timestamp}.json`
"""
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"Generated markdown report: {report_file}")
    
    def _create_sample_year_audit(self) -> Dict[str, Any]:
        """Create sample year audit data for testing without database"""
        return {
            "invalid_range": [],
            "character_id_pattern": [],
            "vault_number_pattern": [],
            "developer_dates": [],
            "missing_year_data": []
        }
    
    def _create_sample_location_audit(self) -> Dict[str, Any]:
        """Create sample location audit data for testing without database"""
        return {
            "vault_tec_location": [],
            "generic_assignments": [],
            "missing_location": []
        }
    
    def _create_sample_content_type_audit(self) -> Dict[str, Any]:
        """Create sample content type audit data for testing without database"""
        return {
            "faction_misclass": [],
            "missing_infobox": [],
            "unknown_content_type": []
        }


def main():
    """Run metadata audit"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 6: Metadata Audit")
    parser.add_argument("--chroma-db", default="chroma_db", 
                       help="Path to ChromaDB directory")
    parser.add_argument("--output", default="output",
                       help="Output directory for reports")
    
    args = parser.parse_args()
    
    auditor = MetadataAuditor(args.chroma_db)
    auditor.generate_audit_reports(args.output)
    
    logger.info("Metadata audit complete!")


if __name__ == "__main__":
    main()
