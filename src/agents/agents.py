from langchain_community.llms import Ollama
from langgraph.graph import StateGraph, END
from langchain.schema import HumanMessage
from typing import TypedDict, List, Optional
import re
import subprocess
import ast
from llm_list.llm import llm

def extract_commands(raw_text):
    try:
        commands = ast.literal_eval(raw_text)
        if isinstance(commands, list):
            return [cmd.strip() for cmd in commands if isinstance(cmd, str)]
    except Exception as ex:
        print(f"Exception : {ex}")

    command_pattern = re.findall(r'"(.*?)"', raw_text)  # grab things inside double quotes
    if command_pattern:
        return [cmd.replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\') for cmd in command_pattern]

    lines = raw_text.strip("[]").splitlines()
    return [line.strip().strip('"').strip(',') for line in lines if line.strip()]

def document_reader(state):
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

def document_analyzer(state):
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

def command_extractor(state):
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

def command_validator(state):
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

def command_executor(state):
    print("Safe commands being executed")
    safe_cmds = state.get("safe_commands", [])
    output = []
    execution_analysis_results = []
    for cmd in safe_cmds:
        try:
            result = subprocess.check_output(
                cmd, shell=True, stderr=subprocess.STDOUT, timeout=10
            )
            print(f"Analysing result {result.decode()}")
            analysis = llm.invoke([HumanMessage(content=get_analysis_prompt(result.decode()))])
            execution_analysis_results.append(analysis)
            output.append(f"{cmd}\n{result.decode()}\n")
        except Exception as e:
            output.append(f"{cmd}\nError: {str(e)}\n")
    analysis_result = '\n'.join(execution_analysis_results)
    return {
        "execution_results": output,
        "execution_analysis_results": execution_analysis_results,
        "messages": state["messages"]
        + [HumanMessage(content=f"Command execution results:\n{analysis_result}")],
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