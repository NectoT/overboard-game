import sys
from enum import Enum

from pydantic import BaseModel


class GameInfo(BaseModel):
    id: int
    started: bool = False


class Player(BaseModel):
    name: str = None


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


class HostChange(GameEvent):
    new_host: str

    def as_mongo_update(self) -> dict:
        return {'$set': {'host': self.new_host}}


class PlayerEvent(GameEvent):
    '''Событие, инициируемое игроком.'''
    client_id: str
    '''Идентификатор, определяющий, какому клиенту-игроку принадлежит событие'''

    @staticmethod
    def from_dict(model: dict) -> 'PlayerEvent':
        '''
        Создаёт событие с классом прописанным в поле `type` в переданном словаре

        @model: Модель события в виде словаря

        :return: Событие, наследующее `PlayerEvent`

        :raises AttributeError: Вызывается, если `type` не передан или не найден класс, соответсвтующий `type`
        '''

        # Этот метод не очень гибок, так как динамично искать он может только классы в этом
        # модуле

        try:
            # Сначала пытаемся по-ленивому искать класс через __dict__ этого модуля
            event_class: type[PlayerEvent] = globals()[model['type']]

            if PlayerEvent not in event_class.mro():
                raise AttributeError('Given type is not a child of PlayerEvent')

            event = event_class(**model)

            return event
        except KeyError:
            # Здесь можно вручную указывать классы, которые мы ищем. Так можно создавать объекты
            # классов, которые создаются в других модулях
            pass
        raise AttributeError(
            'Type not provided or given type cannot be converted to any event class'
        )



class PlayerConnect(PlayerEvent):

    def as_mongo_update(self) -> dict:
        return {'$set': {f'players.{self.client_id}': {}}}


class NameChange(PlayerEvent):
    new_name: str

    def as_mongo_update(self) -> dict:
        return {'$set': {f'players.{self.client_id}.name': self.new_name}}


class GameStart(PlayerEvent):
    def as_mongo_update(self) -> dict:
        return {'$set': {'started': True}}


class SocketError(BaseModel):
    message: str


class GameViewpoint(str, Enum):
    Player = 'Player'
    Spectator = 'Spectator'



class Game(BaseModel):
    '''
    Модель, отображающая состояние игры. В зависимости от `viewpoint` часть информации
    скрывается или искажается.

    #### Это всего лишь модель, само состояние игры хранится в базе данных
    '''
    id: int
    started: bool = False
    players: dict[str, Player] = {}
    host: str = None
    '''Идентификатор игрока, который является хостом'''

    viewpoint: GameViewpoint = None
    '''
    Точка зрения, которую занимает модель.

    То есть, если `viewpoint = None`, то состояние
    игры представлено полно и объективно. Если `viewpoint = GameViewpoint.Player`,
    то в объекте будет представлена только та информация об игре,
    которая доступна игроку с идентификатором `viewpoint_cliend_id`.
    '''
    viewpoint_client_id: str = None
    '''
    Если `viewpoint = GameViewpoint.Player`, то это поле указывает, какому именно игроку
    соответствует эта точка зрения
    '''

    def apply(self, event: PlayerEvent):
        '''
        Обрабатывает пользовательское событие и меняет состояние игры

        :raises ValueError: Вызывается, если в метод подаётся событие, которое не может быть обработано с текущим состоянием игры.
        '''
        if isinstance(event, PlayerConnect):
            if event.client_id in self.players:
                raise ValueError("A player with this client_id already exists in this game.")
            self.players[event.client_id] = Player()

    @staticmethod
    def with_player_view(game: 'Game | dict', client_id: str) -> 'Game':
        '''
        Возвращает состояние игры с точки зрения игрока с идентификатором `client_id`.

        @game: Состояние игры.
        '''
        if isinstance(game, Game):
            new_game = game.copy() # new потому что новый объект
        else:
            new_game = Game.construct(**game) # new потому что новый объект

        #TODO

        return new_game

    @staticmethod
    def with_spectator_view(game: 'Game | dict') -> 'Game':
        '''
        Возвращает состояние игры с точки зрения наблюдателя.

        @game: Состояние игры.
        '''
        if isinstance(game, Game):
            new_game = game.copy() # new потому что новый объект
        else:
            new_game = Game.construct(**game) # new потому что новый объект

        #TODO

        return new_game


# Не хочу стирать эти строчки, потому что мне нравится идея модели, фиксирующей изменение
# состояния и имеющей ту жу структуру, что и сама модель состояния. Но вроде здесь удобнее
# с событиями
# fields = {name: (Game.__fields__[name].type_, None) for name in Game.__fields__}
# # Конечно это не type[Game], а type[BaseModel], Но для того, чтобы type hints работали для инит
# # пишу так
# GameUpdate: type[Game] = create_model('GameUpdate', **fields)
# '''
# Модель, обозначающая новые изменения состояния игры с идентификатором `game_id`.
# Идентична модели `Game`, однако все неизменённые поля равны `None`.

