#!/usr/bin/env python3
"""
ESP32 AI Radio - Interactive Setup and Management Wizard with 3-Format Logging

A user-friendly command-line wizard that guides you through:
- Initial setup and installation
- Running tests
- Managing the ChromaDB database
- Generating broadcast content
- Development tools and utilities

All wizard sessions are logged to 3 formats:
- .log: Human-readable with complete terminal output
- .json: Structured metadata for programmatic analysis
- .llm.md: LLM-optimized markdown (50-60% smaller)

Usage:
    python wizard.py              # Interactive menu
    python wizard.py --help       # Show all options
    python wizard.py --quick-test # Quick action (bypass menu)
"""

import sys
import os
import subprocess
import platform
from pathlib import Path
from typing import Optional, List, Tuple

# Add shared tools to path for logging
sys.path.insert(0, str(Path(__file__).parent / "tools" / "shared"))
from logging_config import capture_output

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def disable():
        """Disable colors for Windows or when not supported"""
        Colors.HEADER = ''
        Colors.BLUE = ''
        Colors.CYAN = ''
        Colors.GREEN = ''
        Colors.YELLOW = ''
        Colors.RED = ''
        Colors.ENDC = ''
        Colors.BOLD = ''
        Colors.UNDERLINE = ''

# Disable colors on Windows unless in modern terminal
if platform.system() == 'Windows' and not os.environ.get('WT_SESSION'):
    Colors.disable()


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}\n")


def print_section(text: str):
    """Print a section divider"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{text}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'-'*len(text)}{Colors.ENDC}")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}[OK] {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}[ERROR] {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARNING] {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.CYAN}[INFO] {text}{Colors.ENDC}")


def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if platform.system() == 'Windows' else 'clear')


def wait_for_key():
    """Wait for user to press Enter"""
    input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")


def get_choice(prompt: str, options: List[Tuple[str, str]], allow_back: bool = True) -> Optional[str]:
    """
    Display options and get user choice.
    
    Args:
        prompt: Question to ask user
        options: List of (key, description) tuples
        allow_back: Allow 'b' to go back
        
    Returns:
        Selected option key or None if back was chosen
    """
    print(f"\n{Colors.BOLD}{prompt}{Colors.ENDC}\n")
    
    for key, description in options:
        print(f"  {Colors.GREEN}{key}{Colors.ENDC}) {description}")
    
    if allow_back:
        print(f"  {Colors.YELLOW}b{Colors.ENDC}) Back to main menu")
    print(f"  {Colors.RED}q{Colors.ENDC}) Quit")
    
    while True:
        choice = input(f"\n{Colors.CYAN}Enter your choice: {Colors.ENDC}").strip().lower()
        
        if choice == 'q':
            print_info("Goodbye!")
            sys.exit(0)
        
        if choice == 'b' and allow_back:
            return None
        
        if any(choice == key for key, _ in options):
            return choice
        
        print_error("Invalid choice. Please try again.")


def run_command(cmd: List[str], description: str, shell: bool = False) -> bool:
    """
    Run a command and show output.
    
    Args:
        cmd: Command to run (list of strings)
        description: What the command does
        shell: Whether to run in shell
        
    Returns:
        True if successful, False otherwise
    """
    print_section(description)
    
    try:
        if shell:
            cmd = ' '.join(cmd)
        
        result = subprocess.run(
            cmd,
            shell=shell,
            check=False,
            text=True,
            capture_output=False
        )
        
        if result.returncode == 0:
            print_success(f"{description} completed successfully!")
            return True
        else:
            print_error(f"{description} failed with exit code {result.returncode}")
            return False
    except FileNotFoundError as e:
        print_error(f"Command not found: {e}")
        print_warning("Make sure all dependencies are installed")
        return False
    except Exception as e:
        print_error(f"Error running command: {e}")
        return False


def check_python_version():
    """Check if Python version meets requirements"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print_error(f"Python 3.10+ required, found {version.major}.{version.minor}")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def check_dependencies() -> dict:
    """Check which dependencies are installed"""
    status = {}
    
    # Check Python packages
    packages = ['pytest', 'chromadb', 'pydantic', 'jinja2', 'tqdm']
    
    for package in packages:
        try:
            __import__(package)
            status[package] = True
        except ImportError:
            status[package] = False
    
    # Check Ollama
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, timeout=5)
        status['ollama'] = result.returncode == 0
    except:
        status['ollama'] = False
    
    return status


