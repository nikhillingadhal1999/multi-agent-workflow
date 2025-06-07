from langchain_community.llms import Ollama
from langgraph.graph import StateGraph, END
from langchain.schema import HumanMessage
from typing import TypedDict, List, Optional
import re
import subprocess
import ast

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


# === Initialize LLM ===
llm = Ollama(model="llama3.2")


def document_reader(state: AgentState) -> AgentState:
    try:
        print("Document is being read")
        with open("src/instructions.txt", "r") as f:
            doc = f.read()
        return {
            "document": doc,
            "messages": state["messages"]
            + [HumanMessage(content=f"Read document:\n{doc[:500]}...")],
        }
    except Exception as e:
        return {
            "document": None,
            "messages": state["messages"]
            + [HumanMessage(content=f"Error reading document: {e}")],
        }


def document_analyzer(state: AgentState) -> AgentState:
    print("Document is being Analyzed")
    if not state.get("document"):
        return {
            "analysis": None,
            "messages": state["messages"]
            + [HumanMessage(content="No document to analyze.")],
        }

    prompt = f"Analyze the following document and explain its purpose and key points:\n\n{state['document']}"
    result = llm.invoke([HumanMessage(content=prompt)])
    return {
        "analysis": result,
        "messages": state["messages"]
        + [HumanMessage(content=f"Document analysis:\n{result}")],
    }



def extract_commands(raw_text):
    # Try AST first
    try:
        commands = ast.literal_eval(raw_text)
        if isinstance(commands, list):
            return [cmd.strip() for cmd in commands if isinstance(cmd, str)]
    except Exception:
        pass  # fallback to regex if literal_eval fails

    # Fallback: extract strings from lines that look like list items
    command_pattern = re.findall(r'"(.*?)"', raw_text)  # grab things inside double quotes
    if command_pattern:
        return [cmd.replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\') for cmd in command_pattern]

    # Final fallback: extract each line and clean
    lines = raw_text.strip("[]").splitlines()
    return [line.strip().strip('"').strip(',') for line in lines if line.strip()]

def command_extractor(state: AgentState) -> AgentState:
    print("Commands being extracted")
    if not state.get("document"):
        return {
            "commands": [],
            "messages": state["messages"]
            + [HumanMessage(content="No document to extract commands from.")],
        }

    prompt = f"Extract all shell/bash commands from the document below. Strictly return only a JSON list of commands.\n\n{state['document']}"
    result = llm.invoke([HumanMessage(content=prompt)])
    try:
        commands = extract_commands(result)
        return {
            "commands": commands,
            "messages": state["messages"]
            + [HumanMessage(content=f"Extracted commands: {commands}")],
        }
    except Exception as ex:
        return {
            "commands": [],
            "messages": state["messages"]
            + [HumanMessage(content=str(ex))],
        }


def command_validator(state: AgentState) -> AgentState:
    print("Commands being validated")
    commands = state.get("commands", [])
    safe = []
    for cmd in commands:
        if re.search(r"rm\s+-rf|shutdown|reboot|mkfs", cmd):
            continue
        safe.append(cmd)
    print("Safe commands: ",safe)
    return {
        "safe_commands": safe,
        "messages": state["messages"]
        + [HumanMessage(content=f"Safe commands: {safe}")],
    }


def command_executor(state: AgentState) -> AgentState:
    print("Safe commands being executed")
    safe_cmds = state.get("safe_commands", [])
    output = []
    for cmd in safe_cmds:
        try:
            result = subprocess.check_output(
                cmd, shell=True, stderr=subprocess.STDOUT, timeout=10
            )
            output.append("{cmd}\n{result.decode()}\n")
        except Exception as e:
            output.append("{cmd}\nError: {str(e)}\n")
    return {
        "execution_results": output,
        "messages": state["messages"]
        + [HumanMessage(content=f"Command execution results:\n{output}")],
    }

def get_analysis_prompt(execution_results):
    prompt = f"""You are a system health analyst.
You are given the output of various system commands (like `df -h`, `vm_stat`, etc.).

Analyze the following output and explain:
- What do these results mean?
- Is the system healthy?
- Are there any warnings?

Command Results: {execution_results}"""
    return prompt

def result_analyzer(state: AgentState) -> AgentState:
    print("Result is being analysed..")
    if not state.get("execution_results"):
        return {
            "commands": [],
            "messages": state["messages"]
            + [HumanMessage(content="No results to analyse.")],
        }
    execution_results = state.get("execution_results", [])
    result_list = []
    count = 0
    for result in execution_results:
        print(f"Analyzing {count}/{len(execution_results)}")
        result_list.append(llm.invoke([HumanMessage(content=get_analysis_prompt(result))]))
        count += 1
    return {
        "execution_analysis_results": result_list,
        "messages": state["messages"]
        + [HumanMessage(content=f"Execution analysis:\n{result_list}")],
    }





graph = StateGraph(AgentState)

graph.add_node("Reader", document_reader)
graph.add_node("Analyzer", document_analyzer)
graph.add_node("Extractor", command_extractor)
graph.add_node("Validator", command_validator)
graph.add_node("Executor", command_executor)
graph.add_node("ResultAnalyzer", result_analyzer)

graph.set_entry_point("Reader")
graph.add_edge("Reader", "Analyzer")
graph.add_edge("Analyzer", "Extractor")
graph.add_edge("Extractor", "Validator")
graph.add_edge("Validator", "Executor")
graph.add_edge("Executor", "ResultAnalyzer")
graph.set_finish_point("ResultAnalyzer")


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