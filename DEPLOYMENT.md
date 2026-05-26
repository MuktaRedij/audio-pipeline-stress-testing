# Audio Pipeline Stress Testing - Deployment & Operations Guide

## Local Development Deployment

### Prerequisites
- Python 3.11 or higher
- pip package manager
- ~500MB disk space (for results and dependencies)
- ~1GB RAM available

### Installation Steps

1. **Clone/Navigate to Project**
```bash
cd audio-pipeline-stress-testing
```

2. **Create Virtual Environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **Verify Installation**
```bash
python -c "import websockets, pandas, matplotlib, psutil; print('All dependencies OK')"
```

### Quick Start
```bash
# Terminal 1
python server.py

# Terminal 2 (wait for server to start)
python stress_test.py

# Terminal 3 (after tests complete)
python dashboard.py
```

---

## Multi-Machine Deployment

### Setup for Distributed Testing

**Machine A (Server)**:
```bash
# Start server accessible from network
python server.py
# Note the IP address and port (default: localhost:8765)
```

**Machine B (Clients)**:
```bash
# Run tests against remote server
python stress_test.py --server ws://[MACHINE_A_IP]:8765 --clients 50 --duration 30
```

### Network Configuration

**Linux/macOS - Open Port in Firewall**:
```bash
# macOS
sudo lsof -i :8765

# Linux
sudo ufw allow 8765
```

**Windows - Open Port in Firewall**:
```powershell
# PowerShell (Admin)
New-NetFirewallRule -DisplayName "Audio Pipeline Server" `
  -Direction Inbound -LocalPort 8765 -Protocol TCP -Action Allow
```

### Performance Tuning for Multi-Machine

**Server Side** (`server.py`):
```python
# Increase backlog and buffer sizes
async with websockets.serve(
    self.handle_client,
    self.host,
    self.port,
    ping_interval=20,
    ping_timeout=10,
    max_size=10 * 1024,      # Increase if needed
    max_queue=32,             # Queue size
    close_timeout=10,         # Close timeout
    compression=None,         # Disable compression for speed
):
```

**Linux - System Limits**:
```bash
# Increase file descriptors
ulimit -n 10000

# Increase socket buffers
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
sysctl -w net.ipv4.tcp_rmem="4096 87380 67108864"
sysctl -w net.ipv4.tcp_wmem="4096 65536 67108864"
```

---

## Docker Deployment

### Dockerfile

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8765

CMD ["python", "server.py"]
```

### Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  server:
    build: .
    ports:
      - "8765:8765"
    volumes:
      - ./logs:/app/logs
      - ./reports:/app/reports
    environment:
      - PYTHONUNBUFFERED=1
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Optional: Run stress test in container
  stress-test:
    build: .
    depends_on:
      - server
    volumes:
      - ./reports:/app/reports
      - ./logs:/app/logs
    command: python stress_test.py --server ws://server:8765
    environment:
      - PYTHONUNBUFFERED=1
```

### Build and Run

```bash
# Build image
docker build -t audio-pipeline-stress-test .

# Run server
docker run -p 8765:8765 -v ./logs:/app/logs -v ./reports:/app/reports audio-pipeline-stress-test

# Or use Docker Compose
docker-compose up -d server
docker-compose run stress-test
```

---

## Kubernetes Deployment

### Server Deployment

Create `server-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: audio-pipeline-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: audio-pipeline-server
  template:
    metadata:
      labels:
        app: audio-pipeline-server
    spec:
      containers:
      - name: server
        image: audio-pipeline-stress-test:latest
        ports:
        - containerPort: 8765
        resources:
          requests:
            memory: "256Mi"
            cpu: "500m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - "import websockets; print('OK')"
          initialDelaySeconds: 10
          periodSeconds: 30
        volumeMounts:
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: logs
        emptyDir: {}
```

### Service

Create `service.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: audio-pipeline-server
spec:
  selector:
    app: audio-pipeline-server
  ports:
  - protocol: TCP
    port: 8765
    targetPort: 8765
  type: LoadBalancer
```

### Deploy to Kubernetes

```bash
# Build and push image to registry
docker build -t your-registry/audio-pipeline:latest .
docker push your-registry/audio-pipeline:latest

# Apply manifests
kubectl apply -f server-deployment.yaml
kubectl apply -f service.yaml

# Check status
kubectl get pods
kubectl get services

# Port forward for testing
kubectl port-forward service/audio-pipeline-server 8765:8765
```

---

## Cloud Deployment (AWS Example)

### EC2 Instance Setup

1. **Launch EC2 Instance**
```bash
# Ubuntu 22.04 LTS, t3.medium
# Security Group: Allow TCP 8765 inbound
```

2. **Connect and Setup**
```bash
ssh -i key.pem ubuntu@instance-ip

# Install Python and dependencies
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip -y

# Clone project
git clone https://github.com/yourname/audio-pipeline-stress-testing.git
cd audio-pipeline-stress-testing

# Setup environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Run Server**
```bash
# Using systemd service
sudo tee /etc/systemd/system/audio-pipeline.service > /dev/null <<EOF
[Unit]
Description=Audio Pipeline Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/audio-pipeline-stress-testing
Environment="PATH=/home/ubuntu/audio-pipeline-stress-testing/venv/bin"
ExecStart=/home/ubuntu/audio-pipeline-stress-testing/venv/bin/python server.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable audio-pipeline
sudo systemctl start audio-pipeline
```

