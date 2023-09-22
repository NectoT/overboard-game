import re
from typing import Any, Callable, Union, get_origin, get_args
from types import UnionType
from inspect import signature, Signature
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


class playerevent:
    '''
        Декоратор, маркирующий функцию как обработчик игрового события от игрока.
        Для каждого типа игрового события может быть только одна функция с этим декоратором

        #### Функции с данным декоратором изменяют игру в базе данных

        Функции с этим декоратором используются методом `handle_player` для обработки события
        того же типа

        Функции с этим декоратором добавляются как путь в FastAPI `router`.
    '''

    handlers: dict[str, 'playerevent'] = {}
    '''Словарь с обработчиками событий, где ключ - это тип события в виде строки'''

    response_events: tuple[type[GameEvent]]
    '''Все потенциальные ответные события'''

    event_type: type[GameEvent]
    '''Тип события, которое обрабатывает функция. Определяется через аннотации параметров'''

    def _set_response_events(self, sig: Signature) -> None:
        # Смотрим на ответные события или их отсутствие
        return_annotation = sig.return_annotation
        if return_annotation == Signature.empty or return_annotation is None:
            self.response_events = tuple()
            return


        # Разбираемся с потенциальным юнионом
        if get_origin(return_annotation) in [Union, UnionType]:
            args = get_args(return_annotation)
            if len(args) > 2:
                raise TypeError(f'Too many union options for "{self._handler.__name__}".')
            return_annotation = args[0] if args[0] is not None else args[1]

        if return_annotation is not None:
            error_msg = (f'Wrong annotation for "{self._handler.__name__}": player event handlers ' +
                        'can only return None or a list of game events.')
            if get_origin(return_annotation) is not list:
                raise TypeError(error_msg)
            for arg in get_args(return_annotation):
                if not hasattr(arg, 'mro') or GameEvent not in arg.mro():
                    raise TypeError(error_msg)

        self.response_events = get_args(return_annotation)

    def _set_event_type(self, sig: Signature):
        event_type = None

        for key in sig.parameters:
            hint = sig.parameters[key].annotation
            if hasattr(hint, 'mro') and PlayerEvent in hint.mro():
                event_type: type = hint
                break
        if event_type is None:
            # Не нашли, где событие подают
            raise TypeError(f'Cannot define "{self._handler.__name__}" as player event handler: ' +
                                'Player event type could not be identified. \nMake sure that ' +
                                'there is a type hint for event argument, and that the ' +
                                'hinted type inherits PlayerEvent')
        self.event_type = event_type

    def _add_fastapi_route(self):
        router_name = re.sub(r'[A-Z]', r' \g<0>', self.event_type.__name__)
        if self._handler.__doc__ is not None:
            description = self._handler.__doc__
        else:
            description = self.event_type.__doc__

        @router.post(
        '/' + self.event_type.__name__.lower(),
        name=router_name,
        description=description,
        status_code=200
        )
        def fastapi_route(game_id: int, event: self.event_type) -> dict:
            # Такие post-запросы можно использовать, только если все игроки пользуются post-запросами
            # и поллингом get_game (или как там называется функция), потому что ответные события в
            # случае пост-запроса не высылаются
            game = Game(**db['games'].find_one({'id': game_id}))
            responses = self._handler(game, event)
            game.save_changes(db['games'])
            return {}

    def __init__(self, handler: Callable[[Game, PlayerEvent], list[GameEvent] | None]) -> None:
        self._handler = handler

        sig = signature(handler)

        self._set_response_events(sig)

        self._set_event_type(sig)

        self._add_fastapi_route()

        playerevent.handlers[self.event_type.__name__] = self

    def __call__(self, game_id: int, event: GameEvent) -> list[GameEvent] | None:
        game = Game(**db['games'].find_one({'id': game_id}))
        responses = self._handler(game, event)
        game.save_changes(db['games'])
        return responses


