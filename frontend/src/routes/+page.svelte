<script lang="ts">
    import { enhance } from "$app/forms";
    import { page } from "$app/stores";
    import type { PageData, ActionData } from "./$types";
    import InputError from "./InputError.svelte";

    export let data: PageData;
    export let form: ActionData | null;
    $: {
        console.log(data);
    }

    const newGameId = data.gameId!;

    let connectError = false;
    let connectMessage = "";

    $: {
        if (form != null && form!.status != 200) {
            connectError = true;
            connectMessage = form!.message;
        } else {
            connectError = false;
        }
    }

    function handleIdInput(event: Event) {
        connectError = false;
    }
</script>

<h1 class="title-large">За Бортом</h1>

<form action="?/create" method="post">
    <input type="hidden" name="game-id" value={newGameId} />
    <input type="submit" value="Создать игру" id="create-button" class="submit-button" />
</form>

<h2 class="annotation-large">Или</h2>

<h1 class="title-small">Подключиться к игре:</h1>
<form action="?/connect" method="post" use:enhance id="connect-form">
    <span id='connect-flex'>
        <!--
            Я предполагаю, что игровые id всегда будут одинаковой длины, поэтому использую
            newGameId как пример
        -->
        <input
            type="text"
            name="game-id"
            id=""
            maxlength={newGameId.toString().length}
            style:width="{newGameId.toString().length}ch"
            on:input={handleIdInput}
        /><input type="submit" class="submit-button" value="" />
    </span>
    {#if connectError}
        <InputError text={connectMessage}></InputError>
    {/if}
</form>

<style>
    /* Пока всё сделано под экраны > 550px */

    * {
        font-family: var(--font-family);
    }

    .title-large {
        font-size: 6rem;
        margin: auto;
        text-align: center;
        margin-bottom: 100px;
        margin-top: 50px;
    }

    .title-small {
        font-size: 2rem;
        margin-left: auto;
        margin-right: auto;
        text-align: center;
        /* margin: 10px; */
    }

    .annotation-large {
        margin: auto;
        text-align: center;
        font-size: 3rem;
        font-style: normal;
        font-weight: 100;
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
        margin-top: 25px;
        margin-bottom: 25px;

        color: rgb(114, 114, 114);
    }

    form {
        width: fit-content;
        margin: auto;
    }

    #create-button {
        /*
        Из-за этой строчки кстати я не могу обращаться этот инпут видоизменять через общий
        селектор input
        */
        all: unset;

        position: relative;

        font-size: 4em;
        white-space: nowrap;

        color: white;
        background-color: tomato;

        padding: 20px 40px;
        margin-left: auto;
        margin-right: auto;
        border-radius: 20vmin;
    }

    .submit-button:hover {
        cursor: pointer !important;
        filter: brightness(80%) !important;
    }

    input[type="text"] {
        font-size: 4rem;
    }

    #connect-form {
        display: flex;
        flex-direction: column;
        align-items: center;
        /* width: min-content; */

    }

    #connect-flex {
        display: flex;
        flex-direction: row;
        align-items: stretch;
    }

    #connect-form .submit-button {
        all: unset;
        background-image: url('double_arrow_right_white.svg');
        background-color: tomato;
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
        width: 32px;
    }
</style>
