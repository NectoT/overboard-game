<script lang="ts">
    import type { PageData } from "./$types";
    import {
        PlayerConnect, GameEvent, PlayerEvent, HostChange, NameChange, Player,
        StartRequest, type Character, GameStart, NewSupplies, type Supply, NewRelationships,
        GamePhase, SupplyShowcase, TakeSupply, PhaseChange, TurnChange, NavigationsOffer,
        type Navigation, SaveNavigation
    } from "$lib/gametypes";
    import Lobby from "./Lobby.svelte";
    import GameBoard from "./GameBoard.svelte";
    import { onMount, type ComponentType, type ComponentProps, SvelteComponent } from "svelte";
    import { clientId } from "./stores";
    import GamePopup from "./GamePopup.svelte";
    import BoatLoader from "./BoatLoader.svelte";
    import Frenemies from "./popup_content/Frenemies.svelte";
    import SuppliesOffer from "./popup_content/SuppliesOffer.svelte";
    import NavigationsChoice from "./popup_content/NavigationsChoice.svelte";
    import { scale } from "svelte/transition";

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


    /** Содержимое модального окна */
    type Popup<T extends SvelteComponent> = {
        component: ComponentType<T>;
        windowProps: ComponentProps<GamePopup>;
        /** Обработчик клика на кнопку в модальном окне */
        onButtonClick?: (event: MouseEvent) => any;
        componentProps: () => ComponentProps<T>;
    };

    /** Всплывающие штуки */
    const popups = {
        None: null,
        Frenemies: {
            component: Frenemies,
            windowProps: {
                darkened: true,
                buttonText: "Got it",
            },
            onButtonClick: (event) => currPopup = null,
            componentProps: () =>  ({
                friendName: gameInfo.players[$clientId].friend,
                enemyName: gameInfo.players[$clientId].friend,
            })
        } as Popup<Frenemies>,
        SuppliesOffer: {
            component: SuppliesOffer,
            windowProps: {darkened: true, buttonText: ""},
            componentProps: () => ({
                supplyStash: gameInfo.supply_stash,
                onClick: (supply) => handleSupplyTake(supply)
            })
        } as Popup<SuppliesOffer>,
        NavigationsOffer: {
            component: NavigationsChoice,
            windowProps: {darkened: true, buttonText: "", popupTransition: scale},
            componentProps: () => ({
                offeredNavigations: gameInfo.offered_navigations,
                players: gameInfo.players,
                onClick: handleNavigationSave
            })
        } as Popup<NavigationsChoice>,
        Boat: {
            component: BoatLoader,
            windowProps: {darkened: true, buttonText: "", popupTransition: scale},
            componentProps: () => ({width: "75%"})
        } as Popup<BoatLoader>
    }

    /** Текущий режим всплывающего окна */
    let currPopup: Popup<any> | null = popups.None;
    if (gameInfo.active_player === $clientId) {
        if (gameInfo.phase === GamePhase.Morning) {
            currPopup = popups.SuppliesOffer;
        } else if (gameInfo.offered_navigations.length > 0) {
            currPopup = popups.NavigationsOffer;
        }
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
                    if (!e.observed) {
                        console.log(`${$clientId} is offered some supplies`)
                        currPopup = popups.SuppliesOffer;
                        gameInfo.supply_stash = (event as SupplyShowcase).supply_stash;
                        gameInfo = gameInfo;
                    }
                },
                'TakeSupply': async (event) => {
                    // Всегда observed
                    let e = event as TakeSupply;
                    gameInfo.active_player = undefined;
                    otherReceiveSupplies(e.client_id, 1);
                },
                'TurnChange': (event) => {
                    gameInfo.active_player = (event as TurnChange).new_active_player;
                },
                'PhaseChange': (event) => {
                    gameInfo.phase = (event as PhaseChange).new_phase;
                    gameInfo = gameInfo;
                },
                'NavigationsOffer': async (event) => {
                    let e = event as NavigationsOffer;
                    gameInfo.offered_navigations = e.offered_navigations;
                    if (!e.observed) {
                        currPopup = popups.Boat;
                        await delay(1);
                        currPopup = popups.NavigationsOffer;
                    }
                },
                'SaveNavigation': (event) => {
                    let e = event as SaveNavigation;

                    gameInfo.offered_navigations = [];
                    gameInfo.navigation_stash.push(e.navigation);
                    gameInfo.navigation_stash = gameInfo.navigation_stash;
                    gameInfo.players[e.client_id].rowed_this_turn = true;
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

    let websocket = data.websocket;

    onMount(() => {
        websocket.onopen = (event) => {
            console.log("Websocket connection made");
            websocket.sendEvent(new PlayerConnect(data.clientId));
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
        websocket.sendEvent( new NameChange(event.detail.clientId, event.detail.newName))
    }

    function startGame(characters: {[key: string]: Character}) {
        gameInfo.phase = GamePhase.Morning;
        for (const client_id in gameInfo.players) {
            gameInfo.players[client_id].character = characters[client_id];
        }
        gameInfo = gameInfo;
    }

    function handleStartRequest() {
        websocket.sendEvent(new StartRequest($clientId));
    }

    async function setFrenemies(friendClientId: string, enemyClientId: string) {
        gameInfo.players[$clientId].enemy = enemyClientId;
        gameInfo.players[$clientId].friend = friendClientId;

        currPopup = popups.Frenemies;

        // Ждём пока в модале popupMode не станет None
        // Лучшего способа ожидания закрытия модала я не придумал
        while (currPopup === popups.Frenemies) {
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
        websocket.sendEvent(new TakeSupply($clientId, supply));
        currPopup = popups.None;
    }

    function handleNavigationSave(navigation: Navigation) {
        currPopup = popups.None;
        websocket.sendEvent(new SaveNavigation($clientId, navigation));
        gameInfo.navigation_stash.push(navigation);
        gameInfo.players[$clientId].rowed_this_turn = true;
        gameInfo = gameInfo;
    }

    $: isHost = gameInfo?.host === $clientId;
</script>

{#if gameInfo.phase !== GamePhase.Lobby}

{#if currPopup !== popups.None}
    <GamePopup {...currPopup.windowProps} on:click={currPopup.onButtonClick}>
        <svelte:component this={currPopup.component} {...currPopup.componentProps()}/>
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