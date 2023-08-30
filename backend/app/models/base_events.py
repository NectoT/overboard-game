from enum import Enum

from pydantic import BaseModel, validator

from .game import Game, Observable
from .ts_transpilers import model_to_ts_class


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
    targets: list[str] | EventTargets = EventTargets.All
    '''
    Кому предназначается событие в его полном виде.
    Содержит список идентификаторов клиентов или значение `EventTargets`

    Сервер использует эту информацию, для того, чтобы понять, кому послать или переслать полученное
    событие
    '''

    def __init__(self, **data):
        data['type'] = type(self).__name__
        super().__init__(**data)

    def as_mongo_update(self, game: Game) -> dict:
        '''
        События в виде обновления MongoDB

        @game Состояние игры, для которой предназначается обновление

        :returns: словарь с update operators, которые используются для
        обновления документа игры в MongoDB
        '''
        raise NotImplementedError

    @classmethod
    def _ts_class_defaults(cls) -> dict[str, str]:
        '''Вспомогательный метод для удобного наследования'''
        targets_property = cls.schema()['properties']['targets']
        return {'targets': f'{EventTargets.__name__}.{targets_property["default"]}'}

    @classmethod
    def as_ts_class(cls, export=True) -> str:
        '''
        Конвертирует модель в typescript класс с простым конструктором и дефолтными значениями

        :returns: Строку с typescript классом
        '''

        readonly = {'type': cls.__name__}
        defaults = cls._ts_class_defaults()

        return model_to_ts_class(cls, default_fields=defaults, readonly_fields=readonly,
                                 export=export)


class TargetedEvent(GameEvent):
    '''
    Событие, предназначенное для одного игрока.

    Идентичен `GameEvent`, за исключением проверки `targets`
    '''

    @validator('targets')
    def target_is_single(cls, value) -> list[str]:
        if value is EventTargets or len(value) != 1:
            raise ValueError(f'Event should target exactly one client in {cls.__class__.__name__}')
        return value


player_events: dict[str, type] = {}
'''Словарь со всеми типами, наследующими PlayerEvent. Ключ - тип в строковом виде'''

class PlayerEvent(GameEvent):
    '''Событие, инициируемое игроком.'''
    client_id: str
    '''Идентификатор, определяющий, какому клиенту-игроку принадлежит событие'''

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
