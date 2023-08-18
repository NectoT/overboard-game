import type { PageServerLoad, Actions } from './$types';
import { BACKEND_URL } from '$lib/constants';
import { ActionFailure, fail, redirect } from '@sveltejs/kit';

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
            throw redirect(303, '/' + data.get('game-id'));
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
        let game_id = data.get('game-id');

        const response = await fetch(new URL('/create?game_id=' + game_id, BACKEND_URL), {
            method: "POST",
            credentials: 'include',
            headers: {
                // Короче actions не обладают теми же куки, что и +page.svelte, поэтому надо
                // вручную сюда вбивать куки с сайта. Почему бы не переделать эндпоинт у бэкэнда
                // и сделать client_id не куки параметром, а чем-то ещё? Хз
                Cookie: 'client_id=' + event.cookies.get('client_id')
            }
        })
        if (response.status == 200) {
            throw redirect(303, '/' + game_id);
        }
        return fail(400);
    }
};