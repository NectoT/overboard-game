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