def setup_wizard():
    """Initial setup and installation wizard"""
    clear_screen()
    print_header("ESP32 AI Radio - Initial Setup Wizard")
    
    print_info("This wizard will help you set up the ESP32 AI Radio project.\n")
    
    # Check Python version
    print_section("Step 1: Checking Python Version")
    if not check_python_version():
        print_warning("Please install Python 3.10 or higher")
        wait_for_key()
        return
    
    # Check dependencies
    print_section("Step 2: Checking Dependencies")
    deps = check_dependencies()
    
    missing = [pkg for pkg, installed in deps.items() if not installed]
    
    if missing:
        print_warning(f"Missing dependencies: {', '.join(missing)}")
        
        if 'ollama' in missing:
            print_info("Ollama not found. Download from: https://ollama.ai/")
        
        if any(pkg != 'ollama' for pkg in missing):
            print_info("To install Python dependencies:")
            print(f"  {Colors.GREEN}pip install -e .[dev]{Colors.ENDC}")
        
        install = get_choice("Would you like to install Python dependencies now?", [
            ('y', 'Yes, install now'),
            ('n', 'No, I will install manually')
        ], allow_back=False)
        
        if install == 'y':
            run_command(['pip', 'install', '-e', '.[dev]'], "Installing dependencies")
    else:
        print_success("All dependencies are installed!")
    
    # Check database
    print_section("Step 3: Checking ChromaDB Database")
    db_path = Path("data/fallout_wiki_chromadb")
    
    if db_path.exists() and any(db_path.iterdir()):
        print_success("ChromaDB database found")
    else:
        print_warning("ChromaDB database not found")
        print_info("You need to ingest the Fallout Wiki (takes 2-3 hours)")
        print_info("Use the 'Database Management' menu option to ingest")
    
    print_section("Setup Complete!")
    print_success("Setup wizard finished. You can now use the main menu.")
    wait_for_key()


def test_menu():
    """Test runner menu"""
    while True:
        clear_screen()
        print_header("Test Runner")
        
        choice = get_choice("Select test suite to run:", [
            ('1', 'Quick Tests (fast, mock-only)'),
            ('2', 'Unit Tests (all unit tests)'),
            ('3', 'Integration Tests (requires Ollama/ChromaDB)'),
            ('4', 'Full Test Suite (all tests)'),
            ('5', 'Test with Coverage Report'),
            ('6', 'Specific Test File (enter path)'),
        ])
        
        if choice is None:
            break
        
        if choice == '1':
            run_command(['python', 'run_tests.py', 'quick'], "Running quick tests")
        elif choice == '2':
            run_command(['python', 'run_tests.py', 'unit'], "Running unit tests")
        elif choice == '3':
            print_warning("Integration tests require Ollama and ChromaDB to be running")
            confirm = get_choice("Continue?", [('y', 'Yes'), ('n', 'No')], allow_back=False)
            if confirm == 'y':
                run_command(['python', 'run_tests.py', 'integration'], "Running integration tests")
        elif choice == '4':
            run_command(['python', 'run_tests.py'], "Running full test suite")
        elif choice == '5':
            run_command(['python', 'run_tests.py', 'coverage'], "Running tests with coverage")
        elif choice == '6':
            test_path = input(f"\n{Colors.CYAN}Enter test file path: {Colors.ENDC}").strip()
            if test_path:
                run_command(['python', '-m', 'pytest', test_path, '-v'], f"Running {test_path}")
        
        wait_for_key()


