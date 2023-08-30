<script lang="ts">
    import { fade, scale } from "svelte/transition";
    import { OnMount } from 'fractils';

    /** Всё покрываемое пространство затемнено */
    export let darkened = true;

    export let buttonText: string = '';
    $: showButton = buttonText !== '';
</script>

<OnMount>
    <div class="modal" class:darkened transition:fade|global={{duration: 200}}>
        <div class="main">
            <slot></slot>
        </div>
        {#if showButton}
        <button on:click>{buttonText.toUpperCase()}</button>
        {/if}
    </div>
</OnMount>

<style>
    .modal {
        position: absolute;
        width: 100%;
        height: 100%;
        z-index: 1000;

        display: flex;
        justify-items: center;
        align-items: center;
    }

    .darkened {
        background-image: radial-gradient(rgba(0, 0, 0, 0.305), rgba(0, 0, 0, 0.487));
        backdrop-filter: blur(4px);
    }

    .main {
        position: relative;
        width: fit-content;
        min-width: min(1000px, 100%);

        display: flex;
        justify-content: space-around;
        align-items: center;
        column-gap: 50px;
        margin: auto;
    }

    button {
        position: absolute;
        bottom: 30px;
        left: 0;
        right: 0;
        width: fit-content;
        margin: auto;
        padding: 30px;

        font-family: var(--font-family);
        font-size: 3em;
        font-weight: 700;
        /* letter-spacing: 0.05em; */

        background-color: tomato;
        border-style:ridge;
        border-color: rgb(116, 49, 37);
        border-radius: 30px;

        filter: drop-shadow(2px 2px 10px black);
        background-image: var(--grain-image);
        background-size: 70%;
    }

    button:hover {
        filter: drop-shadow(2px 2px 10px black) brightness(0.8);
    }

    button:active {
        filter: drop-shadow(2px 2px 10px black);
    }
</style>

<!-- Komenskoho73 -->