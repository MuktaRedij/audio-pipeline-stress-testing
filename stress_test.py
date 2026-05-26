"""
stress_test.py - Orchestrates audio pipeline stress testing
Runs multiple concurrent clients, collects metrics, generates reports
"""

import asyncio
import json
import logging
import psutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from client import AudioClient, ClientMetrics
from metrics import MetricsCollector

# Configure logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "stress_test.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class StressTestOrchestrator:
    """Orchestrates stress testing scenarios"""

    def __init__(
        self,
        server_uri: str = "ws://localhost:8765",
        results_dir: str = "reports",
    ):
        self.server_uri = server_uri
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.process = psutil.Process()

    async def run_stress_test(
        self,
        num_clients: int,
        duration_seconds: float,
        send_interval_ms: float = 20.0,
    ) -> Tuple[MetricsCollector, Dict]:
        """
        Run a stress test with specified parameters
        
        Args:
            num_clients: Number of concurrent clients
            duration_seconds: Duration of the test
            send_interval_ms: Interval between packet sends (in milliseconds)
            
        Returns:
            Tuple of (MetricsCollector, test_summary)
        """
        logger.info(
            f"Starting stress test: {num_clients} clients for {duration_seconds}s"
        )

        # Create clients
        clients = [
            AudioClient(
                client_id=i,
                server_uri=self.server_uri,
                send_interval_ms=send_interval_ms,
            )
            for i in range(num_clients)
        ]

        # Start monitoring
        monitor_task = asyncio.create_task(
            self._monitor_resources(duration_seconds)
        )

        # Create and run client tasks
        client_tasks = [
            asyncio.create_task(client.connect_and_run()) for client in clients
        ]

        # Run for specified duration
        test_start = time.time()
        await asyncio.sleep(duration_seconds)

        # Stop all clients
        logger.info("Stopping all clients...")
        for client in clients:
            await client.stop()

        # Wait for tasks to complete
        await asyncio.gather(*client_tasks, return_exceptions=True)
        monitor_task.cancel()

        test_duration = time.time() - test_start

        # Collect metrics
        metrics_collector = MetricsCollector()
        resource_samples = await monitor_task

        for client in clients:
            for latency in client.metrics.latencies:
                metrics_collector.add_latency(latency)
            
            packets_sent = client.metrics.packets_sent
            packets_acked = client.metrics.packets_acked
            
            if packets_sent > 0:
                loss_pct = (
                    (packets_sent - packets_acked) / packets_sent
                ) * 100
                metrics_collector.add_packet_loss(loss_pct)
            
            if test_duration > 0:
                throughput = packets_acked / test_duration
                metrics_collector.add_throughput(throughput)

        # Add resource metrics
        for cpu, mem, active_clients in resource_samples:
            metrics_collector.add_cpu_usage(cpu)
            metrics_collector.add_memory_usage(mem)
            metrics_collector.add_active_clients(num_clients)

        # Generate summary
        summary = metrics_collector.get_summary(num_clients, test_duration)

        # Log summary
        logger.info("=" * 60)
        logger.info(f"Test Summary for {num_clients} clients:")
        logger.info("=" * 60)
        logger.info(f"Duration: {test_duration:.2f}s")
        logger.info(
            f"Latency - Avg: {summary['latency']['avg_ms']}ms, "
            f"P95: {summary['latency']['p95_ms']}ms, "
            f"Max: {summary['latency']['max_ms']}ms"
        )
        logger.info(
            f"Throughput: {summary['throughput']['avg_packets_per_sec']} pps"
        )
        logger.info(
            f"Packet Loss: {summary['packet_loss']['avg_percentage']}%"
        )
        logger.info(
            f"CPU: Avg {summary['cpu']['avg_percent']}%, "
            f"Max {summary['cpu']['max_percent']}%"
        )
        logger.info(
            f"Memory: Avg {summary['memory']['avg_mb']}MB, "
            f"Max {summary['memory']['max_mb']}MB"
        )
        logger.info("=" * 60)

        return metrics_collector, summary

    async def _monitor_resources(
        self, duration_seconds: float
    ) -> List[Tuple[float, float, int]]:
        """
        Monitor CPU and memory usage during test
        
        Returns:
            List of (cpu_percent, memory_mb, active_clients) tuples
        """
        samples = []
        interval = 1.0  # Sample every 1 second

        try:
            for _ in range(int(duration_seconds)):
                cpu_percent = self.process.cpu_percent(interval=None)
                memory_mb = self.process.memory_info().rss / 1024 / 1024
                
                samples.append((cpu_percent, memory_mb, 0))
                await asyncio.sleep(interval)
        except Exception as e:
            logger.warning(f"Error monitoring resources: {e}")

        return samples

    async def run_scenario_suite(self) -> None:
        """Run complete stress test scenarios"""
        scenarios = [
            (10, 30),
            (50, 30),
            (100, 30),
            (500, 60),
        ]

        all_results = []

        for num_clients, duration in scenarios:
            try:
                metrics, summary = await self.run_stress_test(
                    num_clients=num_clients,
                    duration_seconds=duration,
                )

                all_results.append(summary)

                # Save metrics for this scenario
                scenario_dir = self.results_dir / f"scenario_{num_clients}_clients"
                scenario_dir.mkdir(exist_ok=True)

                # Save summary
                summary_file = scenario_dir / "summary.json"
                metrics.save_summary_to_json(str(summary_file), summary)
                logger.info(f"Saved summary to {summary_file}")

                # Save detailed metrics
                latencies_file = scenario_dir / "latencies.csv"
                metrics.save_metrics_to_csv(
                    str(latencies_file),
                    num_clients=num_clients,
                )
                logger.info(f"Saved latencies to {latencies_file}")

            except Exception as e:
                logger.error(f"Error in scenario {num_clients} clients: {e}")

        # Save combined results
        if all_results:
            combined_file = self.results_dir / "all_scenarios.json"
            with open(combined_file, "w") as f:
                json.dump(all_results, f, indent=2)
            logger.info(f"Saved combined results to {combined_file}")

    def print_summary_table(
        self, results: List[Dict]
    ) -> None:
        """Print a nice summary table"""
        print("\n" + "=" * 100)
        print("STRESS TEST RESULTS SUMMARY")
        print("=" * 100)
        print(
            f"{'Clients':<10} {'Duration':<12} {'Avg Lat':<12} {'P95 Lat':<12} "
            f"{'Throughput':<15} {'Loss %':<10} {'CPU %':<10} {'Memory MB':<12}"
        )
        print("-" * 100)

        for result in results:
            print(
                f"{result['num_clients']:<10} "
                f"{result['duration_seconds']:<12.2f} "
                f"{result['latency']['avg_ms']:<12} "
                f"{result['latency']['p95_ms']:<12} "
                f"{result['throughput']['avg_packets_per_sec']:<15} "
                f"{result['packet_loss']['avg_percentage']:<10} "
                f"{result['cpu']['avg_percent']:<10} "
                f"{result['memory']['avg_mb']:<12}"
            )

        print("=" * 100 + "\n")