def database_menu():
    """Database management menu"""
    while True:
        clear_screen()
        print_header("ChromaDB Database Management")
        
        db_path = Path("data/fallout_wiki_chromadb")
        
        if db_path.exists() and any(db_path.iterdir()):
            print_success(f"Database exists at: {db_path}")
        else:
            print_warning("Database not found")
        
        choice = get_choice("Select database operation:", [
            ('1', 'Ingest Fallout Wiki (takes 2-3 hours, requires internet)'),
            ('2', 'Fresh Ingest (delete existing, then ingest)'),
            ('3', 'Backup Database'),
            ('4', 'Restore Database from Backup'),
            ('5', 'Quick Backup (fast, no compression)'),
            ('6', 'Check Database Status'),
        ])
        
        if choice is None:
            break
        
        if choice == '1':
            print_warning("This will take 2-3 hours and requires internet connection")
            confirm = get_choice("Continue?", [('y', 'Yes'), ('n', 'No')], allow_back=False)
            if confirm == 'y':
                if platform.system() == 'Windows':
                    run_command(['scripts\\ingest_wiki.bat'], "Ingesting wiki", shell=True)
                else:
                    run_command(['python', 'tools/wiki_to_chromadb/process_wiki.py'], "Ingesting wiki")
        
        elif choice == '2':
            print_error("WARNING: This will delete the existing database!")
            confirm = get_choice("Are you sure?", [('y', 'Yes'), ('n', 'No')], allow_back=False)
            if confirm == 'y':
                if platform.system() == 'Windows':
                    run_command(['scripts\\ingest_wiki_fresh.bat'], "Fresh ingest", shell=True)
                else:
                    if db_path.exists():
                        import shutil
                        shutil.rmtree(db_path)
                    run_command(['python', 'tools/wiki_to_chromadb/process_wiki.py'], "Ingesting wiki")
        
        elif choice == '3':
            if platform.system() == 'Windows':
                run_command(['scripts\\backup_database.bat'], "Backing up database", shell=True)
            else:
                timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
                run_command(['tar', '-czf', f'archive/database_backup_{timestamp}.tar.gz', str(db_path)], "Backing up database")
        
        elif choice == '4':
            if platform.system() == 'Windows':
                run_command(['scripts\\restore_database.bat'], "Restoring database", shell=True)
            else:
                print_info("Available backups:")
                backups = list(Path('archive').glob('database_backup_*.tar.gz'))
                if backups:
                    for i, backup in enumerate(backups, 1):
                        print(f"  {i}) {backup.name}")
                    print_warning("Manual restore: tar -xzf <backup_file> -C data/")
                else:
                    print_warning("No backups found in archive/")
        
        elif choice == '5':
            if platform.system() == 'Windows':
                run_command(['scripts\\backup_quick.bat'], "Quick backup", shell=True)
            else:
                timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
                run_command(['cp', '-r', str(db_path), f'archive/db_quick_{timestamp}'], "Quick backup")
        
        elif choice == '6':
            if db_path.exists():
                size = sum(f.stat().st_size for f in db_path.rglob('*') if f.is_file()) / (1024**3)
                print_success(f"Database size: {size:.2f} GB")
                count = len(list(db_path.rglob('*.bin')))
                print_info(f"Database files: {count}")
            else:
                print_error("Database not found")
        
        wait_for_key()