def handle_player(game_id: int, event: PlayerEvent) -> list[GameEvent]:
    '''
    Автоматически подбирает и вызывает обработчик для игрового события игрока.

    @game_id: Идентификатор игры, для которой предназначено событие

    :returns: Ответное игровое событие, предназначенное игрокам или None

    :raises TypeError: Не найден обработчик для переданного типа игрового события
    '''
    if event.type in playerevent.handlers:
        return playerevent.handlers[event.type](game_id, event)

    raise TypeError(f'No event handler for {event.type} is available')


def get_game(game_id: int) -> Game:
    game_document = db['games'].find_one({'id': game_id})
    return Game(**game_document)


@playerevent
def on_player_connect(game: Game, event: PlayerConnect) -> list[HostChange] | None:
    if event.player_id not in game.players:
        game.apply_event(event)

    if isinstance(event, PlayerConnect) and game.host is None:
        # Первый подключившийся к бесхозной игре становится её хостом
        host_event = HostChange(new_host=event.player_id)
        game.apply_event(host_event)
        return [host_event]
    return None


@playerevent
def on_name_change(game: Game, event: NameChange):
    game.apply_event(event)


StartGameResponse = list[GameStart, NewRelationships, NewSupplies, TurnChange, SupplyShowcase]


@playerevent
def start_game(game: Game, event: StartRequest) -> StartGameResponse:

    if game.host != event.player_id:
        raise HTTPException(403, detail='Received event does not belong to game host')

    responses = []

    # Рандомно выбираем персонажей из CharacterEnum
    enum_names = random.sample(CharactersEnum._member_names_, k=len(game.players))

    assigned_characters = {}
    for name, player_id in zip(enum_names, game.players):
        assigned_characters[player_id] = CharactersEnum[name].value

    start_event = GameStart(assigned_characters=assigned_characters)
    game.apply_event(start_event)
    responses.append(start_event)

    # Назначаем друзей и врагов
    friend_ids = list(game.players)
    random.shuffle(friend_ids)
    enemy_ids = list(game.players)
    random.shuffle(enemy_ids)
    for player_id, friend, enemy in zip(game.players, friend_ids, enemy_ids):
        event = NewRelationships(targets=[player_id],
                                 friend_id=friend, enemy_id=enemy)
        game.apply_event(event)
        responses.append(event)

    # Выдаём каждому по припасу
    supply_enum_names = random.choices(SuppliesEnum._member_names_, k=len(game.players))
    for name, player_id in zip(supply_enum_names, game.players):
        supply = SuppliesEnum[name].value
        event = NewSupplies(targets=[player_id], supplies=[supply])
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
def take_supply(game: Game, event: TakeSupply) -> list[PhaseChange, TurnChange, SupplyShowcase]:
    if game.active_player != event.player_id:
        raise HTTPException(403, f"Client {event.player_id} cannot take supplies from supply " +
                            "stash: It is not his turn yet")

    game.apply_event(event)

    game.change_turn()

    if game.active_player is None:
        # Переходим на день
        response = PhaseChange(new_phase=GamePhase.Day)
        game.apply_event(response)
        game.reset_turn_order()
        game.change_turn()
        return [response, TurnChange(new_active_player=game.active_player)]
    else:
        return [
            TurnChange(new_active_player=game.active_player),
            SupplyShowcase(targets=[game.active_player], supply_stash=game.supply_stash)
        ]


@playerevent
def get_navigation(game: Game, event: NavigationRequest) -> list[NavigationsOffer]:
    if game.active_player != event.player_id:
        raise HTTPException(403, f"Client {event.player_id} cannot get navigation cards: " +
                            "it is not his turn yet")
    if game.phase != GamePhase.Day:
        raise HTTPException(403, "Cannot get navigation cards until Day phase arrives")
    if len(game.offered_navigations) != 0:
        raise HTTPException(403, f"Navigation cards are already offered to client {event.player_id}")
    if game.players[event.player_id].rowed_this_turn:
        raise HTTPException(403, "Client already rowed this turn")

    game.generate_offered_navigations()

    return [
        NavigationsOffer(targets=[event.player_id], offered_navigations=game.offered_navigations)]


@playerevent
def save_navigation(game: Game, event: SaveNavigation) -> None:
    if event.navigation in game.offered_navigations:
        game.apply_event(event)
    else:
        raise HTTPException(400)