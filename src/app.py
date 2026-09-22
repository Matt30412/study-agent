"""Interfaccia web di chat per lo study agent."""

import gradio as gr
from langchain_core.messages import HumanMessage

from src.agents import build_agent

agent = build_agent()

DEFAULT_SESSION = "sessione-1"


def respond(message: str, history, session_id: str) -> str:
    thread_id = (session_id or "").strip() or DEFAULT_SESSION
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 15,
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
    demo.launch()
