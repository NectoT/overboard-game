<script lang="ts">
    import { GamePhase, type Game, type Player, type PlayerConnect } from "$lib/gametypes";
    import CharacterCard, { crossfadeDuration } from "./CharacterCard.svelte";
    import { flip } from "svelte/animate";
    import PlayerInfo from "./PlayerInfo.svelte";
    import PlayerCorner from "./PlayerCorner.svelte";
    import { clientId } from "./stores";
    import { Relation } from "$lib/constants";
    import { fade, fly, scale } from "svelte/transition";
    import { OnMount } from "fractils";
    import GameCard from "./GameCard.svelte";
    import { backOut } from "svelte/easing";
    import { flyFrom } from "$lib/transitions";
    import BoatLoader from "./BoatLoader.svelte";

    export let gameInfo: Game;

    type PlayerWithId = Player & {id: string};
    let players: Array<PlayerWithId> = [];

    /** Объект с отношением текущего клиента к другим игрокам */
    let relations: {[clientId: string]: Relation} = {};

    $: {
        players = [];
        relations = {};
        const clientPlayer = gameInfo.players[$clientId];
        for (const key in gameInfo.players) {
            let player = gameInfo.players[key];
            players.push({...player, id: key});

            // Значит клиент наблюдатель
            if (clientPlayer === undefined) {
                continue;
            }

            if (clientPlayer.enemy === key) {
                relations[key] = Relation.Enemy;
            } else if (clientPlayer.friend === key) {
                relations[key] = Relation.Friend;
            } else {
                relations[key] = Relation.Neutral;
            }
        }

    }

    $: clientPlayer = players.find((player) => player.id === $clientId);
    /** Является ли клиент игроком */
    $: isPlayer = clientPlayer !== undefined;

    /** Отсортированный по месту на корме список персонажей*/
    $: characters = Object.values(gameInfo.players).map(
        (player) => player.character!
    ).sort((a, b) => {return a.order - b.order}); // Ну выглядит так себе, но зато в одну строку

    /** Должны ли карточки с игроками находиться на поле */
    let playersOnBoard = gameInfo.phase === GamePhase.Day;

    let stash: Element;
    let stashPos: {x: number, y: number} | null = null;
    $: {
        if (stash == null) {
        } else {
            stashPos = null;
            let rect = stash.getBoundingClientRect();
            stashPos = {
                x: rect.x,
                y: rect.y
            }
        }
    }

    let playerCorner: PlayerCorner;
    let playerInfos: {[playerId: string]: PlayerInfo} = {};

    /** Откуда визуально откладывается карта навигации*/
    let navigationOrigin: PlayerCorner | PlayerInfo;
    $: {
        if (gameInfo.offered_navigations.length > 0) {
            if (gameInfo.active_player === $clientId) {
                navigationOrigin = playerCorner;
            } else {
                navigationOrigin = playerInfos[gameInfo.active_player!];
            }
        }
    }
</script>

