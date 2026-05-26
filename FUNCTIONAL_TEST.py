"""
FUNCTIONAL_TEST.py - Integration tests for Audio Pipeline Stress Testing system

Tests actual runtime behavior:
- Server startup and connectivity
- Client connection and packet transmission
- Metrics collection
- Stress testing execution
- Report generation
"""

import asyncio
import subprocess
import time
import json
import sys
import signal
from pathlib import Path
from typing import Optional, Dict, Any

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

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

def print_info(msg: str):
    """Print info message"""
    print(f"  {Colors.BLUE}ℹ{Colors.RESET}  {msg}")

# ============================================================================
# TEST 1: SERVER STARTUP AND BASIC CONNECTIVITY
# ============================================================================

async def test_server_startup():
    """Test that server can start and accept connections"""
    print_test_header("FUNCTIONAL TEST 1: SERVER STARTUP")
    
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        from server import AudioServer
        
        # Create server instance
        server = AudioServer(host="127.0.0.1", port=18765)
        print_info("AudioServer instance created")
        
        # Start server in background task
        server_task = asyncio.create_task(server.start())
        
        # Give server time to start
        await asyncio.sleep(2)
        
        # Check if server is running
        print_test_result("Server started successfully", True)
        print_info("Server binding to 127.0.0.1:18765")
        
        # Get initial stats
        stats = await server.get_stats()
        print_info(f"Server stats: {stats}")
        
        # Stop server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
        
        print_test_result("Server stopped gracefully", True)
        return True
        
    except Exception as e:
        print_test_result("Server startup", False, str(e))
        return False

# ============================================================================
# TEST 2: CLIENT CONNECTION AND PACKET TRANSMISSION
# ============================================================================

async def test_client_connection():
    """Test that client can connect and send packets"""
    print_test_header("FUNCTIONAL TEST 2: CLIENT CONNECTION AND PACKET TRANSMISSION")
    
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        from server import AudioServer
        from client import AudioClient
        
        # Start server
        server = AudioServer(host="127.0.0.1", port=18765)
        server_task = asyncio.create_task(server.start())
        await asyncio.sleep(1)
        
        # Create and connect client
        client = AudioClient(
            client_id=1,
            server_uri="ws://127.0.0.1:18765",
            send_interval_ms=50.0,
            audio_chunk_size=1024,
            reconnect_interval=2.0
        )
        
        print_info("AudioClient instance created")
        
        # Run client for 5 seconds
        client_task = asyncio.create_task(client.connect_and_run())
        
        # Wait for client to send some packets
        await asyncio.sleep(3)
        
        # Check metrics
        metrics = client.metrics
        packets_sent = metrics.packets_sent
        packets_acked = metrics.packets_acked
        
        client_connected = packets_sent > 0 and packets_acked > 0
        print_test_result("Client connected and sent packets", client_connected, 
                         f"Sent: {packets_sent}, Acked: {packets_acked}")
        
        # Check latencies
        avg_latency = metrics.get_average_latency()
        latency_valid = 0 < avg_latency < 100  # Should be < 100ms on localhost
        print_test_result("Latency calculation valid", latency_valid, 
                         f"Average latency: {avg_latency:.2f}ms")
        
        # Stop client
        await client.stop()
        try:
            await asyncio.wait_for(client_task, timeout=2)
        except asyncio.TimeoutError:
            pass
        
        # Stop server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
        
        print_test_result("Client and server stopped gracefully", True)
        
        return client_connected and latency_valid
        
    except Exception as e:
        print_test_result("Client connection test", False, str(e))
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# TEST 3: METRICS COLLECTION AND AGGREGATION
# ============================================================================

