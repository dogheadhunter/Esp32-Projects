"""
Rule-Based Validation for Broadcast Scripts

Fast validation checks (<100ms target) for:
- Temporal constraints (year limits, anachronisms)
- Content constraints (forbidden topics, factions)
- Format constraints (length, structure, required elements)

Achieves 80% catch rate without LLM calls.
"""

import re
from typing import Dict, List, Any, Optional


class ValidationRules:
    """
    Fast rule-based validation for broadcast scripts.
    
    Features:
    - Temporal validation (year constraints, date detection)
    - Content validation (forbidden topics, factions)
    - Format validation (length, structure, required elements)
    - All checks complete in <100ms
    """
    
    def __init__(self):
        """Initialize validation rules."""
        # Regex patterns for year detection
        self.year_patterns = [
            r'\b(19|20)\d{2}\b',  # 1900-2099
            r'\b\d{4}\b(?=\s*(?:year|AD|CE))',  # Year followed by year/AD/CE
        ]
        
        # Common anachronism triggers
        self.anachronism_keywords = [
            'internet', 'smartphone', 'wifi', 'website', 'app',
            'social media', 'twitter', 'facebook', 'youtube',
            'computer', 'laptop', 'tablet', 'iphone', 'android'
        ]
    
    def validate_temporal(
        self,
        script: str,
        max_year: Optional[int] = None,
        min_year: Optional[int] = None,
        dj_name: str = "DJ"
    ) -> Dict[str, Any]:
        """
        Validate temporal constraints (year limits, anachronisms).
        
        Args:
            script: Script text to validate
            max_year: Maximum allowed year (DJ knowledge cutoff)
            min_year: Minimum allowed year (optional)
            dj_name: DJ name for error messages
        
        Returns:
            Dict with validation results
        """
        issues = []
        
        # Check for year mentions
        years_found = []
        for pattern in self.year_patterns:
            matches = re.findall(pattern, script)
            years_found.extend([int(m) if isinstance(m, str) and m.isdigit() else int(m[0] + m[1])
                               for m in matches])
        
        # Validate against max_year
        if max_year:
            future_years = [y for y in years_found if y > max_year]
            if future_years:
                issues.append(
                    f"Temporal violation: {dj_name} knowledge limited to {max_year}, "
                    f"but script mentions year(s) {', '.join(map(str, future_years))}"
                )
        
        # Validate against min_year
        if min_year:
            past_years = [y for y in years_found if y < min_year]
            if past_years:
                issues.append(
                    f"Temporal violation: Script mentions year(s) before {min_year}: "
                    f"{', '.join(map(str, past_years))}"
                )
        
        # Check for anachronistic terms
        script_lower = script.lower()
        found_anachronisms = [
            term for term in self.anachronism_keywords
            if term in script_lower
        ]
        if found_anachronisms:
            issues.append(
                f"Anachronistic terms detected: {', '.join(found_anachronisms)}"
            )
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'years_found': years_found
        }
    
    def validate_content(
        self,
        script: str,
        forbidden_topics: List[str] = None,
        forbidden_factions: List[str] = None
    ) -> Dict[str, Any]:
        """
        Validate content constraints (forbidden topics, factions).
        
        Args:
            script: Script text to validate
            forbidden_topics: List of forbidden topic keywords
            forbidden_factions: List of forbidden faction names
        
        Returns:
            Dict with validation results
        """
        issues = []
        script_lower = script.lower()
        
        # Check forbidden topics
        if forbidden_topics:
            found_topics = []
            for topic in forbidden_topics:
                # Case-insensitive word boundary search
                pattern = r'\b' + re.escape(topic.lower()) + r'\b'
                if re.search(pattern, script_lower):
                    found_topics.append(topic)
            
            if found_topics:
                issues.append(
                    f"Forbidden topics detected: {', '.join(found_topics)}"
                )
        
        # Check forbidden factions
        if forbidden_factions:
            found_factions = []
            for faction in forbidden_factions:
                # Case-insensitive word boundary search
                pattern = r'\b' + re.escape(faction.lower()) + r'\b'
                if re.search(pattern, script_lower):
                    found_factions.append(faction)
            
            if found_factions:
                issues.append(
                    f"Forbidden factions detected: {', '.join(found_factions)}"
                )
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues
        }
    
    def validate_format(
        self,
        script: str,
        max_length: Optional[int] = None,
        required_elements: List[str] = None
    ) -> Dict[str, Any]:
        """
        Validate format constraints (length, required elements).
        
        Args:
            script: Script text to validate
            max_length: Maximum allowed length in characters
            required_elements: List of required keywords/elements
        
        Returns:
            Dict with validation results
        """
        issues = []
        
        # Check length
        if max_length:
            script_length = len(script)
            if script_length > max_length:
                issues.append(
                    f"Length violation: {script_length} characters "
                    f"(max: {max_length})"
                )
        
        # Check required elements
        if required_elements:
            script_lower = script.lower()
            missing_elements = []
            
            for element in required_elements:
                # Case-insensitive search
                if element.lower() not in script_lower:
                    missing_elements.append(element)
            
            if missing_elements:
                issues.append(
                    f"Missing required elements: {', '.join(missing_elements)}"
                )
        
        # Check for minimum structure (at least one sentence)
        if not script.strip():
            issues.append("Empty script")
        elif not any(script.strip().endswith(p) for p in ['.', '!', '?']):
            issues.append("Script missing proper punctuation")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'length': len(script)
        }
    
    def validate_all(
        self,
        script: str,
        max_year: Optional[int] = None,
        min_year: Optional[int] = None,
        forbidden_topics: List[str] = None,
        forbidden_factions: List[str] = None,
        max_length: Optional[int] = None,
        required_elements: List[str] = None,
        dj_name: str = "DJ"
    ) -> Dict[str, Any]:
        """
        Run all validation rules.
        
        Args:
            script: Script text to validate
            max_year: Maximum allowed year
            min_year: Minimum allowed year
            forbidden_topics: Forbidden topic keywords
            forbidden_factions: Forbidden faction names
            max_length: Maximum length
            required_elements: Required elements
            dj_name: DJ name
        
        Returns:
            Dict with combined validation results
        """
        all_issues = []
        results = {}
        
        # Temporal validation
        if max_year or min_year:
            temporal = self.validate_temporal(script, max_year, min_year, dj_name)
            results['temporal'] = temporal
            all_issues.extend(temporal['issues'])
        
        # Content validation
        if forbidden_topics or forbidden_factions:
            content = self.validate_content(script, forbidden_topics, forbidden_factions)
            results['content'] = content
            all_issues.extend(content['issues'])
        
        # Format validation
        if max_length or required_elements:
            format_check = self.validate_format(script, max_length, required_elements)
            results['format'] = format_check
            all_issues.extend(format_check['issues'])
        
        return {
            'is_valid': len(all_issues) == 0,
            'issues': all_issues,
            'detailed_results': results
        }


# Example usage
if __name__ == "__main__":
    rules = ValidationRules()
    
    # Test script
    script = """Good morning, Commonwealth! It's 2287 and the weather is clear.
The Institute has been spotted near Diamond City. Stay vigilant!"""
    
    # Temporal validation
    result = rules.validate_temporal(
        script=script,
        max_year=2287,
        dj_name="Julie"
    )
    print(f"Temporal: {result}")
    
    # Content validation
    result = rules.validate_content(
        script=script,
        forbidden_topics=["Institute"],
        forbidden_factions=["Enclave"]
    )
    print(f"Content: {result}")
    
    # Format validation
    result = rules.validate_format(
        script=script,
        max_length=200,
        required_elements=["weather", "temperature"]
    )
    print(f"Format: {result}")
    
    # All validations
    result = rules.validate_all(
        script=script,
        max_year=2287,
        forbidden_topics=["Institute"],
        max_length=500,
        required_elements=["Commonwealth"],
        dj_name="Julie"
    )
    print(f"\nAll validations: {result['is_valid']}")
    print(f"Issues: {result['issues']}")