async def main():
    """Main entry point for stress testing"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Audio Pipeline Stress Testing"
    )
    parser.add_argument(
        "--server",
        default="ws://localhost:8765",
        help="Server URI (default: ws://localhost:8765)",
    )
    parser.add_argument(
        "--clients",
        type=int,
        help="Number of concurrent clients (if not specified, run full suite)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Test duration in seconds (default: 30)",
    )
    parser.add_argument(
        "--results-dir",
        default="reports",
        help="Results directory (default: reports)",
    )

    args = parser.parse_args()

    orchestrator = StressTestOrchestrator(
        server_uri=args.server,
        results_dir=args.results_dir,
    )

    try:
        if args.clients:
            # Run single test with specified client count
            logger.info(
                f"Running single test: {args.clients} clients "
                f"for {args.duration}s"
            )
            metrics, summary = await orchestrator.run_stress_test(
                num_clients=args.clients,
                duration_seconds=args.duration,
            )
            orchestrator.print_summary_table([summary])
        else:
            # Run full scenario suite
            logger.info("Running full scenario suite...")
            await orchestrator.run_scenario_suite()
            logger.info("Scenario suite completed!")

    except KeyboardInterrupt:
        logger.info("Stress test interrupted by user")
    except Exception as e:
        logger.error(f"Stress test error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
