# helpers/mongodbhelpers.py
from flask_pymongo import PyMongo

class MongoHelper:
    def __init__(self, mongo: PyMongo):
        self.mongo = mongo

    def get_chat_history(self, collection_name: str, number_of_messages: int, chat_hash: str):
        collection = self.mongo.db[collection_name]
        doc = collection.find_one({"_id": chat_hash})

        if not doc:
            return None

        chat_history = doc.get("chat_history", [])

        if number_of_messages <= 0:
            return []

        return chat_history[-number_of_messages:]

    def get_chat_history_as_string(self, collection_name: str, number_of_messages: int, chat_hash: str):
        """
        Returns the chat history as a formatted text block.
        Uses get_chat_history() to fetch messages.
        """

        messages = self.get_chat_history(collection_name, number_of_messages, chat_hash)

        if messages is None:
            return None

        EXCLUDED_FIELDS = {
            "message_count",
            "chat_creation_date",
            "chat_last_use",
            "message_dt"
        }

        output_lines = []

        for msg in messages:
            # Put message number first for clarity
            message_number = msg.get("message_number", "N/A")
            output_lines.append(f"message_number: {message_number}")

            # Format all remaining fields
            for key, value in msg.items():
                if key == "message_number" or key in EXCLUDED_FIELDS:
                    continue

                # Convert {"$date": "..."} into readable string
                if isinstance(value, dict) and "$date" in value:
                    value = value["$date"]

                output_lines.append(f"{key}: {value}")

            output_lines.append("\n---\n")

        return "\n".join(output_lines)
