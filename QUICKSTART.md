# Audio Pipeline Stress Testing - Quick Start Guide

## 5-Minute Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start the Server
Open Terminal 1:
```bash
python server.py
```

Expected output:
```
2026-05-26 10:30:45 - __main__ - INFO - Starting server on localhost:8765
2026-05-26 10:30:45 - __main__ - INFO - Server running on ws://localhost:8765
```

### Step 3: Run Stress Test
Open Terminal 2:
```bash
python stress_test.py
```

This will run all 4 scenarios automatically (10, 50, 100, 500 clients).

### Step 4: Generate Visualizations
```bash
python dashboard.py
```

View the generated charts in the `reports/` directory:
- `comprehensive_dashboard.png` - Full overview
- `latency_vs_clients.png` - Latency trends
- `throughput_vs_clients.png` - Performance scaling
- `packet_loss_vs_clients.png` - Reliability analysis
- `resource_usage.png` - CPU and memory trends

---

## Common Usage Scenarios

### Scenario 1: Test with 50 Clients for 60 Seconds
```bash
# Terminal 1
python server.py

# Terminal 2
python stress_test.py --clients 50 --duration 60

# Terminal 2 (after test completes)
python dashboard.py
```

### Scenario 2: Test Network Resilience with High Load
```bash
# Terminal 1
python server.py

# Terminal 2
python stress_test.py --clients 500 --duration 120

# Terminal 2 (after test completes)
python dashboard.py
```

### Scenario 3: Quick Functionality Test
```bash
# Terminal 1
python server.py

# Terminal 2
python stress_test.py --clients 5 --duration 10

# Terminal 2 (after test completes)
python dashboard.py
```

### Scenario 4: Test Specific Server
```bash
python stress_test.py --server ws://192.168.1.100:8765 --clients 100 --duration 30
```

### Scenario 5: Single Client Testing (Debugging)
```bash
# Terminal 1
python server.py

# Terminal 2
python client.py
```

The client will send packets and display metrics every packet (Ctrl+C to stop).

---

## Understanding the Output

### Server Output Example
```
2026-05-26 10:35:10 - __main__ - INFO - Client connected: 140234567890123. Active clients: 1
2026-05-26 10:35:10 - __main__ - INFO - Server Stats - Clients: 10, Packets RX: 5432, ACKs TX: 5421, Throughput: 1234.56 pps
2026-05-26 10:35:20 - __main__ - INFO - Client disconnected: 140234567890123
```

- **Clients**: Number of currently connected clients
- **Packets RX**: Total packets received
- **ACKs TX**: Total acknowledgments sent
- **Throughput**: Packets per second

### Client Output Example
```
2026-05-26 10:35:12 - __main__ - INFO - Client 1: Connected to ws://localhost:8765
2026-05-26 10:35:15 - __main__ - INFO - Client 1: Sent=150, Acked=148, AvgLat=2.34ms, MaxLat=5.67ms, MinLat=1.23ms, Loss=1.33%
```

- **Sent**: Total packets sent
- **Acked**: Total packets acknowledged
- **AvgLat**: Average round-trip latency
- **MaxLat**: Maximum latency
- **MinLat**: Minimum latency
- **Loss**: Packet loss percentage

### Stress Test Summary Example
```
============================================================
Test Summary for 100 clients:
============================================================
Duration: 30.18s
Latency - Avg: 4.56ms, P95: 12.34ms, Max: 25.67ms
Throughput: 48923.45 pps
Packet Loss: 0.05%
CPU: Avg 35.2%, Max 42.1%
Memory: Avg 142.1MB, Max 156.3MB
============================================================
```

---

## Result Files Structure

After running tests, check these files:

### JSON Summary (Detailed Metrics)
```bash
cat reports/scenario_100_clients/summary.json
```

Example content:
```json
{
  "num_clients": 100,
  "duration_seconds": 30.18,
  "timestamp": "2026-05-26T10:35:45.123456",
  "latency": {
    "avg_ms": 4.56,
    "median_ms": 4.12,
    "p95_ms": 12.34,
    "p99_ms": 18.45,
    "min_ms": 0.89,
    "max_ms": 25.67,
    "samples": 48923
  },
  "throughput": {
    "avg_packets_per_sec": 48923.45,
    "samples": 30
  },
  "packet_loss": {
    "avg_percentage": 0.05,
    "samples": 30
  },
  "cpu": {
    "avg_percent": 35.2,
    "max_percent": 42.1,
    "samples": 30
  },
  "memory": {
    "avg_mb": 142.1,
    "max_mb": 156.3,
    "samples": 30
  },
  "clients": {
    "max_active": 100,
    "samples": 30
  }
}
```

