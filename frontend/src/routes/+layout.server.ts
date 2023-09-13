import { BACKEND_URL } from '$lib/constants';
import type { LayoutServerLoad } from './$types';

export const load = (async ({cookies}) => {
    if (cookies.get('token') == null) {
        let token = crypto.randomUUID();
        cookies.set('token', token);

        let response = await fetch(BACKEND_URL + '/playerid', {
            headers: {
                Cookie: 'token=' + token
            }
        });
        cookies.set('playerId', (await response.json()).id);
    }
}) satisfies LayoutServerLoad;