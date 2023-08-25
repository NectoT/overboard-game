<script lang="ts" context="module">
    import { cardCrossfade } from "$lib/transitions";

    export let crossfadeDuration = 500;

    let [send, receive] = cardCrossfade();
</script>

<script lang="ts">
    import type { Character } from "$lib/gametypes";
    import { afterUpdate, tick } from "svelte";
    import { scale } from "svelte/transition";

    export let character: Character;
    export let showInfo = true;

    let _showInfo = false; // Херовый способ, по другому как сделать не знаю
    afterUpdate(async () => {
        await tick();

        _showInfo = showInfo
    })
</script>

<div id="card"
style:background-image="url(characters/cards/{character.name}.png)"
in:receive|global={character.name}
out:send|global={character.name}
class:rotated={showInfo}
>
    {#if _showInfo}
    <div class="info left bottom" id="health" in:scale={{duration: 500}}>
        <span>{character.health}</span>
    </div>
    <div class="info right bottom" id="strength" in:scale={{duration: 500}}>
        <span>{character.attack}</span>
    </div>
    {/if}
</div>

<style>
    * {
        font-family: var(--font-family);
    }

    #card {
        position: relative;
        width: 150px;
        aspect-ratio: 2.2 / 3;

        filter: drop-shadow(2px 2px 2px #000000);

        background-position: center;
        background-repeat: no-repeat;
        background-size: contain;
    }

    .info {
        position: absolute;
        width: 35%;
        aspect-ratio: 1 / 1;

        background-position: center;
        background-repeat: no-repeat;
        background-size: contain;

        display: flex;
        justify-content: center;
        align-content: center;

        font-size: 2em;
        font-weight: bold;
        color: white;

        filter: drop-shadow(1px 1px 1px #000000);
    }
    .info span {
        width: fit-content;
        height: fit-content;
        text-shadow: 2px 2px 8px black;
        margin: auto;
    }

    .info.bottom {
        bottom: 0px;
    }

    .info.left {
        left: 0px;
    }

    .info.right {
        right: 0px;
    }

    #health {
        background-image: url('characters/icons/heart.svg');
    }

    #strength {
        background-image: url('characters/icons/strength.svg');
    }

</style>