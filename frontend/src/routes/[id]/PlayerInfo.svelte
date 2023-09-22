<script lang="ts">
    import { Relation } from "$lib/constants";
    import type { Player } from "$lib/gametypes/game";
    import { backOut } from "svelte/easing";
    import { fade, scale } from "svelte/transition";
    import ThinkBubble from "./ThinkBubble.svelte";
    import SupplyCard from "./SupplyCard.svelte";
    import { OnMount } from "fractils";
    import { flyFrom } from "$lib/transitions";
    import BoatLoader from "./BoatLoader.svelte";

    export let player: Player;
    export let relation: Relation = Relation.Neutral;

    /** Откуда визуально должна браться карта */
    export let supplyOrigin: {x: number, y: number} | null = null;

    let supplyAmount = player.supplies.length;
    /** Получена карта из набора припасов и это нужно визуализировать */
    let takingFromStash = false;

    $: {
        if (player.supplies.length > supplyAmount && supplyOrigin !== null) {
            takingFromStash = true;
        }
        supplyAmount = player.supplies.length;
    }

    export let thinking = false;

    let portrait: Element;
    export function getPortraitPos() {
        const rect = portrait.getBoundingClientRect();
        return {
            x: rect.x,
            y: rect.y
        }
    }

    export let rowing = false;

    $: actionEffect = rowing ? BoatLoader : null;
</script>

<div id="outer-container">
    <h2 class="name">{player.name}</h2>
    <div class="portrait" bind:this={portrait}
    class:enemy={relation === Relation.Enemy}
    class:friend={relation === Relation.Friend}>
        <img
        alt="Player icon"
        class="character"
        style:background-image='url("characters/{player.character?.name}.png")'>
        {#if thinking}
            <ThinkBubble></ThinkBubble>
        {/if}
        {#if player.rowed_this_turn}
            <img class="rowed" src="icons/row.png" alt="Rowed this turn" transition:fade>
        {/if}
        {#if actionEffect !== null}
        <div class="effect-container" transition:fade>
            <div class="inner-container" transition:scale|global>
                <svelte:component this={actionEffect}></svelte:component>
            </div>
        </div>
        {/if}
    </div>
    <div class="supply-counter">
        <div class="icon">

        </div>
        {#key player.supplies.length}
        <h3 in:scale={{easing: backOut, start: 2, duration: 500}}>{player.supplies.length}</h3>
        {/key}
    </div>
    <div class="weapon-slot">
        {#if takingFromStash}
        <OnMount>
            <div
            in:flyFrom|global={{...supplyOrigin, dissapear: true}}
            on:introend={() => takingFromStash = false}>
                <SupplyCard type="back"></SupplyCard>
            </div>
        </OnMount>
        {/if}
    </div>
</div>

<style>
    #outer-container {
        position: relative;
        display: grid;

        grid-template-columns: 0.4fr 0.2fr 0.4fr 0.2fr;
        grid-template-rows:  0.4fr 0.3fr 0.8fr 0.6fr;

        min-width: 250px;
        aspect-ratio: 14 / 10;
        column-gap: 10px;

        --neutral-color: rgb(154, 171, 204);
        --inner-color: rgb(235, 196, 176);
    }

    .name {
        grid-row: 1 / 2;
        grid-column: 1 / 3;

        font-family: var(--font-family);
        font-size: 1.5em;

        text-overflow: ellipsis;
        overflow-x: hidden;
        overflow-y: hidden;
        margin: 0;
    }

    .portrait {
        position: relative;
        /* aspect-ratio: 2.2 / 3; */

        grid-row: 2 / 5;
        grid-column: 1 / 3;

        border-style: groove;
        border-width: 8px;
        /* border-color: black; */

        background-image: radial-gradient(var(--inner-color), transparent);
        background-color: var(--neutral-color);
        transition: background-color 0.4s;
    }

    .portrait .effect-container {
        position: absolute;
        width: 100%;
        height: 100%;
        top: 0;
        z-index: 2;
        backdrop-filter: brightness(0.7);

        height: 100%;
        display: flex;
        align-items: center;
    }

    .portrait .rowed {
        width: 20%;
        position: absolute;
        right: 2%;
        bottom: 2%;
        filter: drop-shadow(2px 2px 2px grey);
    }

    .portrait.enemy {
        background-color: var(--enemy-color);
    }

    .portrait.friend {
        background-color: var(--friend-color);
    }

    .character {
        display: block;
        position: relative;
        width: 100%;
        height: 100%;

        background-position: top center;
        background-size: cover;
        font-size: 0;
    }

    .supply-counter {
        display: flex;
        width: fit-content;
        gap: 10px;

        grid-row: 1 / 3;
        grid-column: 3 / 5;

        width: 100%;
        height: 100%;

        margin-left: 10px;
    }

    .supply-counter .icon {
        background-image: url('icons/supply_colored.png');
        background-position: center;
        background-size: contain;
        background-repeat: no-repeat;

        filter: drop-shadow(2px 2px 5px black);

        width: 100%;
        max-width: 50px;
        aspect-ratio: 1 / 1;
    }

    .supply-counter h3 {
        font-family: var(--font-family);
        width: fit-content;
        padding: 10px;
        font-size: 1.8em;
        margin: auto;
        height: fit-content;
    }

    .weapon-slot {
        grid-row: 3 / 5;
        grid-column: 3 / 4;
        align-self: center;
        /* justify-self: center; */
        margin-bottom: 10px;

        width: 100%;
        aspect-ratio: 2.1 / 3;
        background-size: cover;
        background-color: aqua;
        background-image: url('supplies/flaregun.png');
    }

</style>