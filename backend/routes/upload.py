from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.services.pipeline import process_uploaded_transactions
from backend.services.parser import parse_csv, parse_image, parse_pdf

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

        await process_uploaded_transactions(transactions)

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
