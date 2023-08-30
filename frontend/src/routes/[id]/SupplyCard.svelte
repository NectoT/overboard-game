<script lang="ts">
    // Если что это не уверсальная карта припасов, пока что
    export let type: string;

    export let hoverable = true;
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- svelte-ignore a11y-no-static-element-interactions -->
<!-- TODO: возможность выбора карты с помощью клавиатуры -->
<div class="card" class:hoverable
style:background-image='url("supplies/flaregun.png")'
on:click
>
</div>

<style>
    .card {
        width: var(--width, 100%);
        aspect-ratio: 2.2 / 3;

        background-size: cover;

        transition: transform 0.5s;

        transform: rotate(var(--rotation, 0));
        transform-origin: var(--transform-origin, center center);
    }

    .hoverable {
        transition: transform 0.5s, z-index 0.5s cubic-bezier(0.075, 0.82, 0.165, 1);
        z-index: 1;
    }

    .hoverable:hover {
        transform: scale(var(--hoverScale, 1));
        z-index: 1000;
    }
</style>