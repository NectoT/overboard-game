from contextlib import asynccontextmanager
from typing import Annotated, Awaitable
import random

from fastapi import FastAPI, HTTPException, Cookie, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .models import *
from .models import tests
from .databases import mongo_db as db
from . import websocket_connections
from .routers import eventhandlers, schemas
from . import mkdocs
from .utils import Token


@asynccontextmanager
async def lifespan(app: FastAPI):
    # На время разработки это актуально, в рабочем коде этого явно быть не должно
    generate_ts_models("C:/Users/nectot/Desktop/overboard/frontend/src/lib/gametypes.ts")
    result = tests.run()
    if len(result.failures) > 0:
        raise AssertionError(result.failures[0][1])

    mkdocs.build()
    app.mount('/docs', StaticFiles(directory='app/mkdocs/site', html=True), '/docs')

    yield


app = FastAPI(lifespan=lifespan, openapi_tags=[eventhandlers.tag_meta], docs_url='/rest/docs')


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(websocket_connections.router)
app.include_router(eventhandlers.router)
app.include_router(schemas.router)


def game_document(game_id: int) -> dict:
    game_document = db['games'].find_one({'id': game_id})
    if game_document is None:
        raise HTTPException(422, f'Cannot find a game with id {game_id}')

    return game_document


def cookie_token(token: Annotated[str | None, Cookie()] = None) -> Token:
    return Token(token) if token is not None else None


TokenParam = Annotated[Token | None, Depends(cookie_token)]


@app.post('/create')
def create_game(
    game_id: Annotated[int, Query(description="Идентификатор для новой игры")],
    token: TokenParam
):
    '''
    Создаёт новую игру с указанным game_id.
    `game_id` должен быть уникальным, то есть не использоваться в других играх.

    \f
    @token: Идентификатор клиента, создающего игру.
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


class PlayerIdModel(BaseModel):
    id: str


@app.get('/playerid')
def player_id(token: TokenParam) -> PlayerIdModel:
    '''Возвращает id игрока, принадлежащий клиенту с переданным токеном'''
    return PlayerIdModel(id=token.hash())


@app.get('/{game_id:int}/info')
def game_info(game_document: Annotated[dict, Depends(game_document)]) -> GameInfo:
    '''Возвращает основную информацию об игре'''

    return GameInfo(**game_document)


@app.get('/{game_id:int}')
def game(game_document: Annotated[dict, Depends(game_document)], token: TokenParam) -> Game:
    '''
    Возвращает информацию об игре, доступную клиенту с токеном-идентификатором.
    Если токен не передаётся, то возвращается информация, доступная наблюдателям.
    '''
    game = Game(**game_document)
    player_id = token.hash()
    if player_id in game.players:
        game = Game.with_player_view(game, player_id)
    else:
        game = Game.with_spectator_view(game)

    return game