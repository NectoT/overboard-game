/** Автосгенерирован функцией generate_ts_models в модуле app.models */

export enum GamePhase {
	Lobby = 1,
	Morning = 2,
	Day = 3,
	Evening = 4,
};

/** 
    Модель, отображающая состояние игры. В зависимости от `viewpoint` часть информации
    скрывается или искажается.

    #### Это всего лишь модель, само состояние игры хранится в базе данных
     */
export class Game {
	observed: boolean;
	id: number;
	players: { [key: string]: Player };
	host?: string;
	phase: any;
	supply_stash: Array<Supply | UNKNOWN>;
	navigation_stash: Array<Navigation | UNKNOWN>;
	offered_navigations: Array<Navigation | UNKNOWN>;
	active_player?: string;
	player_turn_queue: Array<string>;
	constructor(id: number, players: { [key: string]: Player }, phase: any, supply_stash: Array<Supply | UNKNOWN>, navigation_stash: Array<Navigation | UNKNOWN>, offered_navigations: Array<Navigation | UNKNOWN>, player_turn_queue: Array<string>, observed = false, host?: string, active_player?: string, ) {
		this.observed = observed;
		this.id = id;
		this.players = players;
		this.host = host;
		this.phase = phase;
		this.supply_stash = supply_stash;
		this.navigation_stash = navigation_stash;
		this.offered_navigations = offered_navigations;
		this.active_player = active_player;
		this.player_turn_queue = player_turn_queue;
	}
};

/** 
    Модель, часть информации которой доступна не всем игрокам.

    Информация, которая может быть недоступна, помечается дополнительным типом `UNKNOWN`.

    ### Пример
    Поле `Player.supplies` должно быть известно только тому игроку, которому принадлежат припасы,
    поэтому модель `Player` является Observable, а тип поля - `list[Supply | UNKNOWN]`
     */
export class Observable {
	observed: boolean;
	constructor(observed = false, ) {
		this.observed = observed;
	}
};

export enum EventTargets {
	All = "All",
	Server = "Server",
};

export class GameEvent {
	type = 'GameEvent';
	targets: Array<string> | EventTargets;
	constructor(targets = EventTargets.All, ) {
		this.targets = targets;
	}
};

/** 
    Событие, предназначенное для одного игрока.

    Идентичен `GameEvent`, за исключением проверки `targets`
     */
export class TargetedEvent {
	type = 'TargetedEvent';
	targets: Array<string> | EventTargets;
	constructor(targets = EventTargets.All, ) {
		this.targets = targets;
	}
};

/** Событие, инициируемое игроком. */
export class PlayerEvent {
	type = 'PlayerEvent';
	targets: Array<string> | EventTargets;
	client_id: string;
	constructor(client_id: string, targets = EventTargets.All, ) {
		this.targets = targets;
		this.client_id = client_id;
	}
};

/** 
    Событие, отправленное только некоторым игрокам или серверу, но видное всем.

    Информация, которая может быть невидна, помечается дополнительным типом `UNKNOWN`.

    ### Пример
    Игрок А получает карту припаса. Игроки Б и В не знают, какую именно карту получил игрок А,
    но видели, что у него появилась новая карта.
     */
export class ObservableEvent {
	observed: boolean;
	type = 'ObservableEvent';
	targets: Array<string> | EventTargets;
	constructor(observed = false, targets = EventTargets.All, ) {
		this.observed = observed;
		this.targets = targets;
	}
};

/** 
    У поля есть значение в базе данных, но для модели оно неизвестно.

    ### Пример
    В игре с точки зрения игрока A у игрока Б значение supplies равно [UNKNOWN, UNKNOWN].
    Это означает, что у игрока Б есть две карты припасов, хранящихся в базе данных, но игроку A
    они неизвестны
     */
export type UNKNOWN = {
};

export type GameInfo = {
	id: number;
	started: boolean;
};

export type Character = {
	name: string;
	attack: number;
	health: number;
	survival_bonus: number;
	order: number;
};

export type Supply = {
	type: string;
	strength?: number;
	points: number;
};

/** Карта навигации */
export type Navigation = {
	bird_info: 'exed' | 'missing' | 'present';
	overboard: Array<string>;
	thirsty_players: Array<string>;
	thirst_actions: Array<'row' | 'fight'>;
};

export class Player {
	observed: boolean;
	name?: string;
	character?: Character;
	supplies: Array<Supply | UNKNOWN>;
	friend?: string;
	enemy?: string;
	rowed_this_turn: boolean;
	constructor(supplies: Array<Supply | UNKNOWN>, rowed_this_turn = false, observed = false, name?: string, character?: Character, friend?: string, enemy?: string, ) {
		this.observed = observed;
		this.name = name;
		this.character = character;
		this.supplies = supplies;
		this.friend = friend;
		this.enemy = enemy;
		this.rowed_this_turn = rowed_this_turn;
	}
};

