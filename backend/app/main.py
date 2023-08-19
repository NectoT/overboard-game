from contextlib import asynccontextmanager
import asyncio
from typing import Annotated, Awaitable
import random

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Cookie, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo.database import Database
from pymongo import MongoClient
from pydantic import BaseModel, ValidationError

from .models import *
from .databases import mongo_db as db
from . import websocket_connections


@asynccontextmanager
async def lifespan(app: FastAPI):
    # На время разработки это актуально, в рабочем коде этого явно быть не должно
    generate_ts_models("C:/Users/nectot/Desktop/overboard/frontend/src/lib/gametypes.ts")

    yield


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(websocket_connections.router)


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