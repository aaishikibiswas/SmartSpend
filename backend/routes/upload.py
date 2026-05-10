import asyncio
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.services.pipeline import process_uploaded_transactions
from backend.services.parser import parse_csv, parse_image, parse_pdf
from backend.storage import Storage

router = APIRouter()


@router.post("/")
async def upload_statement(file: UploadFile = File(...)):
    contents = await file.read()
    filename = (file.filename or "").lower()

    try:
        if filename.endswith(".pdf"):
            transactions = parse_pdf(contents)
        elif filename.endswith(".csv"):
            transactions = parse_csv(contents)
        elif filename.endswith(".png") or filename.endswith(".jpg") or filename.endswith(".jpeg"):
            transactions = parse_image(contents)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type.")

        Storage.add_uploaded_statement(
            {
                "filename": file.filename or "statement",
                "content_type": file.content_type or "application/octet-stream",
                "transaction_count": len(transactions),
                "uploaded_at": datetime.utcnow().isoformat(),
            }
        )
        await asyncio.wait_for(process_uploaded_transactions(transactions), timeout=8)

        return {
            "status": 200,
            "data": {
                "success": True,
                "extractedTransactionsCount": len(transactions),
                "message": "Prophet Engine processing complete and alerts generated.",
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
