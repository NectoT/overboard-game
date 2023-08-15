export type GameInfo = {
	id: number;
	started: boolean;
};

export type Player = {
};

export type GameEvent = {
	type: String;
};

/** Событие, инициируемое игроком. */
export type PlayerEvent = {
	type: String;
	client_id: String;
};

export type PlayerConnect = {
	type: String;
	client_id: String;
};

export type SocketError = {
	message: String;
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
	players: Map<any, Player>;
	viewpoint?: GameViewpoint;
	viewpoint_client_id?: String;
};

export type Test = {
	a: Map<any, Map<any, number>>;
};

