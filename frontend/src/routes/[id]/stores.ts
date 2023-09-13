import { writable } from "svelte/store";

export let clientToken = writable('');
export let playerId = writable('');