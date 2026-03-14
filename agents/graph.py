from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from agents.data_agent import run_data_agent
from agents.analysis_agent import run_analysis_agent
from agents.optimizer_agent import run_optimizer_agent
from agents.forecast_agent import run_forecast_agent
from agents.advisor_agent import run_advisor_agent


# ── State schema ─────────────────────────────────────────────
class FinancialState(TypedDict):
    # Input
    raw_summary: dict

    # Agent outputs (filled progressively)
    profile:  Optional[dict]
    analysis: Optional[dict]
    strategy: Optional[dict]
    forecast: Optional[dict]
    advice:   Optional[str]

    # Control
    error:    Optional[str]


# ── Node functions ────────────────────────────────────────────

def data_node(state: FinancialState) -> FinancialState:
    try:
        profile = run_data_agent(state["raw_summary"])
        return {**state, "profile": profile}
    except Exception as e:
        return {**state, "error": f"Data Agent failed: {str(e)}"}


def analysis_node(state: FinancialState) -> FinancialState:
    try:
        analysis = run_analysis_agent(state["profile"])
        return {**state, "analysis": analysis}
    except Exception as e:
        return {**state, "error": f"Analysis Agent failed: {str(e)}"}


def optimizer_node(state: FinancialState) -> FinancialState:
    try:
        strategy = run_optimizer_agent(state["profile"])
        return {**state, "strategy": strategy}
    except Exception as e:
        return {**state, "error": f"Optimizer Agent failed: {str(e)}"}


def forecast_node(state: FinancialState) -> FinancialState:
    try:
        forecast = run_forecast_agent(state["profile"])
        return {**state, "forecast": forecast}
    except Exception as e:
        return {**state, "error": f"Forecast Agent failed: {str(e)}"}


def advisor_node(state: FinancialState) -> FinancialState:
    try:
        advice = run_advisor_agent(
            state["profile"],
            state["analysis"],
            state["strategy"],
            state["forecast"]
        )
        return {**state, "advice": advice}
    except Exception as e:
        return {**state, "error": f"Advisor Agent failed: {str(e)}"}


# ── Conditional edge: stop if error ──────────────────────────

def should_continue(state: FinancialState) -> str:
    if state.get("error"):
        return "end"
    if not state.get("profile", {}).get("is_valid", False):
        return "end"
    return "continue"


# ── Build the graph ───────────────────────────────────────────

def build_graph():
    graph = StateGraph(FinancialState)

    # Add nodes
    graph.add_node("data_agent",     data_node)
    graph.add_node("analysis_agent", analysis_node)
    graph.add_node("optimizer_agent",optimizer_node)
    graph.add_node("forecast_agent", forecast_node)
    graph.add_node("advisor_agent",  advisor_node)

    # Entry point
    graph.set_entry_point("data_agent")

    # Conditional edge after data agent
    graph.add_conditional_edges(
        "data_agent",
        should_continue,
        {
            "continue": "analysis_agent",
            "end": END
        }
    )

    # Linear edges for remaining agents
    graph.add_edge("analysis_agent",  "optimizer_agent")
    graph.add_edge("optimizer_agent", "forecast_agent")
    graph.add_edge("forecast_agent",  "advisor_agent")
    graph.add_edge("advisor_agent",   END)

    return graph.compile()


# Singleton — compile once on import
financial_graph = build_graph()


def run_financial_graph(raw_summary: dict) -> FinancialState:
    """Run the full agent graph and return final state."""
    initial_state = FinancialState(
        raw_summary=raw_summary,
        profile=None,
        analysis=None,
        strategy=None,
        forecast=None,
        advice=None,
        error=None
    )
    return financial_graph.invoke(initial_state)