import os
import asyncio
from dotenv import load_dotenv
from uuid import uuid4

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import (
    QdrantVectorStore,
    FastEmbedSparse,
    RetrievalMode,
)
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    SparseIndexParams,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.services.logger import logger

load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Should be HTTP URL to Qdrant server
QDRANT_DB_URL = os.getenv("qdrant_db_path", "http://localhost:6333")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "rag_demo_collection")
QDRANT_DB_KEY = os.getenv("QDRANT_DB_KEY", None)
class DocumentIndexer:
    def __init__(self, qdrant_url: str = QDRANT_DB_URL, qdrant_api_key:str = QDRANT_DB_KEY):
        # Embedding functions
        self.dense_embedding = OpenAIEmbeddings(model="text-embedding-3-large", api_key=OPENAI_API_KEY)
        self.sparse_embedding = FastEmbedSparse(model_name="Qdrant/bm25")

        # Connect in server mode (no file locks)
        # self.client = AsyncQdrantClient(url=qdrant_url)
        self.sync_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        self.vectors = {}

        # Ensure the collection exists
        self._ensure_collection()


    def _ensure_collection(self):
        existing = self.sync_client.get_collections().collections
        if COLLECTION_NAME not in [c.name for c in existing]:
            logger.info(f"Creating collection '{COLLECTION_NAME}' in Qdrant")
            self.sync_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config={
                    "dense": VectorParams(size=3072, distance=Distance.COSINE)
                },
                sparse_vectors_config={
                    "sparse": SparseVectorParams(index=SparseIndexParams(on_disk=False))
                },
            )

            # 🔧 Create payload indexes for metadata fields
            for field in ["metadata.username", "metadata.file_name", "metadata.doc_type"]:
                logger.info(f"Creating payload index on '{field}'")
                self.sync_client.create_payload_index(
                    collection_name=COLLECTION_NAME,
                    field_name=field,
                    field_schema=PayloadSchemaType.KEYWORD
                )
        else:
            logger.info(f"Collection '{COLLECTION_NAME}' already exists")

    def _get_vector_store(self, mode: str = "dense"):
        # Cache one QdrantVectorStore per mode
        if mode not in self.vectors:
            kwargs = {
                "client": self.sync_client,
                "collection_name": COLLECTION_NAME,
                "embedding": self.dense_embedding,
                "vector_name": "dense",
                "retrieval_mode": RetrievalMode[mode.upper()],
            }
            if mode in ("sparse", "hybrid"):
                kwargs["sparse_embedding"] = self.sparse_embedding
                kwargs["sparse_vector_name"] = "sparse"
            self.vectors[mode] = QdrantVectorStore(**kwargs)
        return self.vectors[mode]

    async def index_in_qdrantdb(
        self,
        extracted_text: str,
        file_name: str,
        doc_type: str,
        chunk_size: int = None,
        username: str = None,
    ) -> bool:
        """
        Index extracted text using dense + sparse embeddings.
        """
        try:
            doc = Document(
                page_content=extracted_text,
                metadata={"file_name": file_name, "doc_type": doc_type, "username": username},
            )

            # Dynamic chunk sizing
            length = len(extracted_text)
            if not chunk_size:
                if length < 10000:
                    chunk_size = int(os.getenv("CHUNK_SIZE", 1000))
                elif length < 50000:
                    chunk_size = 1500
                else:
                    chunk_size = 2000
                logger.info(f"Using chunk size: {chunk_size}")

            splitter = RecursiveCharacterTextSplitter(
                separators=["\n\n", "\n", ","],
                chunk_size=chunk_size,
                chunk_overlap=200,
            )
            docs = splitter.split_documents([doc])
            ids = [str(uuid4()) for _ in docs]

            store = self._get_vector_store(mode="hybrid")
            await store.aadd_documents(documents=docs, ids=ids)

            logger.info("Successfully indexed documents in QdrantDB")
            return True
        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            raise

    async def get_retriever(
        self,
        top_k: int,
        mode: str = "dense",
        score_threshold: float = None,
        metadata_filter: Filter = None,
    ):
        """
        Retrieve with 'dense', 'sparse', or 'hybrid' mode.
        """
        try:
            store = self._get_vector_store(mode=mode)
            search_kwargs = {"k": top_k}
            if score_threshold is not None:
                search_kwargs["score_threshold"] = score_threshold
            if metadata_filter is not None:
                search_kwargs["filter"] = metadata_filter

            return store.as_retriever(
                search_type="similarity",
                search_kwargs=search_kwargs,
            )
        except Exception as e:
            logger.error(f"Error creating retriever: {e}")
            raise

    async def get_retriever_for_user(
        self,
        username: str,
        top_k: int,
        mode: str = "dense",
        score_threshold: float = None,
    ):
        """
        Retrieve only documents matching the given username.
        """
        filter_ = Filter(
            must=[
                FieldCondition(key="metadata.username", match=MatchValue(value=username))
            ]
        )
        return await self.get_retriever(
            top_k=top_k,
            mode=mode,
            score_threshold=score_threshold,
            metadata_filter=filter_,
        )
