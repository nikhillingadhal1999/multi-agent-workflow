# .PHONY: run setup

# VENV := .venv
# SCRIPT := src/multiAgentDocumentExecutionPipeline.py

# run: setup
# 	@echo "🚀 Running script in virtual environment..."
# 	@bash -c "source $(VENV)/bin/activate && python3 $(SCRIPT)"

# setup:
# 	@if [ ! -d "$(VENV)" ]; then \
# 		echo '🧪 Creating virtual environment...'; \
# 		python3 -m venv $(VENV); \
# 	fi
# 	@echo '📦 Installing requirements...'
# 	@bash -c "source $(VENV)/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

# # Makefile

VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
SCRIPT := src/multiAgentDocumentExecutionPipeline.py

# Setup virtual environment and install requirements
setup:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "🔧 Creating virtual environment..."; \
		python3 -m venv $(VENV_DIR); \
	else \
		echo "✅ Virtual environment already exists."; \
	fi
	@echo "📦 Installing requirements..."
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt

# Run the app — assumes env already set up
run:
	@echo "🚀 Running the pipeline..."
	@$(PYTHON) $(SCRIPT)
