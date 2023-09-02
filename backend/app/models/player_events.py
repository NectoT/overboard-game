from .base_events import PlayerEvent, EventTargets, ObservableEvent

from .game import UNKNOWN, Supply

class PlayerConnect(PlayerEvent):

    def apply_to_game(self, game):
        game.players[self.client_id] = {}


class NameChange(PlayerEvent):
    new_name: str

    def apply_to_game(self, game) -> dict:
        game.players[self.client_id].name = self.new_name


class StartRequest(PlayerEvent):
    '''Просьба от хоста начать игру'''
    targets: EventTargets = EventTargets.Server


class TakeSupply(PlayerEvent, ObservableEvent):
    '''Игрок берёт припас из утреннего набора припасов'''
    targets: EventTargets = EventTargets.Server
    supply: Supply | UNKNOWN

    def apply_to_game(self, game) -> dict:
        game.supply_stash.remove(self.supply)

        game.players[self.client_id].supplies.append(self.supply)