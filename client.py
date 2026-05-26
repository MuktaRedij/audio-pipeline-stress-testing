"""
client.py - WebSocket client simulator for audio pipeline stress testing
Sends audio packets at regular intervals, measures latency, tracks metrics
"""

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import websockets
from websockets.client import WebSocketClientProtocol


# Configure logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class ClientMetrics:
    """Tracks metrics for a single client"""

    client_id: int
    packets_sent: int = 0
    packets_acked: int = 0
    latencies: list = None
    send_times: dict = None

    def __post_init__(self):
        if self.latencies is None:
            self.latencies = []
        if self.send_times is None:
            self.send_times = {}

    def add_latency(self, latency_ms: float) -> None:
        """Record a latency measurement"""
        if latency_ms >= 0:
            self.latencies.append(latency_ms)

    def get_average_latency(self) -> float:
        """Get average latency in milliseconds"""
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)

    def get_max_latency(self) -> float:
        """Get maximum latency"""
        if not self.latencies:
            return 0.0
        return max(self.latencies)

    def get_min_latency(self) -> float:
        """Get minimum latency"""
        if not self.latencies:
            return 0.0
        return min(self.latencies)

    def get_packet_loss_percentage(self) -> float:
        """Calculate packet loss percentage"""
        if self.packets_sent == 0:
            return 0.0
        return ((self.packets_sent - self.packets_acked) / self.packets_sent) * 100


