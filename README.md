# Amber Agent Conversation Summariser

An AI-powered tool that consolidates and summarizes student lead interactions across multiple communication channels for Amber Student agents.

## Project Structure
- `/data` - Sample mock inputs (lead, email, WhatsApp, etc.)
- `/nodes` - LangGraph nodes for each summary section
- `/prompts` - Clean prompt templates for LLM calls
- `/graph` - LangGraph orchestration logic
- `app.py` - Main application for testing the flow

## Setup
1. Ensure you have Python 3.9+ installed
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Development
The project uses LangGraph for orchestrating the summarization pipeline. Each summary component is modularized into separate nodes that process specific aspects of the lead's data.

### Key Components
- Student Profile Card Generator
- Lead Status Analyzer
- Property Discussion Summarizer
- Admission Journey Tracker
- Action Item Extractor
- TL;DR Generator

## Usage
(Documentation to be added as components are developed) 