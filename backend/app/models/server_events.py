from types import UnionType

from .base_events import GameEvent, TargetedEvent
from .game import Character, Supply, UNKNOWN, Observable


# Этот класс почти идентичен Observable, я просто хочу для понятности переписать здесь докстринги
class ObservableEvent(GameEvent, Observable):
    '''
    Событие, отправленное только некоторым игрокам, но видное всем.

    Информация, которая может быть невидна, помечается дополнительным типом `UNKNOWN`.

    ### Пример
    Игрок А получает карту припаса. Игроки Б и В не знают, какую именно карту получил игрок А,
    но видели, что у него появилась новая карта.
    '''

    def observer_viewpoint(self) -> Observable:
        '''Возвращает событие с точки зрения наблюдателя'''
        return super().observer_viewpoint()

    @classmethod
    def _ts_class_defaults(cls) -> dict[str, str]:
        '''Вспомогательный метод для удобного переопределения в наследующих классах'''
        observed_property = cls.schema()['properties']['observed']
        fields = GameEvent._ts_class_defaults()
        if observed_property["default"]:
            fields['observed'] = 'true'
        else:
            fields['observed'] = 'false'
        return fields


class HostChange(GameEvent):
    new_host: str

    def as_mongo_update(self) -> dict:
        return {'$set': {'host': self.new_host}}


class GameStart(GameEvent):
    assigned_characters: dict[str, Character]
    '''Пары [идентификатор клиента-игрока, Персонаж, который принадлежит игроку]'''

    def as_mongo_update(self) -> dict:
        update: dict = {'$set': {'started': True}}
        for client_id in self.assigned_characters:
            update['$set'][f'players.{client_id}.character'] = self.assigned_characters[client_id].dict()
        return update


class NewSupplies(TargetedEvent, ObservableEvent):
    '''Клиент получил карту или карты припасов'''
    supplies: list[Supply | UNKNOWN]

    def as_mongo_update(self) -> dict:
        values = []
        for supply in self.supplies:
            values.append(supply.dict())

        array_string = f'players.{self.targets[0]}.supplies'
        if len(values) == 1:
            update = {'$push': {array_string: values[0]}}
        else:
            update = {'$push': {array_string: {'$each': values}}}

        return update