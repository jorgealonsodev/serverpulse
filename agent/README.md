# ServerPulse Agent

Standalone Python agent that collects system metrics and sends them to the ServerPulse API.

## Overview

The agent runs as a systemd service, collecting metrics every 15 seconds via `psutil` and POSTing them to `POST /api/v1/metrics/ingest`. It handles retries with exponential backoff and shuts down cleanly on SIGTERM.

## Requirements

- Python 3.8+
- `psutil` and `requests` (installed by the script)
- systemd (Ubuntu 24.04+)

## Installation

### One-liner install

```bash
curl -fsSL https://raw.githubusercontent.com/jorgealonsodev/serverpulse/main/agent/install.sh | bash -s -- --url https://api.example.com --token your-agent-token
```

### Manual install

1. Install dependencies:
   ```bash
   pip3 install psutil requests
   ```

2. Copy the agent script:
   ```bash
   sudo cp agent/serverpulse-agent.py /usr/local/bin/serverpulse-agent
   sudo chmod +x /usr/local/bin/serverpulse-agent
   ```

3. Install the systemd service:
   ```bash
   sudo cp agent/serverpulse-agent.service /etc/systemd/system/
   sudo systemctl daemon-reload
   ```

4. Create the config file:
   ```bash
   sudo mkdir -p /etc/serverpulse
   sudo cat > /etc/serverpulse/agent.conf <<EOF
   [serverpulse]
   api_url = https://api.example.com
   api_token = your-agent-token
   EOF
   sudo chmod 600 /etc/serverpulse/agent.conf
   sudo chown serverpulse:serverpulse /etc/serverpulse/agent.conf
   ```

5. Enable and start:
   ```bash
   sudo systemctl enable serverpulse-agent
   sudo systemctl start serverpulse-agent
   ```

## Configuration

Config file: `/etc/serverpulse/agent.conf`

```ini
[serverpulse]
api_url = https://api.example.com
api_token = your-agent-token
```

| Key | Description |
|-----|-------------|
| `api_url` | Base URL of the ServerPulse API (no trailing slash) |
| `api_token` | Agent token from the ServerPulse server configuration |

## Verification

Check service status:
```bash
systemctl status serverpulse-agent
```

View live logs:
```bash
journalctl -u serverpulse-agent -f
```

Verify metrics are arriving via the API:
```bash
curl -H "Authorization: Bearer <user-jwt>" \
  "http://localhost:8000/api/v1/servers/<server-id>/metrics?from=2025-01-01T00:00:00Z&to=2025-12-31T23:59:59Z"
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Config file not found` | `/etc/serverpulse/agent.conf` missing | Create config file per instructions above |
| `Authentication failed` | Invalid agent token | Regenerate token via ServerPulse API |
| `Request failed: Connection refused` | Backend unreachable | Check `api_url` and network connectivity |
| Service won't start | Python dependencies missing | Run `pip3 install psutil requests` |

## Uninstall

```bash
sudo systemctl stop serverpulse-agent
sudo systemctl disable serverpulse-agent
sudo rm /etc/systemd/system/serverpulse-agent.service
sudo rm /usr/local/bin/serverpulse-agent
sudo rm -rf /etc/serverpulse
sudo userdel serverpulse
sudo systemctl daemon-reload
```
