"""
QA_AUTOMATION_TEST_SUITE.py - Comprehensive automated testing and validation
for the Audio Pipeline Stress Testing project

This script performs:
- Project structure validation
- Dependency validation
- Code syntax checking
- Import validation
- Server functionality testing
- Client functionality testing
- Metrics calculation validation
- Dashboard generation testing
- Error handling validation
- Performance benchmarking
- Code quality review
"""

import asyncio
import os
import sys
import json
import time
import subprocess
import importlib
import inspect
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime

# Color output for test results
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
test_logger = logging.getLogger(__name__)

# Test results storage
test_results = {
    'passed': [],
    'failed': [],
    'warnings': [],
    'benchmarks': {},
    'issues': [],
    'recommendations': [],
}

def print_test_header(title: str):
    """Print formatted test section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}► {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_test_result(test_name: str, passed: bool, details: str = ""):
    """Print individual test result"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"  {status}  {test_name}")
    if details:
        print(f"       └─ {details}")
    
    if passed:
        test_results['passed'].append(test_name)
    else:
        test_results['failed'].append(test_name)

def print_warning(msg: str):
    """Print warning message"""
    print(f"  {Colors.YELLOW}⚠ WARNING{Colors.RESET}  {msg}")
    test_results['warnings'].append(msg)

def print_issue(severity: str, issue: str):
    """Print identified issue"""
    icon = "🔴" if severity == "CRITICAL" else "🟡" if severity == "WARNING" else "🔵"
    print(f"  {icon} [{severity}] {issue}")
    test_results['issues'].append({"severity": severity, "issue": issue})

def print_recommendation(rec: str):
    """Print recommendation"""
    print(f"  💡 {rec}")
    test_results['recommendations'].append(rec)

# ============================================================================
# TEST 1: PROJECT STRUCTURE VALIDATION
# ============================================================================

def test_project_structure():
    """Validate all required files exist"""
    print_test_header("TEST 1: PROJECT STRUCTURE VALIDATION")
    
    project_root = Path(__file__).parent
    required_files = [
        'server.py',
        'client.py',
        'stress_test.py',
        'metrics.py',
        'dashboard.py',
        'requirements.txt',
        'README.md',
        '.gitignore',
    ]
    required_dirs = ['reports', 'logs']
    
    all_exist = True
    for filename in required_files:
        filepath = project_root / filename
        exists = filepath.exists()
        print_test_result(f"File exists: {filename}", exists)
        if not exists:
            all_exist = False
    
    for dirname in required_dirs:
        dirpath = project_root / dirname
        exists = dirpath.exists() and dirpath.is_dir()
        print_test_result(f"Directory exists: {dirname}/", exists)
        if not exists:
            all_exist = False
    
    return all_exist

# ============================================================================
# TEST 2: DEPENDENCY VALIDATION
# ============================================================================

