from abc import ABC, abstractmethod
from typing import Dict, Any, List

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

    async def run(self, operation: str, path: str, content: str = None) -> str:
        if operation == "read":
            try:
                with open(path, "r") as f:
                    return f.read()
            except FileNotFoundError:
                return "File not found."
        elif operation == "write":
            with open(path, "w") as f:
                f.write(content)
            return "File written."
        return "Invalid operation."