export class PlayerConnect {
	type = 'PlayerConnect';
	targets: Array<string> | EventTargets;
	client_id: string;
	constructor(client_id: string, targets = EventTargets.All, ) {
		this.targets = targets;
		this.client_id = client_id;
	}
};

export class NameChange {
	type = 'NameChange';
	targets: Array<string> | EventTargets;
	client_id: string;
	new_name: string;
	constructor(client_id: string, new_name: string, targets = EventTargets.All, ) {
		this.targets = targets;
		this.client_id = client_id;
		this.new_name = new_name;
	}
};

/** Просьба от хоста начать игру */
export class StartRequest {
	type = 'StartRequest';
	targets: any;
	client_id: string;
	constructor(client_id: string, targets = EventTargets.Server, ) {
		this.targets = targets;
		this.client_id = client_id;
	}
};

/** Игрок берёт припас из утреннего набора припасов */
export class TakeSupply {
	observed: boolean;
	type = 'TakeSupply';
	targets: any;
	client_id: string;
	supply: Supply | UNKNOWN;
	constructor(client_id: string, supply: Supply | UNKNOWN, observed = false, targets = EventTargets.All, ) {
		this.observed = observed;
		this.targets = targets;
		this.client_id = client_id;
		this.supply = supply;
	}
};

export class NavigationRequest {
	type = 'NavigationRequest';
	targets: any;
	client_id: string;
	constructor(client_id: string, targets = EventTargets.Server, ) {
		this.targets = targets;
		this.client_id = client_id;
	}
};

/** Игрок откладывает карту навигации в колоду навигации */
export class SaveNavigation {
	observed: boolean;
	type = 'SaveNavigation';
	targets: any;
	client_id: string;
	navigation: Navigation | UNKNOWN;
	constructor(client_id: string, navigation: Navigation | UNKNOWN, observed = false, targets = EventTargets.All, ) {
		this.observed = observed;
		this.targets = targets;
		this.client_id = client_id;
		this.navigation = navigation;
	}
};

export class HostChange {
	type = 'HostChange';
	targets: Array<string> | EventTargets;
	new_host: string;
	constructor(new_host: string, targets = EventTargets.All, ) {
		this.targets = targets;
		this.new_host = new_host;
	}
};

export class GameStart {
	type = 'GameStart';
	targets: Array<string> | EventTargets;
	assigned_characters: { [key: string]: Character };
	constructor(assigned_characters: { [key: string]: Character }, targets = EventTargets.All, ) {
		this.targets = targets;
		this.assigned_characters = assigned_characters;
	}
};

/** Событие, получаемое игроком при назначении друга и врага */
export class NewRelationships {
	type = 'NewRelationships';
	targets: Array<string> | EventTargets;
	friend_client_id: string;
	enemy_client_id: string;
	constructor(friend_client_id: string, enemy_client_id: string, targets = EventTargets.All, ) {
		this.targets = targets;
		this.friend_client_id = friend_client_id;
		this.enemy_client_id = enemy_client_id;
	}
};

/** Клиент получил карту или карты припасов */
export class NewSupplies {
	observed: boolean;
	type = 'NewSupplies';
	targets: Array<string> | EventTargets;
	supplies: Array<Supply | UNKNOWN>;
	constructor(supplies: Array<Supply | UNKNOWN>, observed = false, targets = EventTargets.All, ) {
		this.observed = observed;
		this.targets = targets;
		this.supplies = supplies;
	}
};

export class TurnChange {
	type = 'TurnChange';
	targets: Array<string> | EventTargets;
	new_active_player: string;
	constructor(new_active_player: string, targets = EventTargets.All, ) {
		this.targets = targets;
		this.new_active_player = new_active_player;
	}
};

export class PhaseChange {
	type = 'PhaseChange';
	targets: Array<string> | EventTargets;
	new_phase: GamePhase;
	constructor(new_phase: GamePhase, targets = EventTargets.All, ) {
		this.targets = targets;
		this.new_phase = new_phase;
	}
};

/** Клиенту показываются утренние припасы и предоставляется возможность выбрать оттуда припас */
export class SupplyShowcase {
	observed: boolean;
	type = 'SupplyShowcase';
	targets: Array<string> | EventTargets;
	supply_stash: Array<Supply | UNKNOWN>;
	constructor(supply_stash: Array<Supply | UNKNOWN>, observed = false, targets = EventTargets.All, ) {
		this.observed = observed;
		this.targets = targets;
		this.supply_stash = supply_stash;
	}
};

/** Клиенту для выбора предоставляется набор карт навигации */
export class NavigationsOffer {
	observed: boolean;
	type = 'NavigationsOffer';
	targets: Array<string> | EventTargets;
	offered_navigations: Array<Navigation | UNKNOWN>;
	constructor(offered_navigations: Array<Navigation | UNKNOWN>, observed = false, targets = EventTargets.All, ) {
		this.observed = observed;
		this.targets = targets;
		this.offered_navigations = offered_navigations;
	}
};

