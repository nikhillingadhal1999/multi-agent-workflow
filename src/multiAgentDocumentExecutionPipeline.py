from langgraph.graph import StateGraph, END
from langchain.schema import HumanMessage
from typing import TypedDict, List, Optional
import re
import subprocess
import ast
from agents.agents import document_reader,document_analyzer,command_extractor,command_validator,command_executor
print("=== Define state schema ===")


class AgentState(TypedDict):
    prompt: Optional[str]
    document: Optional[str]
    analysis: Optional[str]
    commands: Optional[List[str]]
    safe_commands: Optional[List[str]]
    execution_results: Optional[List[str]]
    execution_analysis_results: Optional[List[str]]
    messages: List[HumanMessage]

graph = StateGraph(AgentState)

graph.add_node("Reader", document_reader)
graph.add_node("Analyzer", document_analyzer)
graph.add_node("Extractor", command_extractor)
graph.add_node("Validator", command_validator)
graph.add_node("Executor", command_executor)

graph.set_entry_point("Reader")
graph.add_edge("Reader", "Analyzer")
graph.add_edge("Analyzer", "Extractor")
graph.add_edge("Extractor", "Validator")
graph.add_edge("Validator", "Executor")
graph.set_finish_point("Executor")


app = graph.compile()

if __name__ == "__main__":
    initial_state = {
        "prompt": "analyze and execute commands from document",
        "document": None,
        "analysis": None,
        "commands": [],
        "safe_commands": [],
        "execution_results": None,
        "messages": []
    }
    result = app.invoke(initial_state)

    print("\n🧠 Final Output:\n")
    for msg in result["messages"]:
        print("→", msg.content)