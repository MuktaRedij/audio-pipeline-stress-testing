"""
metrics.py - Metrics calculation and storage utilities for audio pipeline stress testing
"""

import csv
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class MetricsCollector:
    """Collects and calculates metrics from stress test runs"""

    def __init__(self):
        self.latencies: List[float] = []
        self.throughput_samples: List[float] = []
        self.packet_losses: List[float] = []
        self.cpu_samples: List[float] = []
        self.memory_samples: List[float] = []
        self.active_clients_samples: List[int] = []

    def add_latency(self, latency: float) -> None:
        """Add a latency measurement in milliseconds"""
        if latency >= 0:
            self.latencies.append(latency)

    def add_throughput(self, throughput: float) -> None:
        """Add a throughput measurement in packets/sec"""
        if throughput >= 0:
            self.throughput_samples.append(throughput)

    def add_packet_loss(self, loss_percentage: float) -> None:
        """Add a packet loss measurement"""
        if 0 <= loss_percentage <= 100:
            self.packet_losses.append(loss_percentage)

    def add_cpu_usage(self, cpu_percent: float) -> None:
        """Add CPU usage measurement"""
        if 0 <= cpu_percent <= 100:
            self.cpu_samples.append(cpu_percent)

    def add_memory_usage(self, memory_mb: float) -> None:
        """Add memory usage measurement in MB"""
        if memory_mb >= 0:
            self.memory_samples.append(memory_mb)

    def add_active_clients(self, count: int) -> None:
        """Add active client count sample"""
        if count >= 0:
            self.active_clients_samples.append(count)

    def calculate_average_latency(self) -> float:
        """Calculate average latency in milliseconds"""
        if not self.latencies:
            return 0.0
        return statistics.mean(self.latencies)

    def calculate_median_latency(self) -> float:
        """Calculate median latency in milliseconds"""
        if not self.latencies:
            return 0.0
        return statistics.median(self.latencies)

    def calculate_p95_latency(self) -> float:
        """Calculate 95th percentile latency"""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]

    def calculate_p99_latency(self) -> float:
        """Calculate 99th percentile latency"""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]

    def calculate_max_latency(self) -> float:
        """Calculate maximum latency"""
        if not self.latencies:
            return 0.0
        return max(self.latencies)

    def calculate_min_latency(self) -> float:
        """Calculate minimum latency"""
        if not self.latencies:
            return 0.0
        return min(self.latencies)

    def calculate_average_throughput(self) -> float:
        """Calculate average throughput in packets/sec"""
        if not self.throughput_samples:
            return 0.0
        return statistics.mean(self.throughput_samples)

    def calculate_average_packet_loss(self) -> float:
        """Calculate average packet loss percentage"""
        if not self.packet_losses:
            return 0.0
        return statistics.mean(self.packet_losses)

    def calculate_average_cpu_usage(self) -> float:
        """Calculate average CPU usage"""
        if not self.cpu_samples:
            return 0.0
        return statistics.mean(self.cpu_samples)

    def calculate_max_cpu_usage(self) -> float:
        """Calculate maximum CPU usage"""
        if not self.cpu_samples:
            return 0.0
        return max(self.cpu_samples)

    def calculate_average_memory_usage(self) -> float:
        """Calculate average memory usage in MB"""
        if not self.memory_samples:
            return 0.0
        return statistics.mean(self.memory_samples)

    def calculate_max_memory_usage(self) -> float:
        """Calculate maximum memory usage in MB"""
        if not self.memory_samples:
            return 0.0
        return max(self.memory_samples)

    def calculate_max_active_clients(self) -> int:
        """Calculate maximum concurrent active clients"""
        if not self.active_clients_samples:
            return 0
        return max(self.active_clients_samples)

    def get_summary(self, num_clients: int, duration_seconds: float) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        return {
            "num_clients": num_clients,
            "duration_seconds": duration_seconds,
            "timestamp": datetime.now().isoformat(),
            "latency": {
                "avg_ms": round(self.calculate_average_latency(), 2),
                "median_ms": round(self.calculate_median_latency(), 2),
                "p95_ms": round(self.calculate_p95_latency(), 2),
                "p99_ms": round(self.calculate_p99_latency(), 2),
                "min_ms": round(self.calculate_min_latency(), 2),
                "max_ms": round(self.calculate_max_latency(), 2),
                "samples": len(self.latencies),
            },
            "throughput": {
                "avg_packets_per_sec": round(self.calculate_average_throughput(), 2),
                "samples": len(self.throughput_samples),
            },
            "packet_loss": {
                "avg_percentage": round(self.calculate_average_packet_loss(), 2),
                "samples": len(self.packet_losses),
            },
            "cpu": {
                "avg_percent": round(self.calculate_average_cpu_usage(), 2),
                "max_percent": round(self.calculate_max_cpu_usage(), 2),
                "samples": len(self.cpu_samples),
            },
            "memory": {
                "avg_mb": round(self.calculate_average_memory_usage(), 2),
                "max_mb": round(self.calculate_max_memory_usage(), 2),
                "samples": len(self.memory_samples),
            },
            "clients": {
                "max_active": self.calculate_max_active_clients(),
                "samples": len(self.active_clients_samples),
            },
        }

    def save_metrics_to_csv(
        self,
        filepath: str,
        num_clients: int,
        latencies: Optional[List[float]] = None,
    ) -> None:
        """Save detailed metrics to CSV file"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        latencies_to_save = latencies if latencies is not None else self.latencies
        
        with open(filepath, "w", newline="") as csvfile:
            fieldnames = ["client_num", "latency_ms", "timestamp"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for idx, latency in enumerate(latencies_to_save):
                writer.writerow(
                    {
                        "client_num": (idx % num_clients) + 1,
                        "latency_ms": round(latency, 2),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

    def save_summary_to_json(
        self, filepath: str, summary: Dict[str, Any]
    ) -> None:
        """Save metrics summary to JSON file"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w") as jsonfile:
            json.dump(summary, jsonfile, indent=2)


def calculate_average_latency(latencies: List[float]) -> float:
    """Standalone function: Calculate average latency"""
    if not latencies:
        return 0.0
    return statistics.mean(latencies)


def calculate_p95_latency(latencies: List[float]) -> float:
    """Standalone function: Calculate 95th percentile latency"""
    if not latencies:
        return 0.0
    sorted_latencies = sorted(latencies)
    index = int(len(sorted_latencies) * 0.95)
    return sorted_latencies[min(index, len(sorted_latencies) - 1)]


def calculate_packet_loss(
    packets_sent: int, packets_received: int
) -> float:
    """Standalone function: Calculate packet loss percentage"""
    if packets_sent == 0:
        return 0.0
    return ((packets_sent - packets_received) / packets_sent) * 100


def calculate_throughput(packets_processed: int, duration_seconds: float) -> float:
    """Standalone function: Calculate throughput in packets/sec"""
    if duration_seconds == 0:
        return 0.0
    return packets_processed / duration_seconds


def save_metrics_to_csv(
    filepath: str,
    metrics_data: List[Dict[str, Any]],
) -> None:
    """Standalone function: Save metrics to CSV"""
    if not metrics_data:
        return
    
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, "w", newline="") as csvfile:
        fieldnames = metrics_data[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metrics_data)


def save_summary_to_json(filepath: str, summary: Dict[str, Any]) -> None:
    """Standalone function: Save summary to JSON"""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, "w") as jsonfile:
        json.dump(summary, jsonfile, indent=2)
