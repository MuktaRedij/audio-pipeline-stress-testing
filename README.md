# Audio Pipeline Stress Testing System

A production-grade real-time audio pipeline stress testing system built with Python asyncio and WebSockets. This system simulates multiple concurrent audio clients, measures latency, detects packet loss, and generates comprehensive stress testing reports with visualizations.

## Features

### Core Capabilities
- **Real-time WebSocket Communication**: Bidirectional streaming of audio packets with acknowledgment protocol
- **Concurrent Client Simulation**: Asynchronous handling of 10-500+ simultaneous clients
- **Latency Measurement**: Per-packet round-trip time calculation with percentile analysis
- **Packet Loss Detection**: Real-time and aggregated packet loss tracking
- **Resource Monitoring**: CPU and memory usage tracking during stress tests
- **Comprehensive Metrics**: Average, median, P95, P99, and max latency calculations

### Advanced Features
- **Automatic Reconnection**: Clients reconnect automatically on server disconnect
- **Graceful Shutdown**: Proper cleanup of WebSocket connections and resources
- **Configurable Parameters**: 
  - Send interval (default: 20ms)
  - Audio chunk size (default: 1024 bytes)
  - Server host/port
  - Test duration and client count
- **Production-Ready Logging**: Structured logging to both files and console
- **Scenario Suite**: Pre-configured stress test scenarios (10/50/100/500 clients)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Stress Test Orchestrator                 │
│              (stress_test.py - AsyncIO Coordinator)         │
└────────────┬────────────────────────────────────┬───────────┘
             │                                    │
             ▼                                    ▼
    ┌────────────────┐                  ┌─────────────────┐
    │  WebSocket     │                  │   Metrics       │
    │  Server        │◄────────────────►│  Collector      │
    │ (server.py)    │   Packets/ACKs   │ (metrics.py)    │
    └────────────────┘                  └─────────────────┘
             ▲
             │ Packet Stream
             │ (JSON over WebSocket)
             │
    ┌────────┴──────────────────────────────┐
    │                                       │
    ▼               ▼               ▼       ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ...
│ Client 1 │  │ Client 2 │  │ Client N │
│(asyncio) │  │(asyncio) │  │(asyncio) │
└──────────┘  └──────────┘  └──────────┘

    │◄───── Real-time metrics collection (latency, loss) ─────┤

    └─────────────────────┬────────────────────────────────────┘
                          │
                          ▼
                ┌──────────────────────┐
                │  Dashboard Generator │
                │  (dashboard.py)      │
                │  - Latency charts    │
                │  - Throughput graphs │
                │  - Resource usage    │
                └──────────────────────┘
                          │
                          ▼
                ┌──────────────────────┐
                │  Visualization       │
                │  - PNG charts        │
                │  - Summary tables    │
                └──────────────────────┘
```

## Tech Stack

- **Python**: 3.11+
- **Async Framework**: asyncio
- **WebSocket**: websockets 12.0
- **Data Processing**: pandas 2.1.4
- **Visualization**: matplotlib 3.8.2
- **System Monitoring**: psutil 5.9.6
- **Logging**: Python standard logging module

## Installation

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)

### Setup

1. **Clone or navigate to the project directory**:
```bash
cd audio-pipeline-stress-testing
```

2. **Create a virtual environment** (recommended):
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Usage

### 1. Start the Server

In one terminal/tab:
```bash
python server.py
```

Expected output:
```
2026-05-26 10:30:45 - __main__ - INFO - Starting server on localhost:8765
2026-05-26 10:30:45 - __main__ - INFO - Server running on ws://localhost:8765
2026-05-26 10:30:55 - __main__ - INFO - Server Stats - Clients: 0, Packets RX: 0, ACKs TX: 0, Throughput: 0.00 pps
```

### 2. Run Stress Tests

In another terminal:

**Option A: Run Full Scenario Suite (Recommended for comprehensive testing)**
```bash
python stress_test.py
```

This runs:
- 10 clients for 30 seconds
- 50 clients for 30 seconds
- 100 clients for 30 seconds
- 500 clients for 60 seconds

**Option B: Run Single Test with Custom Parameters**
```bash
# 25 clients for 60 seconds
python stress_test.py --clients 25 --duration 60

# Custom server URI
python stress_test.py --clients 100 --duration 30 --server ws://192.168.1.100:8765

# Save results to custom directory
python stress_test.py --results-dir ./custom_results
```

### 3. Generate Visualizations

After stress tests complete:
```bash
python dashboard.py

