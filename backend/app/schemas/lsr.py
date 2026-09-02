from app.schemas.common import ORMModel


class LifeSavingRuleRead(ORMModel):
    code: str
    name: str
