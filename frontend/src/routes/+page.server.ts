import type { PageServerLoad, Actions } from './$types';
import { BACKEND_URL } from '$lib/server/constants';
import { goto } from '$app/navigation';
import { ActionFailure, fail } from '@sveltejs/kit';

type FetchError = {
    status: number;
    message: string;
};

type LoadData = {
    status: number;
    gameId?: number;
};

export const load = (async (): Promise<LoadData | ActionFailure> => {
    const response = await fetch(BACKEND_URL + '/uniqueid');
    if (response.status == 200) {
        let data = await response.json()
        return {
            status: response.status,
            gameId: data['game_id']
        }
    } else {
        return fail(response.status);
    }
}) satisfies PageServerLoad;

export const actions: Actions = {
    connect: async (event) => {
        let data = await event.request.formData();
        const response = await fetch(BACKEND_URL + '/' + data.get('game-id') + '/info');
        if (response.status == 200) {
            console.log('Wheee')
        } else if (response.status == 404) {
            return fail(response.status, {
                status: response.status,
                message: 'Не найдено игры с таким Id.'
            });
        } else {
            return fail(response.status, {
                status: response.status,
                message: 'Ошибка ' + response.status
            });
        }

    },
    create: async (event) => {
        let data = await event.request.formData();
        const response = await fetch(BACKEND_URL + '/' + data.get('game-id'))
        if (response.status == 200) {
            // goto();
        }
        return fail(400);
    }
};