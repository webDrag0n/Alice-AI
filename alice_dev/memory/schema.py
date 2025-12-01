import weaviate.classes.config as wc
from typing import List

class MemorySchema:
    """
    Defines the schema for the 'MemoryItem' class in Weaviate.
    """
    CLASS_NAME = "MemoryItem"

    @staticmethod
    def get_properties() -> List[wc.Property]:
        return [
            wc.Property(name="content", data_type=wc.DataType.TEXT),
            wc.Property(name="type", data_type=wc.DataType.TEXT), # episodic, cognitive, social_state
            wc.Property(name="user_id", data_type=wc.DataType.TEXT),
            wc.Property(name="timestamp", data_type=wc.DataType.DATE),
            wc.Property(name="importance", data_type=wc.DataType.NUMBER),
            wc.Property(name="tags", data_type=wc.DataType.TEXT_ARRAY),
            wc.Property(name="attributes", data_type=wc.DataType.TEXT), # JSON string for structured data
        ]
