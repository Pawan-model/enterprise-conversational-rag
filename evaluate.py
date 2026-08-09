import os
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

from ragas.llms import llm_factory
from ragas.embeddings import GoogleEmbeddings
from ragas.metrics.collections import Faithfulness, AnswerRelevancy

from app.db.session import sessionLocal
from app.db.vector_store import search_vectors
from app.db.bm25_store import search_bm25
from app.db.hybrid_retrieval import (
    reciprocal_rank_fusion,
    get_hybrid_result
)
from app.services.embedding import generate_embedding


# =========================================================
# ENVIRONMENT
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

API_KEY = os.environ["GEMINI_API_KEY"]


# =========================================================
# RAGAS EVALUATOR
# =========================================================

# Gemini's OpenAI-compatible API endpoint
evaluator_client = AsyncOpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Ragas evaluator LLM
evaluator_llm = llm_factory(
    "gemini-2.0-flash",
    provider="openai",
    client=evaluator_client
)

# Google embedding model used by Answer Relevancy
evaluator_embeddings = GoogleEmbeddings(
    model="gemini-embedding-001"
)

# Metrics
faithfulness_metric = Faithfulness(
    llm=evaluator_llm
)

answer_relevancy_metric = AnswerRelevancy(
    llm=evaluator_llm,
    embeddings=evaluator_embeddings
)


# =========================================================
# EVALUATION QUESTIONS
# =========================================================

evaluation_questions = [
    "What is the monthly stipend offered to a Future Founders Fellow?",

    "How long is the Future Founders Fellowship?",

    "Where will the Future Founders Fellowship take place?",

    "Which students are eligible to apply for the fellowship?",

    "Is there a minimum CGPA requirement for the fellowship?",

    "What kinds of roles do fellows primarily work in?",

    "What is the main responsibility of a Future Founders Fellow?",

    "Who will fellows work directly with during the fellowship?",

    "What is the selection process for the fellowship?",

    "What is Peak XV's Surge platform?"
]


# =========================================================
# RUN YOUR EXISTING RAG PIPELINE
# =========================================================

def generate_rag_response(query, db):

    # -----------------------------------------------------
    # 1. Generate query embedding
    # -----------------------------------------------------

    vector = generate_embedding(query)

    # -----------------------------------------------------
    # 2. Qdrant retrieval
    # -----------------------------------------------------

    qdrant_results = search_vectors(vector)

    # -----------------------------------------------------
    # 3. BM25 retrieval
    # -----------------------------------------------------

    bm25_results = search_bm25(
        query=query
    )

    # -----------------------------------------------------
    # 4. Reciprocal Rank Fusion
    # -----------------------------------------------------

    rrf_results = reciprocal_rank_fusion(
        qdrant_results=qdrant_results,
        bm25_results=bm25_results
    )

    # -----------------------------------------------------
    # 5. Get complete chunk information
    # -----------------------------------------------------

    hybrid_results = get_hybrid_result(
        rrf_results=rrf_results,
        db=db
    )

    # -----------------------------------------------------
    # 6. Build context
    # -----------------------------------------------------

    content_blocks = []

    for result in hybrid_results:

        content_blocks.append(
            f"""
Source: {result['filename']}
Page: {result['page_number']}

Content:
{result['content']}
"""
        )

    combined_context = "\n\n".join(content_blocks)

    # -----------------------------------------------------
    # 7. RAG prompt
    # -----------------------------------------------------

    prompt = f"""
You are an intelligent assistant answering questions
about uploaded PDF documents.

Use ONLY the provided context to answer the user's question.

If the answer cannot be found in the provided context,
say:

"I could not find the answer in the uploaded documents."

Do not make up information.

Context:
{combined_context}

Question:
{query}
"""

    # -----------------------------------------------------
    # 8. Use your existing Gemini application
    # -----------------------------------------------------

    # Import your existing Gemini client here.
    #
    # CHANGE THIS IMPORT if your client is located
    # somewhere else in your project.

    from app.api.routes.documents import gemini_client

    response = gemini_client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )

    answer = response.text

    # -----------------------------------------------------
    # 9. Return answer + retrieved contexts
    # -----------------------------------------------------

    contexts = [
        result["content"]
        for result in hybrid_results
    ]

    return answer, contexts


# =========================================================
# EVALUATION
# =========================================================

async def run_evaluation():

    db = sessionLocal()

    faithfulness_scores = []
    relevancy_scores = []

    try:

        for number, query in enumerate(
            evaluation_questions,
            start=1
        ):

            print("\n" + "=" * 70)

            print(
                f"Question {number}/"
                f"{len(evaluation_questions)}"
            )

            print(f"\nQuestion:\n{query}")

            # -------------------------------------------------
            # Run your actual RAG pipeline
            # -------------------------------------------------

            answer, contexts = generate_rag_response(
                query,
                db
            )

            print(f"\nGenerated Answer:\n{answer}")

            # -------------------------------------------------
            # Faithfulness
            # -------------------------------------------------

            faithfulness_result = await (
                faithfulness_metric.ascore(
                    user_input=query,
                    response=answer,
                    retrieved_contexts=contexts
                )
            )

            faithfulness_score = (
                faithfulness_result.value
            )

            # -------------------------------------------------
            # Answer Relevancy
            # -------------------------------------------------

            relevancy_result = await (
                answer_relevancy_metric.ascore(
                    user_input=query,
                    response=answer
                )
            )

            relevancy_score = (
                relevancy_result.value
            )

            # -------------------------------------------------
            # Store scores
            # -------------------------------------------------

            faithfulness_scores.append(
                float(faithfulness_score)
            )

            relevancy_scores.append(
                float(relevancy_score)
            )

            # -------------------------------------------------
            # Display scores
            # -------------------------------------------------

            print(
                f"\nFaithfulness: "
                f"{faithfulness_score:.4f}"
            )

            print(
                f"Answer Relevancy: "
                f"{relevancy_score:.4f}"
            )

    finally:

        db.close()

    # =====================================================
    # FINAL RESULTS
    # =====================================================

    average_faithfulness = (
        sum(faithfulness_scores)
        / len(faithfulness_scores)
    )

    average_relevancy = (
        sum(relevancy_scores)
        / len(relevancy_scores)
    )

    print("\n" + "=" * 70)
    print("                 FINAL RESULTS")
    print("=" * 70)

    print(
        f"\nAverage Faithfulness: "
        f"{average_faithfulness:.4f}"
    )

    print(
        f"Average Answer Relevancy: "
        f"{average_relevancy:.4f}"
    )

    print("=" * 70)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    asyncio.run(
        run_evaluation()
    )