export type GameInfo = {
	id: number;
	started: boolean;
};

export type Player = {
	name?: string;
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

export class HostChange {
	type = 'HostChange';
	targets: Array<string> | EventTargets;
	new_host: string;
	constructor(new_host: string, targets = EventTargets.All, ) {
		this.targets = targets;
		this.new_host = new_host;
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

export class GameStart {
	type = 'GameStart';
	targets: Array<string> | EventTargets;
	client_id: string;
	constructor(client_id: string, targets = EventTargets.All, ) {
		this.targets = targets;
		this.client_id = client_id;
	}
};

export type SocketError = {
	message: string;
};

export enum GameViewpoint {
	Player = "Player",
	Spectator = "Spectator",
};

/** 
    Модель, отображающая состояние игры. В зависимости от `viewpoint` часть информации
    скрывается или искажается.

    #### Это всего лишь модель, само состояние игры хранится в базе данных
     */
export type Game = {
	id: number;
	started: boolean;
	players: { [key: string]: Player };
	host?: string;
	viewpoint?: GameViewpoint;
	viewpoint_client_id?: string;
};

