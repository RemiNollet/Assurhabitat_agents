# src/assurhabitat_agents/agents/declaration_agent.py
import re
import sys
from pathlib import Path
import json
import time


from typing import Tuple, Dict, Any, List
from typing_extensions import TypedDict

#from langgraph.types import interrupt
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# sys.path.insert(0, str(Path.cwd().parent / "src")) -> for notebook only
from assurhabitat_agents.model.llm_model_loading import llm_inference
from assurhabitat_agents.config.tool_config import DECLARATION_TOOLS, DECLARATION_TOOLS_DESCRIPTION
from assurhabitat_agents.utils import parse_output
from assurhabitat_agents.config.langfuse_config import observe

class DeclarationReActState(TypedDict):
    question: str  # La question initiale de l'utilisateur
    pictures: list[str] | None
    history: list[str]  # L'historique des échanges (Thought, Action, Observation)
    last_action: str | None  # Le nom de l'outil à appeler (si applicable)
    last_arguments: dict | None  # Les arguments à passer à l'outil
    last_observation: str | None  # Le résultat de l'outil appelé
    is_complete: bool | None  # La réponse finale
    parsed_declaration: dict | None # Stockage json de la declaration parser par le tool
    missing: list[str] | None # champs manquant dans la declarations
    answer: str | None # Final answer

def format_prompt_declar(state: DeclarationReActState, tools) -> str:
    """
    Build a concise prompt for the ReAct LLM using the whole state.
    - state: the DeclarationReActState dict (contains history, parsed_declaration, missing, question, etc.)
    - actions: list of available tool names with short descriptions (e.g. ["parse_declaration", "verify_completeness", "ask_human"])
    The function returns a prompt string ready to be sent to the LLM.
    """
    # Keep prompt short: only include last few history entries
    HISTORY_KEEP = 10
    history = state.get("history", [])[-HISTORY_KEEP:]

    # Show parsed_declaration and missing fields if available
    parsed = state.get("parsed_declaration")
    missing = state.get("missing", [])

    # Build actions block
    actions_block = "\n".join(f"- {a}" for a in tools) if tools else "- (no tools available)"

    parts = [
        "You are the Declaration Agent for AssurHabitat. Decide the next step: either",
        "1) call a tool (Action) OR 2) give the final answer (answer).",
        "",
        "Available tools:",
        actions_block,
        "Tool descriptions:",
        DECLARATION_TOOLS_DESCRIPTION,
        "",
        "Rules:",
        "- If you call a tool, use a single line: Action: TOOL_NAME",
        "- If arguments are needed, write: Arguments: then either a JSON object or key=value lines",
        "- If you return the final reply to the user, write: answer: <text>",
        "- If you don't know the year of a provided date, consider it's the year 2025."
        "",
        "Decision rules:",
        "- if parsed_declaration is None: you MUST call DeclarationParser first.",
        "- All the field in parsed_declaration.extracted MUST be present. if one field is missing ask the user using AskHuman.",
        "- if the the field pictures is [] then it mean there are no pictures and you need to ask the user for the pictures.",
        "",
        "Context summary:",
    ]

    if state.get("question"):
        parts.append(f"Original question: {state['question']}")
    if state.get("pictures"):
        parts.append(f"Original pictures: {state['pictures']}")

    if history:
        parts.append("Recent history:")
        parts.append("\n".join(history))
    if parsed:
        # pretty print the parsed_declaration small snippet
        try:
            pretty = json.dumps(parsed, ensure_ascii=False)
        except Exception:
            pretty = str(parsed)
        parts.append("Current parsed_declaration JSON:")
        parts.append(pretty)
    if missing:
        parts.append("Missing fields (need to ask human if required):")
        parts.append(", ".join(missing))

    parts.append("")
    parts.append("Now propose the next single Thought + Action (or final answer).")
    # join and return
    return "\n".join(parts)

tools = DECLARATION_TOOLS
tool_names = list(DECLARATION_TOOLS.keys())


