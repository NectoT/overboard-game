from contextlib import asynccontextmanager
import asyncio
from typing import Annotated
import random

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Cookie, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo.database import Database
from pymongo import MongoClient
from pydantic import BaseModel, ValidationError

from models import *

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db
    db = MongoClient(DATABASE_URL)['overboard']

    # На время разработки это актуально, в рабочем коде этого явно быть не должно
    generate_ts_models("C:/Users/nectot/Desktop/overboard/frontend/src/lib/gametypes.ts")

    yield

app = FastAPI(lifespan=lifespan)

DATABASE_URL = 'localhost'
db: Database = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

        GameManager.managed_games

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

    def add(self, websocket: WebSocket, client_id: str) -> None:
        '''Добавляет или заменяет соединение клиента с идентификатором `client_id`'''
        if client_id in self.websockets:
            reason = "Client made a new websocket connection"
            asyncio.create_task(self.websockets[client_id].close(reason=reason))

        self.websockets[client_id] = websocket
        asyncio.create_task(self._handle_socket(client_id))

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
            coroutines.append(self.websockets[client_id].send_json(event.json()))
        asyncio.gather(*coroutines)

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
                game = Game.construct(game_document)
                game.apply(event)


                for key in self.websockets:
                    if client_id != key:
                        asyncio.create_task(self.websockets[key].send_json(event.dict()))

            except AttributeError | ValidationError as e:
                await self.websockets[client_id].send_json(
                    SocketError(message=str(e)).dict()
                )
            except WebSocketDisconnect:
                self.websockets[client_id] = None
                break


@app.websocket('/{game_id}')
def connect(game_id: int, websocket: WebSocket, client_id: str):
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
    manager.add(websocket, client_id)


@app.post('/{game_id}/start')
def start_game(game_id: int):
    pass


@app.post('/create')
def create_game(
    game_id: Annotated[int, Query(description="Идентификатор для новой игры")],
    client_id: Annotated[str, Cookie(description="Идентификатор клиента-игрока, создающего игру")]
):
    '''
    Создаёт новую игру с указанным game_id.
    `game_id` должен быть уникальным, то есть не использоваться в других играх.

    \f
    @client_id: Идентификатор клиента-игрока, создающего игру.
    '''
    if db['games'].find_one({'id': game_id}) is not None:
        raise HTTPException(400, detail=f"Game with {game_id} id already exists")
    db['games'].insert_one(Game(id=game_id).dict())


class UniqueId(BaseModel):
    game_id: int


@app.get('/uniqueid')
def free_id() -> UniqueId:
    '''Возвращает id, не используемый ни в каких активных играх'''
    while True:
        game_id = random.randint(10000, 99999)
        if db['games'].find_one({'id': game_id}) is None:
            return UniqueId(game_id=game_id)


@app.get('/{game_id}/info')
def game_info(game_id: int) -> GameInfo:
    '''Возвращает основную информацию об игре'''
    document = db['games'].find_one({'id': game_id})
    if document is None:
        raise HTTPException(404, detail=f"Game with {game_id} id was not found")

    game: Game = Game(**document)

    return game


@app.get('/{game_id}')
def game(game_id: int, client_id: Annotated[str | None, Cookie()] = None) -> Game:
    '''
    Возвращает информацию об игре, доступную клиенту с идентификатором `client_id`.
    Если `client_id` не передаётся, то возвращается информация, доступная наблюдателям.
    '''
    game_document = db['games'].find_one({'id': game_id})
    if game_document is None:
        raise HTTPException(422, f'Cannot find a game with id {game_id}')
    game = Game.construct(**game_document)
    if client_id is not None and client_id in game.players:
        game = Game.with_player_view(game, client_id)
    else:
        game = Game.with_spectator_view(game)

    return game