from .base_events import GameEvent, TargetedEvent, ObservableEvent
from .game import *


class HostChange(GameEvent):
    new_host: str

    def apply_to_game(self, game) -> dict:
        game.host = self.new_host


class GameStart(GameEvent):
    assigned_characters: dict[str, Character]
    '''Пары [идентификатор клиента-игрока, Персонаж, который принадлежит игроку]'''

    def apply_to_game(self, game) -> dict:
        game.phase = GamePhase.Morning
        for id in self.assigned_characters:
            game.players[id].character = self.assigned_characters[id]


class NewRelationships(TargetedEvent):
    '''Событие, получаемое игроком при назначении друга и врага'''
    friend_client_id: str
    '''Идентификатор клиента, который стал другом'''
    enemy_client_id: str
    '''Идентификатор клиента, который стал врагом'''

    def apply_to_game(self, game) -> dict:
        game.players[self.targets[0]].friend = self.friend_client_id
        game.players[self.targets[0]].enemy = self.enemy_client_id


class NewSupplies(TargetedEvent, ObservableEvent):
    '''Клиент получил карту или карты припасов'''
    supplies: list[Supply | UNKNOWN]

    def apply_to_game(self, game):
        game.players[self.targets[0]].supplies += self.supplies


class TurnChange(GameEvent):
    new_active_player: str
    '''Идентификатор игрока, чей ход наступил'''


class PhaseChange(GameEvent):
    new_phase: GamePhase

    def apply_to_game(self, game):
        game.phase = self.new_phase


class SupplyShowcase(TargetedEvent, ObservableEvent):
    '''Клиенту показываются утренние припасы и предоставляется возможность выбрать оттуда припас'''
    supply_stash: list[Supply | UNKNOWN]


class NavigationsOffer(TargetedEvent, ObservableEvent):
    '''Клиенту для выбора предоставляется набор карт навигации'''
    offered_navigations: list[Navigation | UNKNOWN]