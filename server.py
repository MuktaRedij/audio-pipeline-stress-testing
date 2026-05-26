"""
server.py - WebSocket server for audio pipeline stress testing
Handles multiple concurrent clients, receives audio packets, sends acknowledgments
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Set

import websockets
from websockets.server import WebSocketServerProtocol

# Configure logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "server.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class AudioPacket:
    """Represents an audio packet from client"""

    client_id: int
    packet_id: int
    timestamp: float
    audio_data: str


@dataclass
class AckPacket:
    """Acknowledgment packet sent to client"""

    packet_id: int
    server_timestamp: float
    status: str


class AudioServer:
    """WebSocket server for handling audio pipeline stress testing"""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.active_clients: Dict[str, Dict] = {}
        self.packets_received = 0
        self.packets_acknowledged = 0
        self.start_time = time.time()
        self.lock = asyncio.Lock()

    async def handle_client(
        self, websocket: WebSocketServerProtocol, path: str
    ) -> None:
        """Handle a connected client"""
        client_id = id(websocket)
        client_addr = f"{client_id}"

        async with self.lock:
            self.active_clients[client_addr] = {
                "websocket": websocket,
                "connected_at": time.time(),
                "packets_received": 0,
                "last_packet_time": time.time(),
            }

        logger.info(
            f"Client connected: {client_addr}. "
            f"Active clients: {len(self.active_clients)}"
        )

        try:
            async for message in websocket:
                await self.process_packet(message, client_addr, websocket)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_addr}")
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            async with self.lock:
                if client_addr in self.active_clients:
                    del self.active_clients[client_addr]
            logger.info(
                f"Client removed: {client_addr}. "
                f"Active clients: {len(self.active_clients)}"
            )

    async def process_packet(
        self,
        message: str,
        client_addr: str,
        websocket: WebSocketServerProtocol,
    ) -> None:
        """Process an incoming audio packet from a client"""
        try:
            data = json.loads(message)

            # Validate packet structure
            required_fields = ["client_id", "packet_id", "timestamp", "audio_data"]
            if not all(field in data for field in required_fields):
                logger.warning(f"Invalid packet structure from {client_addr}")
                return

            # Create packet object
            packet = AudioPacket(
                client_id=data["client_id"],
                packet_id=data["packet_id"],
                timestamp=data["timestamp"],
                audio_data=data["audio_data"],
            )

            # Update metrics
            async with self.lock:
                self.packets_received += 1
                if client_addr in self.active_clients:
                    self.active_clients[client_addr]["packets_received"] += 1
                    self.active_clients[client_addr]["last_packet_time"] = time.time()

            # Send acknowledgment
            ack = AckPacket(
                packet_id=packet.packet_id,
                server_timestamp=time.time(),
                status="received",
            )

            await websocket.send(json.dumps(asdict(ack)))

            async with self.lock:
                self.packets_acknowledged += 1

        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from {client_addr}")
        except Exception as e:
            logger.error(f"Error processing packet from {client_addr}: {e}")

    async def get_stats(self) -> Dict:
        """Get current server statistics"""
        async with self.lock:
            elapsed = time.time() - self.start_time
            return {
                "active_clients": len(self.active_clients),
                "packets_received": self.packets_received,
                "packets_acknowledged": self.packets_acknowledged,
                "uptime_seconds": elapsed,
                "throughput_pps": (
                    self.packets_received / elapsed if elapsed > 0 else 0
                ),
            }

    async def print_stats_periodically(self) -> None:
        """Print server statistics every 10 seconds"""
        try:
            while True:
                await asyncio.sleep(10)
                stats = await self.get_stats()
                logger.info(
                    f"Server Stats - Clients: {stats['active_clients']}, "
                    f"Packets RX: {stats['packets_received']}, "
                    f"ACKs TX: {stats['packets_acknowledged']}, "
                    f"Throughput: {stats['throughput_pps']:.2f} pps"
                )
        except Exception as e:
            logger.error(f"Error in stats printer: {e}")

    async def start(self) -> None:
        """Start the WebSocket server"""
        logger.info(f"Starting server on {self.host}:{self.port}")

        # Create stats printer task
        stats_task = asyncio.create_task(self.print_stats_periodically())

        try:
            # Create handler wrapper compatible with websockets 12.0+
            # In websockets 12.0+, handlers receive only the connection object
            async def handler(websocket: WebSocketServerProtocol) -> None:
                """Handler wrapper for websockets 12.0+ compatibility"""
                # In newer versions, path is not passed, so we provide empty string
                await self.handle_client(websocket, "")
            
            async with websockets.serve(
                handler, self.host, self.port, ping_interval=20
            ):
                logger.info(f"Server running on ws://{self.host}:{self.port}")
                await asyncio.Future()  # Run forever
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            stats_task.cancel()


async def main():
    """Main entry point"""
    server = AudioServer(host="localhost", port=8765)
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
