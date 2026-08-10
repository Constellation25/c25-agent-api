#!/bin/bash
# ==============================================================================
# 🛰️ C25 SOVEREIGN DISCOVERY PROTOCOL
# Maps your entire Termux codebase → ~/c25_discovery_map.json
# ==============================================================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

OUT="/workspace/c25_discovery_map.json"
echo -e "${CYAN}[*] C25 Discovery Protocol initiated...${NC}"
echo -e "${YELLOW}[*] Scanning entire filesystem for sovereign modules...${NC}"

# The 27 known sovereign modules
MODULES=(
  "FacePrintPay" "faceprintpays" "biometric"
  "MyBuyO" "mybuyo" "cbdc" "digital-currency"
  "VideoCourts" "videocourts" "legal-tech"
  "agentik" "agent-framework"
  "TotalRecall" "totalrecall" "forensic" "evidence"
  "Constellation25" "constellation25" "c25"
  "AiMetaverse" "aimetaverse" "metaverse"
  "AiKre8tive" "aikre8tive" "kre8tive"
  "sovereign" "sovereign-genesis" "sovereign-kre8tive"
  "planetary-agents" "earth-agent" "moon-agent" "mars-agent" "jupiter-agent" "saturn-agent" "uranus-agent" "neptune-agent" "pluto-agent" "venus-agent" "mercury-agent" "andromeda-agent"
  "claude-artifacts" "artifacts-downloader"
  "empathic-voice" "voice-interface"
  "json-formatter" "coral-server" "repodepot" "ai-records"
)

# Initialize JSON output
echo "{" > "$OUT"
echo '  "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",' >> "$OUT"
echo '  "modules": [' >> "$OUT"

FIRST=true
for module in "${MODULES[@]}"; do
  echo -e "${YELLOW}[*] Scanning for: ${module}${NC}"
  
  # Find all files containing this module name
  MATCHES=$(grep -rli --exclude-dir={node_modules,.git,.next,.vercel,cache,tmp,venv,env} "$module" "/workspace" 2>/dev/null | head -50 || true)
  
  if [ -n "$MATCHES" ]; then
    COUNT=$(echo "$MATCHES" | wc -l)
    
    # Find entry points in matched directories
    DIRS=$(echo "$MATCHES" | xargs -I{} dirname {} | sort -u)
    
    ENTRY_POINTS=""
    for dir in $DIRS; do
      for ep in "app.py" "main.py" "index.js" "server.js" "vercel.json" "api/index.py" "api/index.js" "package.json" "requirements.txt" "Dockerfile"; do
        if [ -f "$dir/$ep" ]; then
          ENTRY_POINTS="$ENTRY_POINTS$dir/$ep,"
        fi
      done
    done
    ENTRY_POINTS=$(echo "$ENTRY_POINTS" | sed 's/,$//')
    
    # Find orchestrator files
    ORCHESTRATORS=$(grep -rli --exclude-dir={node_modules,.git,.next,.vercel} -E "(router|orchestrat|gateway|api|dispatch|route)" "/workspace" 2>/dev/null | head -20 || true)
    ORCH_LIST=$(echo "$ORCHESTRATORS" | tr '\n' ',' | sed 's/,$//')
    
    # Build JSON entry
    if [ "$FIRST" = true ]; then
      FIRST=false
    else
      echo "," >> "$OUT"
    fi
    
    echo "    {" >> "$OUT"
    echo "      \"name\": \"$module\"," >> "$OUT"
    echo "      \"file_count\": $COUNT," >> "$OUT"
    echo "      \"locations\": [" >> "$OUT"
    echo "$MATCHES" | while read -r f; do
      echo "        \"$f\"," >> "$OUT"
    done
    # Fix trailing comma
    sed -i '$ s/,$//' "$OUT"
    echo "      ]," >> "$OUT"
    echo "      \"entry_points\": [$(echo "$ENTRY_POINTS" | sed 's/,/", "/g' | sed 's/^/"/' | sed 's/$/"/')]," >> "$OUT"
    echo "      \"orchestrators\": [$(echo "$ORCH_LIST" | sed 's/,/", "/g' | sed 's/^/"/' | sed 's/$/"/')]" >> "$OUT"
    echo -n "    }" >> "$OUT"
  fi
