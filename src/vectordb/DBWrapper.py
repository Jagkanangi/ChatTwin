# DESIGN RATIONALE:
# The AbstractDBWrapper and its concrete implementations (e.g., ChromaDBWrapper) follow the
# Data Access Object (DAO) pattern. The primary goal is to abstract the underlying vector
# database technology from the rest of the application.

# Key principles of this design:
# 1. No Leaky Abstractions: The user of a DBWrapper instance does not need to know anything
#    about the specific database's client or connection details. The `connect` method has been
#    deliberately removed from the public interface to enforce this.
# 2. Internal Connection Management: Each wrapper implementation is responsible for managing
#    its own database connection. This is done lazily (on first use) to be efficient.
# 3. Swappable Implementations: To change the vector database (e.g., move from ChromaDB to
#    Pinecone), one only needs to create a new concrete class that inherits from
#    AbstractDBWrapper. No application code needs to change.

import uuid
import threading
import chromadb
from chromadb.api import ClientAPI
from chromadb.api.types import QueryResult
from src.vo.Metadata import Metadata
from src.vo.Models import SearchResult
from typing import List, Any
from abc import ABC, abstractmethod

from src.utils.DBUtils import DBConfig, get_config


class AbstractDBWrapper(ABC):
    """
    An abstract base class for a vector database wrapper.

    An instance of a concrete implementation of this class represents a direct, usable
    interface to a specific collection in the vector database.
    """

    @abstractmethod
    def add(self, texts: List[str], metadatas: List[Metadata] | None = None) -> List[str]:
        """
        Adds texts to the vector database.
        Args:
            texts: A list of texts to add.
            metadatas: An optional list of metadata dictionaries corresponding to the texts.
        Returns:
            A list of unique IDs generated for the added texts.
        """
        pass

    @abstractmethod
    def search(self, query_texts: List[str], n_results: int = 5) -> List[SearchResult]:
        """
        Searches the vector database for similar texts.
        Args:
            query_texts: A list of texts to search for.
            n_results: The number of results to return.
        Returns:
            A list of search results.
        """
        pass

    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """
        Deletes texts from the vector database by their IDs.
        Args:
            ids: A list of IDs of the texts to delete.
        """
        pass


class ChromaDBWrapper(AbstractDBWrapper):
    """
    A concrete implementation of the DBWrapper for ChromaDB.
    """
    _client: ClientAPI | None = None
    _client_lock = threading.Lock()

    def __init__(self, collection_name: str = "chattwin_collection"):
        """
        Initializes the wrapper with configuration for the ChromaDB connection.
        Note: It does not connect immediately. Connection is handled lazily.
        """
        self._host = get_config(DBConfig.KEY_DB_HOST)
        self._port = get_config(DBConfig.KEY_DB_PORT)
        self._collection_name = collection_name
        self._collection: chromadb.Collection | None = None

    @property
    def collection(self) -> chromadb.Collection:
        """
        A lazy-loading property to get the ChromaDB collection.

        On first access, it establishes a connection to the ChromaDB server and
        retrieves the specified collection, caching it for subsequent use.
        The HttpClient connection is shared across all instances of ChromaDBWrapper
        to ensure only one connection is made.
        """
        if self._collection is None:
            with ChromaDBWrapper._client_lock:
                if ChromaDBWrapper._client is None:
                    ChromaDBWrapper._client = chromadb.HttpClient(host=self._host, port=self._port)
            self._collection = ChromaDBWrapper._client.get_or_create_collection(self._collection_name)
        return self._collection

    def add(self, texts: List[str], metadatas: List[Metadata] | None = None) -> List[str]:
        # ChromaDB requires unique IDs for each document. We generate them here.
        ids = [str(uuid.uuid4()) for _ in texts]
        
        # Convert Pydantic Metadata models to dictionaries for ChromaDB
        chroma_metadatas = [m.model_dump() for m in metadatas] if metadatas else None

        self.collection.add(
            documents=texts,
            metadatas=chroma_metadatas,
            ids=ids
        )
        return ids

    def search(self, query_texts: List[str], n_results: int = 5) -> List[SearchResult]:
        results: QueryResult = self.collection.query(
            query_texts=query_texts,
            n_results=n_results
        )

        # The result from Chroma is a dictionary of lists of lists.
        # We want to transform it into a more usable, flat list of result objects.
        # Each object will contain the document, its metadata, and distance.
        if not results or not results['documents']:
            return []

        # results['documents'] is a List[List[str]]
        # Let's create one flat list of results across all query_texts
        search_results: List[SearchResult] = []
        
        # The outer list corresponds to each query_text
        for i in range(len(results["documents"])):
            docs = results["documents"][i]
            metadatas = results["metadatas"][i] if results["metadatas"] else [None] * len(docs)
            distances = results["distances"][i] if results["distances"] else [None] * len(docs)
            ids = results["ids"][i]
            
            for j in range(len(docs)):
                meta_dict = metadatas[j]
                search_results.append(SearchResult(
                    id=ids[j],
                    document=docs[j],
                    metadata=Metadata.model_validate(meta_dict) if meta_dict else None,
                    distance=distances[j]
                ))
                
        return search_results

    def delete(self, ids: List[str]) -> None:
        self.collection.delete(ids=ids)


def get_db_wrapper(collection_name: str) -> AbstractDBWrapper:
    """
    Factory function to get an instance of a DB wrapper based on the configuration.

    Args:
        collection_name: The name of the collection to interact with.

    Returns:
        An instance of a class that implements the AbstractDBWrapper interface.
    """
    db_type = get_config(DBConfig.KEY_DB_TYPE)

    if db_type == 'chroma':
        return ChromaDBWrapper(collection_name=collection_name)
    # Add other database types here in the future, e.g.:
    # elif db_type == 'pinecone':
    #     return PineconeDBWrapper(collection_name=collection_name)
    else:
        raise ValueError(f"Unsupported DB_TYPE: {db_type}")
