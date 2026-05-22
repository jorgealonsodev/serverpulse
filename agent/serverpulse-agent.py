#!/usr/bin/env python3
"""ServerPulse Agent — collects system metrics and sends to ServerPulse API."""

import configparser
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone

import psutil
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("serverpulse-agent")

CONFIG_PATH = "/etc/serverpulse/agent.conf"
COLLECT_INTERVAL = 15
MAX_BACKOFF = 300

running = True


def signal_handler(signum, frame):
    global running
    logger.info("Received signal %s, shutting down...", signum)
    running = False


def load_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_PATH):
        logger.error("Config file not found: %s", CONFIG_PATH)
        sys.exit(1)
    config.read(CONFIG_PATH)
    try:
        api_url = config["serverpulse"]["api_url"].rstrip("/")
        api_token = config["serverpulse"]["api_token"]
    except KeyError as e:
        logger.error("Missing config key: %s", e)
        sys.exit(1)
    return api_url, api_token


def collect_metrics():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()

    boot_time = psutil.boot_time()
    uptime = int(time.time() - boot_time) if boot_time else 0

    load = os.getloadavg()

    return {
        "cpu_percent": round(cpu, 2),
        "ram_percent": round(ram.percent, 2),
        "ram_used_mb": ram.used // (1024 * 1024),
        "ram_total_mb": ram.total // (1024 * 1024),
        "disk_percent": round(disk.percent, 2),
        "disk_used_gb": round(disk.used / (1024**3), 2),
        "disk_total_gb": round(disk.total / (1024**3), 2),
        "net_rx_bytes": net.bytes_recv,
        "net_tx_bytes": net.bytes_sent,
        "uptime_seconds": uptime,
        "load_avg_1": round(load[0], 2) if load else None,
        "load_avg_5": round(load[1], 2) if load else None,
        "load_avg_15": round(load[2], 2) if load else None,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


def send_metrics(api_url, api_token, data):
    url = f"{api_url}/api/v1/metrics/ingest"
    headers = {"X-Agent-Token": api_token, "Content-Type": "application/json"}
    backoff = 1
    while True:
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=10)
            if resp.status_code == 202:
                return True
            elif resp.status_code == 401:
                logger.error("Authentication failed — invalid agent token")
                return False
            else:
                logger.warning("Unexpected status %s: %s", resp.status_code, resp.text)
        except requests.RequestException as e:
            logger.warning("Request failed: %s (retry in %ss)", e, min(backoff, MAX_BACKOFF))
            time.sleep(min(backoff, MAX_BACKOFF))
            backoff = min(backoff * 2, MAX_BACKOFF)
            continue
        break
    return False


def main():
    global running
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    api_url, api_token = load_config()
    logger.info("ServerPulse Agent started — sending to %s every %ss", api_url, COLLECT_INTERVAL)

    while running:
        try:
            data = collect_metrics()
            logger.debug("Collected metrics: %s", json.dumps(data))
            send_metrics(api_url, api_token, data)
        except Exception as e:
            logger.error("Collection error: %s", e)

        # Sleep in small increments to respond to signals
        for _ in range(COLLECT_INTERVAL):
            if not running:
                break
            time.sleep(1)

    logger.info("Agent stopped.")


if __name__ == "__main__":
    main()