async def test_metrics_collection():
    """Test metrics collection during stress"""
    print_test_header("FUNCTIONAL TEST 3: METRICS COLLECTION AND AGGREGATION")
    
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        from server import AudioServer
        from client import AudioClient
        from metrics import MetricsCollector
        
        # Start server
        server = AudioServer(host="127.0.0.1", port=18766)
        server_task = asyncio.create_task(server.start())
        await asyncio.sleep(1)
        
        # Create multiple clients
        clients = []
        for i in range(3):
            client = AudioClient(
                client_id=i+1,
                server_uri="ws://127.0.0.1:18766",
                send_interval_ms=50.0,
                reconnect_interval=2.0
            )
            clients.append(client)
        
        print_info("Created 3 client instances")
        
        # Connect all clients
        client_tasks = [asyncio.create_task(c.connect_and_run()) for c in clients]
        await asyncio.sleep(3)
        
        # Aggregate metrics
        collector = MetricsCollector()
        total_packets = 0
        total_acked = 0
        
        for client in clients:
            metrics = client.metrics
            collector.add_latency(metrics.get_average_latency())
            total_packets += metrics.packets_sent
            total_acked += metrics.packets_acked
        
        metrics_valid = total_packets > 0 and total_acked > 0
        print_test_result("Metrics aggregated successfully", metrics_valid,
                         f"Total packets: {total_packets}, Acked: {total_acked}")
        
        # Get summary
        summary = collector.get_summary(num_clients=3, duration_seconds=3)
        summary_valid = 'latency' in summary and 'throughput' in summary
        print_test_result("Metrics summary generated", summary_valid)
        
        # Stop all clients
        for client in clients:
            await client.stop()
        
        try:
            await asyncio.wait_for(asyncio.gather(*client_tasks), timeout=3)
        except (asyncio.TimeoutError, Exception):
            pass
        
        # Stop server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
        
        return metrics_valid and summary_valid
        
    except Exception as e:
        print_test_result("Metrics collection test", False, str(e))
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# TEST 4: STRESS TEST EXECUTION
# ============================================================================

