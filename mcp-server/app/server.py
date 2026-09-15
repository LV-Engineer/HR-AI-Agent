from typing import Any, Literal

from mcp.server.mcpserver import MCPServer

from app.core.db import get_schema_info, run_query
from app.core.policies import PolicyResult, search_hr_policies
from app.core.matching import MatchResult, match_candidate as match_candidate_logic
from app.core.reports import generate_report as generate_report_logic

mcp = MCPServer('hr-ai-agent-mcp')

@mcp.tool()
def get_schema() -> dict[str, Any]:
    """Returns the structure (tables and columns) of the HR analytics database — hr and documents schemas only."""
    return get_schema_info()

@mcp.tool()
def query_database(sql: str) -> list[dict[str, Any]]:
    """Execute a single read-only SELECT query against the staff/documents schemas and return matching rows (max 200)."""
    return run_query(sql)

@mcp.tool()
def search_hr_policy(query: str) -> list[PolicyResult]:
    """Search HR policies and regulations by semantic similarity to the query. Returns the most relevant policy documents."""
    return search_hr_policies(query)

@mcp.tool()
def match_candidate(cv_id: str, job_requirement_id: int) -> MatchResult:
    """Compare a candidate's CV against a specific job vacancy's requirements.
    Returns both full texts and an embedding-similarity distance score — analyze the gap yourself, don't just report the number."""
    return match_candidate_logic(cv_id, job_requirement_id)

@mcp.tool()
def generate_report(title: str, data: list[dict[str, Any]], summary: str, chart_type: Literal['bar', 'line', 'none'] = 'bar') -> str:
    """Generate a PDF report with a title, a chart (if useful for this data), a data table, and a conclusions section written by you.
    chart_type: 'bar' for comparing categories (default), 'line' for trends over time/sequence, 'none' if the data doesn't suit a chart (e.g. free-text rows).
    Returns the file path where the PDF was saved."""
    return generate_report_logic(title, data, summary, chart_type)

app = mcp.streamable_http_app(host='0.0.0.0')

if __name__ == '__main__':
    mcp.run(transport='streamable-http', host='0.0.0.0', port=8000)