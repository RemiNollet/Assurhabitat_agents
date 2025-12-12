# src/assurhabitat_agents/agents/expertise_agent.py
import re
import sys
from pathlib import Path
import json
import time


from typing import Tuple, Dict, Any, List
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END

from assurhabitat_agents.model.llm_model_loading import llm_inference
from assurhabitat_agents.config.tool_config import EXPERTISE_TOOLS, EXPERTISE_TOOLS_DESCRIPTION
from assurhabitat_agents.utils import parse_output
from assurhabitat_agents.config.langfuse_config import observe

class ExpertiseReActState(TypedDict):
    image_paths: list[str]
    history: list[str]

    last_action: str | None        
    last_arguments: dict | None
    last_observation: str | None

    parsed_declaration: dict  # fourni par l’agent Validation

    # tool outputs
    estimation: dict | None   # {"estimated_cost":..., "final_compensation":..., "explanation":...}
    
    # final output
    report: str | None

def format_prompt_expert(state: ExpertiseReActState, tools) -> str:
    
    HISTORY_KEEP = 10
    history = state.get("history", [])[-HISTORY_KEEP:]

    # Show parsed_declaration and missing fields if available
    parsed = state.get("parsed_declaration")
    estimation = state.get("estimation")
    images = state.get("image_paths", [])

    # Build actions block
    actions_block = "\n".join(f"- {a}" for a in tools) if tools else "- (no tools available)"

    parts = [
        "You are the Expertise Agent for AssurHabitat. Decide the next step: either",
        "1) call a tool (Action) OR 2) give the final answer (Réponse).",
        "",
        "Available tools:",
        actions_block,
        "Tool descriptions:",
        EXPERTISE_TOOLS_DESCRIPTION,
        "",
        "Rules:",
        "- If you call a tool, use a single line: Action: TOOL_NAME",
        "- If arguments are needed, write: Arguments: then either a JSON object or key=value lines",
        "- If you return the final reply to the user, write: Réponse: <text>",
        "- Never ask the user for more information.",
        "- Never produce questions.",
        "- You only generate the internal report.",
        "- The available images are stored in state.image_paths."
        "",
        "Decision rules:",
        "- estimation is None: you MUST call CostEstimation first.",
        "- If you need more information from an expert to help you estimate the cost ", 
        "or don't know something you can use the tool AskHuman",
        "When estimation is available, produce the final report.",
        "The report MUST include:"
        "- summary of the sinistre",
        "- estimated cost"
        "- franchise applied",
        "- maximum coverage amount",
        "- final compensation to be paid",
        "- a short textual analysis",
        "- notes for internal advisors",
        "Return it using:",
        "Réponse: <report text>",
        "",
        "Context summary:",
    ]

    if history:
        parts.append("Recent history:")
        parts.append("\n".join(history))
    if parsed:
        # pretty print the parsed_declaration small snippet
        try:
            pretty = json.dumps(parsed, ensure_ascii=False)
        except Exception:
            pretty = str(parsed)
        parts.append("Current parsed_declaration JSON: (you can find the sinistre type inside for CheckConformity)")
        parts.append(pretty)
        
    parts.append("Images available in the state:")
    parts.append(json.dumps(images, ensure_ascii=False))
    
    if estimation:
        parts.append("Estimations: " + json.dumps(estimation, ensure_ascii=False))

    parts.append("")
    parts.append("Now propose the next single Thought + Action (or final Réponse).")
    # join and return
    return "\n".join(parts)

tools = EXPERTISE_TOOLS
tool_names = list(EXPERTISE_TOOLS.keys())

