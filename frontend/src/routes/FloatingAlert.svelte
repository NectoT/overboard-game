<script lang="ts">
    import { cubicOut } from "svelte/easing";
    import { fade } from "svelte/transition";

    export let text: string;
</script>

<div class="info alert" transition:fade={{duration: 200, easing: cubicOut}}>{text}</div>

<style>
    .info.alert {
        font-family: var(--font-family);
        font-size: 1.2em;
        position: absolute;
        width: max-content;

        border-radius: 10px;
        border-style: solid;
        border-width: 2px;

        color: white;
        border-color: rgb(0, 0, 0);
        background-color: rgba(0, 0, 0, 0.739);

        padding: 15px;
        padding-top: 5px;
        padding-bottom: 5px;

        left: calc(100% + 20px);
        bottom: 0;
        height: fit-content;
    }
</style>

