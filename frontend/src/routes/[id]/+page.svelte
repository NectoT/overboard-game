<script lang="ts">
    import type { PageData, ActionData } from "./$types";
    import {
        PlayerConnect, GameEvent, PlayerEvent, HostChange, NameChange,
        type Player, StartRequest
    } from "$lib/gametypes";
    import Lobby from "./Lobby.svelte";
    import { WEBSOCKET_URL } from "$lib/constants";
    import { onMount } from "svelte";
    import { page } from "$app/stores";
    import { clientId } from "./stores";

    export let data: PageData;
    let gameInfo = data.game;
    clientId.set(data.clientId)

    let websocket: WebSocket;

    onMount(() => {
        websocket = new WebSocket(
            WEBSOCKET_URL + '/' + $page.params['id'] + '?client_id=' + data.clientId
        );
        console.log("Websocket connection made");
        websocket.onopen = (event) => {
            sendEvent(new PlayerConnect(data.clientId));
            addPlayer($clientId, {});
        };

        websocket.onmessage = (event) => {
            let data: GameEvent = JSON.parse(event.data);

            console.log("Received " + data.type);

            switch (data.type) {
                case 'PlayerConnect':
                    addPlayer((data as PlayerConnect).client_id, {});
                    break;
                case 'HostChange':
                    changeHost((data as HostChange).new_host);
                    break;
                case 'NameChange':
                    changeName((data as NameChange).client_id, (data as NameChange).new_name)
                    break;
                case 'GameStart':
                    startGame()
                    break;
                default:
                    break;
            }
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

    function startGame() {
        gameInfo.started = true;
        gameInfo = gameInfo;
    }

    function handleGameStart() {
        startGame();
        sendEvent(new StartRequest($clientId));
    }

    $: isHost = gameInfo?.host === $clientId;
</script>

{#if gameInfo.started}
    We've started boys!
{:else}
    <Lobby
        players={gameInfo.players}
        isHost={isHost}
        on:nameChange={handleNameChange}
        on:gameStart={handleGameStart}
    ></Lobby>
{/if}