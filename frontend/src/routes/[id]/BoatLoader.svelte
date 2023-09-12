<script lang="ts">
    export let text = "";
    export let width: any = "100%";
</script>
<div id="outer-container" style:width={width}>
    <div id="sea-container">
        <div class="image base" id="sea-base"></div>
        <div class="image animated" id="sea-back"></div>
        <div class="image animated" id="sea-middle"></div>
        <div class="image animated" id="sea-boat"></div>
        <div class="image animated" id="side-waves"></div>
        <div class="image animated" id="sea-front"></div>
    </div>
    {#if text !== ""}
        <div id="chains">
            <div class="left chain"></div>
            <div class="right chain"></div>
        </div>
        <div id="text-sign">
            <h1 id="text">{text}</h1>
        </div>
    {/if}
</div>

<style>
    #outer-container {
        display: flex;
        flex-direction: column;
        position: relative;
        align-content: flex-start;
    }

    /* #7dadb5 */

    #chains {
        position: relative;
        width: 40%;
        height: 100px;
        margin: auto;
        margin-top: -25px;
        display: flex;
        flex-direction: row;
        justify-content: space-between;
    }

    .chain {
        background-image: url('sea/chains.svg');
        background-position: center;
        background-repeat: no-repeat;
        background-size: contain;
        width: 20%;

        z-index: 2;
    }

    #text-sign {
        min-width: 40%;
        max-width: 80%;
        margin: auto;
        margin-top: -10px;
        width: fit-content;

        background: repeating-linear-gradient(
            #a47120, #a47120 2ch, black 2ch, black 2.5ch
        );

        border-color: black;
        border-style: solid;
        border-radius: 10px;
        border-width: 0.3em;
    }

    #text {
        font-family: var(--font-family);
        /* text-shadow: 1px 1px 0px black, -1px -1px 0px black, 1px -1px 0px black, -1px 1px 0px black; */
        color: rgb(202, 202, 202);

        text-align: center;
        margin: auto;

        padding: 20px;

        animation-name: shine;
        animation-duration: 1s;
        animation-timing-function: ease-in-out;
        animation-iteration-count: infinite;
        animation-direction: alternate;
    }

    #sea-container {
        position: relative;
        height: fit-content;
        z-index: 3;
    }

    .image {
        position: absolute;
        top: 0;
        /* min-height: 200px; */
        min-width: 100px;
        /* Надо знать заранее пропорции картинок видимо, иначе не работает */
        aspect-ratio: 4 / 1;

        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
        width: 100%;
    }

    .image.animated {
        animation-duration: 1.1s;
        animation-iteration-count: infinite;
        animation-timing-function: ease-in-out;
    }

    .image.base {
        /*
        Важно установить это, потому что иначе внешний контейнер вообще не знает, какой
        высоты ему быть
        */
        position: relative;
    }

    #sea-base {
        background-image: url('sea/base.svg');
    }

    #sea-back {
        background-image: url('sea/back.svg');
        animation-name: horizontal;
        animation-direction: alternate;
        animation-delay: -0.7s;
    }

    #sea-middle {
        background-image: url('sea/middle.svg');
        animation-name: horizontal;
        animation-direction: alternate;
    }

    #sea-front {
        background-image: url('sea/front.svg');
        animation-name: horizontal;
        animation-direction: alternate-reverse;
        animation-delay: -0.5s;
    }

    #sea-boat {
        background-image: url('sea/boat.svg');
        animation-name: boat;
        animation-delay: -0.1s;
        animation-direction: alternate;
    }

    #side-waves {
        background-image: url('sea/boat_cover.svg');
    }

    @keyframes horizontal {
        from {
            transform: translateX(0);
        }

        to {
            transform: translateX(20px);
        }
    }

    @keyframes boat {
        from {
            transform: translateY(0) rotate(-2deg);
        }

        to {
            transform: translateY(5%) rotate(5deg);
        }
    }

    @keyframes shine {
        from {
            filter: drop-shadow(0 0 0 rgb(20, 103, 220));
            color: rgb(202, 202, 202);
        }

        to {
            filter: drop-shadow(0 0 1rem rgb(20, 103, 220));
            color: rgb(255, 255, 255);
        }
    }
</style>