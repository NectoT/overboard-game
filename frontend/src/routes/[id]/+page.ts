import { WEBSOCKET_URL } from '$lib/constants';
import type { PageLoad } from './$types';

export const ssr = false;

export const load = (async ({params, data}) => {
    // Так как этот класс наследуется от WebSocket, он доступен только для клиентской стороны.
    // А если импортировать как обычно в начале файла, сервер тоже попытается импортировать
    // файл и ляжет. Вот дурак.
    let GameWebsocket = (await import('$lib/game_websocket')).GameWebsocket;

    let websocket = new GameWebsocket(
        WEBSOCKET_URL + '/' + params['id'] + '?token=' + data.clientToken, data.clientToken
    );
    return {
        ...data,
        websocket
    };
}) satisfies PageLoad;