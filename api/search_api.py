from fastapi import APIRouter, Query
from services.search_service import SearchService

router = APIRouter()

# Mock data for search suggestions
mock_suggestions = [
    {"id": 1, "title": "react", "content": "A JavaScript library for building user interfaces"},
    {"id": 2, "title": "react native", "content": "A framework for building native apps with React"},
    {"id": 3, "title": "react router", "content": "Declarative routing for React"},
    {"id": 4, "title": "redux", "content": "A predictable state container for JavaScript apps"},
    {"id": 5, "title": "python", "content": "A programming language that lets you work quickly"},
    {"id": 6, "title": "pyramid", "content": "A small, fast, down-to-earth Python web framework"},
    {"id": 7, "title": "fastapi", "content": "A modern, fast (high-performance) web framework for building APIs"},
    {"id": 8, "title": "fastapi tutorial", "content": "A tutorial for the FastAPI web framework"},
]

@router.get("/search")
def search(q: str = Query(..., min_length=1)):
    """Return ranked search results."""
    search_service = SearchService()
    results = [s for s in mock_suggestions if q.lower() in s['title'].lower() or q.lower() in s['content'].lower()]
    ranked_results = search_service.rank_results(q, results)
    return {"results": ranked_results}

@router.get("/suggestions")
def get_suggestions(q: str = Query(..., min_length=1)):
    """Return search suggestions based on the query."""
    suggestions = [s['title'] for s in mock_suggestions if q.lower() in s['title'].lower()]
    return {"suggestions": suggestions}

@router.post("/analytics")
def track_search(query: str, num_results: int):
    """Track search queries and the number of results."""
    print(f"Search query: {query}, Num results: {num_results}")
    return {"status": "ok"}
