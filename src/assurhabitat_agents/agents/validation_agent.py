# src/assurhabitat_agents/agents/validation_agent.py
import re
import sys
from pathlib import Path
import json
import time


from typing import Tuple, Dict, Any, List
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from assurhabitat_agents.model.llm_model_loading import llm_inference
from assurhabitat_agents.config.tool_config import VALIDATION_TOOLS, VALIDATION_TOOLS_DESCRIPTION
from assurhabitat_agents.utils import parse_output
from assurhabitat_agents.config.langfuse_config import observe

tools = VALIDATION_TOOLS
tool_names = list(VALIDATION_TOOLS.keys())

class ValidationReActState(TypedDict):
    images_path: list[str]
    history: list[str]  # L'historique des échanges (Thought, Action, Observation)
    last_action: str | None  # Le nom de l'outil à appeler (si applicable)
    last_arguments: dict | None  # Les arguments à passer à l'outil
    last_observation: str | None  # Le résultat de l'outil appelé
    
    parsed_declaration: dict  # Resultat de l'agent Declaration (Ne peut pas etre None, Le superviseur ne peut appeler cet agent que si cet etat est connu)

    # results from tools
    image_conformity: dict | None       # {"match": bool, "raw_output": str}
    guarantee_report: dict | None       # {"is_garanteed": bool, "guarantee": {...}}
    answer: str | None  # Finale answer

def format_prompt_valid(state: ValidationReActState, tools) -> str:
    
    HISTORY_KEEP = 10
    history = state.get("history", [])[-HISTORY_KEEP:]

    # Show parsed_declaration and missing fields if available
    parsed = state.get("parsed_declaration")
    conformity = state.get("image_conformity")
    guarantee = state.get("guarantee_report")
    images = state.get("images_path", [])

    # Build actions block
    actions_block = "\n".join(f"- {a}" for a in tools) if tools else "- (no tools available)"

    parts = [
        "You are the Validation Agent for AssurHabitat. Decide the next step: either",
        "1) call a tool (Action) OR 2) give the final answer (Réponse).",
        "",
        "Available tools:",
        actions_block,
        "Tool descriptions:",
        VALIDATION_TOOLS_DESCRIPTION,
        "",
        "Rules:",
        "- If you call a tool, use a single line: Action: TOOL_NAME",
        "- If arguments are needed, write: Arguments: then either a JSON object or key=value lines",
        "- If you return the final reply to the user, write: Answer: <text>",
        "",
        "Decision rules:",
        "- If image_conformity is None: you MUST call CheckConformity first.",
        "- If guarantee_report is None but image_conformity.compatible == True: then call CheckGuarantee.",
        "- If both are completed: produce a final answer for the supervisor.",
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
    if conformity:
        parts.append("Conformity: " + json.dumps(conformity, ensure_ascii=False))
        
    parts.append("Images available in the state (use them for CheckConformity):")
    parts.append(json.dumps(images, ensure_ascii=False))
    
    if guarantee:
        parts.append("Guarantee: " + json.dumps(guarantee, ensure_ascii=False))

    parts.append("")
    parts.append("Now propose the next single Thought + Action (or final answer).")
    # join and return
    return "\n".join(parts)

@observe(name="validation_thought_step")
def node_thought_action_valid(state: ValidationReActState) -> ValidationReActState:

    prompt = format_prompt_valid(state, tool_names)
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
        state["history"].append(f"Answer: {content[0]}")
        state["answer"] = content[0]
    else:
        # Thought only: no action requested, we keep loop running
        state["history"].append(f"Thought: {content[0] if content else ''}")
    return state

@observe(name="validation_action_step")
def node_tool_execution_valid(state: ValidationReActState) -> ValidationReActState:
    """
    Execute the tool stored in state['last_action'] with state['last_arguments'].
    Update state['last_observation'], state['history'], and structured fields:
      - state['image_conformity']
      - state['guarantee_report']
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

    if tool_name == "CheckConformity":
        if isinstance(observation, dict):
            state["image_conformity"] = observation

            sinistre = state["parsed_declaration"]["sinistre_type"]
            detected = observation.get("detected_damage_types", [])
        
            COMPATIBILITY_RULES = {
                "incendie_explosion": {"fire", "soot", "smoke"},
                "degats_des_eaux": {"water", "mold"},
                "vol_vandalisme": {"impact", "theft_signs"},
            }
        
            state["image_conformity"]["compatible"] = bool(
                set(detected) & COMPATIBILITY_RULES.get(sinistre, set())
            )
        else:
            state["history"].append("check_conformity failed.")
            state['image_conformity'] = {
                    "error": "CheckConformity failed.",
                    "reason": str(observation)
                }

    # ---------- CASE 2: verify_completeness tool (explicit call) ----------
    elif tool_name == "CheckGuarantee":
        if isinstance(observation, dict):
            state['guarantee_report'] = observation
        else:
            # Only overwrite if guarantee_report was empty
            if not state.get('guarantee_report'):
                state['guarantee_report'] = {
                    "error": "CheckGuarantee failed.",
                    "reason": str(observation)
                }
            state["history"].append("CheckGuarantee failed.")

    # reset action so next Thought node computes next step
    state["last_action"] = None
    state["last_arguments"] = None

    return state

def build_graph_valid():
    checkpointer = MemorySaver()
    # ---- BUILD THE GRAPH ----
    graph_builder = StateGraph(ValidationReActState, configurable_fields=["thread_id"])

    graph_builder.add_node("thought", node_thought_action_valid)
    graph_builder.add_node("action", node_tool_execution_valid)

    graph_builder.add_edge(START, "thought")

    def decide_from_thought(runtime_state: ValidationReActState):
        # Stop if final answer is ready
        if runtime_state.get("answer"):
            return END

        # If LLM selected an action → go to tool execution
        if runtime_state.get("last_action"):
            return "action"

        # Otherwise → continue thinking
        return "thought"

    graph_builder.add_conditional_edges("thought", decide_from_thought)
    graph_builder.add_edge("action", "thought")

    # Compile graph
    graph = graph_builder.compile(checkpointer=checkpointer)
    return graph

def run_valid_agent(initial_state: ValidationReActState, max_steps: int = 30):
    """
    Runs the Validation agent using LangGraph's runtime.
    Thought -> Action -> Thought loop is handled automatically.
    """
    graph = build_graph_valid()

    # ---- RUN THE GRAPH ----
    step = 0
    state = initial_state

    # Stream events as they occur
    for event in graph.stream(initial_state, config={"configurable": {"thread_id": "valid1"}}):
        step += 1
        print(f"Step {step} ##########:\n {event}")
        if step > max_steps:
            print("\nReached max steps limit.")
            break

        if event.get('thought'):
            state = event['thought']

        # Stop conditions
        if event.get('thought'):
            if event['thought'].get("answer"):
                state = event['thought']
                print("\nFinal answer produced.\n")
                break

    # ---- FINAL STATE ----
    print("--- FINAL STATE ---")
    print("guarantee_report:", state.get("guarantee_report"))
    print("image_conformity:", state.get("image_conformity"))
    print("answer:", state.get("answer"))

    return state