@observe(name="expertise_thought_step")
def node_thought_action_expert(state: ExpertiseReActState) -> ExpertiseReActState:

    prompt = format_prompt_expert(state, tool_names)
    output = llm_inference(prompt)

    # parse_output must return a tuple like ("action", tool_name, tool_args)
    # or ("answer", answer_text) or ("thought", thought_text)
    step_type, *content = parse_output(output)

    # Append the raw LLM output to history for traceability
    state.setdefault("history", [])
    state["history"].append(f"LLM output: {output}")

    if step_type == "action":
        tool_name, tool_args = content
        # store next action and its arguments
        state["last_action"] = tool_name
        state["last_arguments"] = tool_args or {}
        # keep history friendly: record the action intention
        state["history"].append(f"Action: call tool: {tool_name} with args: {tool_args}")
    elif step_type == "answer":
        # final textual answer produced by the LLM
        state["last_action"] = None
        state["last_arguments"] = None
        state["last_observation"] = None
        state["report"] = content[0]
        state["history"].append(f"Answer: {content[0]}")
    else:
        # Thought only: no action requested, we keep loop running
        state["history"].append(f"Thought: {content[0] if content else ''}")
    return state

@observe(name="expertise_action_step")
def node_tool_execution_expert(state: ExpertiseReActState) -> ExpertiseReActState:
    """
    Execute the tool stored in state['last_action'] with state['last_arguments'].
    Update state['last_observation'], state['history'], and structured fields:
      - state['estimation']
    """
    tool_name = state.get("last_action")
    tool_args = state.get("last_arguments") or {}

    # nothing to execute
    if not tool_name:
        state.setdefault("history", []).append("No action to execute.")
        return state

    # call the tool if available
    if tool_name in tools:
        try:
            observation = tools[tool_name](**tool_args)
        except Exception as e:
            observation = f"Error during tool {tool_name}: {e}"
    else:
        observation = f"Error: Unknown tool {tool_name}"

    # store observation and history
    state["last_observation"] = str(observation)
    state.setdefault("history", []).append(f"Observation from {tool_name}: {state['last_observation']}")

    if tool_name == "CostEstimation":
        if isinstance(observation, dict):
            state['estimation'] = observation
        else:
            state["history"].append("Cost estimation failed.")

    # reset action so next Thought node computes next step
    state["last_action"] = None
    state["last_arguments"] = None

    return state

def build_graph_expert():
    checkpointers = MemorySaver()
    # ---- BUILD THE GRAPH ----
    graph_builder = StateGraph(ExpertiseReActState)

    graph_builder.add_node("thought", node_thought_action_expert)
    graph_builder.add_node("action", node_tool_execution_expert)

    graph_builder.add_edge(START, "thought")

    def decide_from_thought(runtime_state: ExpertiseReActState):
        # Stop when the report is available
        if runtime_state.get("report"):
            return END

        # If LLM selected a tool, go to action node
        if runtime_state.get("last_action"):
            return "action"

        # Otherwise continue thinking
        return "thought"

    graph_builder.add_conditional_edges("thought", decide_from_thought)
    graph_builder.add_edge("action", "thought")

    # Compile the graph
    graph = graph_builder.compile(checkpointers=checkpointers)
    return graph
    
    
def run_expert_agent(initial_state: ExpertiseReActState, max_steps: int = 30):
    """
    Runs the Expertise agent using LangGraph.
    Thought -> Action -> Thought handled automatically.
    """
    graph = build_graph_expert()

    # ---- RUN THE GRAPH ----
    step = 0
    state = initial_state

    for event in graph.stream(initial_state, config={"configurable": {"thread_id": "expert1"}}):
        step += 1
        if step > max_steps:
            print("\nReached maximum step limit.")
            break

        if "state" in event:
            state = event["state"]

        # Print history incrementally
        history = state.get("history", [])
        if history:
            print("\n".join(history))
            state["history"] = []

        # Stop condition: report produced
        if state.get("report"):
            print("\nExpertise process complete.")
            break

    # ---- FINAL STATE ----
    print("--- FINAL STATE ---")
    print("estimation:", state.get("estimation"))
    print("report:", state.get("report"))

    return state