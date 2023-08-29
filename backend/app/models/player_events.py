from .base_events import PlayerEvent, EventTargets


class PlayerConnect(PlayerEvent):

    def as_mongo_update(self, game) -> dict:
        return {'$set': {f'players.{self.client_id}': {}}}


class NameChange(PlayerEvent):
    new_name: str

    def as_mongo_update(self, game) -> dict:
        return {'$set': {f'players.{self.client_id}.name': self.new_name}}


class StartRequest(PlayerEvent):
    '''Просьба от хоста начать игру'''
    targets: EventTargets = EventTargets.Server