@observe(name="declaration_thought_step")
def node_thought_action_declar(state: DeclarationReActState) -> DeclarationReActState:
    """
    Node that produces the next Thought/Action/Answer using the LLM.
    It fills last_action/last_arguments when the LLM asks to call a tool,
    or writes the final answer when the LLM produces an 'answer'.
    """
    # Build the prompt using the state's history and some structured context
    # It's helpful to include parsed_declaration and missing fields in the prompt so the LLM
    # can reason clearly about the next step.
    prompt = format_prompt_declar(state, tool_names)
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
        state["is_complete"] = True
        state["last_action"] = None
        state["last_arguments"] = None
        state["last_observation"] = None
        state["answer"] = content[0]
        state["history"].append(f"Answer: {content[0]}")
    else:
        # Thought only: no action requested, we keep loop running
        state["history"].append(f"Thought: {content[0] if content else ''}")
    return state

@observe(name="declaration_action_step")
def node_tool_execution_declar(state: DeclarationReActState) -> DeclarationReActState:
    """
    Execute the tool stored in state['last_action'] with state['last_arguments'].
    Update state['last_observation'], state['history'], and structured fields:
      - state['parsed_declaration']
      - state['is_complete'], state['missing'] via verify_completeness(parsed_declaration)
    Behavior for ask_human:
      - If parse_declaration tool exists, we call it with a combined raw input that
        contains the old parsed JSON and the new human reply so the LLM can merge them.
      - Otherwise, a simple heuristic fills the first missing field with the reply.
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

    if tool_name == "DeclarationParser":
        if isinstance(observation, dict):
            # Replace entire parsed_declaration with returned dict
            state["parsed_declaration"] = observation

            # After parsing, run verify_completeness if available
            if "InformationVerification" in tools:
                try:
                    verify_res = tools["InformationVerification"](state["parsed_declaration"])
                    if isinstance(verify_res, dict):
                        state["is_complete"] = bool(verify_res.get("is_complete", False))
                        state["missing"] = verify_res.get("missing", [])
                        state["history"].append(f"Auto-verify result: {verify_res}")
                except Exception as e:
                    state["history"].append(f"Auto-verify failed: {e}")
        else:
            state["history"].append("parse_declaration returned non-dict observation.")

    # ---------- CASE 2: verify_completeness tool (explicit call) ----------
    elif tool_name == "InformationVerification":
        if isinstance(observation, dict):
            state["is_complete"] = bool(observation.get("is_complete", False))
            state["missing"] = observation.get("missing", [])
        else:
            state["history"].append("verify_completeness returned unexpected output.")

    # ---------- CASE 3: ask_human tool (human response) ----------
    elif tool_name == "AskHuman":
        # observation expected to be the human reply string (or similar)
        human_reply = observation if isinstance(observation, str) else str(observation)
        state["history"].append(f"Human replied: {human_reply}")

        # If parse_declaration tool exists, call it with merged input:
        # Build combined raw input: include previous parsed_declaration JSON and the new human reply.
        if "DeclarationParser" in tools and isinstance(state.get("parsed_declaration"), dict):
            # Convert previous parsed_declaration to compact JSON and instruct the LLM to merge
            prev_json = json.dumps(state["parsed_declaration"], ensure_ascii=False)
            missing = state.get("missing", [])
            combined_raw_input = f"""
You are now in COMPLETION MODE.

The input below contains:
1. An EXISTING parsed JSON from a previous call.
2. A list of MISSING FIELDS that must be added inside the "extracted" section.
3. A HUMAN REPLY that contains the missing information.

Your ONLY task is to update the JSON by filling the missing fields.

RULES (MANDATORY):
- Return ONLY a valid JSON object.
- Never remove or modify existing fields.
- Only update json["extracted"].
- For each missing field, assign one value extracted from the human reply.
- Values are mapped IN ORDER: first missing field → first value, etc.
- If a field expects a list (like "photo" or "biens_impactes"), wrap the value in a list.
- If not enough values are provided, fill the remaining fields with null.
- Never change classification fields ("sinistre_type", "candidates", etc.).
- Never add explanations, comments, or text outside JSON.

EXAMPLE YOU MUST FOLLOW EXACTLY:

Existing JSON:
{
  "sinistre_type": "vol_vandalisme",
  "sinistre_confidence": 0.99,
  "sinistre_explain": "break-in",
  "candidates": [{"type": "vol_vandalisme", "score": 0.99}],
  "extracted": {
    "date_sinistre": null,
    "lieu": "chambre",
    "description": "effraction",
    "biens_impactes": ["porte"]
  }
}

Missing fields:
["photo", "police_report_number"]

Human reply:
"photo_12.jpg, 445677"

