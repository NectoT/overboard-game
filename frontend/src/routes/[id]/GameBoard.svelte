<script lang="ts">
    import { GamePhase, type Game, type Player, type PlayerConnect } from "$lib/gametypes";
    import CharacterCard, { crossfadeDuration } from "./CharacterCard.svelte";
    import { flip } from "svelte/animate";
    import PlayerInfo from "./PlayerInfo.svelte";
    import PlayerCorner from "./PlayerCorner.svelte";
    import { clientId } from "./stores";
    import { Relation } from "$lib/constants";
    import { fly } from "svelte/transition";
    import { OnMount } from "fractils";

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

    let stash: Element | null = null;
</script>

<div id="outer-container">
    <div id="other-players">
        {#each players as player (player.id)}
        {#if player.id !== $clientId}
        <PlayerInfo
        player={player}
        relation={relations[player.id]}
        thinking={gameInfo.active_player === player.id}
        stash={stash}>
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
    </div>


    {#if clientPlayer !== undefined}
        <PlayerCorner player={clientPlayer}></PlayerCorner>
    {/if}

</div>

<style>
    #middle {
        overflow-x: clip;
    }

    #outer-container {
        display: flex;
        flex-direction: column;

        height: 100%;
    }

    #character-display {
        display: flex;
        /* background-color: grey; */
        justify-content: space-around;
        margin-top: 200px;
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