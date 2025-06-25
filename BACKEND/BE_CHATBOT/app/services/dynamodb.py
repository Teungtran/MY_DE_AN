import datetime
import time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Callable
from .snowflake_id import SnowflakeGenerator
import boto3
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.types import DYNAMODB_CONTEXT

from utils.logging.logger import get_logger

logger = get_logger(__name__)
class DynamoHistory:
    def __init__(
        self,
        region_name: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        table_name: str = "HISTORY_CONVO",
        snowflake_generator: Optional[SnowflakeGenerator] = None
    ):
        self.region_name = region_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.table_name = table_name
        self.dynamodb = self.set_dynamodb()
        self.table = self.dynamodb.Table(self.table_name)
        self.snowflake_gen = snowflake_generator or SnowflakeGenerator(node_id=1)

    def set_dynamodb(self):
        region = self.region_name
        access_key = self.aws_access_key_id
        secret_key = self.aws_secret_access_key
        
        if isinstance(region, Callable):
            region = region()
        if isinstance(access_key, Callable):
            access_key = access_key()
        if isinstance(secret_key, Callable):
            secret_key = secret_key()
            
        return boto3.resource(
            "dynamodb",
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def check_table_exists(self) -> bool:
        try:
            existing_tables = [t.name for t in self.dynamodb.tables.all()]
            exists = self.table_name in existing_tables
            print(f"[INFO] Table '{self.table_name}' exists: {exists}")
            return exists
        except Exception as e:
            print(f"[ERROR] Failed to check table existence: {str(e)}")
            return False
    def check_id_exists(self, message_id: str) -> bool:
        try:
            response = self.table.get_item(Key={"id": message_id})
            return bool(response.get("Item"))
        except Exception as e:
            print(f"[ERROR] Failed to check ID existence: {str(e)}")
            return False
    def save_chat_history(
        self,
        conversation_id: str,
        user_id: str,
        user_input: str,
        prompt_token: Optional[int] = None,
        completion_token: Optional[int] = None,
        total_token: Optional[int] = None,
        tool_call_args: Optional[Dict[str, Any]] = None,
        tool_call_id: Optional[str] = None,
        start_time: Optional[datetime.datetime] = None,
        end_time: Optional[datetime.datetime] = None,
        execution_time: Optional[Decimal] = None,
        response: Optional[str] = None,
        language: Optional[str] = None,
        tool_call_name: Optional[str] = None,
        tool_call_type: Optional[str] = None,
    ) -> Dict[str, Any]:

        if not self.check_table_exists():
            raise Exception(f"DynamoDB table '{self.table_name}' does not exist.")

        now = datetime.datetime.now()
        start_time = start_time or now
        end_time = end_time or now
        execution_time = execution_time or DYNAMODB_CONTEXT.create_decimal(str((end_time - start_time).total_seconds()))

        reply_to_message_id = f"{conversation_id}-{int(start_time.timestamp())}"

        tools_array = (
            [
                {
                    "name": tool_call_name,
                    "id": tool_call_id,
                    "type": tool_call_type,
                    "args": tool_call_args or {},
                }
            ]
            if tool_call_name
            else []
        )

        fields = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "reply_to_message_id": reply_to_message_id,
            "language": language,
            "tools": tools_array,
            "created_at": start_time.isoformat(),
            "updated_at": end_time.isoformat(),
            "tokens": [
                {"prompt_token": prompt_token, "completion_token": completion_token, "total_token": total_token}
            ],
            "latency_s": execution_time,
        }

        # Determine required_form_value
        if response:
            required_form_value = "no"
        elif tool_call_name:
            required_form_value = "yes"
        else:
            required_form_value = "no"  # Default value

        human_id = self.snowflake_gen.generate_snowflake_id(time=start_time)
        ai_id = self.snowflake_gen.generate_snowflake_id(time=end_time)
        human_exists = self.check_id_exists(str(human_id))
        ai_exists = self.check_id_exists(str(ai_id))
        
        # Always save human message if it doesn't exist
        if not human_exists:
            user_item = {
                "id": human_id,
                "type": "HUMAN-MESSAGE",
                "required_form": required_form_value,
                "message": user_input,
                **fields,
            }
            self.table.put_item(Item=user_item)
            logger.info(f"Saved human message with ID: {human_id}")

        # Save AI message if it doesn't exist and we have response or tool call
        if not ai_exists:
            if response:
                ai_item = {
                    "id": ai_id,
                    "type": "AI-MESSAGE",
                    "required_form": required_form_value,
                    "message": response,
                    **fields,
                }
                self.table.put_item(Item=ai_item)
                logger.info(f"Saved AI response with ID: {ai_id}")

            elif tool_call_name:
                tool_item = {
                    "id": ai_id,
                    "type": "AI-MESSAGE",
                    "required_form": required_form_value,
                    "message": f"Tool called: {tool_call_name}",
                    **fields,
                }
                self.table.put_item(Item=tool_item)
                logger.info(f"Saved AI tool call with ID: {ai_id}")

        if human_exists and ai_exists:
            logger.info(f"Both human_id and ai_id already exist: {human_id}, {ai_id}")
            return {"conversation_id": conversation_id, "reply_to_message_id": reply_to_message_id}

        return {"conversation_id": conversation_id, "reply_to_message_id": reply_to_message_id}

    def get_conversation_history(self, conversation_id: str, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        if not conversation_id:
            raise ValueError("conversation_id is required.")
        if not user_id:
            raise ValueError("user_id is required.")

        try:
            response = self.table.query(
                IndexName="conversation_index",
                KeyConditionExpression=Key("conversation_id").eq(conversation_id),
                ScanIndexForward=False,
            )

            items = []
            for item in response.get("Items", []):
                # Ensure it's owned by the correct user and is a valid message type
                if item.get("user_id") != user_id:
                    continue
                if item.get("type") not in {"HUMAN-MESSAGE", "AI-MESSAGE"}:
                    continue
                try:
                    if item.get("id") is not None:
                        int(item["id"])  # Validate ID is numeric
                        items.append(item)
                except ValueError:
                    logger.debug(f"Skipping non-integer ID: {item.get('id')}")
                    continue

            if not items:
                logger.info(f"No messages found for conversation_id={conversation_id}, user_id={user_id}")
                return []

            # Group by reply_to_message_id
            grouped: Dict[str, List[Dict[str, Any]]] = {}
            for item in items:
                reply_id = item.get("reply_to_message_id")
                if reply_id:
                    grouped.setdefault(reply_id, []).append(item)

            # Sort groups by max message ID in group (chronological)
            sorted_groups = sorted(
                grouped.items(),
                key=lambda x: max([int(msg["id"]) for msg in x[1]]),
                reverse=False,
            )

            formatted = []
            pair_count = 0

            for reply_id, msgs in sorted_groups:
                types_present = {msg["type"] for msg in msgs}
                if "HUMAN-MESSAGE" in types_present and "AI-MESSAGE" in types_present:
                    msgs_sorted = sorted(msgs, key=lambda x: 0 if x["type"] == "HUMAN-MESSAGE" else 1)

                    for msg in msgs_sorted:
                        formatted.append({
                            "id": msg.get("id"),
                            "conversation_id": msg.get("conversation_id"),
                            "reply_to_message_id": msg.get("reply_to_message_id"),
                            "type": msg.get("type"),
                            "language": msg.get("language"),
                            "message": msg.get("message", ""),
                            "required_form": msg.get("required_form", ""),
                            "tools": [
                                {
                                    "name": tool.get("name", ""),
                                    "id": tool.get("id", ""),
                                    "type": tool.get("type", ""),
                                    "args": tool.get("args", {}),
                                }
                                for tool in msg.get("tools", [])
                            ],
                            "created_at": msg.get("created_at"),
                            "updated_at": msg.get("updated_at"),
                            "tokens": msg.get("tokens", []),
                            "latency_s": msg.get("latency_s"),
                        })

                    pair_count += 1
                    if pair_count >= limit:
                        break

            return formatted

        except Exception as e:
            logger.error(
                f"Error fetching conversation history from DynamoDB: {str(e)} | conversation_id={conversation_id}, user_id={user_id}"
            )
            raise

    def delete_conversation(self, conversation_id: str) -> int:
        deleted_count = 0
        last_evaluated_key = None

        while True:
            query_kwargs = {
                "IndexName": "conversation_index",
                "KeyConditionExpression": Key("conversation_id").eq(conversation_id),
            }
            if last_evaluated_key:
                query_kwargs["ExclusiveStartKey"] = last_evaluated_key

            response = self.table.query(**query_kwargs)
            items = response.get("Items", [])

            for item in items:
                self.table.delete_item(Key={"id": item["id"]})
                deleted_count += 1
                print(f"Deleted item with ID: {item['id']}")

            if "LastEvaluatedKey" in response:
                last_evaluated_key = response["LastEvaluatedKey"]
            else:
                break

        return deleted_count