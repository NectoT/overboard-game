<script lang="ts">
    import type { PageData } from "./$types";
    import {
        PlayerConnect, GameEvent, PlayerEvent, HostChange, NameChange, Player,
        StartRequest, type Character, GameStart, NewSupplies, type Supply, NewRelationships,
        GamePhase, SupplyShowcase, TakeSupply, PhaseChange
    } from "$lib/gametypes";
    import Lobby from "./Lobby.svelte";
    import GameBoard from "./GameBoard.svelte";
    import { Relation, WEBSOCKET_URL } from "$lib/constants";
    import { onMount } from "svelte";
    import { page } from "$app/stores";
    import { clientId } from "./stores";
    import GamePopup from "./GamePopup.svelte";
    import FrenemyCard from "./FrenemyCard.svelte";
    import SupplyCard from "./SupplyCard.svelte";
    import { known } from "$lib/utils";

    export let data: PageData;
    let gameInfo = data.game;
    clientId.set(data.clientId)

    let enemyName: string;
    let friendName: string;
    $: {
        if (gameInfo.phase !== GamePhase.Lobby) {
            let enemyId = gameInfo.players[$clientId].enemy;
            if (enemyId !== undefined) {
                enemyName = gameInfo.players[enemyId].character!.name;
            }
            let friendId = gameInfo.players[$clientId].friend;
            if (friendId !== undefined) {
                friendName = gameInfo.players[friendId].character!.name;
            }
        }
    }

    let websocket: WebSocket;

    enum popup {
        /** GamePopup не используется */
        None,
        /** Показываются друг и враг клиента */
        Frenemies,
        /** Показываются утренние припасы */
        SupplyStash
    }

    let popupMode = popup.None;
    if (gameInfo.stash_taker === $clientId) {
        popupMode = popup.SupplyStash;
    }

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
                    // await delay(1000);
                },
                'NewRelationships': async (event) => {
                    let e = event as NewRelationships;
                    await setFrenemies(e.friend_client_id, e.enemy_client_id);
                },
                'NewSupplies': async (event: GameEvent) => {
                    let e = event as NewSupplies;
                    if (e.observed) {
                        otherReceiveSupplies((event.targets as string[])[0], e.supplies.length);
                    } else {
                        receiveSupplies(e.supplies as Supply[]);
                        await delay(1000);
                    }
                },
                'SupplyShowcase': (event) => {
                    let e = event as SupplyShowcase;
                    if (e.observed) {
                        gameInfo.stash_taker = e.targets[0];
                    } else {
                        console.log(`${$clientId} is offered some supplies`)
                        popupMode = popup.SupplyStash;
                        gameInfo.supply_stash = (event as SupplyShowcase).supply_stash;
                        gameInfo = gameInfo;
                    }
                },
                'TakeSupply': async (event) => {
                    // Всегда observed
                    let e = event as TakeSupply;
                    gameInfo.stash_taker = undefined;
                    otherReceiveSupplies(e.client_id, 1);
                },
                'PhaseChange': (event) => {
                    gameInfo.phase = (event as PhaseChange).new_phase;
                    gameInfo = gameInfo;
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
        gameInfo.phase = GamePhase.Morning;
        for (const client_id in gameInfo.players) {
            gameInfo.players[client_id].character = characters[client_id];
        }
        gameInfo = gameInfo;
    }

    function handleStartRequest() {
        sendEvent(new StartRequest($clientId));
    }

    async function setFrenemies(friendClientId: string, enemyClientId: string) {
        gameInfo.players[$clientId].enemy = enemyClientId;
        gameInfo.players[$clientId].friend = friendClientId;

        popupMode = popup.Frenemies;

        // Ждём пока в модале popupMode не станет None
        // Лучшего способа ожидания закрытия модала я не придумал
        while (popupMode === popup.Frenemies) {
            await delay(50);
        }

        gameInfo = gameInfo;
    }

    function receiveSupplies(supplies: Array<Supply>) {
        gameInfo.players[$clientId].supplies.push(...supplies);
        gameInfo = gameInfo
    }

    function otherReceiveSupplies(otherId: string, amount: number) {
        gameInfo.players[otherId].supplies.push(...Array(amount).fill({}));
        gameInfo = gameInfo;
    }

    function handleSupplyTake(supply: Supply) {
        receiveSupplies([supply]);
        sendEvent(new TakeSupply($clientId, supply));
        popupMode = popup.None;
    }

    $: isHost = gameInfo?.host === $clientId;
</script>

{#if gameInfo.phase !== GamePhase.Lobby}

{#if popupMode === popup.Frenemies}
<GamePopup buttonText="Got it" on:click={() => popupMode = popup.None}>
    <FrenemyCard name={friendName} relation={Relation.Friend} --width={'300px'}></FrenemyCard>
    <FrenemyCard name={enemyName} relation={Relation.Enemy} --width={'300px'}></FrenemyCard>
</GamePopup>
{:else if popupMode === popup.SupplyStash}
<GamePopup>
    {#each gameInfo.supply_stash as supply}
    <SupplyCard
    type={known(supply).type} --width={'300px'}
    on:click={() => handleSupplyTake(known(supply))}
    --hoverScale={1.2}>
    </SupplyCard>
    {/each}
</GamePopup>
{/if}

<GameBoard gameInfo={gameInfo}></GameBoard>
{:else}
<Lobby
    players={gameInfo.players}
    isHost={isHost}
    on:nameChange={handleNameChange}
    on:gameStart={handleStartRequest}
></Lobby>
{/if}