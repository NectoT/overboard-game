<script lang="ts">
    import { OnMount } from "fractils";
    import { backOut } from "svelte/easing";
    import { scale, type ScaleParams } from "svelte/transition";

    let inDuration = 600;
    let inBaseArgs: ScaleParams = {easing: backOut, duration: inDuration};
</script>

<OnMount>
    <div class="thought-bubble" out:scale|global={{duration: 300}}>
        <div class="little a" in:scale={inBaseArgs}></div>
        <div class="little b" in:scale={{...inBaseArgs, delay: inDuration * 0.5}}></div>
        <div class="main" in:scale={{...inBaseArgs, delay: inDuration}}>
        </div>
    </div>
</OnMount>

<style>

    .thought-bubble {
        position: absolute;
        display: flex;
        width: var(--main-width, 150%);

        z-index: 2;
        bottom: 100%;
        left: 70%;

        filter: drop-shadow(5px 5px 20px rgb(55, 55, 55));
    }

    .thought-bubble * {
        background-size: 100% 100%;
    }

    .main {
        background-image: url('thought/main_with_dots.png');
        aspect-ratio: 18 / 14;
        flex-grow: 7;

        display: flex;
        justify-content: center;
    }

    .little.a {
        background-image: url('thought/little1.png');
        aspect-ratio: 1 / 1;
        flex-grow: 1;
        height: 10%;

        margin-top: 50%;
    }

    .little.b {
        background-image: url('thought/little2.png');
        aspect-ratio: 1 / 1;
        flex-grow: 1.2;
        height: 10%;

        margin-top: 40%;
        /* margin-left: -10px; */
    }

</style>