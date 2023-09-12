<script lang="ts">
    import { fade, scale } from "svelte/transition";
    import { OnMount } from 'fractils';
    import { beforeUpdate } from "svelte";

    /** Всё покрываемое пространство затемнено */
    export let darkened = true;

    export let buttonText: string = '';
    $: showButton = buttonText !== '';

    /** transition для содержимого модального окна.
     *
     * Есть одна деталь: Если при смене содержимого у нового контента `popupTransition` отличается
     * от transition предыдущего, новый контент появляется мнгновенно, без перехода.
     */
    export let popupTransition = fade;

    let updateFlag = false;

    beforeUpdate(() => updateFlag = !updateFlag)
</script>

<OnMount>
    <div class="modal" class:darkened transition:fade|global={{duration: 200}}>
        {#key updateFlag}
        <div class="main" transition:popupTransition|global>
            <slot></slot>
        </div>
        {/key}
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

        transition: filter 0.2s ease-in-out;
    }

    .darkened {
        backdrop-filter: blur(4px) brightness(0.5);
    }

    .main {
        position: absolute;
        width: fit-content;
        min-width: min(1000px, 100%);

        display: flex;
        justify-content: space-around;
        align-items: center;
        column-gap: 50px;
        left: 0;
        right: 0;
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