"""
Create endpoint for dashboard

- Attach filled transcripts amount
- Attach total transcripts amount
- Attach uncategorized files
- Attach categorized files
- Attach categories amount
- Attach audio total length
- Attach categories grouped by amounts attached
- Add maximum and minimum audio length
"""

from fastapi import APIRouter

router = APIRouter(
    tags=["Dashboard"],
    prefix="/dashboard",
    responses={404: {"description": "Not found"}},
)
