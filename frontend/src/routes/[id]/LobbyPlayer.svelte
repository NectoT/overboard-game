<script lang="ts">
    import { createEventDispatcher } from "svelte";

    export let name: string;

    let dispatch = createEventDispatcher<{
        nameChange: {newName: string}
    }>();

    /** Имя, которое устанавливается, если пользователь ввёл что-то неподходящее */
    let startName = name;

    export let editable = true;
    let editMode = false;

    /** Если true, то компонент неактивен, типо. (На самом деле он просто сереньким становится) */
    export let disabled = false;

    export let reversed = false;
    let container_flow = reversed ? 'row-reverse' : 'row';

    $: {
        if (!editMode) {
            name = name.trim();
        }
    }

    let nameInput: HTMLElement;

    async function handleNameEdit(event: MouseEvent) {
        editMode = !editMode;

        if (editMode) {
            // Фокусируемся на имени, чтобы сразу писать можно было
            // Ну и херня, фокус не работает, если его сразу применять, ну что это такое.
            setTimeout(() => {
                nameInput.focus();

                let selection = window.getSelection();
                selection?.extend(selection.focusNode!, name.length);
                selection?.collapseToEnd();
            }, 10);
        }
    }

    function handleFocus(event: FocusEvent) {
        editMode = false;

        if (name.trim() == "") {
            name = startName;
        } else {
            dispatch('nameChange', {newName: name});
        }
    }
</script>

<div id="container" style:flex-flow={container_flow} class:disabled>
    <div id="image-container"></div>
    <div id="name-container">
        {#if editMode}
            <span
                class="name"
                contenteditable="true"
                bind:innerText={name}
                bind:this={nameInput}
                on:focusout={handleFocus}
            ></span>
        {:else}
            <span class="name">{name}</span>
        {/if}
        {#if editable}
            <button id="edit-button" on:mousedown={handleNameEdit}></button>
        {/if}
    </div>
</div>

<style>
    .disabled {
        filter: brightness(0.9) grayscale(0.7);
    }

    #container {
        position: relative;
        max-width: 100%;
        padding: 20px;
        border-style: solid;
        border-radius: 100px;
        border-width: 4px;
        border-color: black;

        display: flex;
        /* flex-flow: row; */
        justify-items: center;
        gap: 20px;

        background-color: white;
    }

    #image-container {
        aspect-ratio: 1 / 1;
        width: 20%;

        background-image: url("life_buoy.svg");
        background-size: contain;
        background-position: center;
        background-repeat: no-repeat;
    }

    #name-container {
        flex-grow: 1;
        display: flex;
        margin: auto;
        justify-content: center;
        gap: 10px;
        max-width: 80%;
    }

    .name {
        position: relative;
        word-break: break-all;
        text-align: center;
        max-width: 80%;
        overflow: hidden;
        font-family: var(--font-family);
        font-size: 2em;
        font-weight: bold;
    }

    .name[contenteditable] {
        display: inline-block;
    }

    .name[contenteditable]:focus {
        outline: none;

        /* border-color: rgb(62, 113, 255);
        border-width: 2px;
        border-style:ridge; */
    }

    #edit-button {
        all: unset;
        position: relative;

        width: 25px;
        aspect-ratio: 1 / 1;

        background-image: url('pencil.svg');
        background-size: contain;
        background-position: center;
        background-repeat: no-repeat;
    }

    #edit-button:hover {
        cursor: pointer;
    }
</style>

