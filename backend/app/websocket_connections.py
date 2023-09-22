import asyncio
from typing import Awaitable, Annotated

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from pydantic import ValidationError

from .databases import mongo_db as db
from .models import *
from .routers.eventhandlers import handle_player
from .utils import Token

router = APIRouter(tags=['Websocket Connection'])


class GameManager:
    '''Менеджер соединений для игры'''

    # Ну как бы вне класса managed_games не должен меняться, но мне кажется, что
    # делать обёртку и проперти, копирующий внутренний словарь это слишком дорогостояще.
    # Думаю и так понятно, что менять его не стоит
    managed_games: dict[int, 'GameManager'] = {}
    '''
    Словарь всех созданных менеджеров соединений через метод `GameManager.create`,
    где идентификатор игры - это ключ
    '''

    def __init__(self, game_id: int) -> None:
        '''Менеджер соединений, связанных с игрой с идентификатором `game_id`'''
        self.game_id = game_id
        self.websockets: dict[str, WebSocket] = {}

    @staticmethod
    def create(game_id: int) -> 'GameManager':
        '''
        Создаёт менеджера соединений для игры с идентификатором `game_id` и сохраняет доступ к
        нему в `GameManager.managed_games`
        '''
        if game_id in GameManager.managed_games:
            raise AttributeError(f'There is already a game manager for game with {game_id} id')

        manager = GameManager(game_id)
        GameManager.managed_games[game_id] = manager
        return manager


    async def add(self, websocket: WebSocket, player_id: str) -> Awaitable[None]:
        '''
        Устанавливает по переданному вебсокету соединение с клиентом с идентификатором `player_id.
        Разрывает предыдущее соединение, если оно было.

        :returns: Awaitable, который завершается при отключении соединения.
        #### Если не ждать этот метод, соединение сразу прервётся
        '''
        await websocket.accept()
        if player_id in self.websockets:
            reason = "Client made a new websocket connection"
            await self.websockets[player_id].close(reason=reason)

        self.websockets[player_id] = websocket
        await self._handle_socket(player_id)

    async def close_all(self, reason: str | None = None):
        '''Закрывает все соединения Менеджера'''
        coroutines = []
        for player_id in self.websockets:
            coroutines.append(self.websockets[player_id].close(reason=reason))
        await asyncio.gather(*coroutines)
        self.websockets.clear()

    async def send(self, event: GameEvent | ObservableEvent, from_player: str | None = None) -> None:
        '''
        Отправляет игровое событие, всем, кому оно предназначено

        Определяет, кому оно предназначено с помощью `event.targets`.
        Если это `Observable`, пересылает тем, кто указан в `event.targets` полное событие,
        остальным - со скрытой информацией

        @from_player: Идентификатор игрока, от которого было изначально получено событие. `None`, если событие создано сервером
        '''

        all_players = set(self.websockets.keys())

        ids: set[str] = set()

        if event.targets == EventTargets.All:
            ids = all_players.copy()
            ids.discard(from_player)
        elif event.targets == EventTargets.Server:
            pass  # Событие предназначалось только для сервера, никому пересылать не надо
        else:
            ids = set(event.targets)

        coroutines = []

        for player_id in ids:
            if player_id not in self.websockets:
                continue  # Мало ли фейковых id переслали с событием
            coroutines.append(self.websockets[player_id].send_json(event.dict()))

        if isinstance(event, ObservableEvent):
            # Пересылаем событие наблюдателям
            observers = all_players.difference(ids)
            observers.discard(from_player)
            for player_id in observers:
                observed_event = event.observer_viewpoint()
                coroutines.append(self.websockets[player_id].send_json(observed_event.dict()))

        await asyncio.gather(*coroutines)

    async def _handle_socket(self, player_id: str):
        '''
        Обрабатывает соединение с вебсокетом, привязанного к `player_id`
        на момент вызова метода.
        '''
        while True:
            try:
                json: dict = await self.websockets[player_id].receive_json()
                event: PlayerEvent = PlayerEvent.from_dict(json)

                # Сначала обрабатываем событие, чтобы не пересылать событие,
                # которое оказалось неверным
                response_events = handle_player(self.game_id, event)

                # пересылаем событие всем, кому нужно
                await self.send(event, from_player=player_id)

                # Отсылаем ответные событие от сервера, если они есть
                if response_events is not None:
                    for event in response_events:
                        await self.send(event)

            except (AttributeError, TypeError, ValidationError, HTTPException) as e:
                await self.websockets[player_id].close(reason=str(e))
                del self.websockets[player_id]
                raise e
            except WebSocketDisconnect:
                del self.websockets[player_id]
                break


@router.websocket('/{game_id}')
async def connect(game_id: int, websocket: WebSocket, token: Annotated[str, Query()]):
    '''
    Подключает вебсокет от игрока к серверу.

    @game_id: Идентификатор игры, к которой подключается клиент
    @token: Токен, определяющий клиента. При разрыве предыдущего
    вебсокета и создании нового с тем же токеном, сервер понимает, что новый вебсокет
    принадлежит тому же клиенту
    '''
    if game_id in GameManager.managed_games:
        manager = GameManager.managed_games[game_id]
    else:
        manager = GameManager.create(game_id)
    await manager.add(websocket, Token(token).hash())