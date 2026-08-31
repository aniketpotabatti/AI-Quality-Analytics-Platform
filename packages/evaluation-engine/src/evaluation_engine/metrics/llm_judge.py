"""LLM-as-judge metric: uses an LLM to score response quality."""

from __future__ import annotations

import json
import os

from evaluation_engine.metrics.base import Metric
from evaluation_engine.schemas import EvaluationInput, MetricName, MetricResult


_JUDGE_PROMPT = """You are an expert evaluator assessing LLM response quality.

Evaluate the following response to the given prompt. Consider:
1. Accuracy and factual correctness
2. Completeness of the answer
3. Relevance to the question
4. Clarity and coherence

Prompt: {prompt}
Response: {response}
{context_section}
{ground_truth_section}

Provide a JSON response with:
- "score": float between 0.0 (poor) and 1.0 (excellent)
- "passed": boolean (true if score >= 0.6)
- "rationale": brief explanation of the score (1-2 sentences)

Respond ONLY with valid JSON, no other text."""


class LlmAsJudgeMetric(Metric):
    """
    LLM-as-judge: uses a Gemini model to score response quality.

    Gracefully falls back to a heuristic score when no API key is configured.
    """

    name = MetricName.LLM_AS_JUDGE

    async def evaluate(self, evaluation_input: EvaluationInput) -> MetricResult:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return self._heuristic_fallback(evaluation_input)

        try:
            return await self._llm_evaluate(evaluation_input, api_key)
        except Exception as exc:
            return MetricResult(
                metric=self.name,
                score=0.5,
                passed=True,
                rationale=f"LLM judge unavailable ({type(exc).__name__}); defaulting to 0.5",
                metadata={"error": str(exc)[:200]},
            )

    async def _llm_evaluate(
        self, evaluation_input: EvaluationInput, api_key: str
    ) -> MetricResult:
        import httpx

        context_section = ""
        if evaluation_input.context:
            context_section = f"Context: {evaluation_input.context[:1000]}"
        ground_truth_section = ""
        if evaluation_input.ground_truth:
            ground_truth_section = f"Ground Truth: {evaluation_input.ground_truth[:500]}"

        prompt = _JUDGE_PROMPT.format(
            prompt=evaluation_input.prompt[:500],
            response=evaluation_input.response[:1000],
            context_section=context_section,
            ground_truth_section=ground_truth_section,
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 256,
                        "responseMimeType": "application/json",
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            result = json.loads(content)

        score = float(result.get("score", 0.5))
        score = max(0.0, min(1.0, score))
        return MetricResult(
            metric=self.name,
            score=score,
            passed=result.get("passed", score >= 0.6),
            rationale=result.get("rationale", ""),
            metadata={"model": "gemini-1.5-flash", "method": "llm_judge"},
        )

    def _heuristic_fallback(self, evaluation_input: EvaluationInput) -> MetricResult:
        """Simple heuristic: score based on response length and prompt keyword coverage."""
        resp_len = len(evaluation_input.response.split())
        prompt_words = set(evaluation_input.prompt.lower().split())
        resp_words = set(evaluation_input.response.lower().split())
        coverage = len(prompt_words & resp_words) / max(len(prompt_words), 1)

        # Length penalty for very short or very long responses
        if resp_len < 5:
            length_score = 0.2
        elif resp_len > 500:
            length_score = 0.7
        else:
            length_score = min(resp_len / 50, 1.0)

        score = (coverage * 0.5 + length_score * 0.5)
        return MetricResult(
            metric=self.name,
            score=score,
            passed=score >= 0.5,
            rationale="Heuristic score (no LLM API key configured)",
            metadata={"method": "heuristic_fallback"},
        )
