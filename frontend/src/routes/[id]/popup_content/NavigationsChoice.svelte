<script lang="ts">
    import type { Navigation, Player, UNKNOWN } from "$lib/gametypes";
    import { known } from "$lib/utils";
    import NavigationCard from "../NavigationCard.svelte";

    export let offeredNavigations: Array<Navigation | UNKNOWN>;
    export let players: {[id: string]: Player};
    /** Обработчик клика карты навигации */
    export let onClick: (navigation: Navigation) => any;
</script>

{#each offeredNavigations as navigation}
    <NavigationCard
    players={players}
    navigation={known(navigation)}
    --width="300px" --hoverScale={1.2} on:click={() => onClick(known(navigation))}>
    </NavigationCard>
{/each}