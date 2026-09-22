"""Agente ReAct in LangGraph: agent <-> tools in ciclo fino alla risposta finale."""

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from src.tools import TOOLS

LLM_MODEL = "qwen2.5:7b"

SYSTEM_PROMPT = """Sei un assistente di studio per un corso universitario di Intelligenza Artificiale.
Basa le risposte sul materiale del corso, usando i tool per cercarlo, e cita sempre file e pagina.
Se il materiale non contiene la risposta, dillo chiaramente invece di inventare."""


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def build_agent():
    llm = ChatOllama(model=LLM_MODEL, temperature=0).bind_tools(TOOLS)

    def agent(state: AgentState):
        messages = [SystemMessage(SYSTEM_PROMPT)] + state["messages"]
        return {"messages": [llm.invoke(messages)]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent)
    graph.add_node("tools", ToolNode(TOOLS))

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")


    return graph.compile(checkpointer=MemorySaver())


if __name__ == "__main__":
    app = build_agent()
    config = {"configurable": {"thread_id": "sessione-1"}, "recursion_limit": 15}
    
    print("Benvenuto! Fai una domanda sul corso di Intelligenza Artificiale (o 'exit' per uscire).")
    while True:
        question = input("Tu: ").strip()
        if question.lower() in {"esci","exit","quit"}:
            break
        if not question:
            continue


        result = app.invoke({"messages": [HumanMessage(question)]},config)
        print(f"\nAssistente: {result['messages'][-1].content}\n")