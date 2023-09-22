from enum import Enum
import json
from typing import Literal, Union, get_args, get_origin, Any
from types import UnionType

from mkdocs.commands.build import build as mkbuild
from mkdocs.config import load_config
from pydantic import BaseModel

from ..routers.eventhandlers import playerevent
from ..models import *


event_handlers = playerevent.handlers
EventInfoKey = Literal["observable", "targeted", "player", "response_events"]
events_info: dict[type[GameEvent], dict[EventInfoKey, Any]] = {}
'''Словарь игровых событий с дополнительной информацией'''

for name in event_handlers:
    handler = event_handlers[name]
    response_events = handler.response_events
    event = handler.event_type
    events_info[event] = {
        "observable": Observable in event.mro(),
        "targeted": TargetedEvent in event.mro(),
        "player": PlayerEvent in event.mro(),
        "response_events": response_events
    }

    for event in response_events:
        events_info[event] = {
            "observable": Observable in event.mro(),
            "targeted": TargetedEvent in event.mro(),
            "player": PlayerEvent in event.mro(),
            "response_events": []
        }


_dir = '/'.join(__path__) + '/'
'''Директория, в котором находится этот файл'''


def _make_event_title(event: type[GameEvent]) -> str:
    left_badges: list[str] = []
    right_badges: list[str] = []

    title_attrs = f'.event-title data-toc-label={event.__name__} #{event.__name__} '
    if PlayerEvent in event.mro():
        left_badges.append('<span class="badge player">Player Event</span>')
        title_attrs += '.player'
    else:
        left_badges.append('<span class="badge server">Server Event</span>')
        title_attrs += '.server'

    if Observable in event.mro():
        right_badges.append('<span class="badge observable"> :material-eye: [Observable](#Observable)</span>')
    if TargetedEvent in event.mro():
        right_badges.append('<span class="badge targeted"> :simple-target: [Targeted](#Targeted)</span>')

    name = f'<span class="name">{event.__name__}</span>'
    title = f'### {" ".join(left_badges)} {name}  {" ".join(right_badges)} {{ {title_attrs} }}'

    return title

def _add_indent(string: str, indent=4) -> str:
    indentation = (' ' * indent)
    return indentation + indentation.join(string.splitlines(True))


def _get_md_type(type_: type) -> str:
    def is_subclass(type_: type, of_type: type) -> bool:
        return hasattr(type_, 'mro') and of_type in type_.mro()

    # def quote_marks(object):
    #     return f'"{object}"'

    if get_origin(type_) in [list]:
        return 'list[' + ' | '.join(map(_get_md_type, get_args(type_))) + ']'
    if get_origin(type_) in [Union, UnionType]:
        return ' | '.join(map(_get_md_type, get_args(type_)))
    elif get_origin(type_) is Literal:
        return ' | '.join(get_args(type_))
    elif is_subclass(type_, Enum):
        return ' | '.join(type_._member_names_)
    else:
        return type_.__name__


def _get_default_value(type_: type, observed=False):

    def is_subclass(type_: type, of_type: type) -> bool:
        return hasattr(type_, 'mro') and of_type in type_.mro()

    if observed and UNKNOWN in get_args(type_):
        return {}
    if type_ is str or is_subclass(type_, str):
        return 'string'
    elif type_ is int:
        return 0
    elif type_ is float:
        return 0.0
    elif get_origin(type_) is dict:
        args = get_args(type_)
        return {_get_default_value(args[0]): _get_default_value(args[1], observed=observed)}
    elif get_origin(type_) is list:
        if len(get_args(type_)) == 0:
            return []
        else:
            return [_get_default_value(get_args(type_)[0], observed=observed)]
    elif get_origin(type_) in [Union, UnionType]:
        return _get_default_value(get_args(type_)[0])
    elif get_origin(type_) is Literal:
        return get_args(type_)[0]
    elif is_subclass(type_, Enum):
        return type_._member_names_[0]
    elif is_subclass(type_, BaseModel):
        return _create_example(type_)
    else:
        print(f'Could not create a default value for {type_} when generating event documentation')


def _create_example(model: type[BaseModel], observed=False) -> dict[str, Any]:
    '''
    Создаёт пример объекта модели в dict-виде

    @observed: Для `Observable` моделей. Если `True`, везде, где может быть `UNKNOWN`, выбирается он
    '''
    example = {}
    for field_name in model.__fields__:
        model_field = model.__fields__[field_name]

        if field_name == 'type':
            example[field_name] = model.__name__
        elif observed and field_name == 'observed':
            example[field_name] = True
        elif 'examples' in model_field.field_info.extra:
            example[field_name] = model_field.field_info.extra['examples'][0]
        elif model_field.default is not None:
            example[field_name] = model_field.default
        else:
            example[field_name] = _get_default_value(model_field.outer_type_, observed=observed)

    return example


# def _make_event_properties(event: type[GameEvent]):
#     md_event += '### Properties: \n\n'

#     for field_name in event.__fields__:
#         model_field = event.__fields__[field_name]
#         md_event += f'{field_name}: {_get_md_type(model_field.outer_type_)} \n\n'


def _make_json_snippet(snippet_name, json_dict: dict) -> str:
    snippet = f'=== "{snippet_name}" \n\n'
    schema_md = '``` json \n\n'
    schema_md += json.dumps(json_dict, indent=4) + '\n\n'
    schema_md += '```\n\n'
    snippet += _add_indent(schema_md)
    return snippet


def _make_event_block(event: type[GameEvent]) -> str:
    md_event = _make_event_title(event) + '\n\n'

    if event.__doc__ is not None:
        md_event += '#### ' + event.__doc__ + '\n\n'


    info = events_info[event]

    if len(info['response_events']) > 0:
        md_event += '#### Response Events: \n\n'
        response_events: list[type[GameEvent]] = info['response_events']
        for response_event in response_events:
            md_event += f'[{response_event.__name__}](#{response_event.__name__}), '
        md_event += '\n\n'

    md_event += '***\n\n'

    md_event += _make_json_snippet('JSON-Schema', event.schema())
    md_event += _make_json_snippet('Example', _create_example(event))

    if Observable in event.mro():
        md_event += _make_json_snippet('Example (observed)', _create_example(event, observed=True))

    md_event += '***\n\n'

    return md_event

def _make_event_page():
    player_events = ""
    server_events = ""

    for event in filter(lambda event: PlayerEvent in event.mro(), events_info.keys()):
        player_events += _make_event_block(event) + '\n\n'
    for event in filter(lambda event: PlayerEvent not in event.mro(), events_info.keys()):
        server_events += _make_event_block(event) + '\n\n'

    md_path = _dir + 'docs/events.md'
    with open(_dir + 'templates/events.md', encoding='utf-8') as template, open(md_path, 'w', encoding='utf-8') as output:
        md = template.read()
        md = md.replace('{%player_events%}', player_events).replace('{%server_events%}', server_events)
        output.write(md)


def build():
    _make_event_page()
    mkbuild(load_config(_dir + 'mkdocs.yml'))