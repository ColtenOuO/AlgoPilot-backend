import asyncio
from app.core.celery_app import celery_app
from app.services.llm_service import llm_service

@celery_app.task(name="generate_text_task")
def generate_text_task(prompt: str, max_tokens: int, temperature: float):
    print(f"[Worker] Processing: {prompt[:10]}...")
    try:
        result = asyncio.run(llm_service.generate_text(
            prompt=prompt, 
            max_tokens=max_tokens, 
            temperature=temperature
        ))
        print(result)
        return result
    except Exception as e:
        return f"Error: {str(e)}"