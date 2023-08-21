from enum import Enum

from pydantic import BaseModel

from .ts_transpilers import _get_property_type


class EventTargets(str, Enum):
    All = 'All'
    '''
    Событие должно быть передано в неизменённом виде всем игрокам.
    '''
    Server = 'Server'
    '''
    Событие должно быть передано на сервер, чтобы сервер обработал его и передал остальным
    игрокам следствие этого события и/или часть этого события.


    Например, в "За Бортом" когда игрок выбрал припас, остальные игроки видят
    только то, что припасов стало меньше.
    '''


class GameEvent(BaseModel):
    type: str
    '''
    Тип события, совпадает с названием класса.
    При создании объекта модели устанавливается автоматически.
    '''
    targets: set[str] | EventTargets = EventTargets.All
    '''
    Кому предназначается событие в его полном виде.
    Содержит список идентификаторов клиентов или значение `EventTargets`

    Сервер использует эту информацию, для того, чтобы понять, кому послать или переслать полученное
    событие
    '''

    def __init__(self, **data):
        data['type'] = type(self).__name__
        super().__init__(**data)

    def as_mongo_update(self) -> dict:
        '''
        Возвращает словарь с update operators, которые используются для
        обновления документа игры в MongoDB
        '''
        raise NotImplementedError

    @classmethod
    def as_ts_class(cls, export=True) -> str:
        '''
        Конвертирует модель в typescript класс с простым конструктором и дефолтными значениями

        :returns: Строку с typescript классом
        '''

        # Я не смог сделать универсальный конвертатор модели в класс, потому что там беда с
        # дефолтными значениями. Тут же просто нужно заранее задавать type и делать дефолтным
        # targets

        schema: dict = cls.schema()
        export_str = 'export ' if export else ''
        doc = '' if (cls.__doc__ is None) else f'/** {(cls.__doc__)} */\n'
        output = doc + export_str + f'class {schema["title"]} {{\n'

        class_body = ''
        constructor_head = '\tconstructor('
        constructor_body = ''

        # Отдельно, потому что необязательные аргументы обязаны быть в конце
        constructor_head_end = ''

        properties: dict = schema['properties']
        for name in properties:
            property = properties[name]

            if name == 'type':
                class_body += f"\t{name} = '{cls.__name__}';\n"
                continue  # Не добавляем type в конструктор

            is_required = not cls.__fields__[name].allow_none
            required_char = '' if is_required else '?'
            property_type = _get_property_type(property)

            class_body += f'\t{name}{required_char}: {property_type};\n'

            if name == 'targets' and 'default' in property:
                arg = f'{name} = {EventTargets.__name__}.{property["default"]}, '
            else:
                arg = f'{name}{required_char}: {property_type}, '

            if is_required and name != 'targets':
                constructor_head += arg
            else:
                constructor_head_end += arg
            constructor_body += f'\t\tthis.{name} = {name};\n'

        constructor_head += constructor_head_end + ') {\n'
        constructor = constructor_head + constructor_body + '\t}\n'

        output += class_body + constructor
        output += '};\n'
        return output


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
