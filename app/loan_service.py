
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas import LoanCreate, LoanUpdate


loans = []


def create_loan(
    loan_data: LoanCreate,
    user_id: str
):

    loan = {

        "loan_id": str(uuid4()),

        "customer_id": loan_data.customer_id,

        "loan_amount": loan_data.loan_amount,

        "interest_rate": loan_data.interest_rate,

        "loan_duration_months": loan_data.loan_duration_months,

        "loan_type": loan_data.loan_type,

        "status": "PENDING",

        "created_by": user_id,

        "created_at": datetime.now(timezone.utc)

    }

    loans.append(loan)

    return loan


def get_all_loans():

    return loans


def get_loan_by_id(loan_id: str):

    for loan in loans:

        if loan["loan_id"] == loan_id:

            return loan

    return None


def update_loan(
    loan_id: str,
    loan_data: LoanUpdate
):

    loan = get_loan_by_id(loan_id)

    if loan is None:

        return None

    updated_data = loan_data.model_dump(
        exclude_unset=True
    )

    loan.update(updated_data)

    return loan


def delete_loan(loan_id: str):

    loan = get_loan_by_id(loan_id)

    if loan is None:

        return False

    loans.remove(loan)

    return True
