import re
from typing import Any, Callable

from fastapi import APIRouter, HTTPException, Depends

from ..databases import mongo_db as db
from ..models import *


def game_exists(game_id: int):
    if db['games'].find_one({'id': game_id}) is None:
        raise HTTPException(422, detail='No game with this id found')


router = APIRouter(tags=["События игрока"], prefix="/{game_id}", dependencies=[Depends(game_exists)])
tag_meta = {
    "name": "События игрока",
    "description": ('#### События, которые отправляет игрок для того, чтобы сообщить серверу ' +
                    'об изменении игры. Все эти события так же можно (и желательно) отправлять ' +
                    'с помощью вебсокет-подключения')
}


__event_handlers: dict[str, Callable[[int, PlayerEvent], GameEvent | None]] = {}
'''Словарь с обработчиками событий, где ключ - это тип события в виде строки'''


def playerevent(func: Callable[[int, PlayerEvent], Any]) -> Callable[[int, PlayerEvent], Any]:
    '''
        Декоратор, маркирующий функцию как обработчик игрового события от игрока.
        Для каждого типа игрового события может быть только одна функция с этим декоратором

        #### Функции с данным декоратором изменяют игру в базе данных

        Функции с этим декоратором добавляются как путь в FastAPI `router`.

        Функции с этим декоратором используются методом `handle` для обработки события
        того же типа
    '''
    event_type = None
    # Определяем событие через type hint
    for key in func.__annotations__:
        hint = func.__annotations__[key]
        if hasattr(hint, 'mro') and PlayerEvent in hint.mro():
            event_type: type = hint
            break
    if event_type is None:
        # Не нашли, где событие подают
        raise AttributeError('Event type could not be determined')

    router_name = re.sub(r'[A-Z]', r' \g<0>', event_type.__name__)
    @router.post(
        '/' + event_type.__name__.lower(),
        name=router_name,
        description=func.__doc__,
        status_code=200
    )
    def wrapper(game_id: int, event: event_type) -> dict:
        func(game_id, event)
        return {}

    __event_handlers[event_type.__name__] = func

    return func


def handle_player(game_id: int, event: PlayerEvent) -> GameEvent | None:
    '''
    Автоматически подбирает и вызывает обработчик для игрового события игрока.

    @game_id: Идентификатор игры, для которой предназначено событие

    :returns: Ответное игровое событие, предназначенное игрокам или None

    :raises TypeError: Не найден обработчик для переданного типа игрового события
    '''
    for event_type in type(event).mro():
        if event_type.__name__ in __event_handlers:
            return __event_handlers[event_type.__name__](game_id, event)
        if event_type is PlayerEvent:
            break
    raise TypeError('No event handler for this event is available')


@playerevent
def base(game_id: int, event: PlayerEvent):
    '''Применяет переданные событием изменения к игре'''
    db['games'].update_one({'id': game_id}, event.as_mongo_update())


@playerevent
def on_player_connect(game_id, event: PlayerConnect):
    game_document = db['games'].find_one({'id': game_id})
    game: Game = Game.construct(**game_document)

    if event.client_id not in game.players:
        db['games'].update_one({'id': game_id}, event.as_mongo_update())

    if (isinstance(event, PlayerConnect) and game.host is None):
        # Первый подключившийся к бесхозной игре становится её хостом
        host_event = HostChange(new_host=event.client_id)
        db['games'].update_one({'id': game_id}, host_event.as_mongo_update())
        return host_event


@playerevent
def start_game(game_id, event: StartRequest):
    game_document = db['games'].find_one({'id': game_id})
    game: Game = Game.construct(**game_document)

    if game.host != event.client_id:
        raise HTTPException(403, detail='Received event does not belong to game host')

    base(game_id, event)
    print('Started the game')