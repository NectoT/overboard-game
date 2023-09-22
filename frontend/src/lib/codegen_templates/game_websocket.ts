{% imports %}

{% types %}

/**
 * API для вебсокет-соединения с возможностью слушать и посылать игровые события
 * 
 * Когда `GameWebsocket` получает новое событие, он добавляет обработку события в очередь,
 * то есть все обработчики события ждут, пока предыдущие закончат свою работу
 */
// @ts-ignore: WebSocket is not defined
export class GameWebsocket extends WebSocket {
    /** Обработчики игровых событий. Для каждого события может быть только один обработчик */
    handlers: {[eventName: string]: (event: any) => void} = {};

    /** Уникальный идентификатор клиента */
    token: string;
    
    /** 
     * Очередь обработчиков событий, реализованная как цепочка Promise
     */
    #handlerQueue: Promise<void> = Promise.resolve()

    constructor(url: string | URL, token: string, protocols?: string | string[]) {
        super(url, protocols);
        this.token = token;
        this.onmessage = (e) => {
            let data = JSON.parse(e.data);
            if (data.type === undefined) {
                throw Error("GameWebsocket received an unknown message")
            }
            let handler = this.handlers[data.type];
            if (handler === undefined) {
                console.warn(`GameWebsocket received an unhandled event ${data.type}. Ignoring...`);
            } else {
                console.log("Received " + data.type)
                this.#handlerQueue = this.#handlerQueue.then(() => handler(data));
            }
        }
    }

    
    {% sendMethods %}
    

    sendEvent(gameEvent: any) {
        console.log("Sent " + gameEvent.type);
        this.send(JSON.stringify(gameEvent));
    }

    
    {% onMethods %}
}
    