"""Build compact, task-focused context for the planner."""

from __future__ import annotations

from core.rag.retriever import KnowledgeRetriever, RetrievedChunk


class ContextBuilder:
    """
    Assembles context for planning from multiple sources:
    - task description
    - repository file list
    - local RAG knowledge retrieval

    Keeps output compact and focused on the task at hand.
    """

    def __init__(self, retriever: KnowledgeRetriever | None = None) -> None:
        self.retriever = retriever

    def build(
        self,
        task_description: str,
        repo_files: list[str] | None = None,
    ) -> str:
        """
        Build a context string for the planner.

        Args:
            task_description: The user's task or goal.
            repo_files: Optional list of relevant repository file paths.

        Returns:
            A compact context string suitable for inclusion in a planning prompt.
        """
        parts: list[str] = [f"Task: {task_description.strip()}"]

        if repo_files:
            parts.append("Repository files:")
            for f in repo_files[:20]:  # cap to avoid flooding
                parts.append(f"  - {f}")

        rag_chunks = self._retrieve_knowledge(task_description)
        if rag_chunks:
            parts.append("Relevant knowledge:")
            for chunk in rag_chunks[:3]:  # cap to top-3 chunks
                preview = chunk.text[:300].replace("\n", " ")
                parts.append(
                    f"  - [{chunk.source_name}] {preview}..."
                )

        return "\n".join(parts)

    def _retrieve_knowledge(self, query: str) -> list[RetrievedChunk]:
        if self.retriever is None:
            return []
        try:
            return self.retriever.query(query, top_k=5)
        except Exception:
            # If Chroma is empty or misconfigured, continue without RAG context.
            return []
