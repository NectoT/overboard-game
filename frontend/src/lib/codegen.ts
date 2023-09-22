import { writeFileSync, readFileSync } from "node:fs";
import { compile, type Options } from "json-schema-to-typescript";
import { BACKEND_URL } from "$lib/constants";

type Schema = {
    [key: string]: any
    properties?: {[property: string]: any},
    definitions?: {[property: string]: any}
}

type Schemas = {
    [eventName: string]: Schema
}

/**
 * Убирает все использования поля
 * @param schema
 * @param key Название ключа, который нужно убрать
 */
function removeKeyFromSchema(schema: {[key: string]: any}, key: string) {
    for (const k in schema) {
        if (typeof schema[k] === 'object') {
            removeKeyFromSchema(schema[k], key);
        }
        if (k === key) {
            delete schema[key];
        }
    }
}

function markDefaultAsRequired(schema: Schema) {
    if (Object.hasOwn(schema, 'properties')) {
        let required: string[] = [];
        for (let property in schema.properties) {
            if (Object.hasOwn(schema.properties[property], 'default')) {
                required.push(property);
            }
        }
        if (Object.hasOwn(schema, 'required')) {
            schema.required.concat(required);
        } else {
            schema.required = required;
        }
    }
    if (Object.hasOwn(schema, 'definitions')) {
        for (let name in schema.definitions) {
            if (Object.hasOwn(schema.definitions[name], 'properties')) {
                markDefaultAsRequired(schema.definitions[name])
            }
        }
    }
}

/**
 *
 * @returns список схем событий
 */
export async function eventSchemasToTs(schemasURL: string, defaultRequired=true): Promise<Schema> {
    let schemas: Schema = await fetch(BACKEND_URL + '/schemas/' + schemasURL).then(data => data.json());

    removeKeyFromSchema(schemas.definitions!, 'title');

    if (defaultRequired) {
        for (let name in schemas.definitions!) {
            removeKeyFromSchema(schemas.definitions![name], 'default');
            markDefaultAsRequired(schemas.definitions![name]);
        }
    }

    let compileOptions: Partial<Options> = {unreachableDefinitions: true, additionalProperties: false};

    compile(schemas, schemasURL, compileOptions).then((result) => {
        writeFileSync(`src/lib/gametypes/${schemasURL}.ts`, result);
    })

    // Фильтруем `schemas.definitions` так, чтобы остались только определения событий
    return schemas.event_names.reduce((obj: {[key: string]: any}, key: string) => {
        obj[key] = schemas.definitions;
        return obj;
    }, {});
}

export async function schemaToTs(schemaURL: string, defaultRequired=true): Promise<void> {
    let schema = await fetch(BACKEND_URL + '/schemas/' + schemaURL).then(data => data.json());
    removeKeyFromSchema(schema, 'title');

    if (defaultRequired) {
        // removeKeyFromSchema(schema, 'default');
        markDefaultAsRequired(schema)
    }

    let compileOptions: Partial<Options> = {unreachableDefinitions: true, additionalProperties: false};

    compile(schema, schemaURL, compileOptions).then((result) => {
        writeFileSync(`src/lib/gametypes/${schemaURL}.ts`, result);
    })
}

/** Генерация ts-файла с классом GameWebsocket */
export function generateGameWebsocket(
    playerEvents: string[], serverEvents: string[]) {

    let ommitedSendTypeName = "UnnecessaryForSend";
    let ommitedSendTypeBody = `"player_id" | "type" | "client_token" | "observed"`;

    let sendMethods: string[] = [];
    for (const eventName of playerEvents) {
        sendMethods.push(`
        send${eventName}(event: Omit<${eventName}, ${ommitedSendTypeName}>) {
            this.sendEvent({...event, type: "${eventName}", client_token: this.token});
        }
        `);
    }

    let onMethods: string[] = [];
    for (const eventName of (serverEvents.concat(playerEvents))) {
        onMethods.push(`
        set on${eventName}(handler: (event: Required<${eventName}>) => Promise<void> | void) {
            this.handlers["${eventName}"] = handler;
        }
        `);
    }

    let buffer = readFileSync('src/lib/codegen_templates/game_websocket.ts');

    let gameWebsocket = buffer.toString();
    gameWebsocket = gameWebsocket.replace(
        '{% imports %}',
        [
        `import type { ${playerEvents.join(', ')} } from "./gametypes/playerevents"`,
        `import type { ${serverEvents.join(', ')} } from "./gametypes/serverevents"`
        ].join('\n')
    );
    gameWebsocket = gameWebsocket.replace(
        '{% types %}',
        `type ${ommitedSendTypeName} = ${ommitedSendTypeBody}\n`
    );
    gameWebsocket = gameWebsocket.replace('{% sendMethods %}', sendMethods.join(''));
    gameWebsocket = gameWebsocket.replace('{% onMethods %}', onMethods.join(''));

    let comment = '/** Автосгенерированно в `codegen.ts` */\n\n';

    writeFileSync('src/lib/game_websocket.ts', comment + gameWebsocket);
}