def broadcast_menu():
    """Broadcast content generation menu"""
    while True:
        clear_screen()
        print_header("Broadcast Content Generation")
        
        choice = get_choice("Select broadcast operation:", [
            ('1', 'Generate Broadcast (guided)'),
            ('2', 'Quick Generate (Julie, 1 hour)'),
            ('3', 'Multi-Day Broadcast (7 days)'),
            ('4', 'View Available DJs'),
            ('5', 'Advanced Options'),
        ])
        
        if choice is None:
            break
        
        if choice == '1':
            # Guided generation
            print_section("Guided Broadcast Generation")
            
            djs = [
                "Julie (2102, Appalachia)",
                "Mr. New Vegas (2281, Mojave)",
                "Travis Miles (Nervous) (2287, Commonwealth)",
                "Travis Miles (Confident) (2287, Commonwealth)"
            ]
            
            print_info("Available DJs:")
            for i, dj in enumerate(djs, 1):
                print(f"  {i}) {dj}")
            
            dj_choice = input(f"\n{Colors.CYAN}Enter DJ number (1-{len(djs)}): {Colors.ENDC}").strip()
            if not dj_choice.isdigit() or int(dj_choice) < 1 or int(dj_choice) > len(djs):
                print_error("Invalid choice")
                wait_for_key()
                continue
            
            dj = djs[int(dj_choice) - 1]
            duration = input(f"{Colors.CYAN}Duration in hours (1-24): {Colors.ENDC}").strip()
            
            if not duration.isdigit():
                print_error("Invalid duration")
                wait_for_key()
                continue
            
            cmd = ['python', 'broadcast.py', '--dj', dj, '--hours', duration]
            run_command(cmd, f"Generating {duration}h broadcast for {dj}")
        
        elif choice == '2':
            run_command(['python', 'broadcast.py', '--dj', 'Julie', '--hours', '1'], "Quick generation")
        
        elif choice == '3':
            dj = input(f"{Colors.CYAN}Enter DJ name (or shortcut like 'julie'): {Colors.ENDC}").strip()
            if dj:
                run_command(['python', 'broadcast.py', '--dj', dj, '--days', '7'], f"7-day broadcast for {dj}")
        
        elif choice == '4':
            print_section("Available DJ Personalities")
            djs = [
                ("Julie", "2102, Appalachia - Friendly, community-focused"),
                ("Mr. New Vegas", "2281, Mojave - Smooth, professional"),
                ("Travis Miles (Nervous)", "2287, Commonwealth - Awkward, endearing"),
                ("Travis Miles (Confident)", "2287, Commonwealth - Professional, confident"),
                ("Three Dog", "2277, Capital Wasteland - Energetic, rebellious")
            ]
            for dj, desc in djs:
                print(f"\n  {Colors.GREEN}{dj}{Colors.ENDC}")
                print(f"    {desc}")
        
        elif choice == '5':
            print_info("Advanced options:")
            print("  --enable-stories          Enable story system")
            print("  --validation-mode MODE    llm, hybrid, or basic")
            print("  --segments-per-hour N     Segments per hour (default: 4)")
            print()
            print_info("Example:")
            print(f"  {Colors.GREEN}python broadcast.py --dj Julie --days 2 --enable-stories{Colors.ENDC}")
        
        wait_for_key()


def development_menu():
    """Development tools menu"""
    while True:
        clear_screen()
        print_header("Development Tools")
        
        choice = get_choice("Select development tool:", [
            ('1', 'Format Code (Black)'),
            ('2', 'Sort Imports (isort)'),
            ('3', 'Lint Code (Ruff)'),
            ('4', 'Type Check (MyPy)'),
            ('5', 'Run All Quality Checks'),
            ('6', 'View Test Logs'),
        ])
        
        if choice is None:
            break
        
        if choice == '1':
            run_command(['black', 'tools/', 'tests/', 'broadcast.py', 'run_tests.py'], "Formatting code with Black")
        elif choice == '2':
            run_command(['isort', 'tools/', 'tests/', 'broadcast.py', 'run_tests.py'], "Sorting imports with isort")
        elif choice == '3':
            run_command(['ruff', 'check', 'tools/', 'tests/'], "Linting with Ruff")
        elif choice == '4':
            run_command(['mypy', 'tools/'], "Type checking with MyPy")
        elif choice == '5':
            print_section("Running all quality checks")
            run_command(['black', 'tools/', 'tests/'], "1/4: Formatting")
            run_command(['isort', 'tools/', 'tests/'], "2/4: Import sorting")
            run_command(['ruff', 'check', 'tools/'], "3/4: Linting")
            run_command(['mypy', 'tools/'], "4/4: Type checking")
        elif choice == '6':
            log_dir = Path('logs/archive')
            if log_dir.exists():
                # Find most recent log
                logs = sorted(log_dir.rglob('*.llm.md'), key=lambda p: p.stat().st_mtime, reverse=True)
                if logs:
                    latest = logs[0]
                    print_info(f"Most recent log: {latest}")
                    print_info(f"Opening in editor...")
                    if platform.system() == 'Windows':
                        os.system(f'notepad {latest}')
                    else:
                        os.system(f'less {latest}')
                else:
                    print_warning("No log files found")
            else:
                print_warning("Log directory not found")
        
        wait_for_key()


