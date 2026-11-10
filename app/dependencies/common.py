from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user


# Reusable database session dependency
DbSession = Annotated[
    Session,
    Depends(get_db),
]


# Reusable authenticated user dependency
CurrentUser = Annotated[
    dict,
    Depends(get_current_user),
]