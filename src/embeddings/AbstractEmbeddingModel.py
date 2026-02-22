from abc import ABC, abstractmethod
from typing import List
from chonkie import BaseChunker, Document
from dotenv import load_dotenv
from chonkie import Pipeline, MarkdownChef
from chonkie import EmbeddingsRefinery
from chonkie.embeddings import OpenAIEmbeddings, GeminiEmbeddings
import logging
from utils.FileProcessor import file_to_text_factory

logger = logging.getLogger(__name__)
OPEN_AI_EMBEDDING_MODELS = ["text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002" ]
class AbstractEmbeddingModel(ABC):
    """
    An abstract base class for creating and running text processing and embedding pipelines.

    This class provides a common structure for models that need to process text from
    various sources (files, directories, or raw text), chunk it, and potentially
    generate embeddings. It uses the 'chonkie' library for its pipeline capabilities.
    Subclasses must implement the 'initialize_client' and 'configure_chunker_for_pipeline'
    methods to provide specific configurations.
    """
    def __init__(self, directory_name : str | None , file_name : str | None, text_to_chunk : str | None, model_name="text-embedding-3-small"):
        """
        Initializes the AbstractEmbeddingModel.

        Args:
            directory_name: The path to a directory of files to be processed. (Currently not supported)
            file_name: The path to a single file to be processed.
            text_to_chunk: A string of text to be processed directly.
            model_name: The name of the embedding model to be used.
        """
        load_dotenv()
        self.pipeline = Pipeline()
        self.file_name = file_name
        self.text_to_chunk = text_to_chunk
        self.directory_name = directory_name  #not supported right now
        self.model_name = model_name


    @abstractmethod
    def initialize_client(self):
        """
        Abstract method for initializing any necessary API clients (e.g., OpenAI).
        """
        pass

    @abstractmethod
    def configure_chunker_for_pipeline(self, pipeline : Pipeline):
        """
        Abstract method for configuring the chunking strategy for the pipeline.
        Subclasses must implement this to define how text is split into chunks.
        """
        pass
    def get_embeddings(self) -> List[float]:
        """
        Runs the pipeline and is intended to return embeddings for the processed documents.
        NOTE: Currently returns an empty list.
        """
        
        documents = self.run_pipeline()
        logger.info(f"Generated {len(documents)} documents for embedding.")
        for document in documents:      
            for chunk in document.chunks:
                logger.debug(f"Processing chunk: {chunk.text[:50]}")
                if(chunk.embedding is not None):
                    logger.debug(f"Processing chunk: {chunk.embedding[:5]}")

        return []

    def get_model(self) -> BaseChunker | None:
        """
        Returns the chunker model instance.
        NOTE: Currently returns None.
        """
        return None

    def is_chonkie(self) -> bool:
        """Returns True, indicating that this model uses the chonkie library."""
        return True
    def add_embeddings_refinery(self):
        """Adds an embedding refinery step to the pipeline."""
        self.pipeline.refine_with("embeddings", embedding_model=self.model_name)

    def run_pipeline(self) -> List[Document]:
        """
        Executes the text processing pipeline based on the provided input.

        The method prioritizes input in the following order:
        1. A single file (`file_name`): The file is processed into text using a factory.
        2. A raw text string (`text_to_chunk`).

        Directory processing is currently disabled. After processing the input into
        text, it configures the chunker and runs the chonkie pipeline.

        Returns:
            A list of Document objects, where each object represents a chunk of text.

        Raises:
            ValueError: If no input (file, directory, or text) is provided.
            NotImplementedError: If the file type is not supported by the factory.
        """
        isText = self.text_to_chunk is not None
        
        if self.file_name is not None:
            try:
                self.text_to_chunk = file_to_text_factory(self.file_name)
                isText = True
            except (NotImplementedError, Exception) as e:
                logger.error(f"Failed to process file {self.file_name}: {e}")
                raise
        
        # Directory processing is currently disabled.
        if self.directory_name is not None and not isText:
            if not self.directory_name.startswith("/app"):
                self.directory_name = "/app/" + self.directory_name
            self.pipeline.fetch_from("file", dir=self.directory_name)

        elif not isText: # Neither file, dir, nor initial text was provided
            logger.error("No input provided for chunking. Please provide a directory, file, or text.")
            raise ValueError("Input is missing")

        self.pipeline.process_with(chef_type=MarkdownChef.__name__)
        self.configure_chunker_for_pipeline(self.pipeline)
        self.add_embeddings_refinery()

        if isText:
            result = self.pipeline.run(self.text_to_chunk)
        else:
            result = self.pipeline.run()

        if isinstance(result, list):
            return result
        else:
            return [result]

    # def build_pipeline(self):
    #     if(self.is_chonkie):
    #         pipeline.chunker()

