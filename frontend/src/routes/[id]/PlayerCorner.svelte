<script lang="ts">
    import type { Player, Supply } from "$lib/gametypes";
    import { flip } from "svelte/animate";
    import { fly } from "svelte/transition";
    import { clientId } from "./stores";

    export let player: Player;
    $: supplies = player.supplies as Array<Supply>;


    /** максимальный поворот карты припаса в turn */
    const maxRotation = 0.03;
    $: rotations = supplies.map((value, index) => {
        const step = maxRotation / Math.floor(supplies.length / 2);
        let i = supplies.length % 2 === 0 ? (index + 2) : (index + 1);
        let angle = Math.floor(i / 2) * step;
        let sign = i % 2 === 0 ? 1 : -1;
        return sign * angle + 'turn';
    });
    /** максимальный поворот карты припаса в turn */
    $: offsets = supplies.map((value, index) => {
        const step = 50;
        const additional_offset = supplies.length % 2 !== 0 ? 0 : -20;
        let i = supplies.length % 2 === 0 ? (index + 2) : (index + 1);
        let offset = Math.floor(i / 2) * step + additional_offset;
        let sign = i % 2 === 0 ? 1 : -1;
        return sign * offset + 'px';
    });
</script>

<div id="client-display">
    <div id="weapon-slot">

    </div>
    <div class="portrait" style="background-image: url(characters/{player.character?.name}.png);"
    class:enemy={player.enemy === $clientId} class:friend={player.friend === $clientId}>
    </div>
    <div id="supplies">
        {#each supplies as supply, i (supply.type)}
        <div class="supply-card zoomable" in:fly={{y: -1000}} animate:flip
        style="
        background-image: url(supplies/flaregun.png);
        transform: rotate({rotations[i]});
        transform-origin: bottom center;
        left: {offsets[i]};
        ">
        </div>
        {/each}

        <!-- <div class="background"></div> -->
    </div>
</div>

<style>

    #client-display {
        position: relative;
        display: flex;
        width: 100%;
        height: 100%;

        align-items: end;
        justify-content: center;
        column-gap: 60px;
    }

    #weapon-slot {

        width: 5%;
        /* max-width: 100px; */
        aspect-ratio: 2.2 / 3;
        background-color: aqua;
        margin-bottom: 20px;
    }

    #supplies {
        position: relative;

        width: 5%;
        /* max-width: 100px; */
        aspect-ratio: 2.2 / 3;
        background-color: transparent;
        margin-bottom: 20px;
        /* margin-left: 50px; */
    }

    #supplies .background {
        position: absolute;
        width: 300%;
        height: 100%;
        margin-top: 50px;
        left: 150%;
        background-image: url('backgrounds/supplies.png');
        background-size: contain;
        background-position: center left;
        background-repeat: no-repeat;
    }

    .supply-card {
        width: 100%;
        height: 100%;

        position: absolute;
        background-size: cover;
    }

    .zoomable {
        transform: scale(1);
        transition: transform 0.5s, z-index 0.5s cubic-bezier(0.075, 0.82, 0.165, 1);
        z-index: 1;
    }

    .zoomable:hover {
        transform-origin: bottom center;
        transform: scale(2) !important;
        z-index: 100;
    }

    .portrait {
        /* position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        margin: auto; */

        background-position: top center;
        background-size: cover;
        width: 8%;
        aspect-ratio: 2.2 / 3;

        z-index: 2;

        transition: filter 0.5s;
    }

    .portrait.enemy {
        filter: drop-shadow(0px 0px 20px var(--enemy-color));
    }

    .portrait.friend {
        filter: drop-shadow(0px 0px 20px var(--friend-color));
    }
</style>