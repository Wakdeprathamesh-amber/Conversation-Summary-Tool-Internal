import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from llm_analysis.requirements_node import RequirementsNode
from llm_analysis.tasks_actionables_node import TasksAndActionablesNode
from llm_analysis.conversation_summary_node import ConversationSummaryNode
from dotenv import load_dotenv
load_dotenv()

def generate_requirements_summary(timeline_path: str):
    print(f"[Orchestrator] Starting requirements extraction...")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("[Orchestrator] ERROR: OPENAI_API_KEY not set!")
        raise ValueError("Please set the OPENAI_API_KEY environment variable.")
    prompt_path = os.path.join("llm_analysis", "prompts", "requirements_prompt.txt")
    node = RequirementsNode(openai_api_key, prompt_path)
    output_path = None
    try:
        result = node.run(timeline_path, output_path)
        print("[Orchestrator] Requirements extraction complete.")
        return result
    except Exception as e:
        print(f"[Orchestrator] ERROR: {e}")
        raise

def generate_tasks_actionables_summary(timeline_path: str):
    print(f"[Orchestrator] Starting tasks/actionables extraction...")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("[Orchestrator] ERROR: OPENAI_API_KEY not set!")
        raise ValueError("Please set the OPENAI_API_KEY environment variable.")
    prompt_path = os.path.join("llm_analysis", "prompts", "tasks_actionables_prompt.txt")
    node = TasksAndActionablesNode(openai_api_key, prompt_path)
    output_path = None
    try:
        result = node.run(timeline_path, output_path)
        print("[Orchestrator] Tasks/Actionables extraction complete.")
        return result
    except Exception as e:
        print(f"[Orchestrator] ERROR: {e}")
        raise

def generate_conversation_summary(timeline_path: str):
    print(f"[Orchestrator] Starting conversation summary extraction...")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("[Orchestrator] ERROR: OPENAI_API_KEY not set!")
        raise ValueError("Please set the OPENAI_API_KEY environment variable.")
    prompt_path = os.path.join("llm_analysis", "prompts", "conversation_summary_prompt.txt")
    node = ConversationSummaryNode(openai_api_key, prompt_path)
    output_path = None
    try:
        result = node.run(timeline_path, output_path)
        print("[Orchestrator] Conversation summary extraction complete.")
        return result
    except Exception as e:
        print(f"[Orchestrator] ERROR: {e}")
        raise

async def generate_combined_summary_async(timeline_path: str):
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as executor:
        req_future = loop.run_in_executor(executor, generate_requirements_summary, timeline_path)
        tasks_future = loop.run_in_executor(executor, generate_tasks_actionables_summary, timeline_path)
        conv_future = loop.run_in_executor(executor, generate_conversation_summary, timeline_path)
        requirements, tasks_actionables, conversation_summary = await asyncio.gather(
            req_future, tasks_future, conv_future
        )
    combined = {
        "requirements": requirements,
        "tasks_and_actionables": tasks_actionables,
        "conversation_summary": conversation_summary
    }
    print("\n[Orchestrator] Combined Output:")
    print(combined)
    return combined

def generate_combined_summary(timeline_path: str):
    """
    Synchronous wrapper for backward compatibility. Runs the async version.
    """
    return asyncio.run(generate_combined_summary_async(timeline_path))


def main():
    timeline_path = "data/timeline_917007220975.json"  # Example timeline
    result = generate_combined_summary(timeline_path)
    print("\n[Orchestrator] Final Combined Extraction Result:")
    print(result)

if __name__ == "__main__":
    main() 