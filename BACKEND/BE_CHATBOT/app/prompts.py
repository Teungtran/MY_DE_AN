# Central prompts module for BE_CHATBOT
from .orchestrator.shop_graph.prompts import SHOP_SYSTEM_PROMPT
from .orchestrator.it_graph.prompts import IT_SYSTEM_PROMPT
from .orchestrator.appointment_graph.prompts import APPOINTMENT_SYSTEM_PROMPT

__all__ = [
    "SHOP_SYSTEM_PROMPT",
    "IT_SYSTEM_PROMPT", 
    "APPOINTMENT_SYSTEM_PROMPT"
]
