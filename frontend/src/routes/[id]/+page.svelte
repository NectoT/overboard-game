<script lang="ts">
    import type { PageData } from "./$types";
    import type { Character, Navigation, Player, Supply } from "$lib/gametypes/game";
    import Lobby from "./Lobby.svelte";
    import GameBoard from "./GameBoard.svelte";
    import { onMount, type ComponentType, type ComponentProps, SvelteComponent } from "svelte";
    import { clientToken, playerId } from "./stores";
    import GamePopup from "./GamePopup.svelte";
    import BoatLoader from "./BoatLoader.svelte";
    import Frenemies from "./popup_content/Frenemies.svelte";
    import SuppliesOffer from "./popup_content/SuppliesOffer.svelte";
    import NavigationsChoice from "./popup_content/NavigationsChoice.svelte";
    import { scale } from "svelte/transition";

    export let data: PageData;
    let gameInfo = data.game;
    clientToken.set(data.clientToken);
    playerId.set(data.playerId);

    let enemyName: string;
    let friendName: string;
    $: {
        if (gameInfo.phase !== 'lobby') {
            let enemyId = gameInfo.players[$playerId].enemy;
            if (enemyId !== undefined) {
                enemyName = gameInfo.players[enemyId].character!.name;
            }
            let friendId = gameInfo.players[$playerId].friend;
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
                friendName: gameInfo.players[$playerId].friend,
                enemyName: gameInfo.players[$playerId].friend,
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
    if (gameInfo.active_player === $clientToken) {
        if (gameInfo.phase === 'morning') {
            currPopup = popups.SuppliesOffer;
        } else if (gameInfo.offered_navigations.length > 0) {
            currPopup = popups.NavigationsOffer;
        }
    }

    async function delay(ms: number) {
        await new Promise(res => setTimeout(res, 1000));
    }

    let websocket = data.websocket;

    onMount(() => {
        websocket.onopen = (event) => {
            console.log("Websocket connection made");
            websocket.sendPlayerConnect({
                targets: "All"
            });
            addPlayer($playerId, {observed: false, supplies: [], rowed_this_turn: false});
            let name = "Игрок " + Object.keys(gameInfo.players).length;
            changeName(data.playerId, name);
            websocket.sendNameChange({new_name: name});
        };


        websocket.onPlayerConnect = (event) => addPlayer(event.player_id, {
            observed: true, supplies: [], rowed_this_turn: false
        });

        websocket.onHostChange = (event) => changeHost(event.new_host);

        websocket.onNameChange = (event) => changeName(event.player_id, event.new_name);

        websocket.onGameStart = (event) => startGame(event.assigned_characters);

        websocket.onNewRelationships = async (event) => {
            await setFrenemies(event.friend_id, event.enemy_id);
        }

        websocket.onNewSupplies = async (event) => {
            if (event.observed) {
                otherReceiveSupplies((event.targets as string[])[0], event.supplies.length);
            } else {
                receiveSupplies(event.supplies as Supply[]);
                await delay(1000);
            }
        }

        websocket.onSupplyShowcase = (e) => {
            if (!e.observed) {
                console.log(`${$clientToken} is offered some supplies`)
                currPopup = popups.SuppliesOffer;
                gameInfo.supply_stash = e.supply_stash;
                gameInfo = gameInfo;
            }
        }

        websocket.onTakeSupply = async (event) => {
            // Всегда observed
            `TODO`
            // gameInfo.active_player = undefined;
            otherReceiveSupplies(event.player_id, 1);
        }

        websocket.onTurnChange = (event) => {
            gameInfo.active_player = event.new_active_player
            gameInfo = gameInfo;
        };

        websocket.onPhaseChange = (event) => {
            gameInfo.phase = event.new_phase;
            gameInfo = gameInfo;
        }

        websocket.onNavigationsOffer = async (e) => {
            gameInfo.offered_navigations = e.offered_navigations;
            if (!e.observed) {
                currPopup = popups.Boat;
                await delay(1);
                currPopup = popups.NavigationsOffer;
            }
        }

        websocket.onSaveNavigation = (e) => {
            gameInfo.offered_navigations = [];
            gameInfo.navigation_stash.push(e.navigation);
            gameInfo.navigation_stash = gameInfo.navigation_stash;
            gameInfo.players[e.player_id!].rowed_this_turn = true;
            gameInfo = gameInfo;
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

    function changeName(playerId: string, newName: string) {
        gameInfo.players[playerId].name = newName;
        gameInfo = gameInfo;
    }

    function handleNameChange(event: CustomEvent<{newName: string}>) {
        changeName(data.playerId, event.detail.newName);
        websocket.sendNameChange({new_name: event.detail.newName});
    }

    function startGame(characters: {[key: string]: Character}) {
        gameInfo.phase = 'morning';
        for (const player_id in gameInfo.players) {
            gameInfo.players[player_id].character = characters[player_id];
        }
        gameInfo = gameInfo;
    }

    function handleStartRequest() {
        websocket.sendStartRequest({});
    }

    async function setFrenemies(friendClientId: string, enemyClientId: string) {
        gameInfo.players[$playerId].enemy = enemyClientId;
        gameInfo.players[$playerId].friend = friendClientId;

        currPopup = popups.Frenemies;

        // Ждём пока в модале popupMode не станет None
        // Лучшего способа ожидания закрытия модала я не придумал
        while (currPopup === popups.Frenemies) {
            await delay(50);
        }

        gameInfo = gameInfo;
    }

    function receiveSupplies(supplies: Array<Supply>) {
        gameInfo.players[$playerId].supplies.push(...supplies);
        gameInfo = gameInfo
    }

    function otherReceiveSupplies(otherId: string, amount: number) {
        gameInfo.players[otherId].supplies.push(...Array(amount).fill({}));
        gameInfo = gameInfo;
    }

    function handleSupplyTake(supply: Supply) {
        receiveSupplies([supply]);
        websocket.sendTakeSupply({
            supply: supply
        })
        currPopup = popups.None;
    }

    function handleNavigationSave(navigation: Navigation) {
        currPopup = popups.None;
        websocket.sendSaveNavigation({
            navigation: navigation
        })
        gameInfo.navigation_stash.push(navigation);
        gameInfo.players[$playerId].rowed_this_turn = true;
        gameInfo = gameInfo;
    }

    $: isHost = gameInfo?.host === $playerId;
</script>

{#if gameInfo.phase !== 'lobby'}

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