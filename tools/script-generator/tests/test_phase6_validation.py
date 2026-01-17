"""
Unit tests for Phase 6 validation system.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open
from pathlib import Path
import sys
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock the external dependencies before import
sys.modules['chromadb_manager'] = MagicMock()
sys.modules['tools.wiki_to_chromadb.chromadb_manager'] = MagicMock()

from phase6_validation import Phase6Validator


class TestPhase6Validator(unittest.TestCase):
    """Test Phase6Validator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = Phase6Validator(db_path="test_db")
    
    def test_initialization(self):
        """Test validator initialization."""
        self.assertIsNotNone(self.validator)
        self.assertEqual(self.validator.db_path, "test_db")
        self.assertIsNone(self.validator.db_manager)
        self.assertIsNone(self.validator.freshness_tracker)
        self.assertEqual(self.validator.results['overall_status'], 'not_run')
    
    @patch('phase6_validation.ChromaDBManager')
    @patch('phase6_validation.BroadcastFreshnessTracker')
    def test_initialize_success(self, mock_freshness, mock_db):
        """Test successful initialization."""
        result = self.validator.initialize()
        self.assertTrue(result)
        self.assertIsNotNone(self.validator.db_manager)
        self.assertIsNotNone(self.validator.freshness_tracker)
    
    @patch('phase6_validation.ChromaDBManager')
    def test_initialize_failure(self, mock_db):
        """Test initialization failure."""
        mock_db.side_effect = Exception("DB error")
        result = self.validator.initialize()
        self.assertFalse(result)
    
    @patch('phase6_validation.ChromaDBManager')
    def test_validate_metadata_accuracy(self, mock_db):
        """Test metadata accuracy validation."""
        # Mock database manager
        mock_collection = Mock()
        mock_collection.get.return_value = {
            'ids': ['chunk1', 'chunk2', 'chunk3'],
            'metadatas': [
                {
                    'year_min': 2077,
                    'year_max': 2077,
                    'location': 'Mojave Wasteland',
                    'emotional_tone': 'hopeful',
                    'complexity_tier': 'moderate',
                    'primary_subject_0': 'water',
                    'theme_0': 'survival',
                    'controversy_level': 'neutral',
                    'last_broadcast_time': 0,
                    'broadcast_count': 0,
                    'freshness_score': 1.0
                },
                {
                    'year_min': 2161,
                    'year_max': 2241,
                    'location': 'Capital Wasteland',
                    'info_source': 'Vault-Tec',
                    'emotional_tone': 'mysterious',
                    'complexity_tier': 'complex',
                    'primary_subject_0': 'radiation',
                    'theme_0': 'humanity',
                    'controversy_level': 'sensitive',
                    'last_broadcast_time': 0,
                    'broadcast_count': 0,
                    'freshness_score': 1.0
                },
                {
                    'year_min': 2102,
                    'year_max': 2102,
                    'location': 'Boston',
                    'emotional_tone': 'tense',
                    'complexity_tier': 'simple',
                    'primary_subject_0': 'factions',
                    'theme_0': 'war',
                    'controversy_level': 'neutral',
                    'last_broadcast_time': 0,
                    'broadcast_count': 0,
                    'freshness_score': 1.0
                }
            ]
        }
        
        mock_db_instance = Mock()
        mock_db_instance.collection = mock_collection
        self.validator.db_manager = mock_db_instance
        
        # Run validation
        results = self.validator.validate_metadata_accuracy(sample_size=3)
        
        # Assertions
        self.assertEqual(results['total_sampled'], 3)
        self.assertEqual(results['year_extraction']['valid'], 3)
        self.assertEqual(results['year_extraction']['invalid'], 0)
        self.assertGreater(results['broadcast_metadata']['emotional_tone']['populated'], 0)
        self.assertGreater(results['broadcast_metadata']['complexity_tier']['populated'], 0)
    
    @patch('phase6_validation.ChromaDBManager')
    @patch('phase6_validation.JulieProfile')
    def test_freshness_effectiveness(self, mock_profile, mock_db):
        """Test freshness effectiveness measurement."""
        # Mock profile
        mock_profile_instance = Mock()
        mock_profile_instance.get_enhanced_filter.return_value = {'confidence_score': {'$gte': 0.7}}
        mock_profile.return_value = mock_profile_instance
        
        # Mock database
        mock_collection = Mock()
        mock_collection.query.return_value = {
            'ids': [['chunk1', 'chunk2', 'chunk3']],
            'metadatas': [[
                {'freshness_score': 0.8},
                {'freshness_score': 0.9},
                {'freshness_score': 0.7}
            ]]
        }
        
        mock_db_instance = Mock()
        mock_db_instance.collection = mock_collection
        self.validator.db_manager = mock_db_instance
        
        # Run test
        results = self.validator.test_freshness_effectiveness(test_broadcasts=2)
        
        # Assertions
        self.assertEqual(results['broadcasts_tested'], 2)
        self.assertGreater(results['total_chunks_pulled'], 0)
        self.assertIn('repetition_rate', results)
    
    @patch('phase6_validation.ChromaDBManager')
    @patch('phase6_validation.JulieProfile')
    def test_content_variety(self, mock_profile, mock_db):
        """Test content variety measurement."""
        # Mock profile
        mock_profile_instance = Mock()
        mock_profile_instance.get_enhanced_filter.return_value = {}
        mock_profile.return_value = mock_profile_instance
        
        # Mock database
        mock_collection = Mock()
        mock_collection.query.return_value = {
            'ids': [['chunk1', 'chunk2']],
            'metadatas': [[
                {
                    'emotional_tone': 'hopeful',
                    'complexity_tier': 'moderate',
                    'primary_subject_0': 'water',
                    'primary_subject_1': 'radiation',
                    'theme_0': 'survival',
                    'theme_1': 'humanity'
                },
                {
                    'emotional_tone': 'mysterious',
                    'complexity_tier': 'complex',
                    'primary_subject_0': 'factions',
                    'theme_0': 'war'
                }
            ]]
        }
        
        mock_db_instance = Mock()
        mock_db_instance.collection = mock_collection
        self.validator.db_manager = mock_db_instance
        
        # Run test
        results = self.validator.measure_content_variety(num_queries=5)
        
        # Assertions
        self.assertEqual(results['total_queries'], 5)
        self.assertGreater(results['total_chunks'], 0)
        self.assertIn('unique_tones', results)
        self.assertIn('unique_subjects', results)
    
    @patch('phase6_validation.ChromaDBManager')
    @patch('phase6_validation.JulieProfile')
    def test_query_performance(self, mock_profile, mock_db):
        """Test query performance benchmark."""
        # Mock profile
        mock_profile_instance = Mock()
        mock_profile_instance.get_base_filter.return_value = {}
        mock_profile_instance.get_enhanced_filter.return_value = {}
        mock_profile.return_value = mock_profile_instance
        
        # Mock database
        mock_collection = Mock()
        mock_collection.query.return_value = {'ids': [['chunk1']]}
        
        mock_db_instance = Mock()
        mock_db_instance.collection = mock_collection
        self.validator.db_manager = mock_db_instance
        
        # Run test
        results = self.validator.benchmark_query_performance(num_queries=10)
        
        # Assertions
        self.assertEqual(results['total_queries'], 10)
        self.assertIn('baseline_avg', results)
        self.assertIn('enhanced_avg', results)
        self.assertIn('overhead_ms', results)
    
    def test_integration_tests(self):
        """Test integration test runner."""
        # Mock database manager
        mock_collection = Mock()
        mock_collection.query.return_value = {'ids': [['chunk1', 'chunk2']]}
        
        mock_db_instance = Mock()
        mock_db_instance.collection = mock_collection
        self.validator.db_manager = mock_db_instance
        
        # Run tests
        results = self.validator.run_integration_tests()
        
        # Assertions
        self.assertIn('tests', results)
        self.assertIn('passed', results)
        self.assertIn('failed', results)
        self.assertIn('complexity_sequencing', results['tests'])
        self.assertIn('subject_tracking', results['tests'])
        self.assertIn('tone_mapping', results['tests'])
    
    def test_generate_report(self):
        """Test report generation."""
        import tempfile
        import json
        
        # Set some test results
        self.validator.results['metadata_accuracy'] = {'total_sampled': 100}
        self.validator.results['freshness_effectiveness'] = {'broadcasts_tested': 10}
        
        # Generate report to temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        self.validator.generate_report(output_path=temp_path)
        
        # Verify report was created
        with open(temp_path, 'r') as f:
            report = json.load(f)
        
        self.assertIn('overall_status', report)
        self.assertIn('timestamp', report)
        self.assertIn('summary', report)
        
        # Cleanup
        Path(temp_path).unlink()
    
    def test_overall_status_determination(self):
        """Test overall status determination logic."""
        # Test passed status
        self.validator.results = {
            'metadata_accuracy': {'total_sampled': 100},
            'freshness_effectiveness': {'broadcasts_tested': 10},
            'content_variety': {'total_chunks': 50},
            'query_performance': {'total_queries': 100},
            'integration_tests': {'passed': 5},
            'overall_status': 'not_run'
        }
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        self.validator.generate_report(output_path=temp_path)
        
        self.assertEqual(self.validator.results['overall_status'], 'passed')
        
        # Cleanup
        Path(temp_path).unlink()
        
        # Test failed status with errors
        self.validator.results['metadata_accuracy'] = {'error': 'Test error'}
        self.validator.generate_report(output_path=temp_path)
        
        self.assertEqual(self.validator.results['overall_status'], 'failed')
        
        # Cleanup
        Path(temp_path).unlink()


if __name__ == '__main__':
    unittest.main()
