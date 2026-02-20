from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pathlib import Path

class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    async def run(self, **kwargs) -> str:
        pass

class PythonInterpreter(Tool):
    name = "python_interpreter"
    description = "Executes Python code. Use for math, data processing, or logic. Input: `code` (string)."

    async def run(self, code: str) -> str:
        try:
            # Dangerous in real prod, use sandbox (e.g., e2b)
            # For this demo, we use a restricted exec with blocked access to unsafe modules
            # WARNING: This is still not fully secure for arbitrary code execution.
            # In a real production deployment, this MUST be run inside a container or microVM.

            # Simple guardrail for demo purposes
            if "os.system" in code or "subprocess" in code or "import os" in code:
                return "Security Violation: Unsafe modules detected."

            local_vars = {}
            # Minimal safety: empty builtins. In production, wrap this in Docker.
            exec(code, {"__builtins__": {}}, local_vars)
            return str(local_vars.get("result", "Code executed successfully, no 'result' variable found."))
        except Exception as e:
            return f"Error executing code: {str(e)}"

class WebSearch(Tool):
    name = "web_search"
    description = "Searches the web for information. Input: `query` (string)."

    async def run(self, query: str) -> str:
        # Mock search
        return f"Results for '{query}': [1] Python 3.12 documentation... [2] StackOverflow: How to center a div..."

class FileSystem(Tool):
    name = "file_system"
    description = "Reads or writes files. Input: `operation` (read/write), `path`, `content`."

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()

    async def run(self, operation: str, path: str, content: str = None) -> str:
        # Sanitize and validate path
        try:
            requested_path = Path(path)
            # If path is absolute, we still want to ensure it's within base_path.
            if requested_path.is_absolute():
                target_path = requested_path.resolve()
            else:
                target_path = (self.base_path / requested_path).resolve()

            if not target_path.is_relative_to(self.base_path):
                return "Error: Path traversal detected. Access denied."
        except Exception as e:
            return f"Error resolving path: {str(e)}"

        if operation == "read":
            try:
                with open(target_path, "r") as f:
                    return f.read()
            except FileNotFoundError:
                return "File not found."
            except Exception as e:
                return f"Error reading file: {str(e)}"
        elif operation == "write":
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(target_path, "w") as f:
                    f.write(content)
                return "File written."
            except Exception as e:
                return f"Error writing file: {str(e)}"
        return "Invalid operation."
