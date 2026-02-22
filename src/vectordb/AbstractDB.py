from abc import ABC, abstractmethod
from typing import List, Any
from src.vo.Metadata import Metadata

class AbstractDB(ABC):
    """
    An abstract base class for vector database implementations.
    """

    @abstractmethod
    def add(self, texts: List[str], metadatas: List[Metadata] | None = None) -> List[str]:
        """
        Adds texts to the vector database.

        Args:
            texts: A list of texts to add.
            metadatas: An optional list of Pydantic Metadata models corresponding to the texts.

        Returns:
            A list of IDs for the added texts.
        """
        pass

    @abstractmethod
    def search(self, query_texts: List[str], n_results: int = 5) -> List[Any]:
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
