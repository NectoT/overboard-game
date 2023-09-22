import { eventSchemasToTs, schemaToTs, generateGameWebsocket } from "$lib/codegen";

// Автогенерация typescript-типов на основе схем игры и событий

let playerEvents = await eventSchemasToTs('playerevents');
let serverEvents = await eventSchemasToTs('serverevents', false);

generateGameWebsocket(Object.keys(playerEvents), Object.keys(serverEvents));
console.info('Generated GameWebsocket');

schemaToTs('game');
console.info('Generated game schemas');