<script lang="ts">
    import { Relation } from "$lib/constants";
    import FrenemyCard from "../FrenemyCard.svelte";

    export let friendName: string;
    export let enemyName: string;
</script>

<FrenemyCard name={friendName} relation={Relation.Friend} --width={'300px'}></FrenemyCard>
<FrenemyCard name={enemyName} relation={Relation.Enemy} --width={'300px'}></FrenemyCard>