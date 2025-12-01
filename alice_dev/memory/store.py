import weaviate
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from .schema import MemorySchema
import weaviate.classes.config as wc
from weaviate.classes.query import Filter, Sort, MetadataQuery
from config.settings import settings

class WeaviateStore:
    def __init__(self, url: str = None, openai_api_key: Optional[str] = None):
        headers = {}
        if openai_api_key:
            headers["X-OpenAI-Api-Key"] = openai_api_key
        
        # Use settings for connection details
        # Note: connect_to_custom is used for Docker networking usually
        print(f"Connecting to Weaviate at {settings.WEAVIATE_HOST}:{settings.WEAVIATE_PORT} (gRPC: {settings.WEAVIATE_GRPC_HOST}:{settings.WEAVIATE_GRPC_PORT})")
        self.client = weaviate.connect_to_custom(
            http_host=settings.WEAVIATE_HOST,
            http_port=settings.WEAVIATE_PORT,
            http_secure=False,
            grpc_host=settings.WEAVIATE_GRPC_HOST,
            grpc_port=settings.WEAVIATE_GRPC_PORT,
            grpc_secure=False,
            headers=headers
        )
        self._ensure_schema()

    def _ensure_schema(self):
        """
        Checks if the schema exists, if not, creates it.
        """
        # Check if collection exists
        if not self.client.collections.exists(MemorySchema.CLASS_NAME):
            self._create_collection()
        else:
            # Simple migration: Try to add new properties if they don't exist
            # Weaviate allows adding properties to existing classes
            collection = self.client.collections.get(MemorySchema.CLASS_NAME)
            
            # We define the new properties we want to ensure exist
            new_props = [
                wc.Property(name="tags", data_type=wc.DataType.TEXT_ARRAY),
                wc.Property(name="attributes", data_type=wc.DataType.TEXT),
            ]
            
            for prop in new_props:
                try:
                    collection.config.add_property(prop)
                    print(f"Added new property '{prop.name}' to {MemorySchema.CLASS_NAME}")
                except Exception as e:
                    # Ignore if property already exists or other minor errors
                    # print(f"Property '{prop.name}' might already exist: {e}")
                    pass

    def _create_collection(self):
        provider = settings.VECTORIZER_PROVIDER
        
        if provider == "openai":
            # Use OpenAI Proxy if configured
            vectorizer_config = wc.Configure.Vectorizer.text2vec_openai(
                model=settings.OPENAI_EMBEDDING_MODEL,
                base_url=settings.OPENAI_BASE_URL
            )
        else:
            # Default to ollama
            # Use OLLAMA_BASE_URL from settings, which might be localhost or host.docker.internal
            # Weaviate needs to reach Ollama. If Weaviate is in docker and Ollama on host, 
            # it needs host.docker.internal.
            # settings.OLLAMA_BASE_URL is configured for the APP to reach Ollama.
            # Weaviate might need the same URL if they are on same network/host setup.
            vectorizer_config = wc.Configure.Vectorizer.text2vec_ollama(
                api_endpoint=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_EMBEDDING_MODEL,
            )

        self.client.collections.create(
            name=MemorySchema.CLASS_NAME,
            vectorizer_config=vectorizer_config,
            properties=MemorySchema.get_properties()
        )

    def add_memory(self, content: str, user_id: str, memory_type: str = "episodic", importance: float = 0.5, tags: List[str] = None, attributes: str = None):
        """
        Adds a new memory item to Weaviate.
        """
        collection = self.client.collections.get(MemorySchema.CLASS_NAME)
        collection.data.insert({
            "content": content,
            "type": memory_type,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "importance": importance,
            "tags": tags or [],
            "attributes": attributes or "{}"
        })

    def get_social_state(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves the latest social state for the user.
        """
        collection = self.client.collections.get(MemorySchema.CLASS_NAME)
        response = collection.query.fetch_objects(
            filters=Filter.by_property("user_id").equal(user_id) & Filter.by_property("type").equal("social_state"),
            limit=1,
            sort=Sort.by_property("timestamp", ascending=False),
            return_properties=["attributes", "timestamp"]
        )
        
        if response.objects:
            import json
            try:
                return json.loads(response.objects[0].properties.get("attributes", "{}"))
            except:
                return {}
        
        # Default State
        return {
            "intimacy": 0,
            "trust": 0,
            "stage": "stranger",
            "summary": "We just met."
        }

    def update_social_state(self, user_id: str, state: Dict[str, Any]):
        """
        Updates (by adding a new record) the social state.
        """
        import json
        self.add_memory(
            content=f"Social State Update: {state.get('stage', 'unknown')}",
            user_id=user_id,
            memory_type="social_state",
            importance=1.0,
            attributes=json.dumps(state)
        )

    def add_cognitive_memory(self, content: str, user_id: str, tags: List[str] = None):
        """
        Adds a cognitive memory (fact/belief).
        """
        self.add_memory(
            content=content,
            user_id=user_id,
            memory_type="cognitive",
            importance=0.8,
            tags=tags
        )

    def search_memories(self, query: str, user_id: str, limit: int = 5, memory_type: str = None) -> List[Dict[str, Any]]:
        """
        Semantic search for memories related to the query.
        """
        collection = self.client.collections.get(MemorySchema.CLASS_NAME)
        
        filters = Filter.by_property("user_id").equal(user_id)
        if memory_type:
            filters = filters & Filter.by_property("type").equal(memory_type)

        if query and query.strip():
            response = collection.query.near_text(
                query=query,
                filters=filters,
                limit=limit,
                return_metadata=MetadataQuery(distance=True),
                return_properties=["content", "type", "timestamp", "importance", "tags", "attributes", "user_id"]
            )
        else:
            response = collection.query.fetch_objects(
                filters=filters,
                limit=limit,
                sort=Sort.by_property("timestamp", ascending=False),
                return_properties=["content", "type", "timestamp", "importance", "tags", "attributes", "user_id"]
            )
        
        results = []
        for obj in response.objects:
            props = obj.properties
            props["id"] = str(obj.uuid)
            if obj.metadata and hasattr(obj.metadata, 'distance'):
                props["distance"] = obj.metadata.distance
            
            # Ensure timestamp is a string for Pydantic compatibility
            if "timestamp" in props and isinstance(props["timestamp"], datetime):
                props["timestamp"] = props["timestamp"].isoformat()
                
            results.append(props)
        return results

    def get_all_memories(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve recent memories for a user.
        """
        collection = self.client.collections.get(MemorySchema.CLASS_NAME)
        response = collection.query.fetch_objects(
            filters=Filter.by_property("user_id").equal(user_id),
            limit=limit,
            sort=Sort.by_property("timestamp", ascending=False),
            return_properties=["content", "type", "timestamp", "importance"]
        )
        
        results = []
        for obj in response.objects:
            props = obj.properties
            props["id"] = str(obj.uuid)
            results.append(props)
        return results

    def delete_memory(self, memory_id: str):
        """
        Delete a memory by UUID.
        """
        collection = self.client.collections.get(MemorySchema.CLASS_NAME)
        collection.data.delete_by_id(memory_id)

    def update_memory(self, memory_id: str, properties: Dict[str, Any]):
        """
        Update a memory by UUID.
        """
        collection = self.client.collections.get(MemorySchema.CLASS_NAME)
        collection.data.update(uuid=memory_id, properties=properties)

    def close(self):
        self.client.close()