def advanced_menu():
    """Advanced tools and configuration menu for power users"""
    while True:
        clear_screen()
        print_header("Advanced Tools & Configuration")
        
        choice = get_choice("Advanced operations:", [
            ('1', 'Custom Test Command (specify pytest args)'),
            ('2', 'Database Query Tool (interactive ChromaDB queries)'),
            ('3', 'Batch Script Generation (multiple DJs/durations)'),
            ('4', 'Configuration Editor (edit project settings)'),
            ('5', 'Log Analysis (parse and analyze test logs)'),
            ('6', 'Performance Profiling (profile code execution)'),
            ('7', 'Cache Management (clear/rebuild caches)'),
            ('8', 'Git Operations (status, diff, log)'),
            ('9', 'Environment Variables (view/set)'),
            ('10', 'Custom Command (run any Python script)'),
        ])
        
        if choice is None:
            break
        
        if choice == '1':
            print_section("Custom Test Command")
            print_info("Examples:")
            print("  -k test_name         # Run specific test")
            print("  --lf                 # Run last failed")
            print("  --maxfail=1          # Stop after first failure")
            print("  -x                   # Stop on first error")
            
            args = input(f"\n{Colors.CYAN}Enter pytest arguments: {Colors.ENDC}").strip()
            if args:
                run_command(['python', '-m', 'pytest'] + args.split(), f"Running pytest {args}")
        
        elif choice == '2':
            print_section("Database Query Tool")
            print_info("ChromaDB interactive query interface")
            
            query_type = get_choice("Query type:", [
                ('1', 'Search by text'),
                ('2', 'Filter by metadata'),
                ('3', 'Collection statistics'),
                ('4', 'Export results to JSON')
            ], allow_back=True)
            
            if query_type == '1':
                query_text = input(f"{Colors.CYAN}Enter search text: {Colors.ENDC}").strip()
                if query_text:
                    cmd = ['python', '-c', f"""
import sys
sys.path.insert(0, 'tools/wiki_to_chromadb')
from chromadb_ingest import ChromaDBIngestor
ingestor = ChromaDBIngestor()
results = ingestor.collection.query(query_texts=['{query_text}'], n_results=5)
for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
    print(f'{{i}}. {{meta.get("wiki_title", "Unknown")}}')
    print(f'   {{doc[:200]}}...')
"""]
                    run_command(cmd, "Querying ChromaDB")
            
            elif query_type == '3':
                cmd = ['python', '-c', """
import sys
sys.path.insert(0, 'tools/wiki_to_chromadb')
from chromadb_ingest import ChromaDBIngestor
ingestor = ChromaDBIngestor()
count = ingestor.collection.count()
print(f'Total documents: {count}')
"""]
                run_command(cmd, "Getting database statistics")
        
        elif choice == '3':
            print_section("Batch Script Generation")
            print_info("Generate multiple broadcasts in one go")
            
            djs_input = input(f"{Colors.CYAN}Enter DJ names (comma-separated): {Colors.ENDC}").strip()
            hours_input = input(f"{Colors.CYAN}Enter hours per broadcast: {Colors.ENDC}").strip()
            
            if djs_input and hours_input:
                djs = [dj.strip() for dj in djs_input.split(',')]
                for dj in djs:
                    run_command(['python', 'broadcast.py', '--dj', dj, '--hours', hours_input], 
                               f"Generating {hours_input}h for {dj}")
        
        elif choice == '4':
            print_section("Configuration Editor")
            config_file = Path('tools/shared/project_config.py')
            if config_file.exists():
                print_info(f"Config file: {config_file}")
                print_info("Opening in default editor...")
                if platform.system() == 'Windows':
                    os.system(f'notepad {config_file}')
                else:
                    editor = os.environ.get('EDITOR', 'nano')
                    os.system(f'{editor} {config_file}')
            else:
                print_error("Config file not found")
        
        elif choice == '5':
            print_section("Log Analysis")
            log_dir = Path('logs/archive')
            
            if log_dir.exists():
                # Find logs
                log_files = sorted(log_dir.rglob('*.llm.md'), key=lambda p: p.stat().st_mtime, reverse=True)
                
                if log_files:
                    print_info(f"Found {len(log_files)} log files")
                    print("\nMost recent 5:")
                    for i, log in enumerate(log_files[:5], 1):
                        print(f"  {i}. {log.name} ({log.stat().st_size} bytes)")
                    
                    choice_num = input(f"\n{Colors.CYAN}Enter number to analyze (1-5): {Colors.ENDC}").strip()
                    if choice_num.isdigit() and 1 <= int(choice_num) <= 5:
                        log_file = log_files[int(choice_num) - 1]
                        with open(log_file) as f:
                            content = f.read()
                        
                        # Parse log
                        lines = content.split('\n')
                        print_section(f"Analysis of {log_file.name}")
                        
                        # Count test results
                        for line in lines:
                            if 'Passed:' in line or 'Failed:' in line or 'Coverage:' in line:
                                print(f"  {line.strip()}")
                else:
                    print_warning("No log files found")
            else:
                print_error("Log directory not found")
        
        elif choice == '6':
            print_section("Performance Profiling")
            print_info("Profile Python script execution")
            
            script_path = input(f"{Colors.CYAN}Enter script path to profile: {Colors.ENDC}").strip()
            if script_path:
                cmd = ['python', '-m', 'cProfile', '-s', 'cumulative', script_path]
                run_command(cmd, f"Profiling {script_path}")
        
        elif choice == '7':
            print_section("Cache Management")
            
            cache_choice = get_choice("Cache operation:", [
                ('1', 'Clear pytest cache'),
                ('2', 'Clear Python bytecode (__pycache__)'),
                ('3', 'Clear all caches'),
            ], allow_back=True)
            
            if cache_choice == '1':
                run_command(['rm', '-rf', '.pytest_cache'], "Clearing pytest cache")
            elif cache_choice == '2':
                run_command(['find', '.', '-type', 'd', '-name', '__pycache__', '-exec', 'rm', '-rf', '{}', '+'], 
                           "Clearing Python bytecode")
            elif cache_choice == '3':
                run_command(['rm', '-rf', '.pytest_cache'], "Clearing pytest cache")
                run_command(['find', '.', '-type', 'd', '-name', '__pycache__', '-exec', 'rm', '-rf', '{}', '+'], 
                           "Clearing Python bytecode")
        
        elif choice == '8':
            print_section("Git Operations")
            
            git_choice = get_choice("Git operation:", [
                ('1', 'Status'),
                ('2', 'Diff'),
                ('3', 'Log (last 10 commits)'),
                ('4', 'Branch info'),
                ('5', 'Show unstaged changes'),
            ], allow_back=True)
            
            if git_choice == '1':
                run_command(['git', 'status'], "Git status")
            elif git_choice == '2':
                run_command(['git', 'diff'], "Git diff")
            elif git_choice == '3':
                run_command(['git', 'log', '--oneline', '-10'], "Git log")
            elif git_choice == '4':
                run_command(['git', 'branch', '-v'], "Branch info")
            elif git_choice == '5':
                run_command(['git', 'diff', 'HEAD'], "Unstaged changes")
        
        elif choice == '9':
            print_section("Environment Variables")
            
            env_choice = get_choice("Environment operation:", [
                ('1', 'Show all environment variables'),
                ('2', 'Show specific variable'),
                ('3', 'Set variable (current session)'),
            ], allow_back=True)
            
            if env_choice == '1':
                print("\nEnvironment Variables:")
                for key, value in sorted(os.environ.items()):
                    if any(term in key.upper() for term in ['PYTHON', 'PATH', 'HOME', 'USER']):
                        print(f"  {key} = {value[:100]}")
            elif env_choice == '2':
                var_name = input(f"{Colors.CYAN}Enter variable name: {Colors.ENDC}").strip()
                if var_name:
                    value = os.environ.get(var_name)
                    if value:
                        print(f"\n{var_name} = {value}")
                    else:
                        print_warning(f"{var_name} not set")
            elif env_choice == '3':
                print_warning("Note: Changes only affect current session")
                var_name = input(f"{Colors.CYAN}Variable name: {Colors.ENDC}").strip()
                var_value = input(f"{Colors.CYAN}Variable value: {Colors.ENDC}").strip()
                if var_name and var_value:
                    os.environ[var_name] = var_value
                    print_success(f"Set {var_name} = {var_value}")
        
        elif choice == '10':
            print_section("Custom Command")
            print_warning("Run any Python script or command")
            
            cmd_input = input(f"{Colors.CYAN}Enter command: {Colors.ENDC}").strip()
            if cmd_input:
                if cmd_input.endswith('.py'):
                    run_command(['python', cmd_input], f"Running {cmd_input}")
                else:
                    run_command(cmd_input.split(), f"Running {cmd_input}")
        
        wait_for_key()


