<script lang="ts">
    import type { PageData, ActionData } from "./$types";
    import type { Game, GameEvent, HostChange, NameChange, Player, PlayerConnect, PlayerEvent } from "$lib/gametypes";
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
            sendEvent({type: "PlayerConnect", client_id: data.clientId});
            addPlayer($clientId, {});
        };

        websocket.onmessage = (event) => {
            let data: GameEvent = JSON.parse(event.data);

            console.log("Received " + data.type);

            if (data.type === 'PlayerConnect') {
                addPlayer((data as PlayerConnect).client_id, {});
            } else if (data.type === 'HostChange') {
                changeHost((data as HostChange).new_host);
            } else if (data.type === 'NameChange') {
                changeName((data as NameChange).client_id, (data as NameChange).new_name)
            }
        }

        websocket.onclose = (event) => {

        }
    })

    function sendEvent(event: PlayerEvent & {[key: string]: any}) {
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
        sendEvent({
            type: "NameChange",
            client_id: event.detail.clientId,
            new_name: event.detail.newName
        } satisfies NameChange)
    }

    $: isHost = gameInfo?.host === $clientId;
</script>

<Lobby players={gameInfo.players} isHost={isHost} on:nameChange={handleNameChange}></Lobby>