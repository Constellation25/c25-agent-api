#!/usr/bin/env python3
"""
C25 Sovereign Path Mesh - Production MCP Client & Agent Orchestrator
Connects to Termux MCP Server (port 8989) and provides global ecosystem awareness.
"""

import os
import sys
import json
import hashlib
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Configuration
MCP_SERVER_URL = os.getenv("C25_MCP_URL", "http://127.0.0.1:8989")
MESH_PORT = int(os.getenv("C25_MCP_PORT", "3000"))
REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "registry")

@dataclass
class NodeInfo:
    """Represents a node in the ecosystem"""
    path: str
    type: str
    size: int
    hash: str
    endpoints: List[str]
    dependencies: List[str]
    last_indexed: str

@dataclass
class AgentCapability:
    """Defines what an agent can do"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    endpoint: str
    method: str

class C25MeshCore:
    """Core engine for the Sovereign Path Mesh"""
    
    def __init__(self, mcp_url: str = MCP_SERVER_URL):
        self.mcp_url = mcp_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.node_cache: Dict[str, NodeInfo] = {}
        self.agent_registry: Dict[str, AgentCapability] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load existing registry if available"""
        registry_file = os.path.join(REGISTRY_PATH, "node_registry.json")
        if os.path.exists(registry_file):
            try:
                with open(registry_file, 'r') as f:
                    data = json.load(f)
                    self.node_cache = {k: NodeInfo(**v) for k, v in data.get('nodes', {}).items()}
                    print(f"[MESH] Loaded {len(self.node_cache)} nodes from cache")
            except Exception as e:
                print(f"[MESH] Cache load failed: {e}")
    
    def _save_registry(self):
        """Persist registry to disk"""
        os.makedirs(REGISTRY_PATH, exist_ok=True)
        registry_file = os.path.join(REGISTRY_PATH, "node_registry.json")
        data = {
            'nodes': {k: asdict(v) for k, v in self.node_cache.items()},
            'agents': {k: asdict(v) for k, v in self.agent_registry.items()},
            'updated': datetime.utcnow().isoformat()
        }
        with open(registry_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_ecosystem_stats(self) -> Dict[str, Any]:
        """Fetch global stats from MCP server"""
        try:
            resp = self.session.get(f"{self.mcp_url}/stats", timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e), "total": len(self.node_cache)}
    
    def search_nodes(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search for nodes matching query"""
        try:
            resp = self.session.get(
                f"{self.mcp_url}/search",
                params={"query": query, "limit": limit},
                timeout=10
            )
            resp.raise_for_status()
            results = resp.json().get('results', [])
            
            # Update cache
            for r in results:
                node_hash = hashlib.sha256(r['path'].encode()).hexdigest()[:16]
                self.node_cache[r['path']] = NodeInfo(
                    path=r['path'],
                    type=r.get('type', 'unknown'),
                    size=r.get('size', 0),
                    hash=node_hash,
                    endpoints=[],
                    dependencies=[],
                    last_indexed=datetime.utcnow().isoformat()
                )
            
            self._save_registry()
            return results
        except Exception as e:
            print(f"[MESH] Search failed: {e}")
            return []
    
    def discover_endpoints(self, file_path: str) -> List[str]:
        """Analyze file to discover API endpoints"""
        endpoints = []
        try:
            # Check if file exists locally or fetch from MCP
            if os.path.exists(file_path):
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()
            else:
                # Could fetch content via MCP if needed
                content = ""
            
            # Pattern matching for common endpoint definitions
            patterns = [
                '@app.get("/' , '@app.post("/', '@app.put("/', '@app.delete("/",',
                'router.get("', 'router.post("', 'FastAPI(', 'APIRouter('
            ]
            
            for pattern in patterns:
                if pattern in content:
                    # Extract endpoint paths (simplified)
                    import re
                    matches = re.findall(r'["\'](/[^"\']+)', content)
                    endpoints.extend(matches)
            
            return list(set(endpoints))
        except Exception as e:
            return []
    
    def register_agent(self, agent_name: str, capability: AgentCapability):
        """Register an agent's capability in the mesh"""
        self.agent_registry[agent_name] = capability
        self._save_registry()
        print(f"[MESH] Registered agent: {agent_name} -> {capability.endpoint}")
    
    def route_task(self, task_description: str, target_agent: Optional[str] = None) -> Dict[str, Any]:
        """Route a task through the mesh to appropriate agent"""
        # Step 1: Search for relevant context
        context_results = self.search_nodes(task_description, limit=10)
        
        # Step 2: Build enriched payload
        payload = {
            "task": task_description,
            "context_files": [r['path'] for r in context_results],
            "timestamp": datetime.utcnow().isoformat(),
            "mesh_stats": self.get_ecosystem_stats()
        }
        
        # Step 3: Dispatch via MCP
        try:
            resp = self.session.post(f"{self.mcp_url}/task", json=payload, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            
            if target_agent and target_agent in self.agent_registry:
                # Forward to specific agent endpoint
                agent = self.agent_registry[target_agent]
                agent_resp = requests.post(
                    f"{self.mcp_url}{agent.endpoint}",
                    json={"task": result, "context": context_results},
                    timeout=60
                )
                result['agent_response'] = agent_resp.json()
            
            return result
        except Exception as e:
            return {"error": str(e), "status": "dispatch_failed"}
    
    def build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build a graph of file dependencies across the ecosystem"""
        graph = {}
        # This would require parsing imports/requires across all files
        # For now, return cached relationships
        for path, node in self.node_cache.items():
            graph[path] = node.dependencies
        return graph
    
    def get_node_full_context(self, path: str) -> Optional[Dict[str, Any]]:
        """Get complete context for a specific node including code analysis"""
        if path not in self.node_cache:
            self.search_nodes(path, limit=1)
        
        if path in self.node_cache:
            node = self.node_cache[path]
            return {
                **asdict(node),
                "endpoints": self.discover_endpoints(path),
                "ecosystem_position": self._calculate_node_importance(path)
            }
        return None
    
    def _calculate_node_importance(self, path: str) -> Dict[str, float]:
        """Calculate importance metrics for a node"""
        # Simplified scoring based on file type and path depth
        score = 1.0
        if '.py' in path: score *= 2.0
        if 'agent' in path.lower(): score *= 3.0
        if 'main' in path.lower() or 'index' in path.lower(): score *= 2.5
        return {"importance_score": score, "centrality": min(score / 10.0, 1.0)}


def initialize_mesh():
    """Initialize the C25 Mesh and run discovery"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     🪐 C25 SOVEREIGN PATH MESH INITIALIZING                 ║")
    print("║     Connecting to MCP Server...                             ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    mesh = C25MeshCore()
    
    # Get stats
    stats = mesh.get_ecosystem_stats()
    print(f"\n[MESH] Ecosystem Stats: {json.dumps(stats, indent=2)}")
    
    # Discover key nodes
    print("\n[MESH] Discovering critical nodes...")
    critical_paths = ['agent', 'api', 'endpoint', 'route', 'main', 'index']
    
    for query in critical_paths:
        results = mesh.search_nodes(query, limit=50)
        print(f"  Found {len(results)} nodes matching '{query}'")
        
        # Analyze first few results for endpoints
        for r in results[:5]:
            endpoints = mesh.discover_endpoints(r['path'])
            if endpoints:
                print(f"    → {r['path']}: {endpoints[:3]}")
    
    # Save final registry
    mesh._save_registry()
    print(f"\n[MESH] Registry saved with {len(mesh.node_cache)} nodes")
    print(f"[MESH] Mesh ready on port {MESH_PORT}")
    
    return mesh


if __name__ == "__main__":
    mesh = initialize_mesh()
    
    # Example: Route a test task
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        print(f"\n[MESH] Routing task: {task}")
        result = mesh.route_task(task)
        print(f"[MESH] Task result: {json.dumps(result, indent=2)}")
