from fastapi import APIRouter
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/notifications")
def get_notification_history():
    """Return the notification history."""
    now = datetime.utcnow()
    return {
        "notifications": [
            {
                "id": 1,
                "title": "Verification Completed",
                "message": "Your verification for Google has been completed.",
                "timestamp": (now - timedelta(minutes=5)).isoformat(),
                "read": True,
            },
            {
                "id": 2,
                "title": "New Message",
                "message": "You have a new message from John Doe.",
                "timestamp": (now - timedelta(hours=1)).isoformat(),
                "read": False,
            },
            {
                "id": 3,
                "title": "Billing Alert",
                "message": "Your subscription is about to expire.",
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "read": False,
            },
        ]
    }
