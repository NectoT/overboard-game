import asyncio
from typing import Awaitable, Annotated

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from pydantic import ValidationError

from .databases import mongo_db as db
from .models import *
from .routers.eventhandlers import handle_player

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


    async def add(self, websocket: WebSocket, client_id: str) -> Awaitable[None]:
        '''
        Устанавливает по переданному вебсокету соединение с клиентом с идентификатором `client_id.
        Разрывает предыдущее соединение, если оно было.

        :returns: Awaitable, который завершается при отключении соединения.
        #### Если не ждать этот метод, соединение сразу прервётся
        '''
        await websocket.accept()
        if client_id in self.websockets:
            reason = "Client made a new websocket connection"
            await self.websockets[client_id].close(reason=reason)

        self.websockets[client_id] = websocket
        await self._handle_socket(client_id)

    async def close_all(self, reason: str | None = None):
        '''Закрывает все соединения Менеджера'''
        coroutines = []
        for client_id in self.websockets:
            coroutines.append(self.websockets[client_id].close(reason=reason))
        await asyncio.gather(*coroutines)
        self.websockets.clear()

    async def send(self, event: GameEvent | ObservableEvent, from_player: str | None = None) -> None:
        '''
        Отправляет игровое событие, всем, кому оно предназначено

        Определяет, кому оно предназначено с помощью `event.targets`.
        Если это `Observable` с точки зрения наблюдателя, отправляет событие всем, кто не указан в
        `event.targets`.

        @from_player: Идентификатор игрока, от которого было изначально получено событие. `None`, если событие создано сервером
        '''

        ids = ()
        if isinstance(event, ObservableEvent) and event.observed:
            # Это событие с точки зрения наблюдателя, значит надо посылать всем, кто не в targets
            if event.targets == EventTargets.All:
                pass  # Это событие предназначалось всем, все о нём уже знают
            elif event.targets == EventTargets.Server:
                ids = set(self.websockets.keys())
                # from_player не должен быть None, ведь на сервер посылает событие игрок
                ids.remove(from_player)
            else:
                ids = set(self.websockets.keys()).difference(set(event.targets))
        else:
            # Это обычное событие
            if event.targets == EventTargets.All:
                ids = set(self.websockets.keys())
                if from_player is not None:
                    ids.remove(from_player)
            elif event.targets == EventTargets.Server:
                pass  # Событие предназначалось только для сервера, никому пересылать не надо
            else:
                ids = event.targets

        coroutines = []
        for client_id in ids:
            if client_id not in self.websockets:
                continue  # Мало ли фейковых id переслали с событием
            coroutines.append(self.websockets[client_id].send_json(event.dict()))
        await asyncio.gather(*coroutines)

    async def _handle_socket(self, client_id: str):
        '''
        Обрабатывает соединение с вебсокетом, привязанного к `client_id`
        на момент вызова метода.
        '''
        while True:
            try:
                json: dict = await self.websockets[client_id].receive_json()
                event: PlayerEvent = PlayerEvent.from_dict(json)

                # Сначала обрабатываем событие, чтобы не пересылать событие,
                # которое оказалось неверным
                response_events = handle_player(self.game_id, event)

                # пересылаем событие всем, кому нужно
                await self.send(event, from_player=client_id)

                # Отсылаем ответные событие от сервера, если они есть
                if response_events is not None:
                    for event in response_events:
                        await self.send(event)

                        # Если это видимое другим событие, посылаем им изменённый вариант события
                        if isinstance(event, ObservableEvent):
                            await self.send(event.observer_viewpoint())

            except (AttributeError, TypeError, ValidationError, HTTPException) as e:
                await self.websockets[client_id].close(reason=str(e))
                raise e
            except WebSocketDisconnect:
                del self.websockets[client_id]
                break


@router.websocket('/{game_id}')
async def connect(game_id: int, websocket: WebSocket, client_id: Annotated[str, Query()]):
    '''
    Подключает вебсокет от игрока к серверу.

    @game_id: Идентификатор игры, к которой подключается клиент
    @client_id: Уникальный идентификатор, определяющий клиента. При разрыве предыдущего
    вебсокета и создании нового с тем же `client_id`, сервер понимает, что новый вебсокет
    принадлежит тому же клиенту
    '''
    if game_id in GameManager.managed_games:
        manager = GameManager.managed_games[game_id]
    else:
        manager = GameManager.create(game_id)
    await manager.add(websocket, client_id)