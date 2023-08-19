import asyncio
from typing import Awaitable, Annotated

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from pydantic import ValidationError

from .databases import mongo_db as db
from .models import *

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
            websocket = self.websockets[client_id]
            asyncio.create_task(websocket.close(reason=reason))

        self.websockets[client_id] = websocket
        await self._handle_socket(client_id)

    async def close_all(self, reason: str | None = None):
        '''Закрывает все соединения Менеджера'''
        coroutines = []
        for client_id in self.websockets:
            coroutines.append(self.websockets[client_id].close(reason=reason))
        await asyncio.gather(*coroutines)
        self.websockets.clear()

    async def send(self, event: GameEvent) -> None:
        '''
        Отправляет игровое событие, инициируемое сервером, всем клиентам-игрокам, подключенным
        к этой игре
        '''
        coroutines = []
        for client_id in self.websockets:
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

                game_document = db['games'].find_one({'id': self.game_id})
                game: Game = Game.construct(**game_document)

                if isinstance(event, PlayerConnect) and event.client_id in game.players:
                    continue
                else:
                    db['games'].update_one({'id': self.game_id}, event.as_mongo_update())

                if (isinstance(event, PlayerConnect) and game.host is None):
                    # Первый подключившийся к бесхозной игре становится её хостом
                    host_event = HostChange(new_host=event.client_id)
                    db['games'].update_one({'id': self.game_id}, host_event.as_mongo_update())
                    await self.send(host_event)


                coroutines = []
                for key in self.websockets:
                    if client_id != key:
                        coroutines.append(
                            self.websockets[key].send_json(event.dict())
                        )
                await asyncio.gather(*coroutines)

            except (AttributeError, ValidationError) as e:
                await self.websockets[client_id].send_json(
                    SocketError(message=str(e)).dict()
                )
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