# Поле, не равное `None`, показывает, что состояние этого поля в игре изменилось
# '''


def _get_property_type(property: dict) -> str:
    type_conversion = {'integer': 'number'}

    if 'anyOf' in property:
        return ' | '.join([_get_property_type(prop) for prop in property['anyOf']])
    if '$ref' in property:
        return property['$ref'].split('/')[-1]
    if 'type' not in property:
        return 'any'
    if property['type'] == 'array':
        return f'Array<{_get_property_type(property["items"])}>'
    if property['type'] == 'object':
        # Скорее всего dict.
        # В схеме почему-то нет типа ключа :(
        return '{ ' + f'[key: string]: {_get_property_type(property["additionalProperties"])}' + ' }'
    if property['type'] in type_conversion:
        return type_conversion[property['type']]
    return property['type']


def model_to_ts_type(model: type[BaseModel], export=True) -> str:
    '''Конвертирует модель в typescript type'''
    schema: dict = model.schema()
    export_str = 'export ' if export else ''
    doc = '' if (model.__doc__ is None) else f'/** {(model.__doc__)} */\n'
    output = doc + export_str + f'type {schema["title"]} = {{\n'
    properties: dict = schema['properties']
    for name in properties:
        property = properties[name]
        required_char = '?' if model.__fields__[name].allow_none else ''
        output += f'\t{name}{required_char}: {_get_property_type(property)};\n'
    output += '};\n'

    return output


def generate_ts_models(file_path: str, excluded_models: list[type]=[],
                       included_models: list[type]=[], include_child_classes=False,
                       exlude_child_classes = False, export=True):
    '''
    Создаёт TypeScript файл с типами данных, соответствующими моделям в models.py.

    Поддерживает enum как тип поля в модели.

    Если у модели прописан метод `as_ts_class` или 'as_ts_type`, для транспиляции используется
    этот метод

    @excluded_models: Модели, которые игнорируются и не записываются в файл.
    @included_models: Модели, которые записываются в файл. Если передаётся пустой список, в файл записываются все модели, кроме тех, которые переданы в excluded_models
    @include_child_classes: Если True, то производные классы тех моделей, которые включены в `included_models`, так же записываются в файл
    @exlude_child_classes: Если True, то производные классы тех моделей, которые включены в `excluded_models`, так же игнорируются
    @export: Если True, все типы экспортируются
    '''
    output = ''
    export_str = 'export ' if export else ''
    _dict_ = globals().copy()
    handled_enum_types = []
    for key in _dict_:
        is_model = (
            hasattr(_dict_[key], '__bases__') and
            _dict_[key] != BaseModel and
            BaseModel in _dict_[key].mro()
        )
        if not is_model:
            continue

        is_included = len(included_models) == 0 or _dict_[key] in included_models
        if include_child_classes and len(included_models) > 0:
            for included_model in included_models:
                is_included = is_included or included_model in _dict_[key].mro()
        if not is_included:
            continue

        is_excluded = _dict_[key] in excluded_models
        if exlude_child_classes and len(excluded_models) > 0:
            for excluded_model in excluded_models:
                if excluded_model in _dict_[key].mro():
                    is_excluded = True
                    break
        if is_excluded:
            continue

        # Ищем потенциальные enums, которые используются в модели
        schema: dict= _dict_[key].schema()
        definitions = schema['definitions'] if 'definitions' in schema else []
        for type_name in definitions:
            definition = schema['definitions'][type_name]
            if 'enum' in definition and definition['title'] not in handled_enum_types:
                handled_enum_types.append(definition['title'])
                if definition['type'] == 'string':
                    # Создаём typescript enum
                    output += export_str + f'enum {definition["title"]} {{\n'
                    for value in definition['enum']:
                        output += f'\t{value} = "{value}",\n'
                    output += '};\n\n'
                else:
                    # Создаём typescript тип с ограниченным кол-вом значений
                    output += export_str + f'type {definition["title"]} = '
                    output += ' | '.join(map(str, definition['enum'])) + ';\n\n'

        # транспилируем саму модель
        if hasattr(_dict_[key], 'as_ts_class'):
            output += _dict_[key].as_ts_class(export=export) + '\n'
        elif hasattr(_dict_[key], 'as_ts_type'):
            output += _dict_[key].as_ts_type(export=export) + '\n'
        else:
            output += model_to_ts_type(_dict_[key], export=export) + '\n'

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(output)


if __name__ == '__main__':
    args = sys.argv
    if len(args) == 1:
        print('Генерирует ts файл с типами данных, соответствующими моделям в models.py')
    elif len(args) == 2:
        generate_ts_models(args[1])