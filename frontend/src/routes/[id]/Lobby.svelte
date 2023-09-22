<script lang="ts">
    import type { Game, Player } from "$lib/gametypes/game";
    import { fade } from "svelte/transition";
    import BoatLoader from "./BoatLoader.svelte";
    import LobbyPlayer from "./LobbyPlayer.svelte";
    import { playerId } from "./stores";
    import { createEventDispatcher } from "svelte";
    import { cubicOut } from "svelte/easing";
    import { page } from "$app/stores";
    import FloatingAlert from "../FloatingAlert.svelte";

    export let isHost = false;
    export let players: Game["players"];

    let dispatch = createEventDispatcher<{
        nameChange: {newName: string},
        gameStart: null
    }>();

    let playerCount = 0;

    let windowWidth = 1920;
    $: compactMode = windowWidth < 1000;

    type PlayerWithId = Player & {id: string};

    let leftColumn: Array<PlayerWithId> = [];
    let rightColumn: Array<PlayerWithId> = [];
    $: {
        leftColumn = [];
        rightColumn = [];
        let i = 0;
        for (const key in players) {
            const player = { ...players[key], id: key };

            if (compactMode || i % 2 == 0) {
                leftColumn.push(player);
            } else {
                rightColumn.push(player);
            }

            i += 1;
        }

        playerCount = i;
    }

    const minPlayers = 2;

    $: loaderText = playerCount < minPlayers ? "Ожидание игроков" : "Ожидание хоста";

    let showCopyAlert = false;

    function handleStartButton(event: MouseEvent) {
        event.preventDefault()
        dispatch('gameStart');
    }

    function handleCodeCopy(event: MouseEvent) {
        navigator.clipboard.writeText($page.params.id);
        showCopyAlert = true;
        setTimeout(() => {
           showCopyAlert = false;
        }, 1000);
    }
</script>

<svelte:window bind:innerWidth={windowWidth}></svelte:window>

<div id="lobby">
    <div class="column">
        {#each leftColumn as player (player.id)}
            <LobbyPlayer
                name={player.name ?? 'Name is null' }
                editable={$playerId === player.id}
                on:nameChange={(e) => dispatch('nameChange', {...e.detail})}
            ></LobbyPlayer>
        {/each}
    </div>

    <div id="center">
        <div id="loader-container">
            <BoatLoader text="{loaderText}"></BoatLoader>
        </div>
        <div id="code-display">
            <h2 class="light-text">Код игры:</h2>
            <div id="copyable-code">
                <h1>{$page.params.id}</h1>
                <button on:click={handleCodeCopy}>
                    {#if showCopyAlert}
                    <FloatingAlert text={"Код скопирован!"}></FloatingAlert>
                    {/if}
                </button>
            </div>
        </div>
        {#if isHost && playerCount >= minPlayers}
            <a
                transition:fade={{duration: 2000, easing: cubicOut}}
                id="start-game"
                href="#start"
                on:click={handleStartButton}
            >Начать</a>
        {/if}
    </div>

    {#if !compactMode }
        <div class="column">
            {#each rightColumn as player (player.id)}
                <LobbyPlayer
                    name={player.name ?? 'Name is null' }
                    editable={$playerId === player.id}
                    on:nameChange={(e) => dispatch('nameChange', {...e.detail})}
                ></LobbyPlayer>
            {/each}
        </div>
    {/if}
</div>



<style>
    #lobby {
        display: flex;
        flex-direction: row;
        flex-wrap: nowrap;
        --margin-top: 50px;
        margin-top: var(--margin-top);
        margin-left: 20px;
        margin-right: 20px;
        height: calc(100% - var(--margin-top));
    }

    #center {
        flex-grow: 1;
        display: flex;
        flex-flow: column-reverse;
        justify-content: space-between;
        height: 100%;
    }

    #code-display {
        position: relative;
        width: fit-content;
        margin-left: auto;
        margin-right: auto;
        flex-grow: 1;
    }

    #code-display h2 {
        font-size: 3em;
        margin-top: 0px;
        margin-bottom: 10px;
    }

    #code-display h1 {
        font-size: 4em;
        font-family: var(--font-family);
        margin-top: 0px;
    }

    #copyable-code {
        display: flex;
        column-gap: 15px;
    }

    #copyable-code>button {
        all: unset;
        position: relative;
        width: 32px;
        height: 35px;

        background-image: url('icons/thicc_files.svg');
        background-size: 100% 100%;

        transition: transform 0.05s;
    }

    #copyable-code>button:hover {
        cursor: pointer;
    }

    #copyable-code>button:active {
        transform: scale(0.95);
    }

    #loader-container {
        position: sticky;
        bottom: 10%;
    }

    #start-game {
        text-decoration: none;

        font-size: 6em;
        font-family: var(--font-family);
        white-space: nowrap;

        color: white;
        background-color: tomato;

        padding: 30px 60px;
        margin-left: auto;
        margin-right: auto;
        margin-bottom: 30px;
        border-radius: 20vmin;
    }

    #start-game:hover {
        filter: brightness(0.8);
    }

    .column {
        display: flex;
        flex-direction: column;
        height: 100%;
        width: 30%;
        gap: 100px;
    }
</style>
