from pydantic import BaseModel

class GameInfo(BaseModel):
    id: int
    started: bool = False

class Game(GameInfo, BaseModel):
    pass