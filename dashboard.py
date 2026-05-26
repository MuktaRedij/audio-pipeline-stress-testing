"""
dashboard.py - Generates visualization dashboards for stress test results
Creates matplotlib charts for latency, throughput, and packet loss
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DashboardGenerator:
    """Generates visualization dashboards from test results"""

    def __init__(self, results_dir: str = "reports"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)

    def load_scenario_results(
        self, scenarios_file: str
    ) -> List[Dict]:
        """Load all scenario results from JSON file"""
        try:
            with open(scenarios_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading scenarios: {e}")
            return []

    def load_latencies_csv(
        self, csv_file: str
    ) -> pd.DataFrame:
        """Load latency data from CSV"""
        try:
            return pd.read_csv(csv_file)
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            return pd.DataFrame()

    def create_latency_vs_clients_chart(
        self,
        results: List[Dict],
        output_file: Optional[str] = None,
    ) -> None:
        """Create latency vs number of clients chart"""
        if not results:
            logger.warning("No results to plot")
            return

        clients = [r["num_clients"] for r in results]
        avg_latencies = [r["latency"]["avg_ms"] for r in results]
        p95_latencies = [r["latency"]["p95_ms"] for r in results]
        max_latencies = [r["latency"]["max_ms"] for r in results]

        fig, ax = plt.subplots(figsize=(12, 7))

        ax.plot(
            clients,
            avg_latencies,
            marker="o",
            linewidth=2,
            markersize=8,
            label="Average Latency",
            color="#1f77b4",
        )
        ax.plot(
            clients,
            p95_latencies,
            marker="s",
            linewidth=2,
            markersize=8,
            label="P95 Latency",
            color="#ff7f0e",
        )
        ax.plot(
            clients,
            max_latencies,
            marker="^",
            linewidth=2,
            markersize=8,
            label="Max Latency",
            color="#d62728",
        )

        ax.set_xlabel("Number of Concurrent Clients", fontsize=12, fontweight="bold")
        ax.set_ylabel("Latency (milliseconds)", fontsize=12, fontweight="bold")
        ax.set_title("Latency vs Number of Concurrent Clients", fontsize=14, fontweight="bold")
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.set_xscale("log")

        plt.tight_layout()

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            logger.info(f"Saved latency chart to {output_file}")
        else:
            plt.show()

        plt.close()

    def create_throughput_chart(
        self,
        results: List[Dict],
        output_file: Optional[str] = None,
    ) -> None:
        """Create throughput vs clients chart"""
        if not results:
            logger.warning("No results to plot")
            return

        clients = [r["num_clients"] for r in results]
        throughputs = [
            r["throughput"]["avg_packets_per_sec"] for r in results
        ]

        fig, ax = plt.subplots(figsize=(10, 6))

        bars = ax.bar(
            range(len(clients)),
            throughputs,
            color="#2ca02c",
            alpha=0.7,
            edgecolor="black",
            linewidth=1.5,
        )

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.0f}",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        ax.set_xlabel("Number of Concurrent Clients", fontsize=12, fontweight="bold")
        ax.set_ylabel("Throughput (packets/second)", fontsize=12, fontweight="bold")
        ax.set_title("Throughput vs Number of Concurrent Clients", fontsize=14, fontweight="bold")
        ax.set_xticks(range(len(clients)))
        ax.set_xticklabels(clients)
        ax.grid(True, alpha=0.3, axis="y")

        plt.tight_layout()

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            logger.info(f"Saved throughput chart to {output_file}")
        else:
            plt.show()

        plt.close()

    def create_packet_loss_chart(
        self,
        results: List[Dict],
        output_file: Optional[str] = None,
    ) -> None:
        """Create packet loss vs clients chart"""
        if not results:
            logger.warning("No results to plot")
            return

        clients = [r["num_clients"] for r in results]
        packet_losses = [
            r["packet_loss"]["avg_percentage"] for r in results
        ]

        fig, ax = plt.subplots(figsize=(10, 6))

        bars = ax.bar(
            range(len(clients)),
            packet_losses,
            color="#d62728",
            alpha=0.7,
            edgecolor="black",
            linewidth=1.5,
        )

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.2f}%",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        ax.set_xlabel("Number of Concurrent Clients", fontsize=12, fontweight="bold")
        ax.set_ylabel("Packet Loss (%)", fontsize=12, fontweight="bold")
        ax.set_title("Packet Loss vs Number of Concurrent Clients", fontsize=14, fontweight="bold")
        ax.set_xticks(range(len(clients)))
        ax.set_xticklabels(clients)
        ax.set_ylim(0, max(packet_losses) * 1.2 if packet_losses else 10)
        ax.grid(True, alpha=0.3, axis="y")

        plt.tight_layout()

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            logger.info(f"Saved packet loss chart to {output_file}")
        else:
            plt.show()

        plt.close()

    def create_resource_usage_chart(
        self,
        results: List[Dict],
        output_file: Optional[str] = None,
    ) -> None:
        """Create resource usage (CPU/Memory) chart"""
        if not results:
            logger.warning("No results to plot")
            return

        clients = [r["num_clients"] for r in results]
        cpu_usage = [r["cpu"]["avg_percent"] for r in results]
        memory_usage = [r["memory"]["avg_mb"] for r in results]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # CPU chart
        ax1.plot(
            clients,
            cpu_usage,
            marker="o",
            linewidth=2,
            markersize=10,
            color="#1f77b4",
        )
        ax1.set_xlabel("Number of Concurrent Clients", fontsize=11, fontweight="bold")
        ax1.set_ylabel("CPU Usage (%)", fontsize=11, fontweight="bold")
        ax1.set_title("Average CPU Usage", fontsize=12, fontweight="bold")
        ax1.grid(True, alpha=0.3)
        ax1.set_xscale("log")

        # Memory chart
        ax2.plot(
            clients,
            memory_usage,
            marker="s",
            linewidth=2,
            markersize=10,
            color="#ff7f0e",
        )
        ax2.set_xlabel("Number of Concurrent Clients", fontsize=11, fontweight="bold")
        ax2.set_ylabel("Memory Usage (MB)", fontsize=11, fontweight="bold")
        ax2.set_title("Average Memory Usage", fontsize=12, fontweight="bold")
        ax2.grid(True, alpha=0.3)
        ax2.set_xscale("log")

        plt.tight_layout()

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            logger.info(f"Saved resource chart to {output_file}")
        else:
            plt.show()

        plt.close()

    def create_comprehensive_dashboard(
        self,
        results: List[Dict],
        output_file: Optional[str] = None,
    ) -> None:
        """Create comprehensive dashboard with all metrics"""
        if not results:
            logger.warning("No results to plot")
            return

        fig = plt.figure(figsize=(16, 12))
        gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)

        clients = [r["num_clients"] for r in results]

        # Latency chart (top-left)
        ax1 = fig.add_subplot(gs[0, 0])
        avg_latencies = [r["latency"]["avg_ms"] for r in results]
        p95_latencies = [r["latency"]["p95_ms"] for r in results]
        ax1.plot(clients, avg_latencies, marker="o", label="Avg", linewidth=2)
        ax1.plot(clients, p95_latencies, marker="s", label="P95", linewidth=2)
        ax1.set_ylabel("Latency (ms)", fontweight="bold")
        ax1.set_title("Latency vs Clients", fontweight="bold")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Throughput chart (top-right)
        ax2 = fig.add_subplot(gs[0, 1])
        throughputs = [r["throughput"]["avg_packets_per_sec"] for r in results]
        ax2.bar(range(len(clients)), throughputs, color="#2ca02c", alpha=0.7)
        ax2.set_ylabel("Throughput (pps)", fontweight="bold")
        ax2.set_title("Throughput vs Clients", fontweight="bold")
        ax2.set_xticks(range(len(clients)))
        ax2.set_xticklabels(clients)
        ax2.grid(True, alpha=0.3, axis="y")

        # Packet Loss chart (middle-left)
        ax3 = fig.add_subplot(gs[1, 0])
        packet_losses = [r["packet_loss"]["avg_percentage"] for r in results]
        ax3.bar(range(len(clients)), packet_losses, color="#d62728", alpha=0.7)
        ax3.set_ylabel("Loss (%)", fontweight="bold")
        ax3.set_title("Packet Loss vs Clients", fontweight="bold")
        ax3.set_xticks(range(len(clients)))
        ax3.set_xticklabels(clients)
        ax3.grid(True, alpha=0.3, axis="y")

        # CPU Usage chart (middle-right)
        ax4 = fig.add_subplot(gs[1, 1])
        cpu_usage = [r["cpu"]["avg_percent"] for r in results]
        ax4.plot(clients, cpu_usage, marker="o", color="#1f77b4", linewidth=2)
        ax4.set_ylabel("CPU (%)", fontweight="bold")
        ax4.set_title("CPU Usage vs Clients", fontweight="bold")
        ax4.grid(True, alpha=0.3)

        # Memory Usage chart (bottom-left)
        ax5 = fig.add_subplot(gs[2, 0])
        memory_usage = [r["memory"]["avg_mb"] for r in results]
        ax5.plot(clients, memory_usage, marker="s", color="#ff7f0e", linewidth=2)
        ax5.set_xlabel("Clients", fontweight="bold")
        ax5.set_ylabel("Memory (MB)", fontweight="bold")
        ax5.set_title("Memory Usage vs Clients", fontweight="bold")
        ax5.grid(True, alpha=0.3)

        # Summary table (bottom-right)
        ax6 = fig.add_subplot(gs[2, 1])
        ax6.axis("tight")
        ax6.axis("off")

        table_data = []
        for r in results:
            table_data.append(
                [
                    str(r["num_clients"]),
                    f"{r['latency']['avg_ms']:.1f}ms",
                    f"{r['throughput']['avg_packets_per_sec']:.0f}",
                    f"{r['packet_loss']['avg_percentage']:.2f}%",
                ]
            )

        table = ax6.table(
            cellText=table_data,
            colLabels=["Clients", "Avg Lat", "Throughput", "Loss"],
            cellLoc="center",
            loc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)

        fig.suptitle(
            "Audio Pipeline Stress Test Results Dashboard",
            fontsize=16,
            fontweight="bold",
            y=0.98,
        )

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            logger.info(f"Saved comprehensive dashboard to {output_file}")
        else:
            plt.show()

        plt.close()

    def generate_all_charts(self) -> None:
        """Generate all charts from results directory"""
        scenarios_file = self.results_dir / "all_scenarios.json"

        if not scenarios_file.exists():
            logger.error(f"Scenarios file not found: {scenarios_file}")
            return

        results = self.load_scenario_results(str(scenarios_file))

        if not results:
            logger.error("No results to generate charts")
            return

        # Create individual charts
        self.create_latency_vs_clients_chart(
            results,
            str(self.results_dir / "latency_vs_clients.png"),
        )
        self.create_throughput_chart(
            results,
            str(self.results_dir / "throughput_vs_clients.png"),
        )
        self.create_packet_loss_chart(
            results,
            str(self.results_dir / "packet_loss_vs_clients.png"),
        )
        self.create_resource_usage_chart(
            results,
            str(self.results_dir / "resource_usage.png"),
        )

        # Create comprehensive dashboard
        self.create_comprehensive_dashboard(
            results,
            str(self.results_dir / "comprehensive_dashboard.png"),
        )

        logger.info("All charts generated successfully!")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate dashboard visualizations"
    )
    parser.add_argument(
        "--results-dir",
        default="reports",
        help="Results directory (default: reports)",
    )

    args = parser.parse_args()

    generator = DashboardGenerator(results_dir=args.results_dir)
    generator.generate_all_charts()


if __name__ == "__main__":
    main()
