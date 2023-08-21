from .base_events import GameEvent

class HostChange(GameEvent):
    new_host: str

    def as_mongo_update(self) -> dict:
        return {'$set': {'host': self.new_host}}