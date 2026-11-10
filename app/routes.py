
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user

from app.schemas import (
    LoanCreate,
    LoanResponse,
    LoanUpdate
)

from app.loan_service import (
    create_loan,
    get_all_loans,
    get_loan_by_id,
    update_loan,
    delete_loan
)


router = APIRouter(
    prefix="/api/loans",
    tags=["Loan Management"]
)


@router.post(
    "/",
    response_model=LoanResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_new_loan(
    loan_data: LoanCreate,
    user=Depends(get_current_user)
):

    return create_loan(
        loan_data,
        user_id=user["sub"]
    )


@router.get(
    "/",
    response_model=list[LoanResponse]
)
async def list_loans(
    user=Depends(get_current_user)
):

    return get_all_loans()


@router.get(
    "/{loan_id}",
    response_model=LoanResponse
)
async def get_loan(
    loan_id: str,
    user=Depends(get_current_user)
):

    loan = get_loan_by_id(loan_id)

    if loan is None:

        raise HTTPException(
            status_code=404,
            detail="Loan not found"
        )

    return loan


@router.put(
    "/{loan_id}",
    response_model=LoanResponse
)
async def update_existing_loan(
    loan_id: str,
    loan_data: LoanUpdate,
    user=Depends(get_current_user)
):

    loan = update_loan(
        loan_id,
        loan_data
    )

    if loan is None:

        raise HTTPException(
            status_code=404,
            detail="Loan not found"
        )

    return loan


@router.delete("/{loan_id}")
async def remove_loan(
    loan_id: str,
    user=Depends(get_current_user)
):

    deleted = delete_loan(loan_id)

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Loan not found"
        )

    return {
        "message": "Loan deleted successfully",
        "loan_id": loan_id
    }
