import re
from typing import Any, Callable
import random

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


__event_handlers: dict[str, Callable[[Game, PlayerEvent], list[GameEvent] | None]] = {}
'''Словарь с обработчиками событий, где ключ - это тип события в виде строки'''


def playerevent(func: Callable[[Game, PlayerEvent], Any]) -> Callable[[int, PlayerEvent], Any]:
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
        raise AttributeError(f'Cannot define "{func.__name__}" as player event handler: ' +
                             'Player event type could not be identified. \nMake sure that ' +
                             'there is a type hint for event argument, and that the ' +
                             'hinted type inherits PlayerEvent')

    router_name = re.sub(r'[A-Z]', r' \g<0>', event_type.__name__)
    @router.post(
        '/' + event_type.__name__.lower(),
        name=router_name,
        description=func.__doc__,
        status_code=200
    )
    def fastapi_route(game_id: int, event: event_type) -> dict:
        # Такие post-запросы можно использовать, только если все игроки пользуются post-запросами
        # и поллингом get_game (или как там называется функция), потому что ответные события в
        # случае пост-запроса не высылаются
        game = Game(**db['games'].find_one({'id': game_id}))
        responses = func(game, event)
        game.save_changes(db['games'])
        return {}

    def wrapper(game_id: int, event: GameEvent):
        game = Game(**db['games'].find_one({'id': game_id}))
        responses = func(game, event)
        game.save_changes(db['games'])
        return responses

    __event_handlers[event_type.__name__] = wrapper

    return wrapper


def handle_player(game_id: int, event: PlayerEvent) -> list[GameEvent] | None:
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


def get_game(game_id: int) -> Game:
    game_document = db['games'].find_one({'id': game_id})
    return Game(**game_document)


@playerevent
def apply_event(game: Game, event: PlayerEvent):
    '''Применяет переданные событием изменения к игре'''
    game.apply_event(event)


@playerevent
def on_player_connect(game: Game, event: PlayerConnect):
    if event.client_id not in game.players:
        game.apply_event(event)

    if isinstance(event, PlayerConnect) and game.host is None:
        # Первый подключившийся к бесхозной игре становится её хостом
        host_event = HostChange(new_host=event.client_id)
        game.apply_event(host_event)
        return [host_event]
    return []

    return get_game(game_id)


@playerevent
def start_game(game: Game, event: StartRequest):

    if game.host != event.client_id:
        raise HTTPException(403, detail='Received event does not belong to game host')

    responses = []

    # Рандомно выбираем персонажей из CharacterEnum
    enum_names = random.sample(CharactersEnum._member_names_, k=len(game.players))

    assigned_characters = {}
    for name, client_id in zip(enum_names, game.players):
        assigned_characters[client_id] = CharactersEnum[name].value

    start_event = GameStart(assigned_characters=assigned_characters)
    game.apply_event(start_event)
    responses.append(start_event)

    # Назначаем друзей и врагов
    friend_ids = list(game.players)
    random.shuffle(friend_ids)
    enemy_ids = list(game.players)
    random.shuffle(enemy_ids)
    for client_id, friend, enemy in zip(game.players, friend_ids, enemy_ids):
        event = NewRelationships(targets=[client_id],
                                 friend_client_id=friend, enemy_client_id=enemy)
        game.apply_event(event)
        responses.append(event)

    # Выдаём каждому по припасу
    supply_enum_names = random.choices(SuppliesEnum._member_names_, k=len(game.players))
    for name, client_id in zip(supply_enum_names, game.players):
        supply = SuppliesEnum[name].value
        event = NewSupplies(targets=[client_id], supplies=[supply])
        game.apply_event(event)
        responses.append(event)


    # Утренняя подготовка
    game.create_supply_stash()
    game.reset_turn_order()
    game.change_turn()
    responses.append(TurnChange(new_active_player=game.active_player))
    responses.append(SupplyShowcase(targets=[game.active_player], supply_stash=game.supply_stash))

    return responses


@playerevent
def take_supply(game: Game, event: TakeSupply):
    if game.active_player != event.client_id:
        raise HTTPException(403, f"Client {event.client_id} cannot take supplies from supply " +
                            "stash: It is not his turn yet")

    game.apply_event(event)

    game.change_turn()

    if game.active_player is None:
        # Переходим на день
        response = PhaseChange(new_phase=GamePhase.Day)
        game.apply_event(response)
        return [response]
    else:
        return [
            TurnChange(new_active_player=game.active_player),
            SupplyShowcase(targets=[game.active_player], supply_stash=game.supply_stash)
        ]