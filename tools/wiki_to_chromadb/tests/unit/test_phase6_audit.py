"""
Tests for Phase 6 Metadata Audit
"""

import pytest
import json
from pathlib import Path
from tools.wiki_to_chromadb.phase6_metadata_audit import MetadataAuditor


class TestMetadataAuditor:
    """Test metadata auditor functionality"""
    
    def test_auditor_init_without_db(self):
        """Test auditor initializes without database"""
        auditor = MetadataAuditor("nonexistent_db")
        assert auditor.chroma_db_path == "nonexistent_db"
        assert auditor.client is None or auditor.collection is None
    
    def test_sample_year_audit(self):
        """Test sample year audit generation"""
        auditor = MetadataAuditor("nonexistent_db")
        result = auditor._create_sample_year_audit()
        
        assert 'invalid_range' in result
        assert 'character_id_pattern' in result
        assert 'vault_number_pattern' in result
        assert 'developer_dates' in result
        assert 'missing_year_data' in result
    
    def test_sample_location_audit(self):
        """Test sample location audit generation"""
        auditor = MetadataAuditor("nonexistent_db")
        result = auditor._create_sample_location_audit()
        
        assert 'vault_tec_location' in result
        assert 'generic_assignments' in result
        assert 'missing_location' in result
    
    def test_sample_content_type_audit(self):
        """Test sample content type audit generation"""
        auditor = MetadataAuditor("nonexistent_db")
        result = auditor._create_sample_content_type_audit()
        
        assert 'faction_misclass' in result
        assert 'unknown_content_type' in result
    
    def test_generate_summary_stats_empty(self):
        """Test summary stats generation with no data"""
        auditor = MetadataAuditor("nonexistent_db")
        summary = auditor._generate_summary_stats()
        
        assert 'audit_timestamp' in summary
        assert 'total_chunks_audited' in summary
        assert 'year_extraction' in summary
        assert 'location_classification' in summary
        assert 'content_type' in summary
        assert 'knowledge_tier' in summary
        
        # Check error rates are 0 for empty data
        assert summary['year_extraction']['error_rate_pct'] == 0
        assert summary['location_classification']['error_rate_pct'] == 0
    
    def test_generate_summary_stats_with_data(self):
        """Test summary stats generation with sample data"""
        auditor = MetadataAuditor("nonexistent_db")
        auditor.stats['total_checked'] = 1000
        auditor.stats['invalid_range'] = 50
        auditor.stats['vault_tec_location'] = 10
        
        summary = auditor._generate_summary_stats()
        
        assert summary['total_chunks_audited'] == 1000
        assert summary['year_extraction']['invalid_range'] == 50
        assert summary['year_extraction']['error_rate_pct'] == 5.0
        assert summary['location_classification']['vault_tec_location'] == 10
        assert summary['location_classification']['error_rate_pct'] == 1.0
    
    def test_audit_year_extraction_without_db(self):
        """Test year extraction audit without database"""
        auditor = MetadataAuditor("nonexistent_db")
        result = auditor.audit_year_extraction()
        
        # Should return sample data structure
        assert isinstance(result, dict)
        assert 'invalid_range' in result
    
    def test_audit_location_classification_without_db(self):
        """Test location classification audit without database"""
        auditor = MetadataAuditor("nonexistent_db")
        result = auditor.audit_location_classification()
        
        # Should return sample data structure
        assert isinstance(result, dict)
        assert 'vault_tec_location' in result
    
    def test_audit_content_type_without_db(self):
        """Test content type audit without database"""
        auditor = MetadataAuditor("nonexistent_db")
        result = auditor.audit_content_type()
        
        # Should return sample data structure
        assert isinstance(result, dict)
        assert 'faction_misclass' in result
    
    def test_audit_knowledge_tier_without_db(self):
        """Test knowledge tier audit without database"""
        auditor = MetadataAuditor("nonexistent_db")
        result = auditor.audit_knowledge_tier()
        
        # Should return sample data structure
        assert isinstance(result, dict)
        assert 'missing_tier' in result
        assert 'none_values' in result
    
    def test_generate_audit_reports_without_db(self, tmp_path):
        """Test audit report generation without database"""
        auditor = MetadataAuditor("nonexistent_db")
        
        # Generate reports to temp directory
        auditor.generate_audit_reports(str(tmp_path))
        
        # Check that files were created
        json_files = list(tmp_path.glob("*.json"))
        md_files = list(tmp_path.glob("*.md"))
        
        assert len(json_files) >= 4  # At least 4 JSON reports
        assert len(md_files) >= 1  # At least 1 markdown report
        
        # Verify JSON structure
        for json_file in json_files:
            with open(json_file, encoding='utf-8') as f:
                data = json.load(f)
                assert isinstance(data, dict)
    
    def test_markdown_report_generation(self, tmp_path):
        """Test markdown report content"""
        auditor = MetadataAuditor("nonexistent_db")
        auditor.stats['total_checked'] = 1000
        auditor.stats['invalid_range'] = 50
        
        summary = auditor._generate_summary_stats()
        auditor._generate_markdown_report(tmp_path, "test", summary)
        
        report_files = list(tmp_path.glob("PHASE_6_AUDIT_REPORT_*.md"))
        assert len(report_files) == 1
        
        with open(report_files[0]) as f:
            content = f.read()
            assert "Phase 6: Metadata Audit Report" in content
            assert "1,000" in content or "1000" in content
            assert "Executive Summary" in content
            assert "Recommendations" in content
