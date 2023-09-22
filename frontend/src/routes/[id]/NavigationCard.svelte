<script lang="ts">
    import type { Navigation, Player } from "$lib/gametypes/game";
    import GameCard from "./GameCard.svelte";

    export let hoverable = true;

    export let navigation: Navigation;
    export let players: {[id: string]: Player};

    let containerWidth = 0;
    $: letterWidth = containerWidth / 8;
</script>

<GameCard hoverable={hoverable} on:click>
    <div id="container" bind:clientWidth={containerWidth}>
        <div id="overboard-people">
            {#each navigation.overboard as id}
                <div style:font-size="{letterWidth}px">
                    {players[id].character?.name}
                </div>
            {/each}
        </div>

        {#if navigation.thirst_actions.includes('fight')}
        <img id="fight-icon" src="icons/fight_colored.png" alt="Fighters are thirsty">
        {/if}

        {#if navigation.thirst_actions.includes('row')}
        <img id="row-icon" src="icons/row.png" alt="Rowers are thirsty">
        {/if}

        {#if navigation.bird_info === 'present'}
        <img id="bird-icon" src="icons/bird.png" alt="Bird found">
        {:else if navigation.bird_info === 'exed'}
        <img id="bird-icon" src="icons/exed_bird.png" alt="Bird lost">
        {/if}

        <div id="thirsty-people">
            {#each navigation.thirsty_players as id}
                <div style:font-size="{letterWidth}px">
                    {players[id].character?.name}
                </div>
            {/each}
        </div>
    </div>
</GameCard>

<style>
    #container {
        position: relative;
        width: 100%;
        height: 100%;
        background-image: url("overboard_card.png");
        background-size: 100% 100%;
    }

    #container * {
        text-align: center;
        font-family: var(--game-light-font);
        user-select: none;
    }

    #overboard-people {
        position: absolute;
        width: 100%;
        top: 2%;
    }

    #thirsty-people {
        position: absolute;
        width: 100%;
        bottom: 2%;
    }

    #fight-icon {
        position: absolute;
        left: 5%;
        bottom: 5%;
        width: 20%;
    }

    #row-icon {
        position: absolute;
        right: 5%;
        bottom: 5%;
        width: 20%;
    }

    #bird-icon {
        position: absolute;
        width: 40%;
        top: 0;
        bottom: 0;
        left: 0;
        right: 0;
        margin: auto;
    }
</style>