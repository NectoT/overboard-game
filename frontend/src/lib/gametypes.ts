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

export type GameEvent = {
	type: string;
	targets: Array<string> | EventTargets;
};

export type HostChange = {
	type: string;
	targets: Array<string> | EventTargets;
	new_host: string;
};

/** Событие, инициируемое игроком. */
export type PlayerEvent = {
	type: string;
	targets: Array<string> | EventTargets;
	client_id: string;
};

export type PlayerConnect = {
	type: string;
	targets: Array<string> | EventTargets;
	client_id: string;
};

export type NameChange = {
	type: string;
	targets: Array<string> | EventTargets;
	client_id: string;
	new_name: string;
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

