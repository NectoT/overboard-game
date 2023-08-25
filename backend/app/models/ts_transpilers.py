import sys

from pydantic import BaseModel

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


def model_to_ts_class(model, default_fields: dict[str, str] = {},
                      readonly_fields: dict[str, str] = {}, export=True) -> str:
        '''
        Конвертирует модель в typescript класс с простым конструктором и дефолтными значениями

        @default_fields: пары строк `Имя поля; Значение поля в ts-виде` для установки дефолтных полей
        @readonly_fields: пары строк `Имя поля; Значение поля в ts-виде` для установки константных полей

        :returns: Строку с typescript классом
        '''

        # Я не смог сделать универсальный конвертатор модели в класс, потому что там беда с
        # дефолтными значениями, поэтому приходится их заранее конвертировать и передавать сюда

        schema: dict = model.schema()
        export_str = 'export ' if export else ''
        doc = '' if (model.__doc__ is None) else f'/** {(model.__doc__)} */\n'
        output = doc + export_str + f'class {schema["title"]} {{\n'

        class_body = ''
        constructor_head = '\tconstructor('
        constructor_body = ''

        # Отдельно, потому что необязательные аргументы обязаны быть в конце
        constructor_head_end = ''

        properties: dict = schema['properties']
        for name in properties:
            property = properties[name]

            if name in readonly_fields:
                class_body += f"\t{name} = '{readonly_fields[name]}';\n"
                continue  # Не добавляем type в конструктор

            is_required = not model.__fields__[name].allow_none
            required_char = '' if is_required else '?'
            property_type = _get_property_type(property)

            class_body += f'\t{name}{required_char}: {property_type};\n'

            if name in default_fields and 'default' in property:
                arg = f'{name} = {default_fields[name]}, '
            else:
                arg = f'{name}{required_char}: {property_type}, '

            if is_required and name not in default_fields:
                constructor_head += arg
            else:
                constructor_head_end += arg
            constructor_body += f'\t\tthis.{name} = {name};\n'

        constructor_head += constructor_head_end + ') {\n'
        constructor = constructor_head + constructor_body + '\t}\n'

        output += class_body + constructor
        output += '};\n'
        return output