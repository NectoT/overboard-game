<script>
    export let text = "Ошибка";
</script>

<div id='container'>
    {text}
</div>

<style>
    #container {
        display: flex;
        align-items: center;

        margin-top: 3px;
        margin-bottom: 3px;
        padding: 10px;
        width: 100%;
        background-color: rgba(254, 148, 148, 0.7);
        border-color: rgba(254, 130, 130, 0.9);
        border-style: solid;
        border-width: 2px;
        border-radius: 15px;
        box-sizing: border-box;

        color: rgb(159, 0, 0);
        font-family: var(--font-family);
        font-size: 1rem;
    }
</style>