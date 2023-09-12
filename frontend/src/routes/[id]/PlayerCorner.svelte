<script lang="ts">
    import { NavigationRequest, type Player, type Supply } from "$lib/gametypes";
    import { flip } from "svelte/animate";
    import { clientId } from "./stores";
    import { flyFrom } from "$lib/transitions";
    import SupplyCard from "./SupplyCard.svelte";
    import { page } from "$app/stores";
    import type { WebSocketMixin } from "./+page"
    import { fly } from "svelte/transition";

    export let player: Player;
    $: supplies = player.supplies as Array<Supply>;

    export let actionsEnabled: boolean;

    const websocket: WebSocketMixin = $page.data.websocket;


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

    /** Откуда визуально прилетает карта припасов */
    export let supplyOrigin: {x: number, y: number} | null = null;

    $: flyArgs = supplyOrigin ?? {x: 0, y: -1000};
    $: supplyTransition = (supplyOrigin !== null) ? flyFrom : fly;

    let portrait: Element;
    export function getPortraitPos() {
        const rect = portrait.getBoundingClientRect();
        return {
            x: rect.x,
            y: rect.y
        }
    }
</script>

<div id="client-display">

    <div class="left flex">
        <div class="spacer" style:width="40px"></div>
        <button
        id="row"
        on:click={() => {websocket.sendEvent(new NavigationRequest($clientId))}}
        disabled={!actionsEnabled || player.rowed_this_turn}
        >
        </button>
        <div class="spacer" style:flex-grow={1}></div>
        <div id="weapon-slot">

        </div>
    </div>

    <div class="portrait" bind:this={portrait}
    style="background-image: url(characters/{player.character?.name}.png);"
    class:enemy={player.enemy === $clientId} class:friend={player.friend === $clientId}>
    </div>

    <div class="right flex">
        <div id="supplies">
            {#each supplies as supply, i (supply)}
            <!-- Тут конечно трудно понять, что происходит, но вообще здесь SupplyCard с настройкой
            трансформации оборачивается в доп контейнер, чтобы задать absolute позицию, сделать нужные
            отступы и добавить переходы. Лучше пока не придумал -->
            <div class="supply-card" in:supplyTransition|global={flyArgs} animate:flip|global
            style:left={offsets[i]}>
                <SupplyCard type={supply.type}
                --rotation={rotations[i]}
                --transform-origin='bottom center' --hoverScale={2}>
                </SupplyCard>
            </div>
            {/each}

        </div>
    </div>
</div>

<style>

    #client-display {
        position: relative;
        display: flex;
        width: 100%;
        height: 100%;
        column-gap: 16%;
    }

    .flex {
        display: flex;
        align-items: end;
        width: 100%;
        height: 92%;
    }

    .left {
        justify-content: end;
    }

    #row {
        --width: 100px;

        width: var(--width);
        aspect-ratio: 1 / 1;

        border-radius: 100vw;
        border-style: solid;
        border-width: 5px;
        background-color: rgb(128, 211, 214);

        background-image: var(--grain-image), url('icons/row.png');
        background-size: 150px, calc(var(--width) * 0.65);
        background-position: center;
        background-repeat: repeat, no-repeat;
    }

    button {
        all: unset;
    }

    button:hover {
        filter: brightness(0.8);
    }

    button:active {
        transform: scale(0.99);
    }

    button:disabled {
        filter: contrast(0.6);
        border-color: grey;
    }

    #weapon-slot {

        width: 10%;
        margin-left: 100px;
        /* max-width: 100px; */
        aspect-ratio: 2.2 / 3;
        background-color: aqua;
    }

    #supplies {
        position: relative;

        width: 10%;
        /* max-width: 100px; */
        aspect-ratio: 2.2 / 3;
        background-color: transparent;
    }

    .supply-card {
        width: 100%;
        height: 100%;

        position: absolute;
    }

    .supply-card {
        transition: transform 0.5s, z-index 0.5s cubic-bezier(0.075, 0.82, 0.165, 1);
        z-index: 1;
    }

    .supply-card:hover {
        z-index: 100;
    }

    .portrait {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        margin: auto;

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