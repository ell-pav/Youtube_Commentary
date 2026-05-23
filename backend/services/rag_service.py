from llama_index.core import (
    VectorStoreIndex,
    Document
)

from llama_index.embeddings.huggingface import (
    HuggingFaceEmbedding
)

from llama_index.vector_stores.faiss import (
    FaissVectorStore
)

from llama_index.core.storage.storage_context import (
    StorageContext
)

import faiss


embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


def build_rag_index(text: str):

    chunk_size = 300

    chunks = [

        text[i:i + chunk_size]

        for i in range(
            0,
            len(text),
            chunk_size
        )
    ]

    documents = [

        Document(text=chunk)

        for chunk in chunks
    ]

    dimension = 384

    faiss_index = faiss.IndexFlatL2(
        dimension
    )

    vector_store = FaissVectorStore(
        faiss_index=faiss_index
    )

    storage_context = StorageContext.from_defaults(
        vector_store=vector_store
    )

    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=embed_model
    )

    return index

def retrieve_relevant_context(
    index,
    query: str
):

    retriever = index.as_retriever(
        similarity_top_k=2
    )

    nodes = retriever.retrieve(
        query
    )

    context = "\n".join([

        node.text

        for node in nodes
    ])

    return context