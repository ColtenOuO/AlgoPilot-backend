# app/services/submitter.py
import httpx
import asyncio
import json
from typing import Dict, Any

class LeetCodeSubmitter:
    def __init__(self, leetcode_session: str, csrf_token: str):
        self.cookies = {
            "LEETCODE_SESSION": leetcode_session,
            "csrftoken": csrf_token
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Referer": "https://leetcode.com/",
            "X-CSRFToken": csrf_token,
            "Content-Type": "application/json"
        }

    async def submit_code(self, slug: str, question_id: str, lang: str, code: str) -> Dict[str, Any]:
        url = f"https://leetcode.com/problems/{slug}/submit/"
        payload = {
            "lang": lang,
            "question_id": question_id,
            "typed_code": code
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                json=payload, 
                cookies=self.cookies, 
                headers=self.headers
            )
            response.raise_for_status()

            return response.json()
    
    async def check_submission_result(self, submission_id: int) -> Dict[str, Any]:
        url = f"https://leetcode.com/submissions/detail/{submission_id}/check/"
        
        async with httpx.AsyncClient() as client:
            for _ in range(10): # try 10 times (per 1 second)
                response = await client.get(
                    url, 
                    cookies=self.cookies, 
                    headers=self.headers
                )
                result = response.json()
                
                if result.get("state") == "SUCCESS":
                    return result
                
                await asyncio.sleep(1)
                
            return {"error": "Timeout waiting for judge result"}

def get_submitter(session: str, csrf: str):
    return LeetCodeSubmitter(session, csrf)