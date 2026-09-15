from mcp.server.mcpserver import MCPServer

from app.core.db import get_schema_info, run_query
from app.core.policies import search_hr_policies
from app.core.matching import match_candidate as match_candidate_logic

mcp = MCPServer('hr-ai-agent-mcp')

@mcp.tool()
def get_schema() -> dict:
    """Returns the structure (tables and columns) of the HR analytics database — hr and documents schemas only."""
    return get_schema_info()

@mcp.tool()
def query_database(sql: str) -> list[dict]:
    """Execute a single read-only SELECT query against the staff/documents schemas and return matching rows (max 200)."""
    return run_query(sql)

@mcp.tool()
def search_hr_policy(query: str) -> list[dict]:
    """Search HR policies and regulations by semantic similarity to the query. Returns the most relevant policy documents."""
    return search_hr_policies(query)

@mcp.tool()
def match_candidate(cv_id: str, job_requirement_id: int) -> dict:
    """Compare a candidate's CV against a specific job vacancy's requirements.
    Returns both full texts and an embedding-similarity distance score — analyze the gap yourself, don't just report the number."""
    return match_candidate_logic(cv_id, job_requirement_id)

app = mcp.streamable_http_app(host='0.0.0.0')

if __name__ == '__main__':
    mcp.run(transport='streamable-http', host='0.0.0.0', port=8000)