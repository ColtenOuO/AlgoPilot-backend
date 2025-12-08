# app/api/v1/endpoints/submission.py
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from app.services.submitter import get_submitter
from app.services.crawler import leetcode_crawler

router = APIRouter()

class SubmissionRequest(BaseModel):
    slug: str               # e.g., "two-sum"
    lang: str               # e.g., "python3"
    code: str               # user's code
    leetcode_session: str   # user's Cookie
    csrf_token: str         # user's CSRF Token

@router.post("/submit")
async def submit_solution(data: SubmissionRequest):
    """
    提交程式碼到 LeetCode
    """

    problem_info = await leetcode_crawler.get_problem_detail(data.slug)
    if "error" in problem_info:
        raise HTTPException(status_code=404, detail="Problem not found")
        
    real_question_id = problem_info["id"]

    submitter = get_submitter(data.leetcode_session, data.csrf_token)

    try:
        submit_resp = await submitter.submit_code(
            slug=data.slug,
            question_id=real_question_id,
            lang=data.lang,
            code=data.code
        )
        submission_id = submit_resp.get("submission_id")
        
        if not submission_id:
            raise HTTPException(status_code=400, detail="Submission failed")
            
        # TODO: rabbitmq to manager buffer queue 
        result = await submitter.check_submission_result(submission_id)
        
        return {
            "submission_id": submission_id,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

class TestAuthRequest(BaseModel):
    leetcode_session: str
    csrf_token: str

HARDCODED_TWO_SUM_CPP = """
class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        for (int i = 0; i < nums.size(); ++i) {
            for (int j = i + 1; j < nums.size(); ++j) {
                if (nums[i] + nums[j] == target) {
                    return {i, j};
                }
            }
        }
        return {};
    }
};
"""

@router.post("/test-health")
async def test_submission_health(auth: TestAuthRequest):
    """
    [Testing] Auto submit Two Sum C++
    """
    target_slug = "two-sum"
    target_lang = "cpp"
    
    print(f"Starting Health Check on {target_slug}...")

    try:
        print("   1. Fetching Question ID...")
        problem_info = await leetcode_crawler.get_problem_detail(target_slug)
        if "error" in problem_info:
            raise HTTPException(status_code=500, detail=f"Crawler failed: {problem_info}")
        
        real_question_id = problem_info["id"]
        print(f"      -> Got ID: {real_question_id}")

        submitter = get_submitter(auth.leetcode_session, auth.csrf_token)

        print("   2. Submitting Code...")
        submit_resp = await submitter.submit_code(
            slug=target_slug,
            question_id=real_question_id,
            lang=target_lang,
            code=HARDCODED_TWO_SUM_CPP
        )
        
        submission_id = submit_resp.get("submission_id")
        if not submission_id:
            raise HTTPException(status_code=400, detail=f"Submission failed: {submit_resp}")
        print(f"      -> Submission ID: {submission_id}")

        print("   3. Polling Result...")
        result = await submitter.check_submission_result(submission_id)
        
        status_msg = result.get("status_msg", "Unknown")
        print(f"      -> Final Status: {status_msg}")
        
        return {
            "health": "Healthy" if status_msg == "Accepted" else "Unhealthy",
            "submission_id": submission_id,
            "leetcode_status": status_msg,
            "runtime": result.get("status_runtime"),
            "memory": result.get("status_memory"),
            "full_response": result
        }

    except Exception as e:
        print(f"Health Check Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))