def main_menu():
    """Main menu - entry point for the wizard"""
    while True:
        clear_screen()
        print_header("ESP32 AI Radio - Interactive Wizard")
        
        print(f"{Colors.BOLD}Welcome to the ESP32 AI Radio project!{Colors.ENDC}\n")
        print_info("This wizard helps you manage and run the project.\n")
        
        choice = get_choice("What would you like to do?", [
            ('1', 'Initial Setup & Installation'),
            ('2', 'Run Tests'),
            ('3', 'Database Management (ChromaDB)'),
            ('4', 'Generate Broadcast Content'),
            ('5', 'Development Tools'),
            ('6', 'Advanced Tools & Configuration'),
            ('7', 'View Documentation'),
            ('8', 'System Information'),
        ])
        
        if choice is None:
            print_info("Use 'q' to quit")
            continue
        
        if choice == '1':
            setup_wizard()
        elif choice == '2':
            test_menu()
        elif choice == '3':
            database_menu()
        elif choice == '4':
            broadcast_menu()
        elif choice == '5':
            development_menu()
        elif choice == '6':
            advanced_menu()
        elif choice == '7':
            print_section("Documentation")
            print_info("README.md - Project overview and quick start")
            print_info("REPOSITORY_STRUCTURE.md - Detailed structure guide")
            print_info("SCRIPTS_REFERENCE.md - All available scripts")
            print_info("docs/ - Architecture and detailed documentation")
            wait_for_key()
        elif choice == '8':
            print_section("System Information")
            print(f"Python: {sys.version}")
            print(f"Platform: {platform.system()} {platform.release()}")
            print(f"Project Root: {Path.cwd()}")
            deps = check_dependencies()
            print("\nDependencies:")
            for pkg, installed in deps.items():
                status = f"{Colors.GREEN}[+]{Colors.ENDC}" if installed else f"{Colors.RED}[-]{Colors.ENDC}"
                print(f"  {status} {pkg}")
            wait_for_key()


