import { cubicInOut, cubicOut } from "svelte/easing";
import type { EasingFunction, FlyParams } from "svelte/transition";

/**
     * Кастомная версия функции crossfade от svelte.
     *
     * Упрощённо, используется для анимированного перехода одного и того же элемента из одного
     * места в DOM дереве в другое
     * @param duration Время перехода в ms (милисекундах)
     * @param easing
     * @returns Два transitions. Первый используется при удалении элемента из DOM-дерева, второй
     * используется при добавлении
     */
export function cardCrossfade(duration: number = 500, easing: EasingFunction = cubicInOut) {
    let in_items: Map<any, Element> = new Map();
    let out_items: Map<any, Element> = new Map();

    function receive(element: Element, key: any) {
        in_items.set(key, element);
        // Хрен знает почему, но deferred transtition возвращает функцию, а не объект с
        // css-указаниями, как обычный transition
        return () => _receive(element, key);
    }

    function _receive(element: Element, key: any) {
        if (!out_items.has(key)) {
            console.log('Custom crossfade receive could not find sending element');
            console.log(out_items);
            return {};
        }

        const from = out_items.get(key)!;
        out_items.delete(key);

        const fromRect = from.getBoundingClientRect();
        const elRect = element.getBoundingClientRect();

        const dX = (elRect.left + elRect.right - fromRect.left - fromRect.right) / 2;
        const dY = (elRect.top + elRect.bottom - fromRect.top - fromRect.bottom) / 2;

        let getTransformMatrix = (style: CSSStyleDeclaration) => {
            if (style.transform === 'none') {
                return [1, 0, 0, 1, 0, 0];
            }
            console.log(style.transform);
            let strings = style.transform.substring(7, style.transform.length - 1).split(", ");
            return strings.map((value) => parseFloat(value));
        }

        let elTransform = getTransformMatrix(getComputedStyle(element));
        let fromTransform = getTransformMatrix(getComputedStyle(from));

        return {
            duration,
            easing,
            css: (t: number, u: number) => {
                let transformMatrix: Array<number> = [];
                for (let i = 0; i < elTransform.length; i++) {
                    transformMatrix.push(elTransform[i] * t + fromTransform[i] * u);
                }
                let transform = 'matrix(' + transformMatrix.join(', ') + ')';
                return `
                transform-origin: center;
                transform: translate(${-dX * u}px, ${-dY * u}px) ${transform};
                `
            }
        };
    }

    function send(element: Element, key: any) {
        out_items.set(key, element);
        // Хрен знает почему, но deferred transtition возвращает функцию, а не объект с
        // css-указаниями, как обычный transition
        return () => _send(element, key);
    }

    function _send(element: Element, key: any) {
        if (!in_items.has(key)) {
            console.log('Custom crossfade send could not find receiving element');
            return {};
        }

        const to = in_items.get(key)!;
        in_items.delete(key);

        return {
            duration,
            css: (t: number, u: number) => `filter: opacity(0);`
        };
    }

    return [send, receive];
}

/** Элемент прилетает из указанных координат `x` `y`
 *
 *  @param dissapear - Должен ли элемент исчезать в конце transition
 * */
export function flyFrom(
   node: Element,
   {
    delay = 0,
    duration = 400,
    easing = cubicOut,
    dissapear = false,
    x = 0, y = 0 } = {})
{
    const nodeRect = node.getBoundingClientRect();
    let dx = x - nodeRect.left; //- nodeRect.width / 2;
    let dy = y - nodeRect.top; //- nodeRect.height / 2;

    const style = getComputedStyle(node);
    const transform = style.transform === 'none' ? '' : style.transform;

    // return fly(node, {x: dx, y: dy});

    return {
        delay,
        duration,
        easing,
        css: (t: number, u: number) => {
            let scale = dissapear ? Math.min(1, u * 3) : 1;
            return `
            transform: ${transform} translateX(${dx * u}px) translateY(${dy * u}px) scale(${scale});
            filter: opacity(${t});
            transform-origin: center;
            `
        }
    }
}
