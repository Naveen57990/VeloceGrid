"""
VeloceGrid: Speculative Verification Engine
Validates intermediate node outputs (code AST, JSON schema, test assertion syntax)
before propagating state downstream, terminating non-viable speculative branches early.
"""

import ast
import json
import re
from typing import Dict, Any, Tuple, Optional

class SpeculativeVerifier:
    def __init__(self):
        self.validation_history = []

    def verify_python_code(self, code_str: str) -> Tuple[bool, str]:
        """Verifies Python syntax and safety constraints."""
        # Strip markdown fences if present
        clean_code = re.sub(r"^```python\s*|\s*```$", "", code_str.strip(), flags=re.MULTILINE)
        try:
            parsed = ast.parse(clean_code)
            # Check for forbidden dangerous calls
            for node in ast.walk(parsed):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in ["eval", "exec", "__import__"]:
                        return False, f"Security Violation: Dangerous call '{node.func.id}' detected."
            return True, "AST Syntax Valid & Safe."
        except SyntaxError as e:
            return False, f"SyntaxError at line {e.lineno}: {e.msg}"

    def verify_json_schema(self, json_str: str, required_keys: Optional[list] = None) -> Tuple[bool, str]:
        """Verifies JSON format and required contract keys."""
        try:
            clean_json = re.sub(r"^```json\s*|\s*```$", "", json_str.strip(), flags=re.MULTILINE)
            data = json.loads(clean_json)
            if required_keys:
                missing = [k for k in required_keys if k not in data]
                if missing:
                    return False, f"Schema Error: Missing required keys {missing}"
            return True, "JSON Schema Contract Satisfied."
        except Exception as e:
            return False, f"JSON Parse Failure: {str(e)}"

    def verify_sql_query(self, sql_str: str) -> Tuple[bool, str]:
        """Verifies basic SQL grammar and prevents destructive queries in read/optimize pipeline."""
        clean_sql = re.sub(r"^```sql\s*|\s*```$", "", sql_str.strip(), flags=re.MULTILINE)
        destructive_keywords = ["DROP", "TRUNCATE", "DELETE FROM", "ALTER TABLE"]
        for kw in destructive_keywords:
            if re.search(r"\b" + kw + r"\b", clean_sql, re.IGNORECASE):
                return False, f"Destructive SQL Operation Blocked: '{kw}'."
        if not re.search(r"^\s*(SELECT|WITH|EXPLAIN)\b", clean_sql, re.IGNORECASE):
            return False, "Query must begin with SELECT, WITH, or EXPLAIN."
        return True, "SQL Grammar & Safety Validated."

    def execute_verification_gate(self, artifact_type: str, content: str, required_keys: Optional[list] = None) -> Dict[str, Any]:
        """Dispatches verification based on expected artifact type."""
        if artifact_type == "python":
            passed, reason = self.verify_python_code(content)
        elif artifact_type == "json":
            passed, reason = self.verify_json_schema(content, required_keys)
        elif artifact_type == "sql":
            passed, reason = self.verify_sql_query(content)
        else:
            # Default text length check
            passed = len(content.strip()) > 0
            reason = "Non-empty text verified."

        result = {
            "artifact_type": artifact_type,
            "passed": passed,
            "reason": reason
        }
        self.validation_history.append(result)
        return result