done

echo "" >> "$OUT"
echo "  ]," >> "$OUT"

# Global entry point scan
echo -e "${YELLOW}[*] Scanning for global entry points...${NC}"
GLOBAL_EPS=$(find "/workspace" -type f \( -name "app.py" -o -name "main.py" -o -name "index.js" -o -name "server.js" -o -name "vercel.json" \) -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null | head -100 || true)
echo '  "global_entry_points": [' >> "$OUT"
echo "$GLOBAL_EPS" | while read -r f; do
  echo "    \"$f\"," >> "$OUT"
done
sed -i '$ s/,$//' "$OUT"
echo "  ]," >> "$OUT"

# Global orchestrator scan
echo -e "${YELLOW}[*] Scanning for orchestrators & routers...${NC}"
GLOBAL_ORCH=$(grep -rli --exclude-dir={node_modules,.git,.next,.vercel} -E "(router|orchestrat|gateway|api_gateway|dispatch)" "/workspace" 2>/dev/null | head -50 || true)
echo '  "global_orchestrators": [' >> "$OUT"
echo "$GLOBAL_ORCH" | while read -r f; do
  echo "    \"$f\"," >> "$OUT"
done
sed -i '$ s/,$//' "$OUT"
echo "  ]," >> "$OUT"

# Vercel project detection
echo -e "${YELLOW}[*] Detecting Vercel projects...${NC}"
VERCEL_PROJECTS=$(find "/workspace" -name "vercel.json" -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null | head -50 || true)
echo '  "vercel_projects": [' >> "$OUT"
echo "$VERCEL_PROJECTS" | while read -r f; do
  echo "    \"$(dirname $f)\"," >> "$OUT"
done
sed -i '$ s/,$//' "$OUT"
echo "  ]," >> "$OUT"

# GitHub repo detection
echo -e "${YELLOW}[*] Detecting Git repositories...${NC}"
GIT_REPOS=$(find "/workspace" -type d -name ".git" -not -path "*/node_modules/*" 2>/dev/null | head -100 || true)
echo '  "git_repositories": [' >> "$OUT"
echo "$GIT_REPOS" | while read -r f; do
  REPO_DIR=$(dirname "$f")
  REMOTE=$(cd "$REPO_DIR" && git config --get remote.origin.url 2>/dev/null || echo "no-remote")
  BRANCH=$(cd "$REPO_DIR" && git branch --show-current 2>/dev/null || echo "no-branch")
  echo "    {\"path\": \"$REPO_DIR\", \"remote\": \"$REMOTE\", \"branch\": \"$BRANCH\"}," >> "$OUT"
done
sed -i '$ s/,$//' "$OUT"
echo "  ]," >> "$OUT"

# Obsidian vault detection
echo -e "${YELLOW}[*] Detecting Obsidian vaults...${NC}"
OBSIDIAN=$(find "/workspace" -name ".obsidian" -type d 2>/dev/null | head -10 || true)
echo '  "obsidian_vaults": [' >> "$OUT"
echo "$OBSIDIAN" | while read -r f; do
  echo "    \"$(dirname $f)\"," >> "$OUT"
done
sed -i '$ s/,$//' "$OUT"
echo "  ]" >> "$OUT"

echo "}" >> "$OUT"

echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}[✓] Discovery complete!${NC}"
echo -e "${CYAN}Map written to: $OUT${NC}"
echo -e "${YELLOW}[*] Now paste the contents of this file back to me.${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"

# Auto-cat the output for easy copy-paste
echo -e "\n${CYAN}--- MAP CONTENTS (copy everything below) ---${NC}"
cat "$OUT"
echo -e "\n${CYAN}--- END MAP ---${NC}"