class AudioClient:
    """WebSocket client for audio pipeline stress testing"""

    def __init__(
        self,
        client_id: int,
        server_uri: str = "ws://localhost:8765",
        send_interval_ms: float = 20.0,
        audio_chunk_size: int = 1024,
        reconnect_interval: float = 5.0,
    ):
        self.client_id = client_id
        self.server_uri = server_uri
        self.send_interval_ms = send_interval_ms
        self.audio_chunk_size = audio_chunk_size
        self.reconnect_interval = reconnect_interval
        self.metrics = ClientMetrics(client_id=client_id)
        self.running = False
        self.connected = False
        self.websocket: Optional[WebSocketClientProtocol] = None

    async def generate_audio_chunk(self) -> str:
        """Generate simulated audio data"""
        # Simulate audio bytes as base64-like string
        audio_bytes = bytes(
            random.randint(0, 255) for _ in range(self.audio_chunk_size)
        )
        return audio_bytes.hex()[:32]  # Return first 32 chars for brevity

    async def send_packet(self) -> None:
        """Send an audio packet to server"""
        if not self.connected or self.websocket is None:
            return

        try:
            packet_id = self.metrics.packets_sent
            current_time = time.time()
            audio_data = await self.generate_audio_chunk()

            # Create packet
            packet = {
                "client_id": self.client_id,
                "packet_id": packet_id,
                "timestamp": current_time,
                "audio_data": audio_data,
            }

            # Store send time for latency calculation
            self.metrics.send_times[packet_id] = current_time

            # Send packet
            await self.websocket.send(json.dumps(packet))
            self.metrics.packets_sent += 1

        except Exception as e:
            logger.error(f"Client {self.client_id}: Error sending packet: {e}")

    async def receive_acks(self) -> None:
        """Receive acknowledgments from server"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)

                    if "status" in data and data["status"] == "received":
                        packet_id = data["packet_id"]
                        server_timestamp = data["server_timestamp"]

                        # Calculate latency
                        if packet_id in self.metrics.send_times:
                            send_time = self.metrics.send_times.pop(packet_id)
                            latency_ms = (server_timestamp - send_time) * 1000
                            self.metrics.add_latency(latency_ms)
                            self.metrics.packets_acked += 1

                except json.JSONDecodeError:
                    logger.warning(
                        f"Client {self.client_id}: Invalid JSON in ACK"
                    )
        except websockets.exceptions.ConnectionClosed:
            logger.warning(
                f"Client {self.client_id}: Connection closed while receiving ACKs"
            )
        except Exception as e:
            logger.error(
                f"Client {self.client_id}: Error receiving ACKs: {e}"
            )

    async def send_packets_periodically(self) -> None:
        """Send packets at regular intervals"""
        interval = self.send_interval_ms / 1000.0
        try:
            while self.running:
                if self.connected:
                    await self.send_packet()
                await asyncio.sleep(interval)
        except Exception as e:
            logger.error(
                f"Client {self.client_id}: Error in periodic send: {e}"
            )

    async def connect_and_run(self) -> None:
        """Connect to server and run client"""
        self.running = True
        retry_count = 0
        max_retries = 10

        while self.running and retry_count < max_retries:
            try:
                async with websockets.connect(self.server_uri) as websocket:
                    self.websocket = websocket
                    self.connected = True
                    retry_count = 0

                    logger.info(
                        f"Client {self.client_id}: Connected to {self.server_uri}"
                    )

                    # Create tasks for sending and receiving
                    send_task = asyncio.create_task(
                        self.send_packets_periodically()
                    )
                    recv_task = asyncio.create_task(self.receive_acks())

                    # Wait for either task to fail
                    await asyncio.gather(send_task, recv_task)

            except websockets.exceptions.WebSocketException as e:
                logger.warning(
                    f"Client {self.client_id}: WebSocket error: {e}. "
                    f"Retrying in {self.reconnect_interval}s..."
                )
                retry_count += 1
                self.connected = False
                await asyncio.sleep(self.reconnect_interval)
            except Exception as e:
                logger.error(
                    f"Client {self.client_id}: Unexpected error: {e}"
                )
                retry_count += 1
                self.connected = False
                await asyncio.sleep(self.reconnect_interval)

        self.connected = False
        logger.info(
            f"Client {self.client_id}: Disconnected "
            f"(packets_sent={self.metrics.packets_sent}, "
            f"packets_acked={self.metrics.packets_acked})"
        )

    async def stop(self) -> None:
        """Stop the client"""
        self.running = False
        if self.websocket:
            await self.websocket.close()

    def print_metrics(self) -> None:
        """Print current metrics"""
        avg_lat = self.metrics.get_average_latency()
        max_lat = self.metrics.get_max_latency()
        min_lat = self.metrics.get_min_latency()
        pkt_loss = self.metrics.get_packet_loss_percentage()

        logger.info(
            f"Client {self.client_id}: "
            f"Sent={self.metrics.packets_sent}, "
            f"Acked={self.metrics.packets_acked}, "
            f"AvgLat={avg_lat:.2f}ms, "
            f"MaxLat={max_lat:.2f}ms, "
            f"MinLat={min_lat:.2f}ms, "
            f"Loss={pkt_loss:.2f}%"
        )


async def run_single_client(
    client_id: int,
    duration_seconds: Optional[float] = None,
    server_uri: str = "ws://localhost:8765",
) -> ClientMetrics:
    """Run a single client for specified duration"""
    client = AudioClient(
        client_id=client_id,
        server_uri=server_uri,
        send_interval_ms=20.0,
        audio_chunk_size=1024,
    )

    try:
        if duration_seconds is None:
            # Run indefinitely
            await client.connect_and_run()
        else:
            # Run for specified duration
            run_task = asyncio.create_task(client.connect_and_run())
            await asyncio.sleep(duration_seconds)
            await client.stop()
            await run_task
    except asyncio.CancelledError:
        await client.stop()

    return client.metrics


async def main():
    """Test a single client"""
    metrics = await run_single_client(client_id=1, duration_seconds=10)
    metrics_obj = metrics
    print(f"\n=== Final Metrics for Client 1 ===")
    print(f"Packets Sent: {metrics_obj.packets_sent}")
    print(f"Packets Acknowledged: {metrics_obj.packets_acked}")
    print(f"Average Latency: {metrics_obj.get_average_latency():.2f}ms")
    print(f"Max Latency: {metrics_obj.get_max_latency():.2f}ms")
    print(f"Min Latency: {metrics_obj.get_min_latency():.2f}ms")
    print(f"Packet Loss: {metrics_obj.get_packet_loss_percentage():.2f}%")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Client stopped by user")
