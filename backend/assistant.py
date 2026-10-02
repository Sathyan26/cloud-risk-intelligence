import json
import os

import anthropic

from backend import queries

MODEL = "claude-sonnet-5"
MAX_TOOL_ITERATIONS = 5

SYSTEM_PROMPT = (
    "You are a data analyst assistant for a transaction risk intelligence platform. "
    "Answer questions using ONLY the data returned by the tools available to you -- "
    "never invent, estimate, or round numbers beyond what the tools return. "
    "If the tools don't contain enough information to answer, say so explicitly rather than guessing. "
    "Cite concrete figures (counts, percentages, dollar amounts) from the tool results in your answer. "
    "Keep answers concise: a few sentences, not a report."
)

TOOLS = [
    {
        "name": "get_weekly_transaction_trends",
        "description": (
            "Week-over-week transaction volume, total amount, and percent change vs. the prior week, "
            "broken down by region. Use for questions about trends over time, increases/decreases, "
            "or regional comparisons."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "region": {
                    "type": "string",
                    "description": "Optional region to filter to, e.g. 'North America'. Omit for all regions.",
                }
            },
        },
    },
    {
        "name": "get_top_anomalies",
        "description": (
            "The highest-scored anomalous transactions flagged by the risk model, with amount, "
            "category, and date. Use for questions about suspicious or high-risk transactions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "How many to return. Default 10."}
            },
        },
    },
    {
        "name": "get_top_churn_risks",
        "description": (
            "Customers with the highest predicted churn probability. Use for questions about "
            "customer retention or churn risk."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "How many to return. Default 10."}
            },
        },
    },
    {
        "name": "get_data_quality_summary",
        "description": (
            "The latest data quality snapshot (customers/transactions loaded vs. rejected) and a "
            "breakdown of rejection reasons. Use for questions about data quality, missing data, "
            "or validation issues."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_top_spenders",
        "description": (
            "Customers ranked by total spending, overall and within their region. Use for questions "
            "about top customers or spending patterns."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "How many to return. Default 10."}
            },
        },
    },
]


def _get_data_quality_summary():
    return {
        "latest_snapshot": queries.get_latest_data_quality_snapshot().to_dict(orient="records"),
        "rejection_breakdown": queries.get_rejection_breakdown().to_dict(orient="records"),
    }


TOOL_FUNCTIONS = {
    "get_weekly_transaction_trends": lambda region=None: (
        queries.get_weekly_trends(region=region).to_dict(orient="records")
    ),
    "get_top_anomalies": lambda limit=10: queries.get_top_anomalies(limit=limit).to_dict(orient="records"),
    "get_top_churn_risks": lambda limit=10: queries.get_top_churn_risks(limit=limit).to_dict(orient="records"),
    "get_data_quality_summary": lambda: _get_data_quality_summary(),
    "get_top_spenders": lambda limit=10: queries.get_top_spenders(limit=limit).to_dict(orient="records"),
}


def _run_tool(name, tool_input):
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return {"error": f"unknown tool: {name}"}
    return func(**tool_input)


def ask_assistant(question: str) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    messages = [{"role": "user", "content": question}]
    tool_calls_log = []

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            final_text = "".join(block.text for block in response.content if block.type == "text")
            return {"answer": final_text, "tool_calls": tool_calls_log}

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = _run_tool(block.name, block.input)
            tool_calls_log.append({"tool": block.name, "input": block.input})
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, default=str),
            })

        messages.append({"role": "user", "content": tool_results})

    return {
        "answer": "I wasn't able to gather enough information to answer that within the allotted steps.",
        "tool_calls": tool_calls_log,
    }
