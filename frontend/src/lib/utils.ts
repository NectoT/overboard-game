import type { UNKNOWN } from "./gametypes";

/**
 * Помечает информацию как известную
 * 
 * Вспомогательная функция для использования потенциально неизвестной информации
 * в html-части svelte файлов. Потому что блин почему-то typescript-синтаксис (типо as) 
 * там не поддерживается, но вот мой
 * intellisense считает, что там typescript и типизацию проверяет
 * */
export function known<T>(info: T | UNKNOWN): T {
    return info as T;
}