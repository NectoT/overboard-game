<script lang="ts">
    import type { PageData } from "./$types";
    import {
        PlayerConnect, GameEvent, PlayerEvent, HostChange, NameChange, Player,
        StartRequest, type Character, GameStart, NewSupplies, type Supply
    } from "$lib/gametypes";
    import Lobby from "./Lobby.svelte";
    import Game from "./Game.svelte";
    import { WEBSOCKET_URL } from "$lib/constants";
    import { onMount } from "svelte";
    import { page } from "$app/stores";
    import { clientId } from "./stores";

    export let data: PageData;
    let gameInfo = data.game;
    clientId.set(data.clientId)

    let websocket: WebSocket;

    // Temp
    let playersOnBoard = gameInfo.started;

    async function delay(ms: number) {
        await new Promise(res => setTimeout(res, 1000));
    }

    /** Обещание от последнего вызванного обработчика событий*/
    let lastHandler: Promise<void> = Promise.resolve();
    async function handleEvent(event: GameEvent) {
        // Тут типо матрёшка. Если изначально lastHandler указывает на функцию A, то функция B будет ждать
        // функцию A, а lastHandler указывает на B. Получается, функция C будет ждать функцию B,
        // которая ждёт функцию A, то есть получается очередь A <- B <- C

        let handler = async () => {
            await lastHandler;


            // Сами обработчики событий
            const handlers: {[key: string]: (event: GameEvent) => void | Promise<void>} = {
                'PlayerConnect': (event) => {
                    addPlayer((event as PlayerConnect).client_id, new Player([]));
                },
                'HostChange': (event) => {
                    changeHost((event as HostChange).new_host);
                },
                'NameChange': (event) => {
                    changeName((event as NameChange).client_id, (event as NameChange).new_name);
                },
                'GameStart': async (event) => {
                    startGame((event as GameStart).assigned_characters);
                    await delay(1000);
                    playersOnBoard = true;
                },
                'NewSupplies': async (event: GameEvent) => {
                    let e = event as NewSupplies;
                    if (e.observed) {
                        otherReceiveSupplies((event.targets as string[])[0], e.supplies.length);
                    } else {
                        receiveSupplies($clientId, e.supplies as Supply[]);
                        await delay(1000);
                    }
                }
            }

            if (handlers[event.type] === undefined) {
                console.error(`Cannot handle event with ${event.type} type. Ignoring it...`)
                return;
            }

            await handlers[event.type](event);
            console.log(`Completed handling ${event.type} event`);
        }
        lastHandler = handler();
    }

    onMount(() => {
        websocket = new WebSocket(
            WEBSOCKET_URL + '/' + $page.params['id'] + '?client_id=' + data.clientId
        );
        console.log("Websocket connection made");
        websocket.onopen = (event) => {
            sendEvent(new PlayerConnect(data.clientId));
            addPlayer($clientId, new Player([]));
        };

        websocket.onmessage = (event) => {
            let data: GameEvent = JSON.parse(event.data);

            console.log("Received " + data.type);
            handleEvent(data);
        }

        websocket.onclose = (event) => {
            console.log("Connection closed. Reason: " + event.reason);
        }
    })

    function sendEvent(event: PlayerEvent) {
        console.log("Sent " + event.type);
        websocket.send(JSON.stringify(event));
    }

    function addPlayer(id: string, player: Player) {
        if (!Object.hasOwn(gameInfo.players, id)) {
            gameInfo.players[id] = player;
            gameInfo = gameInfo;
        }
    }

    function changeHost(host_id: string) {
        gameInfo.host = host_id;
        gameInfo = gameInfo;
    }

    function changeName(clientId: string, newName: string) {
        gameInfo.players[clientId].name = newName;
        gameInfo = gameInfo;
    }

    function handleNameChange(event: CustomEvent<{clientId: string, newName: string}>) {
        changeName(event.detail.clientId, event.detail.newName);
        sendEvent( new NameChange(event.detail.clientId, event.detail.newName))
    }

    function startGame(characters: {[key: string]: Character}) {
        gameInfo.started = true;
        for (const client_id in gameInfo.players) {
            gameInfo.players[client_id].character = characters[client_id];
        }
        gameInfo = gameInfo;
    }

    function handleStartRequest() {
        sendEvent(new StartRequest($clientId));
    }

    function receiveSupplies(clientId: string, supplies: Array<Supply>) {
        gameInfo.players[clientId].supplies.push(...supplies);
        gameInfo = gameInfo
    }

    function otherReceiveSupplies(otherId: string, amount: number) {
        gameInfo.players[otherId].supplies.push(...Array(amount).fill({}));
        gameInfo = gameInfo;
    }

    $: isHost = gameInfo?.host === $clientId;
</script>

{#if gameInfo.started}
    <Game gameInfo={gameInfo} playersOnBoard={playersOnBoard}></Game>
{:else}
    <Lobby
        players={gameInfo.players}
        isHost={isHost}
        on:nameChange={handleNameChange}
        on:gameStart={handleStartRequest}
    ></Lobby>
{/if}