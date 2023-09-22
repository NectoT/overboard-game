import { error, fail } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import type { Game } from '$lib/gametypes/game';
import { BACKEND_URL } from '$lib/constants';

export const load = (async ( { params, cookies } ) => {
    let token = cookies.get('token')!;
    let response = await fetch(BACKEND_URL + '/' + params.id, {
        headers: {
            Cookie: 'token=' + token
        }
    });
    let gameData: Required<Game> = await response.json();
    return {
        game: gameData,
        clientToken: token,
        playerId: cookies.get('playerId')!
    };
}) satisfies PageServerLoad;