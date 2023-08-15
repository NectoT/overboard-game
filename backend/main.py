from contextlib import asynccontextmanager
import asyncio
from typing import Annotated
import random

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Cookie, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo.database import Database
from pymongo import MongoClient
from pydantic import BaseModel

from models import *

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db
    db = MongoClient(DATABASE_URL)['overboard']
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


class Connections:
    websockets: dict[int, list[WebSocket]] = {}

    @staticmethod
    def add(game_id: Hashable, websocket: WebSocket, timeout=10) -> None:
        if game_id in Connections.websockets:
            Connections.websockets[game_id].append(websocket)
        else:
            Connections.websockets[game_id] = [websocket]

        asyncio.create_task(Connections._handle_disconnect(websocket))

    @staticmethod
    async def _handle_disconnect(websocket: WebSocket):
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                await Connections.close(websocket)


    @staticmethod
    async def close(websocket: WebSocket, reason: str | None = None) -> None:
        for game_id in Connections.websockets:
            if websocket in Connections.websockets[game_id]:
                Connections.websockets[game_id].remove(websocket)
                break
        await websocket.close(reason=reason)

    @staticmethod
    async def close_game(game_id: Hashable, reason: str | None = None) -> None:
        # Tell all the websockets connected to game to close and then await them to
        # end the connection
        coroutines = []
        for websocket in Connections.websockets[game_id]:
            coroutines.append(websocket.close(reason=reason))
        await asyncio.gather(*coroutines)

        Connections.websockets[game_id] = None

    @staticmethod
    async def send(game_id: Hashable, data) -> None:
        coroutines = []
        for websocket in Connections.websockets[game_id]:
            coroutines.append(websocket.send_json(data))
        asyncio.gather(*coroutines)


@app.websocket('/{game_id}')
def connect(game_id: int, websocket: WebSocket):
    print('testing!')
    Connections.add(game_id, websocket)
    Connections.send(game_id, 'hiiii')


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