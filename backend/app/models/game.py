import random
from enum import Enum, auto
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel
from pymongo.collection import Collection

if TYPE_CHECKING:
    from .base_events import GameEvent


class ModelEnum(Enum):
    '''Enum, значениями которого являются pydantic модели'''
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


class Navigation(BaseModel):
    '''Карта навигации'''

    bird_info: Literal['exed', 'missing', 'present']
    '''
    Информация о чайках.

    ### Возможные значения:

    - `exed` - Перечёркнутая чайка. Сыгранная карта навигации с таким значением уберёт одну из чаек

    - `missing` - Чайки нет на карте навигации

    - `present` - На карте навигации есть чайка - сыгранная карта навигации добавит чайку в игре
    '''

    overboard: list[str]
    '''Список идентификаторов игроков, которые падают за борт'''

    thirsty_players: list[str]
    '''Список идентификаторов игроков, на которых накладывается жажда в любом случае'''

    thirst_actions: list[Literal['row', 'fight']]
    '''Игрок получит жажду, совершив любое действие из списка'''



class Player(Observable):
    name: str = None
    character: Character = None
    supplies: list[Supply | UNKNOWN] = []
    friend: str = None
    '''Идентификатор клиента, который является другом'''
    enemy: str = None
    '''Идентификатор клиента, который является врагом'''
    rowed_this_turn: bool = False


class GamePhase(str, Enum):
    Lobby = 'lobby'
    '''Игра ещё не началась'''
    Morning = 'morning'
    '''Фаза раздачи припасов'''
    Day = 'day'
    Evening = 'evening'


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

    navigation_stash: list[Navigation | UNKNOWN] = []
    '''Карты навигации, отложенные для выбора вечером'''

    offered_navigations: list[Navigation | UNKNOWN] = []
    '''Карты навигации, из которых активный игрок выбирает одну'''

    active_player: str = None
    '''
    Идентификатор игрока, который сейчас ходит
    '''

    player_turn_queue: list[str] = []
    '''Очередь игроков, ждущих свой ход в текущей фазе'''

    def apply_event(self, event: 'GameEvent'):
        '''Применяет переданные событием изменения к игре'''
        event.apply_to_game(self)

    def reset_turn_order(self):
        '''Заново создаёт очередь ходов игроков и сохраняет изменения в базе данных'''
        self.player_turn_queue = sorted(
            self.players.keys(), key=lambda id: self.players[id].character.order)

    def change_turn(self):
        '''
        Передаёт ход другому игроку и записывает изменение в базе данных
        '''
        if len(self.player_turn_queue) != 0:
            self.active_player = self.player_turn_queue.pop(0)
        else:
            self.active_player = None

    def create_supply_stash(self):
        '''Создаёт утренние припасы и добавляет их в игру в базе данных'''
        self.supply_stash: list[Supply] = random.choices(
            [e.value for e in SuppliesEnum], k=len(self.players))

    def generate_offered_navigations(self):
        '''Генерирует карты навигации, которые будут предложены активному игроку'''
        self.offered_navigations = []
        for i in range(2):
            thirst_actions = []
            if random.random() > 0.5:
                thirst_actions.append('row')
            if random.random() > 0.5:
                thirst_actions.append('fight')

            thirst_mode = random.choices(('none', 'all_except', 'only'), weights=(1, 2, 2))[0]
            if thirst_mode == 'none':
                thirsty_players = []
            elif thirst_mode == 'all_except':
                thirsty_players = list(self.players.keys())  # TEMP
            elif thirst_mode == 'only':
                thirsty_players = random.sample(list(self.players.keys()), k=random.randint(1, 2))

            overboard_mode = random.choices(('none', 'one', 'all'), weights=(1, 10, 1))[0]
            if overboard_mode == 'none':
                overboard = []
            elif overboard_mode == 'all':
                overboard = list(self.players.keys())
            elif overboard_mode == 'one':
                overboard = [random.choice(list(self.players.keys()))]

            bird = random.choices(('exed', 'missing', 'present'), (0.1, 5, 1))[0]

            navigation = Navigation(
                bird_info=bird,
                overboard=overboard,
                thirsty_players=thirsty_players,
                thirst_actions=thirst_actions
            )
            self.offered_navigations.append(navigation)


    def save_changes(self, mongo_collection: Collection):
        if self.observed:
            raise AttributeError('Cannot save game from observer viewpoint')

        curr_document = mongo_collection.find_one({'id': self.id})
        model_dict = self.dict()

        changes = {}
        for name in model_dict:
            if name not in curr_document or curr_document[name] != model_dict[name]:
                changes[name] = model_dict[name]
        mongo_collection.update_one({'id': self.id}, {'$set': changes})

    @staticmethod
    def with_player_view(game: 'Game | dict', player_id: str) -> 'Game':
        '''
        Возвращает состояние игры с точки зрения игрока с идентификатором `player_id`.

        @game: Состояние игры.
        '''
        if isinstance(game, dict):
            game = Game(**game)

        new_game: Game = game.observer_viewpoint()
        new_game.players[player_id] = game.players[player_id]

        if player_id == game.active_player:
            new_game.supply_stash = game.supply_stash
            new_game.offered_navigations = game.offered_navigations
            new_game.navigation_stash = game.navigation_stash

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