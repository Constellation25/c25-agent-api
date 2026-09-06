#!/data/data/com.termux/files/usr/bin/env bash
set -euo pipefail
echo "Booting c25-agent-api..."
python -m c25_agent_api 2>/dev/null || python c25_agent_api/*.py 2>/dev/null || echo "No bootable entry point"
