<script lang="ts">
    import GameCard from "./GameCard.svelte";

    export let type: string;

    export let hoverable = true;
</script>

<GameCard --background-image='url("supplies/flaregun.png")' hoverable={hoverable} on:click>
</GameCard>