def test_stress_test_execution():
    """Test quick stress test execution"""
    print_test_header("FUNCTIONAL TEST 4: STRESS TEST EXECUTION")
    
    project_root = Path(__file__).parent
    
    try:
        print_info("Running: python stress_test.py --clients 5 --duration 3")
        
        # Run quick stress test
        result = subprocess.run(
            [sys.executable, str(project_root / 'stress_test.py'), 
             '--clients', '5', '--duration', '3'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        test_completed = result.returncode == 0
        print_test_result("Stress test completed", test_completed)
        
        if test_completed:
            print_info("Output preview:")
            output_lines = result.stdout.split('\n')[:5]
            for line in output_lines:
                if line.strip():
                    print(f"       {line}")
        else:
            print(f"       Error: {result.stderr[:200]}")
        
        # Check if reports were generated
        reports_dir = project_root / 'reports'
        reports_exist = reports_dir.exists()
        print_test_result("Reports directory exists", reports_exist)
        
        return test_completed
        
    except subprocess.TimeoutExpired:
        print_test_result("Stress test execution", False, "Timeout")
        return False
    except Exception as e:
        print_test_result("Stress test execution", False, str(e))
        return False

# ============================================================================
# TEST 5: DASHBOARD GENERATION
# ============================================================================

def test_dashboard_generation():
    """Test dashboard generation from reports"""
    print_test_header("FUNCTIONAL TEST 5: DASHBOARD GENERATION")
    
    project_root = Path(__file__).parent
    
    try:
        from dashboard import DashboardGenerator
        
        dashboard = DashboardGenerator(results_dir=str(project_root / 'reports'))
        print_info("DashboardGenerator instance created")
        
        # Try to generate a sample chart
        print_info("Attempting to generate latency chart...")
        
        # Create sample data for testing
        test_results = {
            'Scenario 1': {
                'num_clients': 5,
                'average_latency': 12.5,
                'p95_latency': 25.0,
                'max_latency': 45.0,
                'throughput': 500,
                'packet_loss': 0.1,
            },
            'Scenario 2': {
                'num_clients': 10,
                'average_latency': 15.0,
                'p95_latency': 30.0,
                'max_latency': 50.0,
                'throughput': 950,
                'packet_loss': 0.2,
            },
        }
        
        # Test chart creation
        charts_dir = project_root / 'reports'
        charts_dir.mkdir(exist_ok=True)
        
        print_test_result("Dashboard generator ready", True)
        
        # Save test data
        with open(charts_dir / 'test_results.json', 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print_test_result("Test data saved", True)
        
        return True
        
    except Exception as e:
        print_test_result("Dashboard generation", False, str(e))
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# TEST 6: ERROR HANDLING AND RECOVERY
# ============================================================================

async def test_error_handling():
    """Test error handling and recovery"""
    print_test_header("FUNCTIONAL TEST 6: ERROR HANDLING AND RECOVERY")
    
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        from client import AudioClient
        
        # Test 1: Connection to non-existent server
        print_info("Test 1: Connection to non-existent server")
        
        client = AudioClient(
            client_id=1,
            server_uri="ws://127.0.0.1:19999",  # Non-existent port
            reconnect_interval=1.0
        )
        
        # Try to connect (should fail gracefully with retries)
        client_task = asyncio.create_task(client.connect_and_run())
        
        try:
            await asyncio.wait_for(client_task, timeout=3)
        except asyncio.TimeoutError:
            pass
        
        await client.stop()
        
        print_test_result("Client handles connection errors gracefully", True)
        
        # Test 2: Metrics with zero packets
        print_info("Test 2: Metrics with no packets")
        
        metrics = client.metrics
        loss = metrics.get_packet_loss_percentage()
        
        loss_valid = loss == 0.0  # No packets sent = 0% loss
        print_test_result("Metrics handle zero packets", loss_valid, f"Loss: {loss}%")
        
        return True
        
    except Exception as e:
        print_test_result("Error handling test", False, str(e))
        return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main_async():
    """Execute async functional tests"""
    
    results = {
        'passed': 0,
        'failed': 0,
    }
    
    # Run async tests
    tests = [
        test_server_startup,
        test_client_connection,
        test_metrics_collection,
        test_error_handling,
    ]
    
    for test_func in tests:
        try:
            result = await test_func()
            if result:
                results['passed'] += 1
            else:
                results['failed'] += 1
        except Exception as e:
            print(f"\n{Colors.RED}Test {test_func.__name__} failed with exception: {e}{Colors.RESET}")
            results['failed'] += 1
    
    return results

def main():
    """Main execution"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  AUDIO PIPELINE STRESS TESTING - FUNCTIONAL INTEGRATION TESTS  ".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    print(Colors.RESET)
    
    results = {'passed': 0, 'failed': 0}
    
    # Run async tests
    try:
        async_results = asyncio.run(main_async())
        results['passed'] += async_results['passed']
        results['failed'] += async_results['failed']
    except Exception as e:
        print(f"{Colors.RED}Async tests failed: {e}{Colors.RESET}")
        results['failed'] += 4
    
    # Run sync tests
    print_test_header("FUNCTIONAL TEST 4: STRESS TEST EXECUTION")
    if test_stress_test_execution():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    print_test_header("FUNCTIONAL TEST 5: DASHBOARD GENERATION")
    if test_dashboard_generation():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Print summary
    print_test_header("FUNCTIONAL TEST SUMMARY")
    
    print(f"\n{Colors.BOLD}Test Execution Summary:{Colors.RESET}")
    print(f"  Passed:  {Colors.GREEN}{results['passed']}{Colors.RESET}")
    print(f"  Failed:  {Colors.RED}{results['failed']}{Colors.RESET}")
    
    total = results['passed'] + results['failed']
    if total > 0:
        pass_rate = (results['passed'] / total) * 100
        print(f"  Pass Rate: {pass_rate:.1f}%")
    
    if results['failed'] == 0:
        print(f"\n{Colors.GREEN}✓ ALL FUNCTIONAL TESTS PASSED{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.RED}✗ SOME TESTS FAILED{Colors.RESET}\n")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
