#!/bin/bash
set -e

# Defaults
API_URL=""
API_TOKEN=""
CONFIG_DIR="/etc/serverpulse"
BIN_DIR="/usr/local/bin"
SERVICE_DIR="/etc/systemd/system"
GITHUB_RAW="https://raw.githubusercontent.com/jorgealonsodev/serverpulse/main/agent"
DRY_RUN=false

usage() {
    echo "Usage: $0 --url <api_url> --token <api_token> [--dry-run]"
    echo ""
    echo "Options:"
    echo "  --url      ServerPulse API URL (e.g. https://api.example.com)"
    echo "  --token    Agent API token (from ServerPulse server config)"
    echo "  --dry-run  Print actions without executing them"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --url) API_URL="$2"; shift 2 ;;
        --token) API_TOKEN="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        *) usage ;;
    esac
done

[[ -z "$API_URL" || -z "$API_TOKEN" ]] && usage

echo "=== ServerPulse Agent Installer ==="
if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY RUN] No changes will be made."
fi

run() {
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "[DRY RUN] $*"
    else
        "$@"
    fi
}

# Create system user
if ! id -u serverpulse >/dev/null 2>&1; then
    echo "Creating serverpulse user..."
    run useradd --system --no-create-home --shell /usr/sbin/nologin serverpulse
else
    echo "serverpulse user already exists."
fi

# Install dependencies
echo "Installing Python dependencies..."
run pip3 install psutil requests 2>/dev/null || run pip install psutil requests

# Download agent
echo "Downloading agent..."
run curl -fsSL "$GITHUB_RAW/serverpulse-agent.py" -o "$BIN_DIR/serverpulse-agent"
run chmod +x "$BIN_DIR/serverpulse-agent"

# Download service file
echo "Installing systemd service..."
run curl -fsSL "$GITHUB_RAW/serverpulse-agent.service" -o "$SERVICE_DIR/serverpulse-agent.service"

# Create config
echo "Creating config..."
run mkdir -p "$CONFIG_DIR"
if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY RUN] Would write $CONFIG_DIR/agent.conf with api_url=$API_URL"
else
    cat > "$CONFIG_DIR/agent.conf" <<EOF
[serverpulse]
api_url = $API_URL
api_token = $API_TOKEN
EOF
    run chmod 600 "$CONFIG_DIR/agent.conf"
    run chown serverpulse:serverpulse "$CONFIG_DIR/agent.conf"
fi

# Enable and start
if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY RUN] Would run: systemctl daemon-reload"
    echo "[DRY RUN] Would run: systemctl enable serverpulse-agent"
    echo "[DRY RUN] Would run: systemctl start serverpulse-agent"
else
    run systemctl daemon-reload
    run systemctl enable serverpulse-agent
    run systemctl start serverpulse-agent
fi

echo "=== Agent installed and running! ==="
echo "Check status: systemctl status serverpulse-agent"
echo "View logs: journalctl -u serverpulse-agent -f"
