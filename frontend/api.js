/*
 * Cliente HTTP del frontend Tokyo Noodles.
 * El navegador solo recibe el token de sesión del usuario.
 * Los secretos internos permanecen en Vault y nunca se exponen aquí.
 */
(function () {
    "use strict";

    const API_BASE_URL = (
        window.TOKYO_API_BASE_URL || "http://127.0.0.1:8000/api"
    ).replace(/\/+$/, "");

    const TOKEN_KEY = "tn_access_token";
    const EXPIRY_KEY = "tn_access_token_expires_at";


    function obtenerToken() {
        const token = sessionStorage.getItem(TOKEN_KEY);
        const vence = Number(sessionStorage.getItem(EXPIRY_KEY) || 0);
        if (token && vence && Date.now() >= vence) {
            limpiarSesion();
            return null;
        }
        return token;
    }

    function guardarSesion(datos) {
        if (!datos || !datos.access_token) {
            throw new Error("Auth Service no devolvió un token de acceso.");
        }
        sessionStorage.setItem(TOKEN_KEY, datos.access_token);
        sessionStorage.setItem(
            EXPIRY_KEY,
            String(Date.now() + Number(datos.expires_in || 900) * 1000)
        );
    }

    function limpiarSesion() {
        sessionStorage.removeItem(TOKEN_KEY);
        sessionStorage.removeItem(EXPIRY_KEY);
    }

    async function apiRequest(ruta, opciones) {
        const config = opciones || {};
        const requiereAuth = config.auth !== false;
        const headers = new Headers(config.headers || {});
        const metodo = config.method || "GET";
        let body = config.body;

        if (requiereAuth) {
            const token = obtenerToken();
            if (token) headers.set("Authorization", "Bearer " + token);
        }


        if (
            body !== undefined && body !== null && typeof body !== "string" &&
            !(body instanceof FormData)
        ) {
            headers.set("Content-Type", "application/json");
            body = JSON.stringify(body);
        }

        const respuesta = await fetch(
            API_BASE_URL + (ruta.startsWith("/") ? ruta : "/" + ruta),
            {
                method: metodo,
                headers: headers,
                body: body,
                mode: "cors",
                credentials: "omit",
                cache: "no-store"
            }
        );

        const texto = await respuesta.text();
        let datos = null;
        if (texto) {
            try { datos = JSON.parse(texto); }
            catch { datos = { detail: texto }; }
        }

        if (respuesta.status === 401 && requiereAuth) {
            limpiarSesion();
            window.dispatchEvent(new CustomEvent("tokyo:session-expired"));
        }

        if (!respuesta.ok) {
            const mensaje = datos && (datos.detail || datos.message || datos.error);
            const error = new Error(mensaje || ("La API respondió HTTP " + respuesta.status));
            error.status = respuesta.status;
            error.operacionId = respuesta.headers.get("X-Operacion");
            error.response = datos;
            throw error;
        }
        return datos;
    }

    async function apiLogin(username, password) {
        const datos = await apiRequest("/auth/login", {
            method: "POST",
            auth: false,
            body: { username: username, password: password }
        });
        guardarSesion(datos);
        try {
            return await apiRequest("/auth/me");
        } catch (error) {
            limpiarSesion();
            throw error;
        }
    }

    async function apiLogout() {
        try {
            if (obtenerToken()) {
                await apiRequest("/auth/logout", { method: "POST", body: {} });
            }
        } finally {
            limpiarSesion();
        }
    }

    window.TokyoAPI = {
        baseUrl: API_BASE_URL,
        request: apiRequest,
        login: apiLogin,
        logout: apiLogout,
        getToken: obtenerToken,
        clearSession: limpiarSesion,
        getCurrentUser: function () { return apiRequest("/auth/me"); },
        register: function (datos) { return apiRequest("/auth/register", {method: "POST", auth: false, body: datos}); },
        sendEmailCode: function (id) {return apiRequest("/clients/"+encodeURIComponent(id)+"/email/send-code",{method:"POST",body:{}});},
        verifyEmailCode: function (id, codigo) {return apiRequest("/clients/"+encodeURIComponent(id)+"/email/verify",{method:"POST",body:{codigo}});},
        retryOrderEvent: function (id) {return apiRequest("/orders/"+encodeURIComponent(id)+"/publish-event",{method:"POST",body:{}});},
        getMyProfile: async function () {
            const me = await apiRequest("/auth/me");
            return apiRequest("/clients/" + encodeURIComponent(me.user_id));
        },
        getOrders: function () { return apiRequest("/orders"); },
        getOrder: function (id) { return apiRequest("/orders/" + encodeURIComponent(id)); },
        getPaymentForOrder: function (id) { return apiRequest("/payments/order/" + encodeURIComponent(id)); },
        cancelOrder: function (id, motivo) { return apiRequest("/orders/" + encodeURIComponent(id) + "/cancel", {method: "POST", body: {motivo}}); },
        getReceipt: function (id) { return apiRequest("/orders/" + encodeURIComponent(id) + "/comprobante"); },
        confirmTestPayment: function (id) { return apiRequest("/payments/" + encodeURIComponent(id) + "/test-confirm", {method: "POST", body: {}}); },
        updateOrderStatus: function (id, estado) { return apiRequest("/orders/" + encodeURIComponent(id) + "/status", {method: "PUT", body: {estado}}); },
        getSalesReport: function (desde, hasta) { return apiRequest("/orders/reporte-ventas?desde=" + encodeURIComponent(desde) + "&hasta=" + encodeURIComponent(hasta)); },
        getEventStatus: function () { return apiRequest("/orders/eventos"); },
        updateProduct: function (id, product) { return apiRequest("/products/" + encodeURIComponent(id), {method: "PUT", body: product}); },
        getClients: function () { return apiRequest("/clients"); },
        getCatalog: function () { return apiRequest("/public/products", { auth: false }); },
        createOrder: function (datos) { return apiRequest("/orders", {method: "POST", body: datos}); },
        createPayment: function (orderId) {
            return apiRequest("/payments", { method: "POST", body: { order_id: orderId } });
        },
        getOrderSummary: function (orderId) {
            const query = `query ResumenPedido($id: ID!) {
                resumenPedido(id: $id) {
                    id estado total modalidad
                    items { productId nombre cantidad precioUnitario subtotal disponibleActual }
                    advertencias
                }
            }`;
            return apiRequest("/graphql", {
                method: "POST",
                body: { query: query, variables: { id: orderId } }
            });
        }
    };
})();
