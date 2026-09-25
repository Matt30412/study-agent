"""Interfaccia web di chat per lo study agent."""

import gradio as gr
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver

from src.agents import build_agent
from src.config import APP_USERS, LLM_MODEL, RECURSION_LIMIT
from src.tenancy import current_owner, load_users

LLM = ChatOllama(model=LLM_MODEL, temperature=0)
CHECKPOINTER = MemorySaver()

DEFAULT_SESSION = "sessione-1"


def respond(message: str, history, session_id: str, request: gr.Request) -> str:
    owner = current_owner(request)
    session = (session_id or "").strip() or DEFAULT_SESSION
    agent = build_agent(owner, LLM, CHECKPOINTER)
    config = {
        # L'owner nel thread_id separa le conversazioni: "sessione-1" di Alice non è quella di Bob.
        "configurable": {"thread_id": f"{owner}:{session}"},
        "recursion_limit": RECURSION_LIMIT,
    }
    result = agent.invoke({"messages": [HumanMessage(message)]}, config)
    return result["messages"][-1].content


session_box = gr.Textbox(
    value=DEFAULT_SESSION,
    label="Nome sessione",
    info="Stesso nome = stessa conversazione, anche dopo un refresh. Cambialo per ripartire da zero.",
)

demo = gr.ChatInterface(
    fn=respond,
    title="Study Agent",
    description="Assistente di studio sul materiale del corso di Intelligenza Artificiale.",
    additional_inputs=[session_box],
    additional_inputs_accordion=gr.Accordion("Sessione", open=True),
    examples=[
        ["Cos'e' la ricerca best-first?", None],
        ["Quali documenti del corso sono disponibili?", None],
        ["Confronta ricerca in ampiezza e in profondita' e salvami un riassunto", None],
    ],
)

if __name__ == "__main__":
    demo.launch(auth=load_users(APP_USERS))
