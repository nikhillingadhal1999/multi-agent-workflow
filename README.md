# multi-agent-workflow
# First workflow AgentSmith

> Autonomous Multi-Agent System for Document-Driven System Health Checks
> Powered by **Ollama**, **LangGraph**, and **LangChain**

---

## 📚 Overview

**AgentSmith** is a modular multi-agent framework that takes natural language instructions from a document, interprets them using a team of AI agents, and executes validated system commands. It’s designed for developers, system admins, and AI tinkerers who want to automate system-level health monitoring intelligently.

---

## 🔁 What It Does

Given a plain-text instruction file (like `instructions.txt`), the system will:

1. 🧑‍💼 **Read** and understand the document  
2. 🧠 **Analyze** context and intent  
3. 🔍 **Extract** all relevant system commands  
4. 🛡️ **Validate** the safety of commands  
5. 🚀 **Execute** only safe commands  
6. 📊 **Analyze Results** to provide clear insights

---

🚀 Getting Started
1. Clone the repository
```
git clone https://github.com/your-username/agentsmith.git
cd agentsmith
```
2. Run with Make

```
make run
```

This will:

Create a virtual environment in .venv/ (if not already created)

Install all Python dependencies

Run the multiAgentDocumentExecutionPipeline.py script using the local LLM
