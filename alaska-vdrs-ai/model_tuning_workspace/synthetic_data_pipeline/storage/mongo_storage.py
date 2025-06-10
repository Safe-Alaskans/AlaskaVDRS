import certifi
from pymongo import MongoClient
import datetime
from typing import Any, Dict, Optional, List


class MongoDBHandler:
    def __init__(
            self,
            connection_string: str,
            database_name: str,
    ):
        if not connection_string:
            raise ValueError("Connection string is required")
        if not database_name:
            raise ValueError("Database name is required")
        self.client = MongoClient(connection_string, tlsCAFile=certifi.where())
        self.db = self.client[database_name]

    def get_collection(self, collection_name: str):
        """Get or create a collection."""
        return self.db[collection_name]

    def insert_document(self, collection_name: str, data: Dict[str, Any]) -> str:
        collection = self.get_collection(collection_name)
        data['created_at'] = datetime.datetime.now(datetime.UTC)
        result = collection.insert_one(data)
        return str(result.inserted_id)

    def insert_bulk_documents(self, collection_name: str, data: List[Dict[str, Any]]) -> List[str]:
        collection = self.get_collection(collection_name)
        for doc in data:
            doc['created_at'] = datetime.datetime.now(datetime.UTC)
        result = collection.insert_many(data)
        return [str(oid) for oid in result.inserted_ids]

    def find_documents(self, collection_name: str, query: Optional[Dict] = None):
        collection = self.get_collection(collection_name)
        return collection.find(query or {})

    def get_all_documents(self, collection_name: str) -> List[Dict[str, Any]]:
        collection = self.get_collection(collection_name)
        return list(collection.find())

    def count_documents(self, collection_name: str, query: Optional[Dict] = None) -> int:
        """Count documents in a collection that match the query."""
        collection = self.get_collection(collection_name)
        return collection.count_documents(query or {})

    def update_document(
            self,
            collection_name: str,
            document_id: str,
            update_data: Dict[str, Any]
    ) -> int:
        collection = self.get_collection(collection_name)
        result = collection.update_one(
            {'_id': document_id},
            {'$set': update_data}
        )
        return result.modified_count

    def update_document_by_query(self, collection_name: str, query: dict, update: dict) -> None:
        collection = self.db[collection_name]
        collection.update_one(query, update)

    def delete_document(self, collection_name: str, document_id: str) -> int:
        collection = self.get_collection(collection_name)
        result = collection.delete_one({'_id': document_id})
        return result.deleted_count

    def close_connection(self):
        """Close the MongoDB connection."""
        self.client.close()