Correct output:
{
  "sinistre_type": "vol_vandalisme",
  "sinistre_confidence": 0.99,
  "sinistre_explain": "break-in",
  "candidates": [{"type": "vol_vandalisme", "score": 0.99}],
  "extracted": {
    "date_sinistre": null,
    "lieu": "chambre",
    "description": "effraction",
    "biens_impactes": ["porte"],
    "photo": ["photo_12.jpg"],
    "police_report_number": "445677"
  }
}

NOW APPLY THE SAME PROCESS.

Existing parsed JSON:
{prev_json}

Missing fields:
{missing}

Human reply:
{human_reply}

Return the UPDATED JSON below:
            """
            try:
                merged_obs = tools["DeclarationParser"](combined_raw_input)
                # If the parse_declaration returns dict, update parsed_declaration and re-run verify
                if isinstance(merged_obs, dict):
                    state["parsed_declaration"] = merged_obs

                    # call verify_completeness automatically
                    if "InformationVerification" in tools:
                        try:
                            verify_res = tools["InformationVerification"](state["parsed_declaration"])
                            if isinstance(verify_res, dict):
                                state["is_complete"] = bool(verify_res.get("is_complete", False))
                                state["missing"] = verify_res.get("missing", [])
                                state["history"].append(f"Auto-verify after human reply: {verify_res}")
                        except Exception as e:
                            state["history"].append(f"Auto-verify failed after human reply: {e}")

                    # Clear asked missing fields or remove those filled by LLM
                    # We keep the current 'missing' returned by verify_completeness.
                else:
                    # If parse_declaration did not return dict, fallback: simple fill
                    if state.get("missing"):
                        first = state["missing"][0]
                        state.setdefault("parsed_declaration", {}).setdefault("extracted", {})[first] = human_reply
                        state["missing"] = state.get("missing", [])[1:]
                        state["history"].append(f"Filled {first} with human reply (fallback).")

            except Exception as e:
                # on error, fallback to naive update
                if state.get("missing"):
                    first = state["missing"][0]
                    state.setdefault("parsed_declaration", {}).setdefault("extracted", {})[first] = human_reply
                    state["missing"] = state.get("missing", [])[1:]
                    state["history"].append(f"Filled {first} with human reply (fallback due to error: {e}).")
        else:
            # No parse tool available -> naive fill into first missing field
            if state.get("missing"):
                first = state["missing"][0]
                state.setdefault("parsed_declaration", {}).setdefault("extracted", {})[first] = human_reply
                state["missing"] = state.get("missing", [])[1:]
                state["history"].append(f"Filled {first} with human reply (no parse tool).")

    # reset action so next Thought node computes next step
    state["last_action"] = None
    state["last_arguments"] = None

    return state

def build_graph_declar():
    checkpointer = MemorySaver()
    
    # ---- BUILD THE GRAPH ----
    graph_builder = StateGraph(DeclarationReActState, configurable_fields=["thread_id"])

    graph_builder.add_node("thought", node_thought_action_declar)
    graph_builder.add_node("action", node_tool_execution_declar)

    graph_builder.add_edge(START, "thought")

    def decide_from_thought(runtime_state: DeclarationReActState):
        # Stop if done
        if runtime_state.get("answer"):
            return END
        # Action selected → go to action node
        if runtime_state.get("last_action"):
            return "action"
        # Otherwise → think again
        return "thought"

    graph_builder.add_conditional_edges("thought", decide_from_thought)
    graph_builder.add_edge("action", "thought")

    # Compile the graph
    graph = graph_builder.compile(checkpointer=checkpointer)
    return graph

def run_declar_agent(initial_state, max_steps=30):
    graph = build_graph_declar()

    step = 0
    final_state = None

    for event in graph.stream(initial_state, config={"configurable": {"thread_id": "declar1"}}):
        step += 1
        print(f"Step {step} ##########:\n {event}")

        # Stop condition
        if event.get('thought'):
            if event['thought'].get("answer"):
                final_state = event['thought']
                break

        if event.get('thought'):
            final_state = event['thought']

        if step >= max_steps:
            break

    print("\n--- FINAL STATE ---")
    print("is_complete:", final_state.get("is_complete"))
    print("parsed_declaration:", final_state.get("parsed_declaration"))
    print("missing:", final_state.get("missing"))
    print("answer:", final_state.get("answer"))
    return final_state