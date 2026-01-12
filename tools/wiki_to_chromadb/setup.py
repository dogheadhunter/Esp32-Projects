"""
Setup and Installation Verification Script

Checks dependencies and runs initial tests.
"""

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Verify Python version is 3.8+"""
    print("Checking Python version...")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"  ✗ Python {version.major}.{version.minor} detected")
        print("  Python 3.8 or higher is required")
        return False
    
    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def install_dependencies():
    """Install required packages from requirements.txt"""
    print("\nInstalling dependencies...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"  ✗ requirements.txt not found at {requirements_file}")
        return False
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("  ✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to install dependencies: {e}")
        return False


def verify_imports():
    """Verify all required modules can be imported"""
    print("\nVerifying imports...")
    
    required_modules = [
        ('mwxml', 'mwxml'),
        ('mwparserfromhell', 'mwparserfromhell'),
        ('chromadb', 'chromadb'),
        ('sentence_transformers', 'sentence-transformers'),
        ('transformers', 'transformers'),
        ('tqdm', 'tqdm'),
    ]
    
    all_ok = True
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            print(f"  ✗ {package_name} not found")
            all_ok = False
    
    return all_ok


def check_xml_file():
    """Check if wiki XML file exists"""
    print("\nChecking for wiki XML file...")
    
    xml_path = Path(__file__).parent.parent.parent / "lore" / "fallout_wiki_complete.xml"
    
    if xml_path.exists():
        size_mb = xml_path.stat().st_size / 1024 / 1024
        print(f"  ✓ Found: {xml_path}")
        print(f"  Size: {size_mb:.1f} MB")
        return True
    else:
        print(f"  ⚠ Not found: {xml_path}")
        print("  You'll need to export the wiki first")
        print("  See: tools/lore-scraper/export_wiki_xml.py")
        return False


def run_tests():
    """Run test suite"""
    print("\nRunning test suite...")
    
    test_file = Path(__file__).parent / "test_pipeline.py"
    
    if not test_file.exists():
        print(f"  ✗ Test file not found: {test_file}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("  ✓ All tests passed")
            return True
        else:
            print("  ✗ Some tests failed")
            print("\nTest output:")
            print(result.stdout)
            if result.stderr:
                print("Errors:")
                print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("  ✗ Tests timed out (>60s)")
        return False
    except Exception as e:
        print(f"  ✗ Failed to run tests: {e}")
        return False


def main():
    print("=" * 60)
    print("Fallout Wiki → ChromaDB Pipeline Setup")
    print("=" * 60)
    
    steps = [
        ("Python Version", check_python_version),
        ("Dependencies", install_dependencies),
        ("Import Verification", verify_imports),
        ("XML File", check_xml_file),
        ("Test Suite", run_tests),
    ]
    
    results = {}
    
    for step_name, step_func in steps:
        print(f"\n{'─' * 60}")
        result = step_func()
        results[step_name] = result
    
    # Summary
    print("\n" + "=" * 60)
    print("Setup Summary")
    print("=" * 60)
    
    for step_name, result in results.items():
        status = "✓" if result else "✗"
        print(f"{status} {step_name}")
    
    # Next steps
    print("\n" + "=" * 60)
    print("Next Steps")
    print("=" * 60)
    
    if all(results.values()):
        print("\n✓ Setup complete! You're ready to process the wiki.")
        print("\nTo process the complete wiki:")
        print("  python process_wiki.py ../../lore/fallout_wiki_complete.xml")
        print("\nTo process a small test (first 100 pages):")
        print("  python process_wiki.py ../../lore/fallout_wiki_complete.xml --limit 100")
        print("\nTo query the database:")
        print("  python example_query.py")
    else:
        print("\n⚠ Setup incomplete. Please address the failed steps above.")
        
        if not results.get("Dependencies"):
            print("\nTo install dependencies manually:")
            print("  pip install -r requirements.txt")
        
        if not results.get("XML File"):
            print("\nTo export the wiki XML:")
            print("  cd ../../lore")
            print("  python ../tools/lore-scraper/export_wiki_xml.py")
    
    print("\n" + "=" * 60)
    
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    exit(main())