<div id="outer-container">
    <div id="other-players">
        {#each players as player (player.id)}
        {#if player.id !== $clientId}
        <PlayerInfo bind:this={playerInfos[player.id]}
        player={player}
        relation={relations[player.id]}
        thinking={gameInfo.active_player === player.id}
        supplyOrigin={stashPos}
        rowing={gameInfo.active_player === player.id && gameInfo.offered_navigations.length > 0}>
        </PlayerInfo>
        {/if}
        {/each}
    </div>

    <div id="middle">
        {#if playersOnBoard}
        <div id="character-display">
            {#each characters as character (character.name)}
            <div
            animate:flip={{duration: crossfadeDuration}}>
                <CharacterCard character={character}></CharacterCard>
            </div>
            {/each}
        </div>
        {:else}
        <div id="character-store">
            {#each characters as character, index (character.name)}
                <div
                style:transform="translateX({index * 10}px)"
                animate:flip={{duration: crossfadeDuration}}
                >
                    <CharacterCard character={character} showInfo={false}></CharacterCard>
                </div>
            {/each}
        </div>
        {/if}

        {#if gameInfo.phase === GamePhase.Morning}
        <!-- Куча припасов -->
        <OnMount>
            <div
            bind:this={stash}
            id="supply-stash"
            out:fly|global={{x: 1000}}
            on:outroend={() => playersOnBoard=true}>
                <div class="item suitcase" in:fly={{y: -1000, delay: 30}}></div>
                <div class="item medkit" in:fly={{y: -1000}}></div>
                <div class="item basket" in:fly={{y: -1000, delay: 60}}></div>
                <div class="dust">
                    <div class="l a"></div>
                    <div class="l b"></div>
                    <div class="r c"></div>
                    <div class="r d"></div>
                </div>
            </div>
        </OnMount>
        {/if}

        <div id="navigation-stash" class="navigation-cards">
            {#if gameInfo.navigation_stash.length > 0}
            <div class="counter" transition:fade>
                <img src="icons/row.png" alt="Navigation cards in stash">
                {#key gameInfo.navigation_stash.length}
                <h2 in:scale={{easing: backOut, start: 2, duration: 500}}>
                    {gameInfo.navigation_stash.length}
                </h2>
                {/key}
            </div>
            {/if}
            <img id="navigation-place" src="navigation/navigation_place.png" alt="place for navigation cards">
            {#each gameInfo.navigation_stash as navigation, index}
            <div
            class="outer-navigation-card"
            style:right="{-5 * index}px"
            in:flyFrom={{...navigationOrigin.getPortraitPos()}}>
                <GameCard --background-image='url(navigation/navigation_back.png)'></GameCard>
            </div>
            {/each}
        </div>
    </div>


    {#if clientPlayer !== undefined}
        <PlayerCorner bind:this={playerCorner}
        player={clientPlayer}
        supplyOrigin={stashPos}
        actionsEnabled={gameInfo.phase == GamePhase.Day && gameInfo.active_player == $clientId}>
        </PlayerCorner>
    {/if}

</div>

<style>
    #middle {
        /*
        Это для того, чтобы transition не создавал скролл, но в ситуации с слишком маленькой
        шириной возможно это стоит убирать
        */
        overflow-x: clip;

        display: flex;
        flex-flow: row;
    }

    #outer-container {
        display: flex;
        flex-direction: column;

        height: 100%;
    }

    #character-display {
        display: flex;
        flex-grow: 1;
        justify-content: space-around;
        margin-top: 200px;
    }

    #navigation-stash {
        position: relative;
        width: 120px;
        margin-top: 200px;
        margin-right: 5%;
    }

    #navigation-place {
        position: absolute;
        object-fit: cover;
        bottom: 0;
        top: 0;
        margin: auto;
        width: 100%;
        height: fit-content;
        filter: drop-shadow(0px 0px 2px black);
    }

    #navigation-stash .counter {
        display: flex;
        justify-content: center;
        column-gap: 20px;
        align-items: center;
        position: absolute;
        bottom: 95%;
    }

    #navigation-stash .counter img {
        width: 40%;
        object-fit: contain;
    }

    #navigation-stash .counter h2 {
        width: fit-content;
        font-family: var(--game-bold-font);
        font-size: 2.5em;
        margin: 0;
        height: fit-content;
        color: cadetblue;
        filter: drop-shadow(0px 0px 1px grey);
    }

    .outer-navigation-card {
        position: absolute;
        bottom: 0;
        top: 0;
        margin: auto;
        width: 100%;
        height: fit-content;

        filter: drop-shadow(-2px 2px 2px black);
    }

    #character-store {
        position: absolute;
        left: 20px;
        top: 0px;
        bottom: 0px;
        margin: auto;
        width: fit-content;
        height: 300px;
    }

    #character-store>* {
        position: absolute;
    }

    #other-players {
        display: flex;
        position: relative;
        width: 100%;
        justify-content: space-around;
        margin-left: auto;
        margin-right: auto;

        border-style: groove;
        border-width: 0px 0px 4px 0px;
        border-color: black;
        height: fit-content;

        background-image: url('backgrounds/seagulls.png');
        background-position: center;
        background-size: contain;
    }

    #supply-stash {
        position: relative;
        width: 250px;
        aspect-ratio: 1 / 1;

        /* background-image: url('backgrounds/supplies2_no_flask.png');
        background-size: contain;
        background-position: center;
        background-repeat: no-repeat; */

        filter: drop-shadow(-0px 4px 8px black);

        margin: auto;
        margin-top: 100px;
        z-index: 10;
    }

    #supply-stash .item {
        position: absolute;

        background-size: contain;
        background-position: center;
        background-repeat: no-repeat;
    }

    #supply-stash .item.medkit {
        width: 80%;
        aspect-ratio: 1 / 1;

        background-image: url('backgrounds/medkit.png');

        left: -18%;
    }

    #supply-stash .item.suitcase {
        width: 90%;
        aspect-ratio: 1 / 1;

        background-image: url('backgrounds/suitcase.png');
        right: -18%;
    }

    #supply-stash .item.basket {
        width: 60%;
        aspect-ratio: 1 / 1;

        background-image: url('backgrounds/basket.png');
        bottom: 0px;
        left: 0px;
        right: -18%;
        margin: auto;
    }

    @keyframes dust {
        0% {
            filter: opacity(0);
            transform: translateX(0%) scale(0);
        }

        10% {
            filter: opacity(1) drop-shadow(-2px 2px 30px rgba(0, 0, 0, 0.563));
            transform: translateX(calc(var(--max-offset) / 5)) scale(1);
        }

        80% {
            filter: opacity(1) drop-shadow(-2px 2px 30px rgba(0, 0, 0, 0.563));
        }

        100% {
            filter: opacity(0) drop-shadow(-2px 2px 30px rgba(0, 0, 0, 0.563));
            transform: translateX(var(--max-offset));
        }
    }

    .dust * {
        position: absolute;
        width: 35%;
        aspect-ratio: 1 / 1;

        background-size: contain;
        background-position: center;
        background-repeat: no-repeat;

        bottom: 0;
        filter: opacity(0);
    }

    .dust * {
        animation-timing-function: ease-out;
        animation-duration: 1.5s;
        animation-iteration-count: 1;
        animation-delay: 210ms;
        animation-name: dust;
    }

    .dust .l {
        --max-offset: -50%;
        transform-origin: bottom right;
    }

    .dust .r {
        --max-offset: 50%;
        transform-origin: bottom left;
    }

    .dust .a {
        background-image: url('dust/cloud1.png');
    }

    .dust .b {
        background-image: url('dust/cloud3.png');
        bottom: -10%;
        left: 0;
        right: 0;
        margin: auto;
    }

    .dust .c {
        right: 0;
        background-image: url('dust/cloud2.png');
    }

    .dust .d {
        bottom: -10%;
        left: 0;
        right: 0;
        margin: auto;
        background-image: url('dust/cloud7.png');
    }
</style>