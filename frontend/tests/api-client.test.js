const assert = require('node:assert/strict');
const crypto = require('node:crypto');

const almacen = new Map();
global.window = global;
global.window.crypto = crypto.webcrypto;
global.window.TOKYO_API_BASE_URL = 'http://127.0.0.1:8000/api';
global.window.dispatchEvent = () => {};
global.CustomEvent = class CustomEvent { constructor(type) { this.type = type; } };
global.sessionStorage = {
    getItem: (key) => almacen.has(key) ? almacen.get(key) : null,
    setItem: (key, value) => almacen.set(key, String(value)),
    removeItem: (key) => almacen.delete(key)
};

const llamadas = [];
global.fetch = async (url, options) => {
    llamadas.push({ url, options });
    let payload = {};
    if (url.endsWith('/auth/login')) {
        payload = { access_token: 'token-ficticio-test', token_type: 'bearer', expires_in: 900 };
    } else if (url.endsWith('/auth/me')) {
        payload = { user_id: 'USR-001', username: 'ana', roles: ['user'] };
    } else if (url.endsWith('/public/products')) {
        payload = { products: [{ id: '1', nombre: 'Shio Ramen', precio: 13800 }] };
    } else if (url.endsWith('/orders')) {
        payload = { id: 'ORD-TEST', estado: 'pendiente_pago', total: 13800 };
    } else if (url.endsWith('/payments')) {
        payload = { id: 'PAY-TEST', order_id: 'ORD-TEST', monto: 13800, estado: 'pendiente' };
    } else if (url.endsWith('/graphql')) {
        payload = { data: { resumenPedido: { id: 'ORD-TEST' } } };
    } else if (url.endsWith('/auth/logout')) {
        payload = { message: 'Sesion finalizada' };
    }
    return new Response(JSON.stringify(payload), {
        status: 200,
        headers: { 'Content-Type': 'application/json', 'X-Operacion': 'operacion-test-1234' }
    });
};

require('../api.js');

(async () => {
    const identidad = await TokyoAPI.login('ana', 'test-password');
    assert.equal(identidad.user_id, 'USR-001');
    assert.equal(almacen.get('tn_access_token'), 'token-ficticio-test');

    const catalogo = await TokyoAPI.getCatalog();
    assert.equal(catalogo.products.length, 1);
    assert.equal(llamadas[2].options.headers.get('Authorization'), null);

    await TokyoAPI.createOrder(
        { codigo_compra: '12345678-1234-1234-1234-123456789012', modalidad: 'retiro', items: [{ product_id: '1', quantity: 1 }] }
    );
    assert.equal(llamadas[3].options.headers.get('Authorization'), 'Bearer token-ficticio-test');
    assert.equal(llamadas[3].options.headers.get('X-Operacion'), null);
    assert.equal(llamadas[3].options.headers.get('Authorization'), 'Bearer token-ficticio-test');
    assert.equal(JSON.parse(llamadas[3].options.body).codigo_compra, '12345678-1234-1234-1234-123456789012');

    await TokyoAPI.createPayment('ORD-TEST');
    await TokyoAPI.getOrderSummary('ORD-TEST');
    await TokyoAPI.logout();
    assert.equal(almacen.has('tn_access_token'), false);
    assert.equal(almacen.has('tn_access_token_expires_at'), false);
    assert.equal(llamadas.length, 7);
    console.log('Frontend API client tests: 7 requests verified; auth, public catalogue, codigo_compra, payment, GraphQL and logout OK.');
})().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
