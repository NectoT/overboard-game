
<header>
    <a href="/" id="home-link">
        <img src="favicon.png" alt="Вернуться на главную страницу" width="100" height="100">
    </a>
    <slot name="header"/>
</header>

<slot/>

<style>
    :global(body) {
        --font-family: Arial, Helvetica, sans-serif;
        margin: 0%;
    }

    header {
        padding-left: 20px;
        padding-bottom: 5px;
        padding-top: 5px;
        background-color: cadetblue;
        border-color: rgba(222, 184, 135, 0.751);
        border-style: solid;
        border-width: 0 0 2px 0;
    }

    @keyframes rotation {
        from {
            transform: scale(0%);
            filter: brightness(100%);
        }

        50% {
            transform: scale(50%);
            filter: brightness(10%);
        }

        to {
            transform: rotate(-0.5turn);
            filter: brightness(0%);
        }
    }

    #home-link img {
        transform: rotate(0);
        transition: transform 0.8s ease-in-out 0s;
    }

    #home-link:hover img {
        transform: rotate(-0.3turn);
    }
</style>