def main():
    """Main entry point with 3-format logging"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ESP32 AI Radio Interactive Wizard')
    parser.add_argument('--quick-test', action='store_true', help='Run quick tests and exit')
    parser.add_argument('--setup', action='store_true', help='Run setup wizard and exit')
    parser.add_argument('--advanced', action='store_true', help='Go directly to advanced menu')
    parser.add_argument('--no-color', action='store_true', help='Disable colored output')
    
    args = parser.parse_args()
    
    if args.no_color:
        Colors.disable()
    
    # Determine wizard mode for logging context
    if args.quick_test:
        context = "Running quick tests via wizard"
        session_name = "wizard_quick_test"
    elif args.setup:
        context = "Running setup wizard"
        session_name = "wizard_setup"
    elif args.advanced:
        context = "Running advanced wizard menu"
        session_name = "wizard_advanced"
    else:
        context = "Interactive wizard session"
        session_name = "wizard"
    
    # Wrap entire wizard operation with 3-format logging
    with capture_output(session_name, context) as session:
        session.log_event("WIZARD_START", {
            "mode": "quick_test" if args.quick_test else "setup" if args.setup else "advanced" if args.advanced else "interactive",
            "no_color": args.no_color
        })
        
        try:
            # Quick actions (bypass menu)
            if args.quick_test:
                result = run_command(['python', 'run_tests.py', 'quick'], "Running quick tests")
                session.log_event("WIZARD_COMPLETE", {"action": "quick_test", "success": result})
                return result
            
            if args.setup:
                setup_wizard()
                session.log_event("WIZARD_COMPLETE", {"action": "setup"})
                return
            
            if args.advanced:
                advanced_menu()
                session.log_event("WIZARD_COMPLETE", {"action": "advanced"})
                return
            
            # Default: show interactive menu
            main_menu()
            session.log_event("WIZARD_COMPLETE", {"action": "interactive"})
            
        except KeyboardInterrupt:
            session.log_event("USER_CANCELLED", {
                "message": "Wizard interrupted by user (Ctrl+C)"
            })
            print(f"\n\n{Colors.YELLOW}[WARNING] Interrupted by user{Colors.ENDC}")
            print(f"\n📝 Wizard session logs:")
            print(f"   {session.log_file}")
            print(f"   {session.metadata_file}")
            print(f"   {session.llm_file}")
            sys.exit(0)
        except Exception as e:
            session.log_event("WIZARD_ERROR", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            print(f"\n{Colors.RED}[ERROR] Wizard error: {e}{Colors.ENDC}")
            raise


if __name__ == '__main__':
    main()
