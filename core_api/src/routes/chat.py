from fastapi import FastAPI, HTTPException
from langchain.chains.llm import LLMChain
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain_community.chat_models import ChatLiteLLM
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_elasticsearch import ElasticsearchStore, ApproxRetrievalStrategy
import logging

from redbox.llm.prompts.chat import (
    CONDENSE_QUESTION_PROMPT,
    STUFF_DOCUMENT_PROMPT,
    WITH_SOURCES_PROMPT,
)
from redbox.models import Settings, EmbeddingResponse, EmbeddingModelInfo, Embedding
from redbox.models.chat import ChatRequest, ChatResponse, ChatMessage

# === Logging ===

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

env = Settings()


chat_app = FastAPI(
    title="Core Chat API",
    description="Redbox Core Chat API",
    version="0.1.0",
    openapi_tags=[
        {"name": "chat", "description": "Chat interactions with LLM and RAG backend"},
        {"name": "embedding", "description": "Embedding interactions with SentenceTransformer"},
        {"name": "llm", "description": "LLM information and parameters"},
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

log.info("Loading embedding model from environment: %s", env.embedding_model)
embedding_model = SentenceTransformerEmbeddings(model_name=env.embedding_model, cache_folder="/app/models")
log.info("Loaded embedding model from environment: %s", env.embedding_model)


def populate_embedding_model_info() -> EmbeddingModelInfo:
    test_text = "This is a test sentence."
    embedding = embedding_model.embed_documents([test_text])[0]
    model_info = EmbeddingModelInfo(
        model=env.embedding_model,
        vector_size=len(embedding),
    )
    return model_info


embedding_model_info = populate_embedding_model_info()


# === LLM setup ===


llm = ChatLiteLLM(
    model="gpt-3.5-turbo",
    streaming=True,
)

es = env.elasticsearch_client()
if env.elastic.subscription_level == "basic":
    strategy = ApproxRetrievalStrategy(hybrid=False)
elif env.elastic.subscription_level in ["platinum", "enterprise"]:
    strategy = ApproxRetrievalStrategy(hybrid=True)
else:
    raise ValueError(f"Unknown Elastic subscription level {env.elastic.subscription_level}")

vector_store = ElasticsearchStore(
    es_connection=es,
    index_name="redbox-data-chunk",
    embedding=embedding_model,
    strategy=strategy,
    vector_query_field="embedding",
)


@chat_app.get("/embedding", tags=["embedding"])
def get_model() -> EmbeddingModelInfo:
    """Returns information about the embedding model

    Returns:
        EmbeddingModelInfo: Information about the embedding model
    """

    return embedding_model_info


@chat_app.post("/embedding", tags=["embedding"])
def embed_sentences(sentences: list[str]) -> EmbeddingResponse:
    """Embeds a list of sentences using a given model

    Args:
        sentences (list[str]): A list of sentences

    Returns:
        EmbeddingResponse: The embeddings of the sentences
    """

    embeddings = embedding_model.embed_documents(sentences)
    embeddings = [Embedding(object="embedding", index=i, embedding=embedding) for i, embedding in enumerate(embeddings)]

    response = EmbeddingResponse(
        object="list", data=embeddings, model=env.embedding_model, embedding_model_info=embedding_model_info
    )

    return response


@chat_app.post("/vanilla", tags=["chat"], response_model=ChatResponse)
def simple_chat(chat_request: ChatRequest) -> ChatResponse:
    """Get a LLM response to a question history"""

    if len(chat_request.message_history) < 2:
        raise HTTPException(
            status_code=422,
            detail="Chat history should include both system and user prompts",
        )

    if chat_request.message_history[0].role != "system":
        raise HTTPException(
            status_code=422,
            detail="The first entry in the chat history should be a system prompt",
        )

    if chat_request.message_history[-1].role != "user":
        raise HTTPException(
            status_code=422,
            detail="The final entry in the chat history should be a user question",
        )

    chat_prompt = ChatPromptTemplate.from_messages((msg.role, msg.text) for msg in chat_request.message_history)
    # Convert to LangChain style messages
    messages = chat_prompt.format_messages()

    response = llm(messages)

    return ChatResponse(response_message=ChatMessage(text=response.text, role="ai"))


@chat_app.post("/rag", tags=["chat"], response_model=ChatResponse)
def rag_chat(chat_request: ChatRequest) -> ChatResponse:
    """Get a LLM response to a question history and file

    Args:


    Returns:
        StreamingResponse: a stream of the chain response
    """
    question = chat_request.message_history[-1].text
    previous_history = [msg for msg in chat_request.message_history[:-1]]
    previous_history = ChatPromptTemplate.from_messages(
        (msg.role, msg.text) for msg in previous_history
    ).format_messages()

    docs_with_sources_chain = load_qa_with_sources_chain(
        llm,
        chain_type="stuff",
        prompt=WITH_SOURCES_PROMPT,
        document_prompt=STUFF_DOCUMENT_PROMPT,
        verbose=True,
    )

    condense_question_chain = LLMChain(llm=llm, prompt=CONDENSE_QUESTION_PROMPT)

    standalone_question = condense_question_chain({"question": question, "chat_history": previous_history})["text"]

    docs = vector_store.as_retriever().get_relevant_documents(standalone_question)

    result = docs_with_sources_chain(
        {
            "question": standalone_question,
            "input_documents": docs,
        },
    )

    return ChatResponse(response_message=ChatMessage(text=result["output_text"], role="ai"))
