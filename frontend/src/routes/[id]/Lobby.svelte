<script lang="ts">
    import type { Game, Player } from "$lib/gametypes";
    import { fade } from "svelte/transition";
    import BoatLoader from "./BoatLoader.svelte";
    import LobbyPlayer from "./LobbyPlayer.svelte";
    import { clientId } from "./stores";
    import { createEventDispatcher } from "svelte";

    export let isHost = false;
    export let players: Game["players"];

    let dispatch = createEventDispatcher<{
        nameChange: {clientId: string, newName: string}
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

            if (player.name == null) {
                player.name = "Игрок " + (i + 1);
            }
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
</script>

<svelte:window bind:innerWidth={windowWidth}></svelte:window>

<div id="lobby">
    <div class="column">
        {#each leftColumn as player (player.id)}
            <LobbyPlayer
                name={player.name ?? 'Name is null' }
                editable={$clientId === player.id}
                on:nameChange={(e) => dispatch('nameChange', {...e.detail, clientId: player.id})}
            ></LobbyPlayer>
        {/each}
    </div>

    <div id="center">
        <div id="loader-container">
            <BoatLoader text="{loaderText}"></BoatLoader>
        </div>
        {#if isHost && playerCount >= minPlayers}
            <a transition:fade={{duration: 2000}} id="start-game" href="#start">Начать</a>
        {/if}
    </div>

    {#if !compactMode }
        <div class="column">
            {#each rightColumn as player (player.id)}
                <LobbyPlayer
                    name={player.name ?? 'Name is null' }
                    editable={$clientId === player.id}
                    on:nameChange={(e) => dispatch('nameChange', {...e.detail, clientId: player.id})}
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
