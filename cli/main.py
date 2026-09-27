"""
VeloceGrid Tactical CLI: Real-Time Agentic Mesh Orchestrator
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from velocegrid.engine.mesh_router import MeshRouter, DAGNode
from velocegrid.engine.token_budgeter import TokenBudgeter
from velocegrid.engine.speculative_verifier import SpeculativeVerifier
from velocegrid.engine.nebius_client import NebiusClient

def print_banner():
    banner = """
\033[1;36m██╗   ██╗███████╗██╗      ██████╗  ██████╗███████╗ ██████╗ ██████╗ ██╗██████╗ 
██║   ██║██╔════╝██║     ██╔═══██╗██╔════╝██╔════╝██╔════╝ ██╔══██╗██║██╔══██╗
██║   ██║█████╗  ██║     ██║   ██║██║     █████╗  ██║  ███╗██████╔╝██║██║  ██║
╚██╗ ██╔╝██╔══╝  ██║     ██║   ██║██║     ██╔══╝  ██║   ██║██╔══██╗██║██║  ██║
 ╚████╔╝ ███████╗███████╗╚██████╔╝╚██████╗███████╗╚██████╔╝██║  ██║██║██████╔╝
  ╚═══╝  ╚══════╝╚══════╝ ╚═════╝  ╚═════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝ \033[0m
  \033[1;33m► Nebius Token Factory & NVIDIA Nemotron Agentic Execution Mesh\033[0m
  \033[90mDeterministic Speculative Graph Orchestration • 0.000s Local Core\033[0m
"""
    print(banner)

def run_workflow_demo(workflow_type: str = "refactor"):
    print_banner()
    router = MeshRouter()
    budgeter = TokenBudgeter(max_pipeline_budget_usd=10.0)
    verifier = SpeculativeVerifier()
    client = NebiusClient()

    print(f"\033[1;32m[+] Initializing Workflow Graph: '{workflow_type.upper()}'\033[0m")
    
    if workflow_type == "refactor":
        router.add_node(DAGNode("ingest", "Codebase AST Ingestion", "nvidia/nemotron-mini-4b", "Analyze AST for legacy patterns", artifact_type="text"))
        router.add_node(DAGNode("lint", "Speculative Linting Gate", "nvidia/nemotron-4-70b", "Check schema & invariants", dependencies=["ingest"], artifact_type="json"))
        router.add_node(DAGNode("optimize", "Algorithmic Vectorizer", "nvidia/nemotron-4-340b", "Optimize compute loops", dependencies=["ingest"], artifact_type="python"))
        router.add_node(DAGNode("synthesis", "Final Refactor Synthesis", "nvidia/nemotron-4-340b", "Merge vectorization with AST safety constraints", dependencies=["lint", "optimize"], artifact_type="python"))
    elif workflow_type == "sql":
        router.add_node(DAGNode("query_parse", "SQL Query Ingest", "nvidia/nemotron-mini-4b", "Parse input query", artifact_type="text"))
        router.add_node(DAGNode("index_advisor", "Index Recommendations", "nvidia/nemotron-4-70b", "Suggest B-tree indexing", dependencies=["query_parse"], artifact_type="json"))
        router.add_node(DAGNode("rewrite_engine", "Cost-Based Rewriter", "nvidia/nemotron-3-8b", "Rewrite nested subqueries", dependencies=["query_parse"], artifact_type="sql"))
        router.add_node(DAGNode("plan_verify", "Execution Plan Verifier", "nvidia/nemotron-4-340b", "Verify EXPLAIN query cost", dependencies=["index_advisor", "rewrite_engine"], artifact_type="python"))
    else:
        router.add_node(DAGNode("extract", "Extract Knowledge", "nvidia/nemotron-3-8b", "Extract core propositions", artifact_type="text"))
        router.add_node(DAGNode("synthesize", "Synthesize Report", "nvidia/nemotron-4-340b", "Synthesize final report", dependencies=["extract"], artifact_type="text"))

    batches = router.get_topological_batches()
    print(f"\033[1;35m[*] Compiled Graph: {len(router.nodes)} nodes across {len(batches)} parallel execution stages.\033[0m\n")

    stage_idx = 1
    for batch in batches:
        print(f"\033[1;34m--- [STAGE {stage_idx}/{len(batches)}: Concurrent Dispatch ({len(batch)} nodes)] ---\033[0m")
        for node_id in batch:
            node = router.nodes[node_id]
            print(f"  \033[1;37m▶ Dispatching [{node.node_id}]: {node.task_name} -> {node.model_tier} on Nebius Token Factory...\033[0m")
            
            # Execute inference
            res = client.execute_inference(node.model_tier, node.prompt_template, max_tokens=node.token_limit)
            node.output = res["output"]
            node.tokens_used = res["usage"]["total_tokens"]
            node.execution_time_ms = res["latency_ms"]
            
            # Record cost
            cost_info = budgeter.record_usage(node.model_tier, res["usage"]["prompt_tokens"], res["usage"]["completion_tokens"])
            
            # Run verification gate
            v_res = verifier.execute_verification_gate(node.artifact_type, node.output)
            
            status_symbol = "\033[1;32m✔ VERIFIED\033[0m" if v_res["passed"] else "\033[1;31m✖ REJECTED\033[0m"
            print(f"    └─ Status: {status_symbol} ({v_res['reason']}) | Latency: {node.execution_time_ms:.1f}ms | Throughput: {res['tokens_per_sec']} tok/s | Cost: ${cost_info.estimated_cost_usd:.6f}")
            node.status = "COMPLETED" if v_res["passed"] else "FAILED"
        stage_idx += 1
        print()

    summary = budgeter.get_summary()
    print("\033[1;32m========================================================\033[0m")
    print(f"\033[1;32m✔ Workflow Complete! Total Tokens: {summary['total_tokens']} | Total Cost: ${summary['total_cost_usd']:.6f} ({summary['budget_utilized_pct']}% of budget)\033[0m")
    print("\033[1;32m========================================================\033[0m")

if __name__ == "__main__":
    wf = sys.argv[1] if len(sys.argv) > 1 else "refactor"
    run_workflow_demo(wf)
