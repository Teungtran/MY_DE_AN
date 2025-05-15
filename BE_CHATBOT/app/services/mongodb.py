import datetime
from typing import Any, Dict, List, Optional

import pymongo
from pymongo.server_api import ServerApi


class ChatHistoryManager:
    """MongoDB chat message history with custom schema."""

    def __init__(
        self,
        connection_string: str = "MONGO_URL",
        database_name: str = "DATABASE",
        collection_name: str = "MESSAGE",
        session_id: str = "default",
    ):
        """Initialize with MongoDB connection details."""
        self.client: pymongo.MongoClient = pymongo.MongoClient(connection_string, server_api=ServerApi("1"))
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name
        self.session_id = session_id
        self.db = self.client[database_name]

        existing_collections = self.db.list_collection_names()
        if collection_name not in existing_collections:
            print(f"[Info] Collection '{collection_name}' will be created automatically")
        else:
            print("use existing db")

        self.collection = self.db[collection_name]

    def save_chat_history(
        self,
        conversation_id: str,
        user_input: str,
        prompt_token: Optional[int] = None,
        completion_token: Optional[int] = None,
        total_token: Optional[int] = None,
        start_time: Optional[datetime.datetime] = None,
        end_time: Optional[datetime.datetime] = None,
        execution_time: Optional[float] = None,
        response: Optional[str] = None,
        category_id: Optional[str] = None,
        category_name: Optional[str] = None,
        source: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if category_id and category_name:
            category_code = {"category_id": category_id, "category_name": category_name}
        else:
            category_code = {"category_id": "general", "category_name": "general"}

        user_message = {
            "conversation_id": conversation_id,
            "type": "HUMAN-MESSAGE",
            "prompt_token": prompt_token,
            "content": user_input,
            "created_at": start_time.isoformat() if start_time else None,
            "category_code": category_code,
        }

        user_result = self.collection.insert_one(user_message)
        question_id = str(user_result.inserted_id)

        answer_id = None
        if response:
            assistant_message = {
                "conversation_id": conversation_id,
                "question_id": question_id,
                "type": "AI-MESSAGE",
                "prompt_token": prompt_token,
                "completion_token": completion_token,
                "total_token": total_token,
                "content": response,
                "created_at": start_time.isoformat() if start_time else None,
                "updated_at": end_time.isoformat() if end_time else None,
                "responded_in_s": execution_time,
                "category_code": category_code,
            }

            if source:
                assistant_message["source"] = source

            response_result = self.collection.insert_one(assistant_message)
            answer_id = str(response_result.inserted_id)

        return {"conversation_id": conversation_id, "question_id": question_id, "answer_id": answer_id or "N/A"}

    def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve and format conversation history with metadata.

        Args:
            conversation_id: ID of the conversation to retrieve.
            limit: Max number of messages to return.

        Returns:
            List of formatted message dictionaries.
        """
        messages = list(
            self.collection.find(
                {"conversation_id": conversation_id}, sort=[("created_at", pymongo.ASCENDING)], limit=limit
            )
        )

        return [
            {
                "type": msg["type"],
                "content": msg["content"],
                "category": msg.get("category_code", {}),
                "timestamp": msg.get("created_at"),
                "answer_id": msg.get("answer_id", None),
            }
            for msg in messages
        ]

    def delete_conversation(self, conversation_id: str) -> int:
        """
        Delete all messages in a conversation

        Args:
            conversation_id: ID of the conversation to delete

        Returns:
            Number of messages deleted
        """
        result = self.collection.delete_many({"conversation_id": conversation_id})
        return result.deleted_count
