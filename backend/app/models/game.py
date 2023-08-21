from enum import Enum

from pydantic import BaseModel

class GameViewpoint(str, Enum):
    Player = 'Player'
    Spectator = 'Spectator'


class GameInfo(BaseModel):
    id: int
    started: bool = False


class Player(BaseModel):
    name: str = None


class Game(BaseModel):
    '''
    Модель, отображающая состояние игры. В зависимости от `viewpoint` часть информации
    скрывается или искажается.

    #### Это всего лишь модель, само состояние игры хранится в базе данных
    '''
    id: int
    started: bool = False
    players: dict[str, Player] = {}
    host: str = None
    '''Идентификатор игрока, который является хостом'''

    viewpoint: GameViewpoint = None
    '''
    Точка зрения, которую занимает модель.

    То есть, если `viewpoint = None`, то состояние
    игры представлено полно и объективно. Если `viewpoint = GameViewpoint.Player`,
    то в объекте будет представлена только та информация об игре,
    которая доступна игроку с идентификатором `viewpoint_cliend_id`.
    '''
    viewpoint_client_id: str = None
    '''
    Если `viewpoint = GameViewpoint.Player`, то это поле указывает, какому именно игроку
    соответствует эта точка зрения
    '''

    @staticmethod
    def with_player_view(game: 'Game | dict', client_id: str) -> 'Game':
        '''
        Возвращает состояние игры с точки зрения игрока с идентификатором `client_id`.

        @game: Состояние игры.
        '''
        if isinstance(game, Game):
            new_game = game.copy() # new потому что новый объект
        else:
            new_game = Game.construct(**game) # new потому что новый объект

        #TODO

        return new_game

    @staticmethod
    def with_spectator_view(game: 'Game | dict') -> 'Game':
        '''
        Возвращает состояние игры с точки зрения наблюдателя.

        @game: Состояние игры.
        '''
        if isinstance(game, Game):
            new_game = game.copy() # new потому что новый объект
        else:
            new_game = Game.construct(**game) # new потому что новый объект

        #TODO

        return new_game