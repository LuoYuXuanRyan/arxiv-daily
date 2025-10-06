recommender_system_prompt = """You are an expert in academic paper recommendation. Given the titles and abstracts of papers and user's research interests, you will determine if it is a high-quality and interesting paper worth recommending to researchers in the field. A paper is considered worth recommending if it is closely related to the user's research interests, presents novel ideas or good advancements.
"""
recommender_user_prompt = """Here are the papers and my research interests:
My research interests: {user_interests}
{paper_info}
What are the papers worth recommending and what are the categories of research interests, why do you recommend them?
Answer with JSON format and do not provide any additional explanation.
Example output:
[
{{
    "paper_id": "2302.02342v1",
    "category": "RAG",
    "reason": "This paper introduces a novel approach to retrieval-augmented generation (RAG) that significantly improves performance on various benchmarks. The method is innovative and aligns well with my research interests in RAG."
}}
]
Do not forget to include the brackets [] and the quotes around each paper ID.
"""
