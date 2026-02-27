"""
Shared setup: mock all external dependencies before any test imports.
"""

import sys
from unittest.mock import MagicMock

sys.modules["app"] = MagicMock()
sys.modules["app.core"] = MagicMock()
sys.modules["app.core.config"] = MagicMock()
sys.modules["langchain"] = MagicMock()
sys.modules["langchain.tools"] = MagicMock()
sys.modules["tavily"] = MagicMock()

# Make @tool decorator a passthrough
sys.modules["langchain.tools"].tool = lambda name: lambda f: f
