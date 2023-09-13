import { WEBSOCKET_URL } from '$lib/constants';
import type { PlayerEvent } from '$lib/gametypes';
import type { PageLoad } from './$types';

export const ssr = false;

/** Вебсокет с методом отправки игрового события `sendEvent` */
export interface WebSocketMixin extends WebSocket {
    /** Отправляет игровое событие на сервер */
    sendEvent(event: PlayerEvent): void
};

export const load = (async ({params, data}) => {

    class WebSocketMixin extends WebSocket {
        sendEvent(event: PlayerEvent) {
            console.log("Sent " + event.type);
            this.send(JSON.stringify(event));
        }
    }

    let websocket = new WebSocketMixin(
        WEBSOCKET_URL + '/' + params['id'] + '?token=' + data.clientToken
    );
    return {
        ...data,
        websocket
    };
}) satisfies PageLoad;