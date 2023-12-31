from enum import Enum

from pydantic import BaseModel, validator, Field

from .game import Game, Observable

from ..utils import Token, PlayerId


class EventTargets(str, Enum):
    All = 'All'
    '''
    Событие должно быть передано в неизменённом виде всем игрокам.
    '''
    Server = 'Server'
    '''
    Событие должно быть передано на сервер, чтобы сервер обработал его и передал остальным
    игрокам следствие этого события и/или часть этого события.
    '''


class GameEvent(BaseModel):
    type: str
    '''
    Тип события, совпадает с названием класса.
    При создании объекта модели устанавливается автоматически.
    '''
    targets: list[PlayerId] | EventTargets = EventTargets.All
    '''
    Кому предназначается событие в его полном виде.
    Содержит список идентификаторов клиентов или значение `EventTargets`

    Сервер использует эту информацию, для того, чтобы понять, кому послать или переслать полученное
    событие
    '''

    def __init__(self, **data):
        data['type'] = type(self).__name__
        super().__init__(**data)

    def apply_to_game(self, game: Game):
        '''Применяет игровое событие к игре и сохраняет изменения в базе данных'''
        raise NotImplementedError()


class TargetedEvent(GameEvent):
    '''
    Событие, предназначенное для одного игрока.
    '''

    targets: list[PlayerId]
    '''Кому предназначается событие в его полном виде.'''

    @validator('targets', always=True)
    def target_is_single(cls, value) -> list[str]:
        if len(value) != 1:
            raise ValueError(f'Event should target exactly one client in {cls.schema()["title"]}')
        return value


player_events: dict[str, type] = {}
'''Словарь со всеми типами, наследующими PlayerEvent. Ключ - тип в строковом виде'''

class PlayerEvent(GameEvent):
    '''Событие, инициируемое игроком.'''
    client_token: Token = Field(exclude=True)
    '''
    Токен, определяющий клиента.
    #### Не пересылается сервером другим игрокам
    '''
    player_id: PlayerId = None
    '''Идентификатор, определяющий, какому игроку принадлежит событие'''

    @validator('player_id', always=True)
    def player_id_setup(cls, value, values):
        client_token = Token(values['client_token'])
        if client_token is not None:
            return client_token.hash()
        return value


    def __init_subclass__(cls) -> None:
        player_events[cls.__name__] = cls
        return super().__init_subclass__()

    @staticmethod
    def from_dict(model: dict) -> 'PlayerEvent':
        '''
        Создаёт событие с классом прописанным в поле `type` в переданном словаре

        @model: Модель события в виде словаря

        :return: Событие, наследующее `PlayerEvent`

        :raises AttributeError: Вызывается, если `type` не передан или не найден класс, соответсвтующий `type`
        '''

        if 'type' not in model:
            'Type not provided'

        if model['type'] not in player_events:
            raise AttributeError(f'Given type is not a child of {PlayerEvent.__name__}')

        event = player_events[model['type']](**model)
        return event


# Этот класс почти идентичен Observable, я просто хочу для понятности переписать здесь докстринги
class ObservableEvent(GameEvent, Observable):
    '''
    Событие, отправленное только некоторым игрокам или серверу, но видное всем.

    Информация, которая может быть невидна, помечается дополнительным типом `UNKNOWN`.

    ### Пример
    Игрок А получает карту припаса. Игроки Б и В не знают, какую именно карту получил игрок А,
    но видели, что у него появилась новая карта.
    '''

    def observer_viewpoint(self) -> Observable:
        '''Возвращает событие с точки зрения наблюдателя'''
        return super().observer_viewpoint()