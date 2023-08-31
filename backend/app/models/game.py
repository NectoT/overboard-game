from enum import Enum, auto

from pydantic import BaseModel

from .ts_transpilers import model_to_ts_class


class ModelEnum(Enum):
    @property
    def value(self):
        '''Возвращает копию значения, хранимого в enum'''
        return type(super().value).construct(**super().value.dict())


class UNKNOWN(BaseModel):
    '''
    У поля есть значение в базе данных, но для модели оно неизвестно.

    ### Пример
    В игре с точки зрения игрока A у игрока Б значение supplies равно [UNKNOWN, UNKNOWN].
    Это означает, что у игрока Б есть две карты припасов, хранящихся в базе данных, но игроку A
    они неизвестны
    '''

class Observable(BaseModel):
    '''
    Модель, часть информации которой доступна не всем игрокам.

    Информация, которая может быть недоступна, помечается дополнительным типом `UNKNOWN`.

    ### Пример
    Поле `Player.supplies` должно быть известно только тому игроку, которому принадлежат припасы,
    поэтому модель `Player` является Observable, а тип поля - `list[Supply | UNKNOWN]`
    '''
    observed: bool = False
    '''Если True, то модель отображает точку зрения наблюдателя'''

    def observer_viewpoint(self) -> 'Observable':
        '''Возвращает модель с точки зрения наблюдателя'''
        changed_values: dict = self._observer_diff()
        changed_values['observed'] = True
        copy = self.copy(update=changed_values)

        # BaseModel что-то делает с __setattr__, и при попытке переопределить метод
        # через переадресацию он делает этот метод полем в модели. Ну и бред
        # object.__setattr__(copy, 'as_mongo_update', self._as_mongo_update)

        return copy

    def _observer_diff(self) -> dict[str, any]:
        '''
        Поля, которые должны быть скрыты или изменены для наблюдателя.

        Используется в `observer_viewpoint`.
        '''
        diff = {}
        for name in self.__fields__:

            field = self.__fields__[name]
            value = self.__getattribute__(name)

            # По идее если у аннотации есть __args__, то это означает, что это type hint, который
            # принимает несколько разных типов
            if hasattr(field.type_, '__args__') and UNKNOWN in field.type_.__args__:
                if isinstance(value, list):
                    diff[name] = [UNKNOWN() for el in value]
                elif isinstance(value, dict):
                    diff[name] = {}
                    for key in value:
                        diff[name][key] = UNKNOWN()
                else:
                    diff[name] = UNKNOWN()
            # Разбираемся с Observable-полями
            elif isinstance(value, Observable):
                diff[name] = value.observer_viewpoint()
            elif isinstance(value, list):
                diff[name] = [
                    el.observer_viewpoint() if isinstance(el, Observable) else el for el in value
                ]
            elif isinstance(value, dict):
                diff[name] = {}
                for key in value:
                    if isinstance(value[key], Observable):
                        diff[name][key] = value[key].observer_viewpoint()
                    else:
                        diff[name][key] = value[key]

        if len(diff) == 0:
            raise RuntimeWarning(
                'No changes could be made when converting Observable to observer viewpoint. ' +
                'You might want to override `_observer_diff` or `observer_viewpoint`'
            )

        return diff

    @classmethod
    def as_ts_class(cls, export=True):
        observed_property = cls.schema()['properties']['observed']
        fields = {'observed': 'true' if observed_property["default"] else 'false'}

        return model_to_ts_class(cls, default_fields=fields, export=export)


class GameViewpoint(str, Enum):
    Player = 'Player'
    Spectator = 'Spectator'


class GameInfo(BaseModel):
    id: int
    started: bool = False


class Character(BaseModel):
    name: str
    '''Уникальное имя персонажа'''
    attack: int
    health: int
    survival_bonus: int
    '''Бонус за выживание до конца игры'''
    order: int
    '''На каком месте в лодке сидит персонаж, где 1 - самое близкое место к носу лодки'''


class CharactersEnum(ModelEnum):
    '''Энумератор с шаблонами персонажей.'''

    LADY = Character(name="Lady", attack=4, health=4, survival_bonus=8, order=1)
    DUKE = Character(name="Duke", attack=5, health=5, survival_bonus=7, order=2)
    CAPTAIN = Character(name="Captain", attack=7, health=7, survival_bonus=5, order=3)
    CHAD = Character(name="Chad", attack=8, health=8, survival_bonus=4, order=4)
    ROWER = Character(name="Rower", attack=6, health=6, survival_bonus=6, order=5)
    KIDDO = Character(name="Kiddo", attack=3, health=3, survival_bonus=9, order=6)


class Supply(BaseModel):
    # Припасы в За Бортом ведут себя очень по-разному, поэтому нецелесообразно пытаться все их
    # особенности выразить через модель. Вместо этого у них есть уникальный тип, который
    # определяет, что в коде делать с таким-то припасом (как на фронте, так и на бэке).
    # Тем не менее, такие вещи, как оружие и сокровища не являются уникальными, и легче хранить
    # их параметры напрямую в модели.
    # Если бы не эти параметры, можно было бы ограничиться enum-ом

    type: str
    '''Тип припаса. Каждый тип по-своему влияет на состояние игры'''
    strength: int = None
    '''Сила оружия. Припас считается оружием, если сила не равна `None`'''
    points: int = 0
    '''Ценность припаса.'''


class SuppliesEnum(ModelEnum):
    MEDKIT = Supply(type="medkit")
    SHARK_BAIT = Supply(type="shark_bait")


class Player(Observable):
    name: str = None
    character: Character = None
    supplies: list[Supply | UNKNOWN] = []
    friend: str = None
    '''Идентификатор клиента, который является другом'''
    enemy: str = None
    '''Идентификатор клиента, который является врагом'''


class GamePhase(int, Enum):
    Lobby = auto()
    '''Игра ещё не началась'''
    Morning = auto()
    '''Фаза раздачи припасов'''
    Day = auto()
    Evening = auto()


class Game(Observable):
    '''
    Модель, отображающая состояние игры. В зависимости от `viewpoint` часть информации
    скрывается или искажается.

    #### Это всего лишь модель, само состояние игры хранится в базе данных
    '''
    id: int
    players: dict[str, Player] = {}
    host: str = None
    '''Идентификатор игрока, который является хостом'''

    phase: GamePhase = GamePhase.Lobby
    '''Текущая фаза игры'''

    supply_stash: list[Supply | UNKNOWN] = []
    '''Припасы, найденные в утреннюю фазы игры и разбираемые игроками этим же утром'''

    active_player: str = None
    '''
    Идентификатор игрока, который сейчас ходит
    '''

    player_turn_queue: list[str] = []
    '''Очередь игроков, ждущих свой ход в текущей фазе'''

    @staticmethod
    def with_player_view(game: 'Game | dict', client_id: str) -> 'Game':
        '''
        Возвращает состояние игры с точки зрения игрока с идентификатором `client_id`.

        @game: Состояние игры.
        '''
        if isinstance(game, dict):
            game = Game(**game)

        new_game: Game = game.observer_viewpoint()
        new_game.players[client_id] = game.players[client_id]

        if client_id == game.active_player:
            new_game.supply_stash = list(game.supply_stash)

        return new_game

    @staticmethod
    def with_spectator_view(game: 'Game | dict') -> 'Game':
        '''
        Возвращает состояние игры с точки зрения наблюдателя.

        @game: Состояние игры.
        '''
        if isinstance(game, dict):
            game = Game.construct(**game)

        return game.observer_viewpoint()