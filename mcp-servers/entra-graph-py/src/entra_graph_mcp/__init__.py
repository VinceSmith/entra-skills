"""Entra Graph MCP Server — Microsoft Entra identity management via Microsoft Graph API."""

from .server import mcp

# Import tool modules to register tools with the MCP server
from . import tools_users_groups  # noqa: F401
from . import tools_apps  # noqa: F401
from . import tools_diagnostics  # noqa: F401
from . import tools_rbac  # noqa: F401
from . import tools_agent_identity  # noqa: F401
from . import tools_governance  # noqa: F401
from . import tools_id_protection  # noqa: F401
from . import tools_workload_id  # noqa: F401

__all__ = ["mcp"]

