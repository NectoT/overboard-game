import { error, fail } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import type { Game } from '$lib/gametypes';
import { BACKEND_URL } from '$lib/constants';

export const load = (async ( { params, cookies } ) => {
    let response = await fetch(BACKEND_URL + '/' + params.id);
    let gameData: Game = await response.json();
    return {
        game: gameData,
        clientId: cookies.get('client_id')!
    };
}) satisfies PageServerLoad;