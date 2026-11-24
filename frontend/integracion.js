/* Flujos de autenticación y compra de Tokyo Noodles. */
(function () {
    "use strict";

    function el(id) { return document.getElementById(id); }

    function mensaje(id, texto, tipo) {
        const destino = el(id);
        if (!destino) return;
        destino.textContent = texto;
        destino.className = "alert alert-" + (tipo || "info");
        destino.hidden = false;
    }

    function ocultarMensaje(id) {
        const destino = el(id);
        if (destino) {
            destino.hidden = true;
            destino.textContent = "";
        }
    }

    function destinoTrasLogin() {
        const solicitado = new URLSearchParams(window.location.search).get("return") || "menu.php";
        const destinosPermitidos = ["index.php", "menu.php", "promociones.php", "carrito.php", "verificar-correo.php"];
        return destinosPermitidos.includes(solicitado) ? solicitado : "menu.php";
    }

    function gestionarLogin() {
        const formulario = el("loginForm");
        if (!formulario) return;

        formulario.addEventListener("submit", async function (evento) {
            evento.preventDefault();
            ocultarMensaje("estado-login");
            const usuario = el("usuario").value.trim();
            const clave = el("password").value;
            const boton = el("btnLogin");
            if (!usuario || !clave) {
                mensaje("estado-login", "Ingresa tu usuario y contraseña.", "warning");
                return;
            }

            boton.disabled = true;
            boton.textContent = "Validando...";
            try {
                const identidad = await TokyoAPI.login(usuario, clave);
                el("password").value = "";
                mensaje("estado-login", "Sesión iniciada: " + identidad.username +
                    " (" + identidad.user_id + "). Redirigiendo...", "success");
                window.location.assign(destinoTrasLogin());
            } catch (error) {
                mensaje("estado-login", "No fue posible iniciar sesión: " + error.message,
                    error.status === 401 ? "warning" : "danger");
            } finally {
                boton.disabled = false;
                boton.textContent = "Iniciar Sesión";
            }
        });
    }

    async function mostrarSesionActual() {
        const estado = el("estado-sesion");
        if (!estado || !TokyoAPI.getToken()) return;
        try {
            const identidad = await TokyoAPI.getCurrentUser();
            estado.textContent = "Sesión activa: " + identidad.username + " · " +
                identidad.user_id + " · Roles: " + identidad.roles.join(", ");
            estado.className = "alert alert-success";
            estado.hidden = false;
            if (el("btnLogout")) el("btnLogout").hidden = false;
        } catch (error) {
            estado.textContent = "La sesión ya no está disponible. Inicia sesión nuevamente.";
            estado.className = "alert alert-warning";
            estado.hidden = false;
        }
    }

    function gestionarLogout() {
        const boton = el("btnLogout");
        if (!boton) return;
        boton.addEventListener("click", async function () {
            boton.disabled = true;
            try {
                await TokyoAPI.logout();
                mensaje("estado-sesion", "Sesión finalizada correctamente.", "info");
                boton.hidden = true;
            } catch (error) {
                mensaje("estado-sesion", "No se pudo cerrar la sesión: " + error.message, "danger");
            } finally {
                boton.disabled = false;
            }
        });
    }

    function mostrarResultadoPedido(order, payment) {
        const contenedor = el("resultadoPedido");
        if (!contenedor) return;
        contenedor.hidden = false;
        contenedor.replaceChildren();

        const titulo = document.createElement("h2");
        titulo.className = "h4";
        titulo.textContent = "Pedido registrado";
        contenedor.appendChild(titulo);

        const lista = document.createElement("ul");
        [
            "Pedido: " + order.id,
            "Estado del pedido: " + order.estado,
            "Total calculado por Orders: $" + Number(order.total).toLocaleString("es-CL"),
            "Pago: " + payment.id + " · " + payment.estado,
            "Estado del pago: pendiente de confirmación"
        ].forEach(function (dato) {
            const item = document.createElement("li");
            item.textContent = dato;
            lista.appendChild(item);
        });
        contenedor.appendChild(lista);

        const nota = document.createElement("p");
        nota.textContent = "El backend creó el pedido y la solicitud de pago. No se ha conectado un proveedor de pago real.";
        contenedor.appendChild(nota);

        const resumen = document.createElement("div");
        resumen.id = "resumenGraphQL";
        resumen.className = "mt-3";
        resumen.textContent = "Consultando resumen GraphQL...";
        contenedor.appendChild(resumen);
    }

    async function cargarResumenGraphQL(orderId) {
        const resumen = el("resumenGraphQL");
        if (!resumen) return;
        try {
            const respuesta = await TokyoAPI.getOrderSummary(orderId);
            if (respuesta.errors && respuesta.errors.length) {
                throw new Error(respuesta.errors.map(e => e.message).join("; "));
            }
            const pedido = respuesta.data && respuesta.data.resumenPedido;
            if (!pedido) throw new Error("GraphQL no devolvió el pedido solicitado.");

            resumen.replaceChildren();
            const titulo = document.createElement("h3");
            titulo.className = "h5";
            titulo.textContent = "Resumen consultado mediante GraphQL";
            resumen.appendChild(titulo);

            const estado = document.createElement("p");
            estado.textContent = "Pedido " + pedido.id + " · " + pedido.estado +
                " · Total $" + Number(pedido.total).toLocaleString("es-CL");
            resumen.appendChild(estado);

            const lista = document.createElement("ul");
            pedido.items.forEach(function (item) {
                const li = document.createElement("li");
                const disponibilidad = item.disponibleActual === null ? "no comprobada" :
                    (item.disponibleActual ? "disponible" : "no disponible");
                li.textContent = item.nombre + " × " + item.cantidad +
                    " · disponibilidad actual: " + disponibilidad;
                lista.appendChild(li);
            });
            resumen.appendChild(lista);
            if (pedido.advertencias && pedido.advertencias.length) {
                const advertencia = document.createElement("p");
                advertencia.className = "text-warning";
                advertencia.textContent = pedido.advertencias.join(" · ");
                resumen.appendChild(advertencia);
            }
        } catch (error) {
            resumen.textContent = "El pedido quedó registrado, pero no fue posible consultar GraphQL: " + error.message;
        }
    }


    function mostrarBotonReintentarPago(orderId) {
        const contenedor = el("estado-carrito");
        if (!contenedor) return;
        let boton = el("btnReintentarPago");
        if (!boton) {
            boton = document.createElement("button");
            boton.type = "button";
            boton.id = "btnReintentarPago";
            boton.className = "btn btn-dorado mt-2";
            boton.textContent = "Reintentar solicitud de pago";
            contenedor.appendChild(boton);
        }
        boton.onclick = function () { reintentarPago(orderId, boton); };
    }

    async function reintentarPago(orderId, boton) {
        boton.disabled = true;
        try {
            const payment = await TokyoAPI.createPayment(orderId);
            sessionStorage.removeItem("tn_pending_order_id");
            sessionStorage.removeItem("tn_codigo_compra");
            sessionStorage.removeItem("tn_compra_payload_json");
            sessionStorage.setItem("tn_last_order_id", orderId);
            const order = { id: orderId, estado: "pendiente_pago", total: payment.monto };
            guardarCarrito([]);
            if (typeof cargarCarrito === "function") cargarCarrito();
            mostrarResultadoPedido(order, payment);
            await cargarResumenGraphQL(orderId);
        } catch (error) {
            mensaje("estado-carrito", "El pedido " + orderId +
                " ya fue creado. No vuelvas a enviar el pedido; reintenta la solicitud de pago. " +
                error.message, "warning");
            mostrarBotonReintentarPago(orderId);
            boton.disabled = false;
        }
    }

    async function confirmarPedido() {
        const boton = el("btnConfirmarPedido");
        if (!boton) return;
        ocultarMensaje("estado-carrito");

        if (!TokyoAPI.getToken()) {
            window.location.assign("login.php?return=" + encodeURIComponent("carrito.php"));
            return;
        }

        const pedidoPendiente = sessionStorage.getItem("tn_pending_order_id");
        if (pedidoPendiente) {
            await reintentarPago(pedidoPendiente, boton);
            return;
        }

        const carrito = obtenerCarrito();
        if (!carrito.length) {
            mensaje("estado-carrito", "Tu carrito está vacío.", "warning");
            return;
        }

        const delivery = el("btnDelivery") && el("btnDelivery").classList.contains("activo");
        const modalidad = delivery ? "delivery" : "retiro";
        let direccion = null;
        let coordenadas = {};
        if (delivery) {
            direccion = [
                el("direccion") ? el("direccion").value.trim() : "",
                el("depto") ? el("depto").value.trim() : "",
                el("referencia") ? el("referencia").value.trim() : ""
            ].filter(Boolean).join(", ");
            if (!direccion) {
                mensaje("estado-carrito", "Ingresa la dirección para delivery.", "warning");
                return;
            }
            const latTxt = el("latitude") ? el("latitude").value.trim() : "";
            const lonTxt = el("longitude") ? el("longitude").value.trim() : "";
            if (!latTxt || !lonTxt || !Number.isFinite(Number(latTxt)) || !Number.isFinite(Number(lonTxt))) {
                mensaje("estado-carrito", "Indica coordenadas de destino válidas para comprobar cobertura de 3 km.", "warning");
                return;
            }
            coordenadas = {latitude: Number(latTxt), longitude: Number(lonTxt)};
        }

        boton.disabled = true;
        boton.textContent = "Registrando pedido...";
        try {
            // Conserva el mismo código ante reintentos de la misma compra;
            // genera otro si el usuario modifica carrito o modalidad.
            const datosCompra = {
                modalidad: modalidad,
                direccion: direccion,
                ...coordenadas,
                items: carrito.map(item => ({
                    product_id: String(item.id),
                    quantity: Number(item.cantidad)
                }))
            };
            const resumenCompra = JSON.stringify(datosCompra);
            let codigoCompra = sessionStorage.getItem("tn_codigo_compra");
            if (!codigoCompra || sessionStorage.getItem("tn_compra_payload_json") !== resumenCompra) {
                codigoCompra = window.crypto && window.crypto.randomUUID
                    ? window.crypto.randomUUID()
                    : "tn-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2);
                sessionStorage.setItem("tn_codigo_compra", codigoCompra);
                sessionStorage.setItem("tn_compra_payload_json", resumenCompra);
            }

            const pedido = await TokyoAPI.createOrder({codigo_compra: codigoCompra, ...datosCompra});

            // El ID permite reintentar el pago sin crear otro pedido.
            sessionStorage.setItem("tn_pending_order_id", pedido.id);
            boton.textContent = "Iniciando pago...";
            const pago = await TokyoAPI.createPayment(pedido.id);

            sessionStorage.removeItem("tn_pending_order_id");
            sessionStorage.removeItem("tn_codigo_compra");
            sessionStorage.removeItem("tn_compra_payload_json");
            sessionStorage.setItem("tn_last_order_id", pedido.id);
            guardarCarrito([]);
            if (typeof cargarCarrito === "function") cargarCarrito();

            const modal = el("modalPedido");
            if (modal && window.bootstrap) {
                const instancia = window.bootstrap.Modal.getInstance(modal);
                if (instancia) instancia.hide();
            }
            mostrarResultadoPedido(pedido, pago);
            await cargarResumenGraphQL(pedido.id);
        } catch (error) {
            const orderId = sessionStorage.getItem("tn_pending_order_id");
            if (orderId) {
                mensaje("estado-carrito", "El pedido " + orderId +
                    " ya quedó registrado. La solicitud de pago no se completó; no vuelvas a crear el pedido.", "warning");
                mostrarBotonReintentarPago(orderId);
            } else {
                mensaje("estado-carrito", "No fue posible registrar el pedido: " + error.message,
                    error.status === 401 ? "warning" : "danger");
            }
        } finally {
            boton.disabled = false;
            boton.textContent = "Continuar";
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        gestionarLogin();
        gestionarLogout();
        const ubicacion = el("btnUbicacion");
        if (ubicacion) ubicacion.addEventListener("click", function () {
            const estado = el("ubicacionEstado");
            if (!navigator.geolocation) { estado.textContent = "Geolocalización no disponible."; return; }
            estado.textContent = "Solicitando permiso de ubicación...";
            navigator.geolocation.getCurrentPosition(function (pos) {
                el("latitude").value = pos.coords.latitude.toFixed(6);
                el("longitude").value = pos.coords.longitude.toFixed(6);
                estado.textContent = "Coordenadas obtenidas. Confirma que corresponden al domicilio de entrega.";
            }, function () { estado.textContent = "No se pudo obtener ubicación; introduce las coordenadas manualmente."; },
            {enableHighAccuracy: true, timeout: 12000});
        });
        const boton = el("btnConfirmarPedido");
        if (boton) boton.addEventListener("click", confirmarPedido);
        mostrarSesionActual();

        window.addEventListener("tokyo:session-expired", function () {
            const estado = el("estado-sesion");
            if (estado) {
                estado.textContent = "La sesión expiró. Inicia sesión nuevamente.";
                estado.className = "alert alert-warning";
                estado.hidden = false;
            }
        });
    });
})();
