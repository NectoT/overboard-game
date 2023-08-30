<script lang="ts">
    import { Relation } from "$lib/constants";
    import { scale } from "svelte/transition";

    export let name: string;
    export let relation: Relation = Relation.Enemy

    let picUrl: string;
    if (relation === Relation.Enemy) {
        picUrl = `characters/friends/Chad.png`;
    } else {
        picUrl = `characters/enemies/Chad.png`
    }
</script>

<div
transition:scale
class="card"
style:background-image='url({picUrl})'>
</div>

<style>
    .card {
        width: var(--width, 100%);
        aspect-ratio: 2.2 / 3;

        background-repeat: no-repeat;
        background-position: center;
        background-size: cover;


        /* TEMP */
        border-style: ridge;
        border-width: 5px;
        border-color: rgb(142, 110, 79);
    }
</style>