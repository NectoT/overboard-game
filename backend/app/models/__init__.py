from .base_events import *
from .player_events import *
from .server_events import *
from .game import *
from .ts_transpilers import *


def generate_ts_models(file_path: str, excluded_models: list[type]=[],
                       included_models: list[type]=[], include_child_classes=False,
                       exlude_child_classes = False, export=True):
    '''
    Создаёт TypeScript файл с типами данных, соответствующими моделям в models

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

                enum_type: type = type(definition["enum"][0])
                if BaseModel in enum_type.mro():
                    # Создаём typescript класс с статическими полями
                    output += export_str + f'const {definition["title"]} = {{\n'
                else:
                    # Создаём typescript enum
                    output += export_str + f'enum {definition["title"]} {{\n'

                enum_names: list[str] = _dict_[definition['title']]._member_names_
                for i in range(len(definition['enum'])):
                    value: object = definition['enum'][i]
                    name = enum_names[i]
                    if BaseModel in enum_type.mro():
                        value_str = '{' + str(value).replace(' ', ', ').replace('=', ': ') + '}'
                        output += f'\t{name}: {value_str},\n'
                    elif enum_type is str:
                        output += f'\t{name} = "{value}",\n'
                    elif enum_type is bool:  # ...Ну мало ли
                        output += f'\t{name} = {value},\n'
                    else:
                        output += f'\t{name} = {value},\n'

                output += '};\n\n'
                if BaseModel in enum_type.mro():
                    # Создаём typescript класс с статическими полями
                    output += export_str + f'type {definition["title"]} = {enum_type.__name__}\n\n'

        # транспилируем саму модель
        if hasattr(_dict_[key], 'as_ts_class'):
            output += _dict_[key].as_ts_class(export=export) + '\n'
        elif hasattr(_dict_[key], 'as_ts_type'):
            output += _dict_[key].as_ts_type(export=export) + '\n'
        else:
            output += model_to_ts_type(_dict_[key], export=export) + '\n'

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(f'/** Автосгенерирован функцией {generate_ts_models.__name__} в модуле {__name__} */\n\n')
        file.write(output)