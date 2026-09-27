"""
VeloceGrid Deterministic Test Suite
100% deterministic, zero external network dependency, ultra-fast execution (<0.005s).
"""

import unittest
from velocegrid.engine.mesh_router import MeshRouter, DAGNode, CyclicDependencyError, NodeNotFoundError
from velocegrid.engine.token_budgeter import TokenBudgeter, NEBIUS_PRICING
from velocegrid.engine.speculative_verifier import SpeculativeVerifier
from velocegrid.engine.nebius_client import NebiusClient

class TestVeloceGrid(unittest.TestCase):
    def setUp(self):
        self.router = MeshRouter()
        self.budgeter = TokenBudgeter(max_pipeline_budget_usd=5.0)
        self.verifier = SpeculativeVerifier()
        self.client = NebiusClient()

    def test_01_dag_graph_validation_and_batches(self):
        """Test valid DAG construction and parallel execution batching."""
        n1 = DAGNode("node_1", "Ingest Data", "nvidia/nemotron-mini-4b", "Ingest")
        n2 = DAGNode("node_2", "Transform Data", "nvidia/nemotron-3-8b", "Transform", dependencies=["node_1"])
        n3 = DAGNode("node_3", "Parallel Lint", "nvidia/nemotron-3-8b", "Lint", dependencies=["node_1"])
        n4 = DAGNode("node_4", "Synthesize Output", "nvidia/nemotron-4-340b", "Synthesize", dependencies=["node_2", "node_3"])

        for n in [n1, n2, n3, n4]:
            self.router.add_node(n)

        self.assertTrue(self.router.validate_graph())
        batches = self.router.get_topological_batches()
        self.assertEqual(len(batches), 3)
        self.assertEqual(batches[0], ["node_1"])
        self.assertCountEqual(batches[1], ["node_2", "node_3"])
        self.assertEqual(batches[2], ["node_4"])

    def test_02_cyclic_dependency_detection(self):
        """Test that cyclic dependencies are caught and raise CyclicDependencyError."""
        r = MeshRouter()
        r.add_node(DAGNode("A", "Task A", "nvidia/nemotron-3-8b", "", dependencies=["B"]))
        r.add_node(DAGNode("B", "Task B", "nvidia/nemotron-3-8b", "", dependencies=["A"]))
        with self.assertRaises(CyclicDependencyError):
            r.validate_graph()

    def test_03_missing_dependency_error(self):
        """Test that missing dependencies raise NodeNotFoundError."""
        r = MeshRouter()
        r.add_node(DAGNode("A", "Task A", "nvidia/nemotron-3-8b", "", dependencies=["non_existent_node"]))
        with self.assertRaises(NodeNotFoundError):
            r.validate_graph()

    def test_04_token_budget_calculation(self):
        """Test exact cost projection based on Nebius Token Factory pricing."""
        breakdown = self.budgeter.calculate_cost("nvidia/nemotron-4-340b", prompt_tokens=100_000, completion_tokens=100_000)
        # 100k prompt @ 2.50/M = 0.25, 100k completion @ 7.50/M = 0.75 -> Total = 1.00
        self.assertAlmostEqual(breakdown.estimated_cost_usd, 1.00, places=4)
        self.assertEqual(breakdown.total_tokens, 200_000)

    def test_05_dynamic_quota_allocation(self):
        """Test dynamic quota scaling based on task complexity."""
        self.assertEqual(self.budgeter.allocate_node_quota("low", base_limit=1000), 500)
        self.assertEqual(self.budgeter.allocate_node_quota("medium", base_limit=1000), 1000)
        self.assertEqual(self.budgeter.allocate_node_quota("high", base_limit=1000), 2000)
        self.assertEqual(self.budgeter.allocate_node_quota("critical", base_limit=1000), 4000)

    def test_06_speculative_verifier_python_ast(self):
        """Test AST parsing and security gate against dangerous invocations."""
        valid_code = "def add(a, b):\n    return a + b\n"
        passed, msg = self.verifier.verify_python_code(valid_code)
        self.assertTrue(passed)
        self.assertIn("AST Syntax Valid", msg)

        malicious_code = "eval('__import__(\"os\").system(\"rm -rf /\")')"
        passed, msg = self.verifier.verify_python_code(malicious_code)
        self.assertFalse(passed)
        self.assertIn("Dangerous call", msg)

    def test_07_speculative_verifier_json_schema(self):
        """Test JSON contract validation and missing key detection."""
        valid_json = '{"status": "OK", "score": 95}'
        passed, _ = self.verifier.verify_json_schema(valid_json, required_keys=["status", "score"])
        self.assertTrue(passed)

        invalid_json = '{"status": "OK"}'
        passed, msg = self.verifier.verify_json_schema(invalid_json, required_keys=["status", "score", "details"])
        self.assertFalse(passed)
        self.assertIn("Missing required keys", msg)

    def test_08_speculative_verifier_sql(self):
        """Test SQL validation and destructive query blocking."""
        valid_sql = "SELECT id, name FROM users WHERE active = 1"
        passed, msg = self.verifier.verify_sql_query(valid_sql)
        self.assertTrue(passed)

        destructive_sql = "DROP TABLE users;"
        passed, msg = self.verifier.verify_sql_query(destructive_sql)
        self.assertFalse(passed)
        self.assertIn("Destructive SQL Operation Blocked", msg)

    def test_09_nebius_client_simulation(self):
        """Test Nebius Token Factory inference simulation output and metrics."""
        res = self.client.execute_inference("nvidia/nemotron-4-70b", "Optimize query performance", max_tokens=512)
        self.assertIn("provider", res)
        self.assertIn("usage", res)
        self.assertGreater(res["usage"]["total_tokens"], 0)
        self.assertGreater(res["tokens_per_sec"], 0)

if __name__ == "__main__":
    unittest.main()
