from .base_events import PlayerEvent, EventTargets, ObservableEvent

from .game import UNKNOWN, Supply

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


class TakeSupply(PlayerEvent, ObservableEvent):
    '''Игрок берёт припас из утреннего набора припасов'''
    targets: EventTargets = EventTargets.Server
    supply: Supply | UNKNOWN

    def as_mongo_update(self, game) -> dict:
        print(self.supply)
        supply_stash = game.supply_stash
        supply_stash.remove(self.supply)

        player_supplies = game.players[self.client_id].supplies
        player_supplies.append(self.supply)

        return {'$set': {
            'supply_stash': [supply.dict() for supply in supply_stash],
            f'players.{self.client_id}.supplies': [supply.dict() for supply in player_supplies]
        }}