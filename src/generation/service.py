import time
from typing import Optional, List, Any
from src.config import get_config
from src.logging_config import logger
from src.retrieval.retriever import MedicalRetriever
from src.generation.provider import LLMProvider
from src.generation.factory import get_llm_provider
from src.generation.context import ContextBuilder
from src.generation.citation import CitationBuilder
from src.generation.prompts import GroundedPrompts
from src.generation.models import GenerationResponse, GenerationMetrics

class MedicalGenerationService:
    """
    Core business logic service orchestrating Grounded Medical Generation:
    Retriever -> Grounding Check -> Context Builder -> Prompt Builder -> LLM Provider -> Citation Builder -> GenerationResponse.
    """

    def __init__(
        self,
        retriever: Optional[MedicalRetriever] = None,
        llm_provider: Optional[LLMProvider] = None,
        max_context_chunks: Optional[int] = None,
    ):
        config = get_config()
        self.retriever = retriever or MedicalRetriever()
        self.llm_provider = llm_provider or get_llm_provider()
        self.context_builder = ContextBuilder(max_chunks=max_context_chunks or config.GENERATION_MAX_CONTEXT_CHUNKS)

    def answer_question(
        self,
        question: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
        language: Optional[str] = None,
    ) -> GenerationResponse:
        """
        Processes a user question end-to-end, generating a grounded answer and citations.
        """
        start_total = time.perf_counter()
        q_str = (question or "").strip()
        lang_str = (language or get_config().DEFAULT_LANGUAGE).strip()

        if not q_str:
            raise ValueError("Question string cannot be empty.")

        logger.info(f"Processing generation query: '{q_str}' (Language: {lang_str})")

        # Step 1: Retrieval Phase
        start_retrieval = time.perf_counter()
        retrieval_response = self.retriever.retrieve(query=q_str, top_k=top_k, min_score=min_score)
        retrieval_ms = round((time.perf_counter() - start_retrieval) * 1000, 2)

        match_quality = retrieval_response.match_quality
        results = retrieval_response.results

        # Programmatically construct citations from retrieval results
        citations = CitationBuilder.build_citations(results)

        # Step 2: Grounding Check for Weak / Out-of-Domain Queries
        if match_quality == "None" or not results:
            logger.warning(f"Weak/unsupported query detected (Match Quality: '{match_quality}'). Returning controlled fallback.")
            total_ms = round((time.perf_counter() - start_total) * 1000, 2)
            return GenerationResponse(
                question=q_str,
                answer="I could not find sufficiently relevant information in the medical knowledge base to answer this question.",
                match_quality=match_quality,
                citations=[],
                retrieval_results=results,
                metrics=GenerationMetrics(
                    retrieval_latency_ms=retrieval_ms,
                    generation_latency_ms=0.0,
                    total_latency_ms=total_ms,
                    chunks_used=0,
                    llm_provider=self.llm_provider.provider_name,
                    llm_model=self.llm_provider.model_name,
                )
            )

        # Step 3: Build Context & Grounded Prompts
        context_block = self.context_builder.build_context_block(results)
        user_prompt = GroundedPrompts.build_user_prompt(question=q_str, context_block=context_block, language=lang_str)

        messages = [
            {"role": "system", "content": GroundedPrompts.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        # Step 4: Execute LLM Generation
        start_gen = time.perf_counter()
        try:
            answer_text = self.llm_provider.generate(messages=messages)
        except Exception as e:
            logger.warning(f"LLM Provider '{self.llm_provider.provider_name}' generation failed/timed out ({e}). Generating grounded extraction from retrieved reference chunks.")
            answer_text = self._build_extracted_fallback_answer(results)
        gen_ms = round((time.perf_counter() - start_gen) * 1000, 2)

        total_ms = round((time.perf_counter() - start_total) * 1000, 2)

        logger.info(f"Answer generated successfully in {gen_ms} ms (Total: {total_ms} ms).")

        return GenerationResponse(
            question=q_str,
            answer=answer_text,
            match_quality=match_quality,
            citations=citations,
            retrieval_results=results,
            metrics=GenerationMetrics(
                retrieval_latency_ms=retrieval_ms,
                generation_latency_ms=gen_ms,
                total_latency_ms=total_ms,
                chunks_used=min(len(results), self.context_builder.max_chunks),
                llm_provider=self.llm_provider.provider_name,
                llm_model=self.llm_provider.model_name,
            )
        )

    def _build_extracted_fallback_answer(self, results: List[Any]) -> str:
        """
        Builds a structured medical summary directly from retrieved vectorstore chunks
        when external LLM APIs are unreachable or timing out.
        """
        if not results:
            return "I could not find sufficiently relevant information in the medical knowledge base to answer this question."

        top_chunk = results[0]
        title = getattr(top_chunk, "article_title", "Medical Reference")

        paragraphs = [f"### Medical Knowledge Reference: {title}\n"]

        for idx, res in enumerate(results[:3], 1):
            snippet = getattr(res, "text", "").strip()
            page = getattr(res, "page", "N/A")
            section = getattr(res, "section", "")
            sec_text = f" — *{section}*" if section else ""

            if len(snippet) > 350:
                snippet = snippet[:350].rsplit(' ', 1)[0] + "..."

            paragraphs.append(f"**{idx}. Excerpt from {res.article_title}{sec_text} (Page {page})**:\n{snippet}\n")

        paragraphs.append("*Note: Grounded information extracted directly from verified Gale Encyclopedia of Medicine reference text.*")
        return "\n".join(paragraphs)

