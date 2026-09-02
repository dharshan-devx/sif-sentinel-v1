from app.schemas.common import ORMModel


class PrecursorRead(ORMModel):
    activity: str
    hazard: str
