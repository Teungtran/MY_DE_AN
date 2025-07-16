from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.memory.v2.db.mongodb import MongoMemoryDb
from agno.memory.v2.memory import Memory
from agno.storage.agent.mongodb import MongoDbAgentStorage
from agno.knowledge.agent import AgentKnowledge
from agno.tools.tavily import TavilyTools
from agno.tools.reasoning import ReasoningTools
from agno.team.team import Team
from agno.vectordb.qdrant import Qdrant
from agno.embedder.openai import OpenAIEmbedder
from agno.agent import Agent
from agno.tools.sql import SQLTools

# === Shared Persistent Memory ===
memory_db = MongoMemoryDb(
    db_url="mongodb+srv://nguyentrantrung2504:NBg7vdR1KSDlW1E3@cluster0.hpkg9.mongodb.net/admin?retryWrites=true&w=majority&appName=Cluster0",
    db_name="Store_agent_memory",
    collection_name="agent_memmory")
memory = Memory(model=OpenAIChat(id="gpt-4o-mini",api_key=OPENAI_API_KEY), db=memory_db)
storage = MongoDbAgentStorage(    
    db_url="mongodb+srv://nguyentrantrung2504:NBg7vdR1KSDlW1E3@cluster0.hpkg9.mongodb.net/admin?retryWrites=true&w=majority&appName=Cluster0",
    db_name="Store_agent_memory",
    collection_name="chat_history")
