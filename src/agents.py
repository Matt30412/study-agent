"""Agente ReAct in LangGraph: router -> agent <-> tools, con rifiuto fuori tema."""

from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from src.config import LLM_MODEL,RECURSION_LIMIT

from src.tools import TOOLS

SYSTEM_PROMPT = """Sei un assistente di studio per un corso universitario di Intelligenza Artificiale.
Basa le risposte sul materiale del corso, usando i tool per cercarlo, e cita sempre file e pagina.
Se il materiale non contiene la risposta, dillo chiaramente invece di inventare."""

ROUTER_PROMPT = """Classifichi le domande rivolte a un assistente di studio di un corso
universitario di Intelligenza Artificiale (ricerca nello spazio degli stati, agenti
intelligenti, machine learning, Prolog, logica e rappresentazione della conoscenza).

Rispondi con UNA sola parola:
- PERTINENTE se la domanda riguarda quegli argomenti, il materiale del corso, o prosegue
  un discorso gia' avviato su di essi (es. "approfondisci", "e quindi?", "fammi un riassunto").
- FUORI_TEMA in tutti gli altri casi.

Non rispondere alla domanda, classificala e basta."""

REFUSAL = (
    "Posso aiutarti solo sul materiale del corso di Intelligenza Artificiale "
    "(ricerca, agenti intelligenti, machine learning, Prolog, logica). "
    "Prova a chiedermi qualcosa su quegli argomenti."
)

ROUTER_CONTEXT_WINDOW = 4


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    route: str


def build_agent():
    llm = ChatOllama(model=LLM_MODEL, temperature=0)
    llm_with_tools = llm.bind_tools(TOOLS)

    def router(state: AgentState):
        # Passiamo una finestra di contesto, non solo l'ultimo messaggio: senza,
        # un follow-up come "approfondisci" verrebbe classificato fuori tema.
        recent = state["messages"][-ROUTER_CONTEXT_WINDOW:]
        transcript = "\n".join(
            f"{'Utente' if isinstance(m, HumanMessage) else 'Assistente'}: {m.content}"
            for m in recent
            if m.content
        )
        verdict = llm.invoke(
            [SystemMessage(ROUTER_PROMPT), HumanMessage(transcript)]
        ).content.upper()
        return {"route": "refuse" if "FUORI_TEMA" in verdict else "agent"}

    def agent(state: AgentState):
        messages = [SystemMessage(SYSTEM_PROMPT)] + state["messages"]
        return {"messages": [llm_with_tools.invoke(messages)]}

    def refuse(state: AgentState):
        return {"messages": [AIMessage(REFUSAL)]}

    graph = StateGraph(AgentState)
    graph.add_node("router", router)
    graph.add_node("agent", agent)
    graph.add_node("tools", ToolNode(TOOLS))
    graph.add_node("refuse", refuse)

    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router", lambda s: s["route"], {"agent": "agent", "refuse": "refuse"}
    )
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    graph.add_edge("refuse", END)

    return graph.compile(checkpointer=MemorySaver())


if __name__ == "__main__":
    app = build_agent()
    config = {"configurable": {"thread_id": "sessione-1"}, "recursion_limit": RECURSION_LIMIT}

    print("Benvenuto! Fai una domanda sul corso di Intelligenza Artificiale (o 'exit' per uscire).")
    while True:
        question = input("Tu: ").strip()
        if question.lower() in {"esci", "exit", "quit"}:
            break
        if not question:
            continue

        result = app.invoke({"messages": [HumanMessage(question)]}, config)
        print(f"\nAssistente: {result['messages'][-1].content}\n")