# Or with custom results directory
python dashboard.py --results-dir ./custom_results
```

This generates:
- `latency_vs_clients.png` - Latency trends
- `throughput_vs_clients.png` - Throughput analysis
- `packet_loss_vs_clients.png` - Packet loss graph
- `resource_usage.png` - CPU and memory usage
- `comprehensive_dashboard.png` - All metrics combined

### 4. Run Single Client (Testing/Debugging)

```bash
python client.py
```

The client will:
- Connect to localhost:8765
- Send audio packets every 20ms
- Display live metrics
- Reconnect automatically on disconnect

## Stress Test Scenarios

The system includes pre-configured scenarios that test different concurrency levels:

### Scenario 1: Light Load
- **Clients**: 10
- **Duration**: 30 seconds
- **Use Case**: Baseline performance, single-digit client load

### Scenario 2: Medium Load
- **Clients**: 50
- **Duration**: 30 seconds
- **Use Case**: Expected production load

### Scenario 3: Heavy Load
- **Clients**: 100
- **Duration**: 30 seconds
- **Use Case**: Peak usage detection

### Scenario 4: Extreme Load
- **Clients**: 500
- **Duration**: 60 seconds
- **Use Case**: System breaking point analysis

## Metrics Collected

### Latency Metrics
- **Average Latency**: Mean round-trip time (ms)
- **Median Latency**: Median round-trip time (ms)
- **P95 Latency**: 95th percentile (ms)
- **P99 Latency**: 99th percentile (ms)
- **Min/Max Latency**: Range bounds (ms)
- **Sample Count**: Number of measurements

### Throughput Metrics
- **Average Throughput**: Mean packets per second
- **Sample Count**: Number of measurements

### Packet Loss Metrics
- **Average Loss**: Mean packet loss percentage
- **Sample Count**: Number of measurements

### Resource Metrics
- **CPU Usage**: Average and maximum CPU percentage
- **Memory Usage**: Average and maximum memory in MB
- **Active Clients**: Maximum concurrent connections

### Output Files

```
reports/
├── scenario_10_clients/
│   ├── summary.json          # Detailed metrics
│   └── latencies.csv         # Per-packet latencies
├── scenario_50_clients/
│   ├── summary.json
│   └── latencies.csv
├── scenario_100_clients/
│   ├── summary.json
│   └── latencies.csv
├── scenario_500_clients/
│   ├── summary.json
│   └── latencies.csv
├── all_scenarios.json        # Combined results
├── latency_vs_clients.png
├── throughput_vs_clients.png
├── packet_loss_vs_clients.png
├── resource_usage.png
└── comprehensive_dashboard.png

logs/
├── server.log                # Server logs
└── stress_test.log           # Stress test logs
```

## Sample Results

When running the full scenario suite, you should see output like:

```
============================================================
Test Summary for 10 clients:
============================================================
Duration: 30.12s
Latency - Avg: 2.34ms, P95: 5.67ms, Max: 12.45ms
Throughput: 4891.23 pps
Packet Loss: 0.00%
CPU: Avg 5.2%, Max 8.1%
Memory: Avg 45.3MB, Max 52.1MB
============================================================

============================================================
Test Summary for 50 clients:
============================================================
Duration: 30.15s
Latency - Avg: 3.12ms, P95: 7.89ms, Max: 18.34ms
Throughput: 24156.78 pps
Packet Loss: 0.01%
CPU: Avg 18.5%, Max 24.3%
Memory: Avg 78.9MB, Max 95.2MB
============================================================

[Additional scenarios...]
```

### Results Summary Table

```
==================================================================================================
STRESS TEST RESULTS SUMMARY
==================================================================================================
Clients    Duration     Avg Lat      P95 Lat      Throughput      Loss %     CPU %     Memory MB
------------------------------------------------------------------------------------------------------
10         30.12        2.34         5.67         4891.23         0.00       5.2       45.3
50         30.15        3.12         7.89         24156.78        0.01       18.5      78.9
100        30.18        4.56         12.34        48923.45        0.05       35.2      142.1
500        60.22        8.91         23.45        243451.12       0.12       72.1      325.4
==================================================================================================
```

## Packet Protocol

### Client → Server (Audio Packet)
```json
{
  "client_id": 1,
  "packet_id": 42,
  "timestamp": 1716710445.123456,
  "audio_data": "48656c6c6f20576f726c6421"
}
```

### Server → Client (ACK)
```json
{
  "packet_id": 42,
  "server_timestamp": 1716710445.125123,
  "status": "received"
}
```

## Performance Tuning

### For Testing Higher Client Counts
1. Increase system file descriptor limit:
```bash
# On Linux/macOS
ulimit -n 10000
```

2. Adjust WebSocket parameters in `server.py`:
```python
async with websockets.serve(
    self.handle_client,
    self.host,
    self.port,
    ping_interval=20,
    max_size=10 * 1024,  # Increase max message size
    max_queue=32,        # Increase queue size
):
```

### For Measuring Realistic Latency
- Run server and clients on the same machine for minimal network latency
- Use separate machines for more realistic network conditions
- Disable CPU frequency scaling for consistent results

## Future Improvements

1. **Enhanced Metrics**
   - Jitter analysis
   - Histogram-based latency distribution
   - Per-client metrics breakdown

2. **Advanced Features**
   - Configurable packet loss simulation
   - Network latency simulation
   - Protocol recording/playback

3. **Dashboard Enhancements**
   - Web-based real-time dashboard
   - Live metrics streaming
   - Interactive charts

4. **Scalability**
   - Distributed multi-machine testing
   - Horizontal load balancing
   - Test result federation

5. **Integration**
   - CI/CD pipeline integration
   - Performance regression detection
   - Automated alerting

## Troubleshooting

### Connection Refused
```
ConnectionRefusedError: [Errno 111] Connection refused
```
**Solution**: Ensure the server is running on `localhost:8765`

### Too Many Open Files
```
OSError: [Errno 24] Too many open files
```
**Solution**: Increase system limits with `ulimit -n 10000`

### Out of Memory
```
MemoryError
```
**Solution**: Reduce client count or duration, or add more system RAM

### WebSocket Connection Timeouts
```
asyncio.TimeoutError
```
**Solution**: Check network connectivity, increase timeout in `client.py`

## License

This project is available for educational and commercial use.

## Contributing

Contributions welcome! Please ensure:
- Code follows PEP 8 style guide
- Type hints are included
- Tests pass before submission
- Documentation is updated

## Support

For issues, questions, or improvements:
1. Check existing documentation
2. Review logs in `logs/` directory
3. Create detailed bug reports with reproduction steps

---

**Built with Python asyncio | WebSockets | Pandas | Matplotlib**

*Performance testing simplified for production audio pipelines*
