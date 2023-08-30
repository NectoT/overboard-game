from .base_events import GameEvent, TargetedEvent, ObservableEvent
from .game import *


class HostChange(GameEvent):
    new_host: str

    def as_mongo_update(self, game) -> dict:
        return {'$set': {'host': self.new_host}}


class GameStart(GameEvent):
    assigned_characters: dict[str, Character]
    '''Пары [идентификатор клиента-игрока, Персонаж, который принадлежит игроку]'''

    def as_mongo_update(self, game) -> dict:
        update: dict = {'$set': {'phase': GamePhase.Morning}}
        for client_id in self.assigned_characters:
            update['$set'][f'players.{client_id}.character'] = self.assigned_characters[client_id].dict()
        return update


class NewRelationships(TargetedEvent):
    '''Событие, получаемое игроком при назначении друга и врага'''
    friend_client_id: str
    '''Идентификатор клиента, который стал другом'''
    enemy_client_id: str
    '''Идентификатор клиента, который стал врагом'''

    def as_mongo_update(self, game) -> dict:
        return {'$set': {
            f'players.{self.targets[0]}.friend': self.friend_client_id,
            f'players.{self.targets[0]}.enemy': self.enemy_client_id,
        }}


class NewSupplies(TargetedEvent, ObservableEvent):
    '''Клиент получил карту или карты припасов'''
    supplies: list[Supply | UNKNOWN]

    def as_mongo_update(self, game) -> dict:
        values = []
        for supply in self.supplies:
            values.append(supply.dict())

        array_string = f'players.{self.targets[0]}.supplies'
        if len(values) == 1:
            update = {'$push': {array_string: values[0]}}
        else:
            update = {'$push': {array_string: {'$each': values}}}

        return update