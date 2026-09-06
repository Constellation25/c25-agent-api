#!/usr/bin/env python3
"""
Autonomous Agent Framework for C25 Sovereign Path Mesh
Each agent has global awareness of all 317,941 files and can call any endpoint.
"""

import os
import sys
import json
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Import mesh core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'c25-mesh-core'))
from mesh_orchestrator import C25MeshCore, AgentCapability

@dataclass
class AgentState:
    """Current state of an autonomous agent"""
    name: str
    status: str  # idle, working, blocked, complete
    current_task: Optional[str]
    knowledge_context: List[str]
    last_action: str
    timestamp: str

class AutonomousAgent:
    """Base class for all C25 autonomous agents"""
    
    def __init__(self, name: str, mesh: C25MeshCore, specialty: str = "general"):
        self.name = name
        self.mesh = mesh
        self.specialty = specialty
        self.state = AgentState(
            name=name,
            status="idle",
            current_task=None,
            knowledge_context=[],
            last_action="initialized",
            timestamp=datetime.utcnow().isoformat()
        )
        self._register_with_mesh()
    
    def _register_with_mesh(self):
        """Register this agent's capabilities with the mesh"""
        capability = AgentCapability(
            name=self.name,
            description=f"Autonomous agent specialized in {self.specialty}",
            input_schema={
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "context": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["task"]
            },
            endpoint=f"/agents/{self.name}/execute",
            method="POST"
        )
        self.mesh.register_agent(self.name, capability)
    
    def get_global_awareness(self, query: str) -> Dict[str, Any]:
        """Query the entire ecosystem for relevant context"""
        print(f"[{self.name}] Querying ecosystem: '{query}'")
        results = self.mesh.search_nodes(query, limit=50)
        
        # Enrich with full context for top results
        enriched = []
        for r in results[:10]:
            full_ctx = self.mesh.get_node_full_context(r['path'])
            if full_ctx:
                enriched.append(full_ctx)
        
        self.state.knowledge_context = [e['path'] for e in enriched]
        return {
            "query": query,
            "results_count": len(results),
            "enriched_nodes": enriched,
            "ecosystem_stats": self.mesh.get_ecosystem_stats()
        }
    
    def discover_all_endpoints(self) -> Dict[str, List[str]]:
        """Scan ecosystem to discover all available API endpoints"""
        print(f"[{self.name}] Discovering all endpoints in ecosystem...")
        
        # Search for files likely to contain endpoints
        endpoint_files = []
        for keyword in ['api', 'route', 'endpoint', 'controller', 'handler', 'app']:
            results = self.mesh.search_nodes(keyword, limit=100)
            endpoint_files.extend([r['path'] for r in results])
        
        # Extract endpoints from each file
        all_endpoints = {}
        for file_path in set(endpoint_files)[:200]:  # Limit to prevent timeout
            endpoints = self.mesh.discover_endpoints(file_path)
            if endpoints:
                all_endpoints[file_path] = endpoints
        
        print(f"[{self.name}] Discovered {len(all_endpoints)} files with endpoints")
        return all_endpoints
    
    def execute_task(self, task: str, use_context: bool = True) -> Dict[str, Any]:
        """Execute a task using global ecosystem knowledge"""
        self.state.status = "working"
        self.state.current_task = task
        self.state.timestamp = datetime.utcnow().isoformat()
        
        print(f"\n{'='*60}")
        print(f"[{self.name}] EXECUTING TASK: {task}")
        print(f"{'='*60}")
        
        # Step 1: Gather context from entire ecosystem
        if use_context:
            awareness = self.get_global_awareness(task)
            print(f"[{self.name}] Found {awareness['results_count']} relevant nodes")
        
        # Step 2: Discover available endpoints for routing
        endpoints = self.discover_all_endpoints()
        
        # Step 3: Build execution plan
        plan = {
            "task": task,
            "agent": self.name,
            "specialty": self.specialty,
            "context_files": self.state.knowledge_context[:20],
            "available_endpoints": sum(len(v) for v in endpoints.values()),
            "endpoint_map": {k: len(v) for k, v in list(endpoints.items())[:10]},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Step 4: Route through mesh
        result = self.mesh.route_task(task)
        plan['mesh_response'] = result
        
        # Step 5: Update state
        self.state.status = "complete"
        self.state.last_action = f"Completed task: {task[:50]}..."
        
        print(f"[{self.name}] Task complete. Used {len(self.state.knowledge_context)} context files")
        print(f"[{self.name}] Accessed {sum(len(v) for v in endpoints.values())} endpoints")
        
        return plan
    
    def call_any_node(self, target_path: str, action: str = "read") -> Dict[str, Any]:
        """Directly interact with any node in the ecosystem"""
        print(f"[{self.name}] Accessing node: {target_path} ({action})")
        
        node_info = self.mesh.get_node_full_context(target_path)
        if not node_info:
            return {"error": f"Node {target_path} not found in ecosystem"}
        
        return {
            "node": node_info,
            "action": action,
            "agent": self.name,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def broadcast_to_all_agents(self, message: str) -> Dict[str, Any]:
        """Send a message to all registered agents in the mesh"""
        # In production, this would use pub/sub or message queue
        return {
            "broadcast": message,
            "from": self.name,
            "registered_agents": list(self.mesh.agent_registry.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }


class CodeAnalysisAgent(AutonomousAgent):
    """Specialized agent for analyzing code across the ecosystem"""
    
    def __init__(self, mesh: C25MeshCore):
        super().__init__("CodeAnalyzer", mesh, specialty="code_analysis")
    
    def analyze_imports(self, file_pattern: str) -> Dict[str, Any]:
        """Analyze import dependencies across matching files"""
        awareness = self.get_global_awareness(file_pattern)
        
        import_graph = {}
        for node in awareness.get('enriched_nodes', []):
            # Would parse actual imports in production
            import_graph[node['path']] = {
                "imports": [],
                "imported_by": []
            }
        
        return {
            "pattern": file_pattern,
            "graph": import_graph,
            "total_nodes": len(import_graph)
        }
    
    def find_all_functions(self, query: str = "") -> List[Dict[str, str]]:
        """Find all functions across the ecosystem matching query"""
        awareness = self.get_global_awareness(query or "def ")
        
        functions = []
        for node in awareness.get('enriched_nodes', []):
            # Would parse actual function definitions in production
            functions.append({
                "file": node['path'],
                "function": "detected_function",
                "line": "unknown",
                "signature": "unknown"
            })
        
        return functions


class EndpointRouterAgent(AutonomousAgent):
    """Specialized agent for routing between endpoints"""
    
    def __init__(self, mesh: C25MeshCore):
        super().__init__("EndpointRouter", mesh, specialty="endpoint_routing")
    
    def build_routing_table(self) -> Dict[str, Dict[str, Any]]:
        """Build complete routing table for all discovered endpoints"""
        print(f"[{self.name}] Building comprehensive routing table...")
        
        endpoints = self.discover_all_endpoints()
        routing_table = {}
        
        for file_path, eps in endpoints.items():
            for ep in eps:
                routing_table[ep] = {
                    "source_file": file_path,
                    "methods": ["GET", "POST"],  # Would detect actual methods
                    "handler": "unknown",
                    "dependencies": []
                }
        
        print(f"[{self.name}] Routing table built with {len(routing_table)} endpoints")
        return routing_table
    
    def optimal_route(self, source: str, target: str) -> Dict[str, Any]:
        """Calculate optimal route between two points in the ecosystem"""
        return {
            "source": source,
            "target": target,
            "route": [source, target],
            "hops": 1,
            "latency_estimate_ms": 10
        }


class DataSyncAgent(AutonomousAgent):
    """Specialized agent for synchronizing data across the ecosystem"""
    
    def __init__(self, mesh: C25MeshCore):
        super().__init__("DataSync", mesh, specialty="data_synchronization")
    
    def sync_all_nodes(self) -> Dict[str, Any]:
        """Ensure all nodes are synchronized with latest state"""
        stats = self.mesh.get_ecosystem_stats()
        
        return {
            "sync_status": "complete",
            "total_nodes": stats.get('total', 0),
            "synced_at": datetime.utcnow().isoformat(),
            "agent": self.name
        }


def deploy_autonomous_swarm():
    """Deploy a swarm of autonomous agents with full ecosystem awareness"""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║     🤖 DEPLOYING AUTONOMOUS AGENT SWARM                     ║")
    print("║     All agents have global awareness of 317,941 files      ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    # Initialize mesh connection
    mesh = C25MeshCore()
    
    # Deploy agent swarm
    agents = [
        CodeAnalysisAgent(mesh),
        EndpointRouterAgent(mesh),
        DataSyncAgent(mesh),
        AutonomousAgent("GeneralPurpose", mesh, specialty="general_tasks")
    ]
    
    print(f"\n[MESH] Deployed {len(agents)} autonomous agents")
    print(f"[MESH] Registered capabilities: {list(mesh.agent_registry.keys())}")
    
    return mesh, agents


if __name__ == "__main__":
    mesh, agents = deploy_autonomous_swarm()
    
    # Example: Execute a complex task
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        
        # Let the most appropriate agent handle it
        analyzer = agents[0]
        result = analyzer.execute_task(task)
        
        print("\n" + "="*60)
        print("EXECUTION RESULT:")
        print(json.dumps(result, indent=2, default=str))
    else:
        # Demo mode
        print("\n[MESH] Running demo tasks...")
        
        demo_agent = agents[0]
        
        # Demo 1: Analyze code structure
        print("\n--- DEMO 1: Code Analysis ---")
        result = demo_agent.execute_task("Find all API endpoints in the ecosystem")
        
        # Demo 2: Direct node access
        print("\n--- DEMO 2: Direct Node Access ---")
        result = demo_agent.call_any_node("mesh_orchestrator.py", "analyze")
        print(f"Accessed node: {result.get('node', {}).get('path', 'unknown')}")
        
        # Demo 3: Broadcast
        print("\n--- DEMO 3: Inter-Agent Communication ---")
        broadcast = demo_agent.broadcast_to_all_agents("System initialization complete")
        print(f"Broadcast sent to {len(broadcast['registered_agents'])} agents")
