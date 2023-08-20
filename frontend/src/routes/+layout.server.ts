import type { LayoutServerLoad } from './$types';

export const load = (async ({cookies}) => {
    if (cookies.get('client_id') == null) {
        cookies.set('client_id', crypto.randomUUID())
    }
}) satisfies LayoutServerLoad;