from app.tools.market_tools import get_quote
from app.tools.portfolio_analysis_tools import (
    calculate_concentration,
    calculate_sector_allocation,
)
from app.tools.portfolio_tools import (
    calculate_portfolio_metrics,
    get_portfolio,
)


TOOL_REGISTRY = {
    "get_portfolio": get_portfolio,
    "calculate_portfolio_metrics": calculate_portfolio_metrics,
    "calculate_sector_allocation": calculate_sector_allocation,
    "calculate_concentration": calculate_concentration,
    "get_quote": get_quote,
}