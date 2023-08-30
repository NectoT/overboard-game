import { error, fail } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import type { Game } from '$lib/gametypes';
import { BACKEND_URL } from '$lib/constants';

export const load = (async ( { params, cookies } ) => {
    let clientId = cookies.get('client_id')!;
    let response = await fetch(BACKEND_URL + '/' + params.id, {
        headers: {
            Cookie: 'client_id=' + clientId
        }
    });
    let gameData: Game = await response.json();
    return {
        game: gameData,
        clientId: clientId
    };
}) satisfies PageServerLoad;