4. **Monitor**
```bash
sudo systemctl status audio-pipeline
sudo journalctl -u audio-pipeline -f
```

---

## CI/CD Integration (GitHub Actions)

Create `.github/workflows/stress-test.yml`:
```yaml
name: Daily Stress Test

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:

jobs:
  stress-test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Start server
      run: |
        python server.py &
        sleep 5
    
    - name: Run stress tests
      run: python stress_test.py --duration 30
    
    - name: Generate dashboard
      run: python dashboard.py
    
    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: stress-test-results
        path: reports/
        retention-days: 30
    
    - name: Compare with baseline
      run: |
        # Add comparison logic
        echo "Comparing results..."
```

---

## Monitoring and Observability

### Logging Configuration

Edit `server.py` to customize logging:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for verbose output
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/server.log"),
        logging.StreamHandler(),
    ],
)
```

### Log Rotation

Add log rotation (create `setup_logging.py`):
```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "logs/server.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

### Metrics Export (Prometheus)

Create `prometheus_exporter.py`:
```python
from prometheus_client import start_http_server, Counter, Gauge, Histogram

# Define metrics
packets_received = Counter('packets_received_total', 'Total packets received')
active_connections = Gauge('active_connections', 'Active connections')
latency_histogram = Histogram('latency_ms', 'Latency in ms', buckets=(1, 5, 10, 20, 50, 100))

# Start metrics server
start_http_server(8000)
```

### Real-time Dashboard (Grafana)

1. Add Prometheus data source pointing to `http://localhost:8000`
2. Create dashboard with:
   - Active connections gauge
   - Throughput graph
   - Latency histogram
   - Packet loss percentage

---

## Performance Optimization

### For Maximum Throughput

1. **Disable Logging**
```python
# In server.py
logging.disable(logging.CRITICAL)
```

2. **Increase Buffer Sizes**
```bash
# Linux
sysctl -w net.core.rmem_max=67108864
sysctl -w net.core.wmem_max=67108864
```

3. **Use Production ASGI Server**
```bash
# Instead of raw asyncio, use Hypercorn
pip install hypercorn
hypercorn server:app
```

### For Maximum Reliability

1. **Enable Connection Pooling**
```python
# In client.py
connection_pool = asyncio.Semaphore(10)
```

2. **Add Health Checks**
```python
async def health_check(request):
    return {"status": "healthy"}
```

3. **Enable Metrics**
```python
# Export metrics to monitoring system
```

---

## Troubleshooting

### Server Won't Start

```bash
# Check if port is in use
netstat -tulpn | grep 8765

# Kill existing process
lsof -i :8765
kill -9 <PID>
```

### Clients Can't Connect

```bash
# Test connectivity
python -c "
import socket
s = socket.socket()
s.connect(('localhost', 8765))
s.close()
"
```

### High Memory Usage

```bash
# Monitor memory in real-time
watch -n 1 'ps aux | grep python'

# Reduce client count
python stress_test.py --clients 50 --duration 30
```

### Connection Timeouts

```bash
# Increase timeout in client.py
reconnect_interval = 10.0  # From 5.0
```

---

## Scaling Guidelines

| Load | Single Machine | Required Setup |
|------|---|---|
| 10-50 clients | ✅ | Laptop/Desktop |
| 50-100 clients | ✅ | Mid-range server |
| 100-500 clients | ⚠️ | Dedicated server |
| 500+ clients | ❌ | Multi-machine setup |

### Scaling Strategy

```
Single Machine (100 clients)
    ↓
Multi-Machine (500 clients)
    ↓
Kubernetes (1000+ clients)
    ↓
Cloud-Native (10000+ clients)
```

---

## Backup and Recovery

### Backup Results

```bash
# Backup reports directory
tar -czf audio-pipeline-backup-$(date +%Y%m%d).tar.gz reports/

# Backup logs
tar -czf audio-pipeline-logs-$(date +%Y%m%d).tar.gz logs/
```

### Automate Backups

```bash
# Create cron job
0 */6 * * * cd /path/to/project && tar -czf backups/results-$(date +\%Y\%m\%d-\%H\%M\%S).tar.gz reports/
```

---

## Security Considerations

### Network Security

1. **Firewall Configuration**
   - Only allow trusted IPs to port 8765
   - Use VPN for remote access

2. **TLS/SSL**
   - Enable WSS (WebSocket Secure) for production
   - Use self-signed certificates for internal testing

3. **Authentication**
   - Add token-based authentication
   - Implement rate limiting

### Data Security

1. **Sensitive Data**
   - Logs may contain timing information
   - Sanitize before sharing

2. **Access Control**
   - Restrict who can run tests
   - Audit test executions

---

## Performance Baseline

### Expected Performance

On a mid-range machine (4-core CPU, 8GB RAM):
- ✅ 10 clients: Smooth, <2% CPU
- ✅ 50 clients: Smooth, 10-15% CPU
- ✅ 100 clients: Good, 25-35% CPU
- ⚠️ 500 clients: Acceptable, 60-75% CPU

### If Below Baseline

1. Check system resources
2. Review logs for errors
3. Check network connectivity
4. Profile with `cProfile`

---

## References

- **Docker Docs**: https://docs.docker.com/
- **Kubernetes Docs**: https://kubernetes.io/docs/
- **AWS EC2**: https://aws.amazon.com/ec2/
- **Prometheus**: https://prometheus.io/
- **Grafana**: https://grafana.com/
