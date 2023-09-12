<script lang="ts">
    import type { Supply, UNKNOWN } from "$lib/gametypes";
    import { known } from "$lib/utils";
    import SupplyCard from "../SupplyCard.svelte";

    export let supplyStash: Array<Supply | UNKNOWN>;
    /** Обработчик клика карты припасов */
    export let onClick: (supply: Supply) => any;
</script>

{#each supplyStash as supply}
<SupplyCard type={known(supply).type} --width={'300px'} on:click={() => onClick(known(supply))}
--hoverScale={1.2}>
</SupplyCard>
{/each}