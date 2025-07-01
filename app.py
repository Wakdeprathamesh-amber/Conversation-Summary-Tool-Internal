import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from nodes.student_card import StudentCardNode
from nodes.lead_status import LeadStatusNode
from nodes.student_requirements import StudentRequirementsNode
from nodes.admission_journey import AdmissionJourneyNode
from nodes.property_preferences import PropertyPreferencesNode
from nodes.conversation_timeline import ConversationTimelineNode
from nodes.conversation_summary import ConversationSummaryNode
from nodes.actionables import ActionablesNode
from nodes.tasks_and_next_steps import TasksAndNextStepsNode
import json
import asyncio
import time
from graph.summary_store import SummaryStore
from graph.data_loader import DataLoader
from graph.data_consolidator import consolidate_and_report

# Load environment variables
load_dotenv()

def init_llm():
    """Initialize the language model"""
    return ChatOpenAI(
        temperature=0,
        model_name="gpt-4.1-mini",
        api_key=os.getenv("OPENAI_API_KEY")
    )

# Helper to wrap node process with timing and logging
async def timed_node_process(node, name, input_data):
    # Only print the LLM input string (llm_text) being sent
    if isinstance(input_data, dict) and "conversation" in input_data:
        print("\n===== LLM INPUT SENT TO NODE =====\n")
        print(input_data["conversation"])
        print("\n===== END LLM INPUT =====\n")
    result = await node.process(input_data)
    return result

def to_serializable(obj):
    if isinstance(obj, list):
        return [to_serializable(item) for item in obj]
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    if hasattr(obj, 'dict'):
        return obj.dict()
    return obj

def generate_summary_on_demand(lead_id: str, force_refresh: bool = False):
    summary_store = SummaryStore(lead_id)
    data_loader = DataLoader(lead_id)

    # Load last processed state
    last_processed = summary_store.get_last_processed() if not force_refresh else {}
    prev_summary = summary_store.get_summary() if not force_refresh else {}

    # Load new data
    new_data = data_loader.load_all(last_processed)

    # Consolidate conversation events (calls, whatsapp, email, etc.)
    consolidation = consolidate_and_report(new_data)
    timeline = consolidation["timeline"]
    llm_timeline = consolidation["llm_timeline"]
    llm_text = consolidation["llm_text"]
    counts = consolidation["counts"]
    # Write to file for easier inspection
    with open("consolidated_timeline.json", "w") as f:
        json.dump(timeline, f, indent=2)
    with open("consolidated_llm_timeline.json", "w") as f:
        json.dump(llm_timeline, f, indent=2)
    with open("consolidated_llm_text.txt", "w") as f:
        f.write(llm_text)
    with open("consolidated_counts.json", "w") as f:
        json.dump(counts, f, indent=2)

    # Prepare input for nodes
    # Find the first key that looks like lead data
    lead_data = None
    for k in new_data:
        if "lead" in k.lower():
            lead_data = new_data[k]
            break
    student_card_input = {"lead": lead_data or {}}
    other_nodes_input = {"conversation": llm_text}

    # If all data is empty and not force_refresh, return cached summary
    if all(
        (not v or v == [] or v == "") for v in new_data.values()
    ) and not force_refresh:
        if prev_summary:
            print("No new data. Returning cached summary.")
            return {"message": "No new data. Returning last summary.", "summary": prev_summary}
        else:
            print("No data found for this lead yet.")
            return {"message": "No data found for this lead yet.", "summary": {}}

    # Enable node execution for all nodes
    student_card_node = StudentCardNode(init_llm())
    lead_status_node = LeadStatusNode(init_llm())
    student_requirements_node = StudentRequirementsNode(init_llm())
    admission_journey_node = AdmissionJourneyNode(init_llm())
    property_preferences_node = PropertyPreferencesNode(init_llm())
    conversation_summary_node = ConversationSummaryNode(init_llm())
    actionables_node = ActionablesNode(init_llm())
    tasks_and_next_steps_node = TasksAndNextStepsNode(init_llm())

    async def run_all_nodes():
        try:
            results = await asyncio.gather(
                timed_node_process(student_card_node, "StudentCardNode", student_card_input),
                timed_node_process(lead_status_node, "LeadStatusNode", other_nodes_input),
                timed_node_process(student_requirements_node, "StudentRequirementsNode", other_nodes_input),
                timed_node_process(admission_journey_node, "AdmissionJourneyNode", other_nodes_input),
                timed_node_process(property_preferences_node, "PropertyPreferencesNode", other_nodes_input),
                timed_node_process(conversation_summary_node, "ConversationSummaryNode", other_nodes_input),
                timed_node_process(actionables_node, "ActionablesNode", other_nodes_input),
                timed_node_process(tasks_and_next_steps_node, "TasksAndNextStepsNode", other_nodes_input),
            )
            return results
        except Exception as e:
            print("\n[ERROR] Exception during node execution:", str(e))
            import traceback
            traceback.print_exc()
            return [None] * 8

    results = asyncio.run(run_all_nodes())
    # Aggregate results into a summary object (all nodes)
    summary = {
        "student_card": to_serializable(results[0]),
        "lead_status": to_serializable(results[1]),
        "student_requirements": to_serializable(results[2]),
        "admission_journey": to_serializable(results[3]),
        "property_preferences": to_serializable(results[4]),
        "conversation_summary": to_serializable(results[5]),
        "actionables": to_serializable(results[6]),
        "tasks_and_next_steps": to_serializable(results[7]),
        "conversation_timeline": timeline,
        "counts": counts,
    }
    # Save summary
    summary_store.save(summary, last_processed)
    print("\n===== STRUCTURED SUMMARY OUTPUT =====")
    print(json.dumps(summary, indent=2))
    return {"message": "Summary generated.", "summary": summary}

if __name__ == "__main__":
    # For now, just test with Lead001
    result = generate_summary_on_demand("Lead001", force_refresh=True)
    print("\n===== ON-DEMAND SUMMARY OUTPUT =====")
    print(json.dumps(result, indent=2)) 