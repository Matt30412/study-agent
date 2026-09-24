import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage

from src.agents import classify_question

QUESTION = [HumanMessage("qual è la ricetta della carbonara?")]


@pytest.mark.parametrize("verdict", ["FUORI_TEMA", "fuori_tema", "Classificazione: FUORI_TEMA."])
def test_router_refuses(verdict):
    llm = FakeListChatModel(responses=[verdict])
    assert classify_question(llm, QUESTION) == "refuse"


# OFF_TOPIC è incluso di proposito: è il caso in cui il router smette di rifiutare
# in silenzio (vedi "Limiti noti" nel README). Se questo test cambia, cambia il contratto.
@pytest.mark.parametrize("verdict", ["PERTINENTE", "", "Non saprei", "OFF_TOPIC", "FUORI TEMA"])
def test_router_fail_open(verdict):
    llm = FakeListChatModel(responses=[verdict])
    assert classify_question(llm, QUESTION) == "agent"