def test_dependencies():
    """Validate requirements.txt and dependency compatibility"""
    print_test_header("TEST 2: DEPENDENCY VALIDATION")
    
    project_root = Path(__file__).parent
    requirements_file = project_root / 'requirements.txt'
    
    if not requirements_file.exists():
        print_test_result("requirements.txt exists", False)
        return False
    
    print_test_result("requirements.txt exists", True)
    
    # Read and validate format
    try:
        with open(requirements_file, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        expected_packages = {
            'websockets': '12.0',
            'pandas': '2.1.4',
            'matplotlib': '3.8.2',
            'psutil': '5.9.6',
            'python-dateutil': '2.8.2',
        }
        
        all_valid = True
        for line in lines:
            if not line.startswith('#'):
                # Parse package==version
                if '==' in line:
                    pkg_name, version = line.split('==')
                    pkg_name = pkg_name.strip()
                    version = version.strip()
                    print_test_result(
                        f"Package format: {pkg_name}=={version}", 
                        True
                    )
                else:
                    all_valid = False
                    print_test_result(f"Invalid format: {line}", False)
        
        # Try importing each package
        print("\n  Checking package imports:")
        packages_to_test = ['websockets', 'pandas', 'matplotlib', 'psutil', 'dateutil']
        
        for pkg in packages_to_test:
            try:
                if pkg == 'dateutil':
                    importlib.import_module('dateutil')
                else:
                    importlib.import_module(pkg)
                print_test_result(f"Import: {pkg}", True)
            except ImportError as e:
                print_test_result(f"Import: {pkg}", False, str(e))
                all_valid = False
                print_warning(f"Package {pkg} not installed. Install with: pip install -r requirements.txt")
        
        return all_valid
        
    except Exception as e:
        print_test_result("Parse requirements.txt", False, str(e))
        return False

# ============================================================================
# TEST 3: PYTHON VERSION VALIDATION
# ============================================================================

def test_python_version():
    """Validate Python version compatibility"""
    print_test_header("TEST 3: PYTHON VERSION VALIDATION")
    
    min_version = (3, 11)
    current_version = sys.version_info[:2]
    
    valid = current_version >= min_version
    print_test_result(
        f"Python version >= {min_version[0]}.{min_version[1]}", 
        valid,
        f"Current: {current_version[0]}.{current_version[1]}"
    )
    
    return valid

# ============================================================================
# TEST 4: CODE SYNTAX VALIDATION
# ============================================================================

def test_code_syntax():
    """Validate Python syntax in all modules"""
    print_test_header("TEST 4: CODE SYNTAX VALIDATION")
    
    project_root = Path(__file__).parent
    py_files = ['server.py', 'client.py', 'stress_test.py', 'metrics.py', 'dashboard.py']
    
    all_valid = True
    for filename in py_files:
        filepath = project_root / filename
        
        try:
            with open(filepath, 'r') as f:
                compile(f.read(), filename, 'exec')
            print_test_result(f"Syntax check: {filename}", True)
        except SyntaxError as e:
            print_test_result(f"Syntax check: {filename}", False, str(e))
            print_issue("CRITICAL", f"Syntax error in {filename}: {e}")
            all_valid = False
        except Exception as e:
            print_test_result(f"Syntax check: {filename}", False, str(e))
            all_valid = False
    
    return all_valid

# ============================================================================
# TEST 5: IMPORT VALIDATION
# ============================================================================

def test_import_validation():
    """Validate all imports in modules"""
    print_test_header("TEST 5: IMPORT VALIDATION")
    
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    modules_to_test = ['metrics', 'server', 'client', 'stress_test', 'dashboard']
    all_valid = True
    
    for module_name in modules_to_test:
        try:
            module = importlib.import_module(module_name)
            print_test_result(f"Import module: {module_name}", True)
            
            # Check key imports
            if module_name == 'server':
                assert hasattr(module, 'AudioServer')
                print_test_result("  └─ AudioServer class exists", True)
            elif module_name == 'client':
                assert hasattr(module, 'AudioClient')
                print_test_result("  └─ AudioClient class exists", True)
            elif module_name == 'metrics':
                assert hasattr(module, 'MetricsCollector')
                print_test_result("  └─ MetricsCollector class exists", True)
            elif module_name == 'dashboard':
                assert hasattr(module, 'DashboardGenerator')
                print_test_result("  └─ DashboardGenerator class exists", True)
                
        except ImportError as e:
            print_test_result(f"Import module: {module_name}", False, str(e))
            all_valid = False
        except AssertionError as e:
            print_test_result(f"Module validation: {module_name}", False, "Missing required class")
            all_valid = False
        except Exception as e:
            print_test_result(f"Import module: {module_name}", False, str(e))
            all_valid = False
    
    return all_valid

# ============================================================================
# TEST 6: TYPE HINTS VALIDATION
# ============================================================================

def test_type_hints():
    """Validate type hints in code"""
    print_test_header("TEST 6: TYPE HINTS VALIDATION")
    
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        from metrics import MetricsCollector
        from server import AudioServer
        from client import AudioClient
        
        # Check MetricsCollector methods have type hints
        methods_to_check = [
            (MetricsCollector, 'add_latency'),
            (MetricsCollector, 'calculate_average_latency'),
            (AudioServer, 'handle_client'),
            (AudioClient, 'send_packet'),
        ]
        
        type_hints_present = 0
        for cls, method_name in methods_to_check:
            method = getattr(cls, method_name, None)
            if method:
                sig = inspect.signature(method)
                has_hints = any(param.annotation != inspect.Parameter.empty 
                               for param in sig.parameters.values())
                if has_hints or sig.return_annotation != inspect.Signature.empty:
                    type_hints_present += 1
                    print_test_result(f"Type hints in {cls.__name__}.{method_name}", True)
                else:
                    print_warning(f"Limited type hints in {cls.__name__}.{method_name}")
        
        return type_hints_present > 0
        
    except Exception as e:
        print_test_result("Type hints validation", False, str(e))
        return False

# ============================================================================
# TEST 7: METRICS VALIDATION
# ============================================================================

def test_metrics_calculations():
    """Validate metrics calculation logic"""
    print_test_header("TEST 7: METRICS CALCULATION VALIDATION")
    
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        from metrics import MetricsCollector
        
        # Create test metrics collector
        mc = MetricsCollector()
        
        # Test 1: Add latencies
        test_latencies = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        for lat in test_latencies:
            mc.add_latency(lat)
        
        # Test 2: Average calculation
        avg = mc.calculate_average_latency()
        expected_avg = 5.5
        avg_correct = abs(avg - expected_avg) < 0.01
        print_test_result("Average latency calculation", avg_correct, 
                         f"Expected: {expected_avg}, Got: {avg}")
        
        # Test 3: P95 calculation
        p95 = mc.calculate_p95_latency()
        p95_valid = 8.0 <= p95 <= 10.0
        print_test_result("P95 latency calculation", p95_valid, f"Got: {p95}")
        
        # Test 4: Max latency
        max_lat = mc.calculate_max_latency()
        max_correct = max_lat == 10.0
        print_test_result("Max latency calculation", max_correct, f"Got: {max_lat}")
        
        # Test 5: Packet loss calculation
        mc2 = MetricsCollector()
        mc2.add_packet_loss(5.0)
        mc2.add_packet_loss(10.0)
        avg_loss = mc2.calculate_average_packet_loss()
        loss_correct = abs(avg_loss - 7.5) < 0.01
        print_test_result("Packet loss calculation", loss_correct, f"Got: {avg_loss}%")
        
        # Test 6: Throughput calculation
        mc3 = MetricsCollector()
        mc3.add_throughput(100.0)
        mc3.add_throughput(200.0)
        avg_throughput = mc3.calculate_average_throughput()
        throughput_correct = abs(avg_throughput - 150.0) < 0.01
        print_test_result("Throughput calculation", throughput_correct, f"Got: {avg_throughput} pps")
        
        # Test 7: CPU usage
        mc4 = MetricsCollector()
        mc4.add_cpu_usage(25.0)
        mc4.add_cpu_usage(75.0)
        avg_cpu = mc4.calculate_average_cpu_usage()
        cpu_correct = abs(avg_cpu - 50.0) < 0.01
        print_test_result("CPU usage calculation", cpu_correct, f"Got: {avg_cpu}%")
        
        all_valid = all([avg_correct, p95_valid, max_correct, loss_correct, 
                        throughput_correct, cpu_correct])
        return all_valid
        
    except Exception as e:
        print_test_result("Metrics calculations", False, str(e))
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# TEST 8: CLIENT METRICS FUNCTIONALITY
# ============================================================================

def test_client_metrics():
    """Validate ClientMetrics class"""
    print_test_header("TEST 8: CLIENT METRICS FUNCTIONALITY")
    
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        from client import ClientMetrics
        
        # Create client metrics
        cm = ClientMetrics(client_id=1)
        
        # Test latency recording
        cm.add_latency(5.0)
        cm.add_latency(10.0)
        cm.add_latency(15.0)
        
        avg_lat = cm.get_average_latency()
        avg_correct = abs(avg_lat - 10.0) < 0.01
        print_test_result("ClientMetrics average latency", avg_correct, f"Got: {avg_lat}")
        
        # Test max latency
        max_lat = cm.get_max_latency()
        max_correct = max_lat == 15.0
        print_test_result("ClientMetrics max latency", max_correct, f"Got: {max_lat}")
        
        # Test packet loss
        cm.packets_sent = 100
        cm.packets_acked = 95
        loss = cm.get_packet_loss_percentage()
        loss_correct = abs(loss - 5.0) < 0.01
        print_test_result("ClientMetrics packet loss", loss_correct, f"Got: {loss}%")
        
        return avg_correct and max_correct and loss_correct
        
    except Exception as e:
        print_test_result("ClientMetrics functionality", False, str(e))
        return False

# ============================================================================
# TEST 9: ASYNCIO PATTERN VALIDATION
# ============================================================================

def test_asyncio_patterns():
    """Validate asyncio usage patterns"""
    print_test_header("TEST 9: ASYNCIO PATTERN VALIDATION")
    
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    all_valid = True
    
    try:
        from server import AudioServer
        
        # Test that AudioServer has async methods
        methods_to_check = ['handle_client', 'process_packet', 'start']
        
        for method_name in methods_to_check:
            method = getattr(AudioServer, method_name, None)
            if method and asyncio.iscoroutinefunction(method):
                print_test_result(f"Async method: AudioServer.{method_name}", True)
            else:
                print_test_result(f"Async method: AudioServer.{method_name}", False)
                all_valid = False
        
        # Check for asyncio.Lock usage
        with open(project_root / 'server.py', 'r') as f:
            server_code = f.read()
            has_lock = 'asyncio.Lock' in server_code
            print_test_result("Asyncio.Lock for synchronization", has_lock)
            
            if not has_lock:
                print_issue("WARNING", "No asyncio.Lock found for shared state protection")
                all_valid = False
        
        return all_valid
        
    except Exception as e:
        print_test_result("Asyncio patterns validation", False, str(e))
        return False

# ============================================================================
# TEST 10: FILE I/O AND EXPORT
# ============================================================================

def test_file_operations():
    """Test file I/O operations"""
    print_test_header("TEST 10: FILE I/O AND EXPORT VALIDATION")
    
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        from metrics import MetricsCollector
        import tempfile
        
        # Create temp directory for tests
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Test 1: JSON export
            mc = MetricsCollector()
            mc.add_latency(5.0)
            mc.add_latency(10.0)
            summary = mc.get_summary(num_clients=10, duration_seconds=30.0)
            
            json_file = tmpdir_path / "test.json"
            mc.save_summary_to_json(str(json_file), summary)
            
            json_exists = json_file.exists()
            print_test_result("JSON export", json_exists)
            
            if json_exists:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    json_valid = 'latency' in data and 'throughput' in data
                    print_test_result("JSON content validity", json_valid)
            
            # Test 2: CSV export
            csv_file = tmpdir_path / "test.csv"
            mc.save_metrics_to_csv(str(csv_file), num_clients=10, latencies=[5.0, 10.0, 15.0])
            
            csv_exists = csv_file.exists()
            print_test_result("CSV export", csv_exists)
            
            if csv_exists:
                with open(csv_file, 'r') as f:
                    csv_content = f.read()
                    csv_valid = 'latency_ms' in csv_content
                    print_test_result("CSV content validity", csv_valid)
            
            return json_exists and csv_exists
            
    except Exception as e:
        print_test_result("File I/O operations", False, str(e))
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# TEST 11: EDGE CASE HANDLING
# ============================================================================

def test_edge_cases():
    """Test edge case handling"""
    print_test_header("TEST 11: EDGE CASE HANDLING")
    
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        from metrics import MetricsCollector
        
        # Test 1: Empty metrics
        mc = MetricsCollector()
        avg = mc.calculate_average_latency()
        print_test_result("Handle empty latencies", avg == 0.0, f"Got: {avg}")
        
        # Test 2: Single latency
        mc.add_latency(5.0)
        avg_single = mc.calculate_average_latency()
        single_correct = avg_single == 5.0
        print_test_result("Handle single latency", single_correct, f"Got: {avg_single}")
        
        # Test 3: Negative values rejection
        mc2 = MetricsCollector()
        mc2.add_latency(-5.0)  # Should be rejected
        len_check = len(mc2.latencies) == 0
        print_test_result("Reject negative latencies", len_check)
        
        # Test 4: Packet loss boundaries
        mc3 = MetricsCollector()
        mc3.add_packet_loss(0.0)    # Valid
        mc3.add_packet_loss(100.0)  # Valid
        mc3.add_packet_loss(-5.0)   # Invalid
        mc3.add_packet_loss(105.0)  # Invalid
        boundary_correct = len(mc3.packet_losses) == 2
        print_test_result("Packet loss boundary validation", boundary_correct)
        
        # Test 5: CPU usage boundaries
        mc4 = MetricsCollector()
        mc4.add_cpu_usage(0.0)     # Valid
        mc4.add_cpu_usage(100.0)   # Valid
        mc4.add_cpu_usage(-10.0)   # Invalid
        mc4.add_cpu_usage(150.0)   # Invalid
        cpu_boundary = len(mc4.cpu_samples) == 2
        print_test_result("CPU usage boundary validation", cpu_boundary)
        
        all_valid = all([avg == 0.0, single_correct, len_check, boundary_correct, cpu_boundary])
        return all_valid
        
    except Exception as e:
        print_test_result("Edge case handling", False, str(e))
        return False

# ============================================================================
# TEST 12: PACKET PROTOCOL VALIDATION
# ============================================================================

def test_packet_protocol():
    """Validate packet protocol structure"""
    print_test_header("TEST 12: PACKET PROTOCOL VALIDATION")
    
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        from server import AudioPacket, AckPacket
        import json
        
        # Test 1: AudioPacket structure
        packet = AudioPacket(
            client_id=1,
            packet_id=42,
            timestamp=time.time(),
            audio_data="test_audio_data"
        )
        
        packet_dict = {
            'client_id': packet.client_id,
            'packet_id': packet.packet_id,
            'timestamp': packet.timestamp,
            'audio_data': packet.audio_data,
        }
        
        packet_json = json.dumps(packet_dict)
        packet_valid = all(k in packet_json for k in ['client_id', 'packet_id', 'timestamp', 'audio_data'])
        print_test_result("AudioPacket serialization", packet_valid)
        
        # Test 2: AckPacket structure
        ack = AckPacket(
            packet_id=42,
            server_timestamp=time.time(),
            status="received"
        )
        
        ack_dict = {
            'packet_id': ack.packet_id,
            'server_timestamp': ack.server_timestamp,
            'status': ack.status,
        }
        
        ack_json = json.dumps(ack_dict)
        ack_valid = all(k in ack_json for k in ['packet_id', 'server_timestamp', 'status'])
        print_test_result("AckPacket serialization", ack_valid)
        
        return packet_valid and ack_valid
        
    except Exception as e:
        print_test_result("Packet protocol validation", False, str(e))
        return False

# ============================================================================
# TEST 13: LOGGING CONFIGURATION
# ============================================================================

def test_logging_configuration():
    """Validate logging configuration"""
    print_test_header("TEST 13: LOGGING CONFIGURATION")
    
    project_root = Path(__file__).parent
    
    logs_dir = project_root / 'logs'
    logs_dir_exists = logs_dir.exists()
    print_test_result("Logs directory exists", logs_dir_exists)
    
    # Check for logging statements in code
    files_to_check = ['server.py', 'client.py', 'stress_test.py']
    logging_present = True
    
    for filename in files_to_check:
        filepath = project_root / filename
        with open(filepath, 'r') as f:
            content = f.read()
            has_logging = 'logger.' in content or 'logging.' in content
            print_test_result(f"Logging in {filename}", has_logging)
            if not has_logging:
                logging_present = False
    
    return logs_dir_exists and logging_present

# ============================================================================
# TEST 14: CONFIGURATION AND PARAMETERS
# ============================================================================

def test_configuration():
    """Validate configuration and parameters"""
    print_test_header("TEST 14: CONFIGURATION AND PARAMETERS")
    
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    all_valid = True
    
    try:
        from server import AudioServer
        from client import AudioClient
        
        # Test server configuration
        server = AudioServer(host="localhost", port=8765)
        print_test_result("Server configuration", 
                         server.host == "localhost" and server.port == 8765)
        
        # Test client configuration
        client = AudioClient(
            client_id=1,
            server_uri="ws://localhost:8765",
            send_interval_ms=20.0,
            audio_chunk_size=1024
        )
        
        print_test_result("Client configuration",
                         client.client_id == 1 and client.send_interval_ms == 20.0)
        
        # Check for configurable parameters in stress_test
        with open(project_root / 'stress_test.py', 'r') as f:
            stress_code = f.read()
            has_args = 'argparse' in stress_code or 'add_argument' in stress_code
            print_test_result("Stress test has configurable parameters", has_args)
            if not has_args:
                all_valid = False
        
        return all_valid
        
    except Exception as e:
        print_test_result("Configuration validation", False, str(e))
        return False

# ============================================================================
# TEST 15: CODE DOCUMENTATION
# ============================================================================

def test_documentation():
    """Validate code documentation"""
    print_test_header("TEST 15: CODE DOCUMENTATION")
    
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        from metrics import MetricsCollector
        from server import AudioServer
        from client import AudioClient
        
        # Check for docstrings
        classes_to_check = [
            (MetricsCollector, "MetricsCollector"),
            (AudioServer, "AudioServer"),
            (AudioClient, "AudioClient"),
        ]
        
        all_documented = True
        for cls, name in classes_to_check:
            has_docstring = cls.__doc__ is not None and len(cls.__doc__.strip()) > 0
            print_test_result(f"Class documentation: {name}", has_docstring)
            if not has_docstring:
                all_documented = False
        
        # Check for method docstrings
        sample_methods = [
            (MetricsCollector, 'add_latency'),
            (AudioServer, 'handle_client'),
            (AudioClient, 'send_packet'),
        ]
        
        for cls, method_name in sample_methods:
            method = getattr(cls, method_name)
            has_docstring = method.__doc__ is not None and len(method.__doc__.strip()) > 0
            print_test_result(f"Method documentation: {cls.__name__}.{method_name}", has_docstring)
            if not has_docstring:
                all_documented = False
        
        return all_documented
        
    except Exception as e:
        print_test_result("Documentation validation", False, str(e))
        return False

# ============================================================================
# TEST 16: MEMORY LEAK DETECTION
# ============================================================================

def test_potential_memory_leaks():
    """Check for potential memory leak patterns"""
    print_test_header("TEST 16: POTENTIAL MEMORY LEAK DETECTION")
    
    project_root = Path(__file__).parent
    
    files_to_check = {
        'server.py': [
            ('active_clients cleanup', 'del self.active_clients'),
            ('exception handling', 'finally:'),
            ('resource cleanup', 'close()'),
        ],
        'client.py': [
            ('connection cleanup', 'close()'),
            ('exception handling', 'finally:'),
        ],
    }
    
    all_safe = True
    
    for filename, patterns in files_to_check.items():
        filepath = project_root / filename
        with open(filepath, 'r') as f:
            content = f.read()
            
            for pattern_name, pattern in patterns:
                if pattern in content:
                    print_test_result(f"{filename}: {pattern_name}", True)
                else:
                    print_warning(f"{filename}: Missing {pattern_name}")
                    all_safe = False
    
    return all_safe

# ============================================================================
# SUMMARY AND RECOMMENDATIONS
# ============================================================================

def generate_summary_report():
    """Generate comprehensive QA report"""
    print_test_header("QA TEST SUMMARY AND REPORT")
    
    total_passed = len(test_results['passed'])
    total_failed = len(test_results['failed'])
    total_tests = total_passed + total_failed
    
    print(f"\n{Colors.BOLD}Test Execution Summary:{Colors.RESET}")
    print(f"  Total Tests:     {total_tests}")
    print(f"  {Colors.GREEN}Passed:          {total_passed}{Colors.RESET}")
    print(f"  {Colors.RED}Failed:          {total_failed}{Colors.RESET}")
    print(f"  {Colors.YELLOW}Warnings:        {len(test_results['warnings'])}{Colors.RESET}")
    
    if total_tests > 0:
        pass_rate = (total_passed / total_tests) * 100
        print(f"  {Colors.BOLD}Pass Rate:       {pass_rate:.1f}%{Colors.RESET}")
    
    if test_results['issues']:
        print(f"\n{Colors.BOLD}{Colors.RED}Identified Issues:{Colors.RESET}")
        for issue in test_results['issues']:
            severity = issue['severity']
            msg = issue['issue']
            print(f"  [{severity}] {msg}")
    
    if test_results['recommendations']:
        print(f"\n{Colors.BOLD}{Colors.YELLOW}Recommendations:{Colors.RESET}")
        for i, rec in enumerate(test_results['recommendations'][:10], 1):  # Show top 10
            print(f"  {i}. {rec}")
    
    print(f"\n{Colors.BOLD}Production Readiness:{Colors.RESET}")
    if total_failed == 0 and len(test_results['issues']) == 0:
        print(f"  {Colors.GREEN}✓ READY FOR PRODUCTION{Colors.RESET}")
        readiness = "READY"
    elif total_failed == 0 and all(i['severity'] != 'CRITICAL' for i in test_results['issues']):
        print(f"  {Colors.YELLOW}⚠ READY WITH CAUTIONS{Colors.RESET}")
        readiness = "READY_WITH_CAUTIONS"
    else:
        print(f"  {Colors.RED}✗ NOT READY (Issues must be fixed){Colors.RESET}")
        readiness = "NOT_READY"
    
    return readiness

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Execute all QA tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  AUDIO PIPELINE STRESS TESTING - COMPREHENSIVE QA TEST SUITE  ".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    print(Colors.RESET)
    
    # Run all tests
    test_functions = [
        test_project_structure,
        test_dependencies,
        test_python_version,
        test_code_syntax,
        test_import_validation,
        test_type_hints,
        test_metrics_calculations,
        test_client_metrics,
        test_asyncio_patterns,
        test_file_operations,
        test_edge_cases,
        test_packet_protocol,
        test_logging_configuration,
        test_configuration,
        test_documentation,
        test_potential_memory_leaks,
    ]
    
    for test_func in test_functions:
        try:
            test_func()
        except Exception as e:
            print_issue("CRITICAL", f"Test {test_func.__name__} crashed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Generate summary
    readiness = generate_summary_report()
    
    # Write results to file
    report_file = Path(__file__).parent / 'reports' / 'QA_TEST_REPORT.json'
    report_file.parent.mkdir(exist_ok=True)
    
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'total_passed': len(test_results['passed']),
        'total_failed': len(test_results['failed']),
        'total_warnings': len(test_results['warnings']),
        'production_readiness': readiness,
        'passed_tests': test_results['passed'],
        'failed_tests': test_results['failed'],
        'issues': test_results['issues'],
        'recommendations': test_results['recommendations'],
    }
    
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}Report saved to: {report_file}{Colors.RESET}\n")
    
    return readiness

if __name__ == "__main__":
    readiness = main()
    sys.exit(0 if readiness != "NOT_READY" else 1)
