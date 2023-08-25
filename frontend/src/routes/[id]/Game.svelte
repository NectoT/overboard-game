<script lang="ts">
    import type { Game, Player, PlayerConnect } from "$lib/gametypes";
    import CharacterCard, { crossfadeDuration } from "./CharacterCard.svelte";
    import { onMount, tick } from "svelte";
    import { flip } from "svelte/animate";
    import PlayerInfo from "./PlayerInfo.svelte";
    import PlayerCorner from "./PlayerCorner.svelte";
    import { clientId } from "./stores";

    export let gameInfo: Game;
    type PlayerWithId = Player & {id: string};
    let players: Array<PlayerWithId> = [];
    $: {
        players = [];
        for (const key in gameInfo.players) {
            players.push({...gameInfo.players[key], id: key});
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
    export let playersOnBoard = true;

    // onMount(async () => {
    //     await tick();

    //     playersOnBoard = true;
    // })

    // onMount(() => setTimeout(() => {
    //     playersOnBoard = true;
    //     gameInfo.players[Object.keys(gameInfo.players)[0]].character!.order = -2;
    //     gameInfo = gameInfo;
    // }, 500));
</script>

<div id="outer-container">
    <div id="other-players">
        {#each players as player (player.id)}
        {#if player.id !== $clientId}
        <PlayerInfo player={player}></PlayerInfo>
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
    </div>


    {#if clientPlayer !== undefined}
        <PlayerCorner player={clientPlayer}></PlayerCorner>
    {/if}

</div>

<style>
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
</style>