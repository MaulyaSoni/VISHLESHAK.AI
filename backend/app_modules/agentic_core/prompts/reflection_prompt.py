"""Reflection prompts for self-correction"""

REFLECTION_PROMPT = """Review the following answer for quality and accuracy:

QUESTION: {question}

ANSWER: {answer}

CONTEXT: {context}

Evaluate on these criteria:
1. **Accuracy**: Are facts and numbers correct?
2. **Completeness**: Does it fully answer the question?
3. **Clarity**: Is it easy to understand?
4. **Relevance**: Does it stay on topic?
5. **Evidence**: Is it backed by data?

Provide:
1. Confidence score (0-100)
2. Issues found (if any)
3. Suggested improvements

Format:
Confidence: [0-100]
Issues: [list any problems]
Suggestions: [list improvements]
Verdict: [ACCEPT/REVISE/REJECT]
"""

CONFIDENCE_INTERPRETATION = {
    (90, 100): "High confidence - answer is comprehensive and accurate",
    (70, 89):  "Good confidence - answer is solid with minor gaps",
    (50, 69):  "Medium confidence - answer needs improvement",
    (0, 49):   "Low confidence - answer should be rejected",
}