### CSV Latency Data
```bash
head -20 reports/scenario_100_clients/latencies.csv
```

Example content:
```csv
client_num,latency_ms,timestamp
1,2.34,2026-05-26T10:35:45.123456
2,3.45,2026-05-26T10:35:46.234567
3,2.12,2026-05-26T10:35:47.345678
...
```

---

## Interpreting Results

### Good Performance Indicators
✅ Average latency < 5ms
✅ P95 latency < 20ms
✅ P99 latency < 50ms
✅ Packet loss < 0.1%
✅ Throughput scales linearly with clients
✅ CPU usage < 70%
✅ Memory usage stable (no growth)

### Warning Signs
⚠️ Average latency > 10ms
⚠️ P95 latency > 50ms
⚠️ Packet loss > 1%
⚠️ Throughput plateaus before expected client count
⚠️ CPU usage > 80%
⚠️ Memory usage grows with time

### Critical Issues
🔴 Average latency > 50ms
🔴 Packet loss > 5%
🔴 Server crashes or disconnects
🔴 Throughput decreases with more clients
🔴 CPU usage maxes out
🔴 Memory leak detected

---

## Advanced Configuration

### Customize Packet Send Interval
Edit `stress_test.py` line ~150:
```python
send_interval_ms=50.0,  # Change from 20.0 to 50.0 (slower packets)
```

### Customize Audio Chunk Size
Edit `stress_test.py` line ~151:
```python
audio_chunk_size=2048,  # Change from 1024 to 2048 (larger packets)
```

### Custom Server Host/Port
```bash
# In server.py, change:
server = AudioServer(host="0.0.0.0", port=9999)

# Then run stress test against it:
python stress_test.py --server ws://localhost:9999
```

### Save Results to Custom Directory
```bash
python stress_test.py --results-dir ./my_results
python dashboard.py --results-dir ./my_results
```

---

## Troubleshooting

### Issue: "Connection refused"
```
asyncio.CancelledError
```
**Fix**: Ensure server is running before starting stress test
```bash
python server.py  # Must run FIRST
```

### Issue: "Too many open files"
```
OSError: [Errno 24] Too many open files
```
**Fix**: Increase system limits (Linux/macOS)
```bash
ulimit -n 10000
```

### Issue: Client crashes with memory error
**Fix**: Reduce client count or test duration
```bash
python stress_test.py --clients 100 --duration 30  # Instead of 500 clients
```

### Issue: Inconsistent results between runs
**Cause**: System load variations
**Fix**: 
- Close other applications
- Run test multiple times and average results
- Use `nice` command (Linux): `nice -n -5 python stress_test.py`

### Issue: Charts not generating
**Fix**: Check if results exist:
```bash
ls -la reports/all_scenarios.json
python dashboard.py  # Verbose output shows errors
```

---

## Performance Analysis Tips

### Identifying Bottlenecks

1. **High Latency with Low CPU Usage**
   - Network latency issue
   - Server processing bottleneck
   - Consider adding connection pooling

2. **High CPU Usage with Low Throughput**
   - CPU-bound processing
   - Too much logging
   - Context switching overhead

3. **Packet Loss Under Load**
   - Buffer overflow
   - Network congestion
   - Increase socket buffer size

4. **Memory Leak Detection**
   - Compare memory at start vs end of long test
   - Check `memory_avg_mb` vs `memory_max_mb`
   - May indicate connection pooling issues

---

## Next Steps

1. **Baseline Testing**: Run the full suite once to establish baseline
2. **Optimization**: Identify bottlenecks from results
3. **Targeted Testing**: Run specific scenarios to test improvements
4. **Comparison**: Compare before/after optimization results
5. **Production Deployment**: Monitor real-world audio pipeline using same metrics

---

## Additional Resources

- **README.md**: Full project documentation
- **server.py**: WebSocket server implementation
- **client.py**: Client simulator with metrics
- **stress_test.py**: Test orchestration and reporting
- **metrics.py**: Metrics collection and calculations
- **dashboard.py**: Visualization generation

---

Need help? Check the logs:
```bash
tail -50 logs/server.log
tail -50 logs/stress_test.log
```
