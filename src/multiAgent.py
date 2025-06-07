from langchain_community.llms import Ollama
from langgraph.graph import StateGraph, END
from langchain.schema import HumanMessage
from typing import TypedDict, List, Optional


print("=== Define state schema ===")
class AgentState(TypedDict):
    logs: Optional[str]
    error_info: Optional[str]
    resolution: Optional[str]
    messages: List[HumanMessage]
    prompt: Optional[str]


# === Initialize LLM ===
llm = Ollama(model="llama3.2")


# === Define agent functions ===
def log_collector(state: AgentState) -> AgentState:
    prompt = state.get("prompt", "").lower()
    if "collect logs" not in prompt:
        return {
            "messages": state.get("messages", []) + [HumanMessage(content="Skipping log collection.")],
            "logs": None,
        }
    try:
        with open("app.log", "r") as f:
            logs = f.read()
        msg = f"Collected logs:\n{logs[:500]}..."
        return {
            "logs": logs,
            "messages": state.get("messages", []) + [HumanMessage(content=msg)],
        }
    except Exception as e:
        return {
            "logs": None,
            "messages": state.get("messages", []) + [HumanMessage(content=f"Error reading logs: {e}")],
        }


def error_checker(state: AgentState) -> AgentState:
    prompt = state.get("prompt", "").lower()
    if "analyze" not in prompt:
        return {
            "messages": state.get("messages", []) + [HumanMessage(content="Skipping error analysis.")],
            "error_info": None,
        }

    logs = state.get("logs")
    if not logs:
        return {
            "messages": state.get("messages", []) + [HumanMessage(content="No logs available to analyze.")],
            "error_info": None,
        }

    prompt_msg = f"Analyze the following logs. Find and explain any errors:\n\n{logs}"
    result = llm.invoke([HumanMessage(content=prompt_msg)])
    return {
        "error_info": result,
        "messages": state.get("messages", []) + [HumanMessage(content=result)],
    }


def error_resolver(state: AgentState) -> AgentState:
    prompt = state.get("prompt", "").lower()
    if "resolve" not in prompt:
        return {
            "messages": state.get("messages", []) + [HumanMessage(content="Skipping error resolution.")],
            "resolution": None,
        }

    error_info = state.get("error_info")
    if not error_info:
        return {
            "messages": state.get("messages", []) + [HumanMessage(content="No error info to resolve.")],
            "resolution": None,
        }

    prompt_msg = f"Based on these errors:\n\n{error_info}\n\nSuggest how to resolve them."
    result = llm.invoke([HumanMessage(content=prompt_msg)])
    return {
        "resolution": result,
        "messages": state.get("messages", []) + [HumanMessage(content=result)],
    }


print("=== Build the graph ===")
graph = StateGraph(AgentState)

graph.add_node("LogCollector", log_collector)
graph.add_node("ErrorChecker", error_checker)
graph.add_node("ErrorResolver", error_resolver)

graph.set_entry_point("LogCollector")

graph.add_edge("LogCollector", "ErrorChecker")
graph.add_edge("ErrorChecker", "ErrorResolver")

graph.set_finish_point("ErrorResolver")

app = graph.compile()


print("=== Run the system with a prompt ===")
if __name__ == "__main__":
    user_prompt = input("Enter prompt for the agents (e.g., 'collect logs and analyze errors and resolve'): ").strip()

    initial_state = {
        "logs": None,
        "error_info": None,
        "resolution": None,
        "messages": [],
        "prompt": user_prompt,
    }

    result = app.invoke(initial_state)

    print("\n🧠 Final Output:\n")
    for message in result.get("messages", []):
        print("→", message.content)
