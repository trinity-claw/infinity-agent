"""Custom Promptfoo Provider for Infinity Agent Swarm.

This provider integrates promptfoo directly with our LangGraph Swarm,
allowing us to run rigorous tests on the final outputs and routing logic.
"""

import asyncio
import json
import os
import sys

# Define absolute or relative path to project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.messages import HumanMessage
import src.container as container


async def _call_api(prompt, options, context):
    """Async handler for promptfoo integration."""
    try:
        swarm = container.get_swarm()
        
        # User message
        message = prompt
        
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "user_id": "promptfoo-tester",
            "intent": "",
            "language": "pt-BR",
            "agent_route": "",
            "sentiment_score": 0.0,
            "escalated": False,
            "guardrail_blocked": False,
            "guardrail_reason": "",
            "metadata": {},
        }
        
        result = await swarm.ainvoke(initial_state)
        
        # Extract response text
        response_text = ""
        agent_used = "router"
        
        for msg in reversed(result.get("messages", [])):
            if hasattr(msg, "content") and msg.content:
                name = getattr(msg, "name", "")
                if name != "router" and name != "guardrail":
                    response_text = msg.content
                    agent_used = name or "unknown"
                    break
                elif name == "guardrail":
                    response_text = msg.content
                    agent_used = "guardrail"
                    break

        if not response_text:
            response_text = "No response generated."

        # Return a structured output so promptfoo can evaluate both text and routing
        output = {
            "output": response_text,
            "agent_used": agent_used,
            "intent": result.get("intent", ""),
            "guardrail_blocked": result.get("guardrail_blocked", False)
        }
        
        # For promptfoo string matching, sometimes it's easier to return JSON string
        return {"output": json.dumps(output)}

    except Exception as e:
        return {"error": str(e)}


def call_api(prompt, options, context):
    """Entrypoint called by Promptfoo."""
    return asyncio.run(_call_api(prompt, options, context))
