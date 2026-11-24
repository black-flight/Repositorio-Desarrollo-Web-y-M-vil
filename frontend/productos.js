let responseAPI = {
    status: 0,
    message: "Catálogo pendiente de cargar",
    data: []
};


async function cargarCatalogo() {
    try {
        const respuesta = await TokyoAPI.getCatalog();
        responseAPI = {
            status: 200,
            message: "Productos obtenidos desde Inventory",
            data: Array.isArray(respuesta.products) ? respuesta.products : []
        };
        cargarProductos();
        cargarCarrito();
        actualizarContadorCarrito();

        const estado = document.getElementById("estado-catalogo");
        if (estado) {
            // El catalogo se muestra directamente; no exponer mensajes tecnicos al cliente.
            estado.textContent = "";
            estado.hidden = true;
        }
        const estadoCarrito = document.getElementById("estado-carrito");
        if (estadoCarrito && estadoCarrito.textContent.startsWith("No fue posible cargar el catálogo:")) {
            estadoCarrito.hidden = true;
            estadoCarrito.textContent = "";
        }
        return responseAPI.data;
    } catch (error) {
        responseAPI = { status: 0, message: error.message, data: [] };
        const estado = document.getElementById("estado-catalogo") ||
            document.getElementById("estado-carrito");
        if (estado) {
            estado.textContent = "No pudimos cargar el menú. Actualiza la página e inténtalo de nuevo.";
            estado.className = "alert alert-danger";
            estado.hidden = false;
        }
        console.error("Error al cargar catálogo:", error);
        return [];
    }
}


function mostrarAviso(mensaje, tipo) {
    const estado = document.getElementById("estado-carrito") ||
        document.getElementById("estado-catalogo");
    if (estado) {
        estado.textContent = mensaje;
        estado.className = "alert alert-" + (tipo || "info");
        estado.hidden = false;
        return;
    }
    console.info(mensaje);
}

function formatearPrecio(valor) {

    return "$" + valor.toLocaleString("es-CL");

}


function obtenerCarrito() {

    let carritoGuardado = localStorage.getItem("carritoTokyo");

    if (carritoGuardado == null) {

        return [];

    }

    return JSON.parse(carritoGuardado);

}


function guardarCarrito(carrito) {

    localStorage.setItem(
        "carritoTokyo",
        JSON.stringify(carrito)
    );

    actualizarContadorCarrito();

}


function agregarProducto(id) {

    const producto = buscarProducto(id);
    if (!producto) {
        mostrarAviso("El producto no está disponible en el catálogo del backend.", "warning");
        return;
    }
    if (producto.available === false) {
        mostrarAviso("Este producto está temporalmente no disponible.", "warning");
        return;
    }

    let carrito = obtenerCarrito();

    let encontrado = false;


    carrito.forEach((item) => {

        if (item.id == id) {

            item.cantidad = item.cantidad + 1;

            encontrado = true;

        }

    });


    if (encontrado == false) {

        carrito.push({
            "id": id,
            "cantidad": 1
        });

    }


    guardarCarrito(carrito);
    confirmarAgregadoAlCarrito(producto.nombre);

}

function confirmarAgregadoAlCarrito(nombre) {
    let aviso = document.getElementById("tn-toast-carrito");
    if (!aviso) {
        aviso = document.createElement("div");
        aviso.id = "tn-toast-carrito";
        aviso.className = "tn-toast-carrito";
        aviso.setAttribute("role", "status");
        aviso.setAttribute("aria-live", "polite");
        document.body.appendChild(aviso);
    }
    aviso.textContent = nombre + " agregado a tu carrito";
    aviso.hidden = false;
    clearTimeout(confirmarAgregadoAlCarrito.temporizador);
    confirmarAgregadoAlCarrito.temporizador = setTimeout(function () {
        aviso.hidden = true;
    }, 2600);
}


function actualizarContadorCarrito() {

    let carrito = obtenerCarrito();

    let cantidadTotal = 0;


    carrito.forEach((item) => {

        cantidadTotal = cantidadTotal + item.cantidad;

    });


    let contador = document.getElementById("contador-carrito");

    if (contador != null) {

        contador.innerText = cantidadTotal;

    }


    let titulo = document.getElementById("cantidad-carrito-titulo");

    if (titulo != null) {

        titulo.innerText = cantidadTotal;

    }

}


function buscarProducto(id) {

    let productoEncontrado = null;


    responseAPI.data.forEach((prod) => {
        if (String(prod.id) === String(id)) productoEncontrado = prod;
    });


    return productoEncontrado;

}


function cambiarCantidad(id, cambio) {

    let carrito = obtenerCarrito();


    for (let i = 0; i < carrito.length; i++) {

        if (carrito[i].id == id) {

            carrito[i].cantidad =
                carrito[i].cantidad + cambio;


            if (carrito[i].cantidad <= 0) {

                carrito.splice(i, 1);

            }

            break;

        }

    }


    guardarCarrito(carrito);

    cargarCarrito();

}


function cargarProductos() {

    console.log(
        "Tipo de responseAPI:",
        typeof responseAPI
    );


    let ramen =
        document.getElementById("productos-ramen");

    let barra =
        document.getElementById("productos-barra");


    if (ramen == null || barra == null) return;
    ramen.innerHTML = "";
    barra.innerHTML = "";

    responseAPI.data.forEach((prod) => {

        if (prod.available === false) return;

        if (
            prod.categoria != "ramen" &&
            prod.categoria != "barra"
        ) {

            return;

        }


        let columna =
            document.createElement("div");

        columna.setAttribute(
            "class",
            "col-12 col-lg-6"
        );


        let tarjeta =
            document.createElement("div");

        tarjeta.setAttribute(
            "class",
            "tarjeta-producto"
        );


        let fila =
            document.createElement("div");

        fila.setAttribute(
            "class",
            "row align-items-center"
        );


        let columnaImagen =
            document.createElement("div");

        columnaImagen.setAttribute(
            "class",
            "col-12 col-sm-5"
        );


        let imagen =
            document.createElement("img");

        imagen.setAttribute(
            "src",
            prod.imagen
        );

        imagen.setAttribute(
            "alt",
            prod.nombre
        );


        columnaImagen.appendChild(imagen);


        let informacion =
            document.createElement("div");

        informacion.setAttribute(
            "class",
            "col-12 col-sm-7 mt-3 mt-sm-0"
        );


        let nombre =
            document.createElement("h3");

        nombre.innerText =
            prod.nombre;


        let descripcion =
            document.createElement("p");

        descripcion.innerText =
            prod.descripcion;


        let inferior =
            document.createElement("div");

        inferior.setAttribute(
            "class",
            "d-flex justify-content-between align-items-center"
        );


        let precio =
            document.createElement("span");

        precio.setAttribute(
            "class",
            "precio"
        );

        precio.innerText =
            formatearPrecio(prod.precio);


        let boton =
            document.createElement("button");

        boton.setAttribute(
            "type",
            "button"
        );

        boton.setAttribute(
            "class",
            "btn btn-dorado"
        );

        boton.setAttribute(
            "onclick",
            "agregarProducto('" + prod.id + "')"
        );

        boton.innerText = "Agregar";
        boton.setAttribute("aria-label", "Agregar " + prod.nombre + " al carrito");


        inferior.appendChild(precio);
        inferior.appendChild(boton);

        informacion.appendChild(nombre);
        informacion.appendChild(descripcion);
        informacion.appendChild(inferior);

        fila.appendChild(columnaImagen);
        fila.appendChild(informacion);

        tarjeta.appendChild(fila);

        columna.appendChild(tarjeta);


        if (prod.categoria == "ramen") {

            ramen.appendChild(columna);

        }


        if (prod.categoria == "barra") {

            barra.appendChild(columna);

        }

    });

}


function cargarCarrito() {

    let contenedor =
        document.getElementById("lista-carrito");

    let subtotalTexto =
        document.getElementById("subtotal-carrito");


    if (contenedor == null) return;

    if (responseAPI.status !== 200) {
        contenedor.innerHTML = "<p class='text-center py-4'>Cargando catálogo del backend...</p>";
        return;
    }

    contenedor.innerHTML = "";


    let carrito = obtenerCarrito();

    let subtotal = 0;


    if (carrito.length == 0) {

        let mensaje =
            document.createElement("p");

        mensaje.setAttribute(
            "class",
            "text-center fs-4 py-5"
        );

        mensaje.innerText =
            "Tu carrito está vacío. Agrega productos desde el menú.";

        contenedor.appendChild(mensaje);


        if (subtotalTexto != null) {

            subtotalTexto.innerText = "$0";

        }


        actualizarContadorCarrito();

        return;

    }


    carrito.forEach((item) => {

        let prod =
            buscarProducto(item.id);


        if (prod == null || prod.available === false) {
            mostrarAviso(
                "Uno o más productos del carrito ya no están disponibles. Actualiza tu selección.",
                "warning"
            );
            return;
        }


        subtotal =
            subtotal +
            (prod.precio * item.cantidad);


        let producto =
            document.createElement("div");

        producto.setAttribute(
            "class",
            "carrito-producto"
        );


        let fila =
            document.createElement("div");

        fila.setAttribute(
            "class",
            "row align-items-center g-3"
        );


        let columnaImagen =
            document.createElement("div");

        columnaImagen.setAttribute(
            "class",
            "col-4 col-md-3"
        );


        let imagen =
            document.createElement("img");

        imagen.setAttribute(
            "src",
            prod.imagen
        );

        imagen.setAttribute(
            "alt",
            prod.nombre
        );


        columnaImagen.appendChild(imagen);


        let informacion =
            document.createElement("div");

        informacion.setAttribute(
            "class",
            "col-8 col-md-6"
        );


        let nombre =
            document.createElement("h3");

        nombre.innerText =
            prod.nombre;


        let descripcion =
            document.createElement("p");

        descripcion.innerText =
            prod.descripcion;


        let cantidad =
            document.createElement("div");

        cantidad.setAttribute(
            "class",
            "cantidad"
        );


        let menos =
            document.createElement("button");

        menos.setAttribute(
            "type",
            "button"
        );

        menos.setAttribute(
            "class",
            "btn btn-sm btn-dorado"
        );

        menos.setAttribute(
            "onclick",
            "cambiarCantidad('" +
            prod.id +
            "', -1)"
        );

        menos.innerText = "−";


        let numero =
            document.createElement("span");

        numero.setAttribute(
            "class",
            "mx-3"
        );

        numero.innerText =
            item.cantidad;


        let mas =
            document.createElement("button");

        mas.setAttribute(
            "type",
            "button"
        );

        mas.setAttribute(
            "class",
            "btn btn-sm btn-dorado"
        );

        mas.setAttribute(
            "onclick",
            "cambiarCantidad('" +
            prod.id +
            "', 1)"
        );

        mas.innerText = "+";


        cantidad.appendChild(menos);
        cantidad.appendChild(numero);
        cantidad.appendChild(mas);


        informacion.appendChild(nombre);
        informacion.appendChild(descripcion);
        informacion.appendChild(cantidad);


        let columnaPrecio =
            document.createElement("div");

        columnaPrecio.setAttribute(
            "class",
            "col-12 col-md-3 text-md-end"
        );


        let precio =
            document.createElement("span");

        precio.setAttribute(
            "class",
            "precio"
        );

        precio.innerText =
            formatearPrecio(
                prod.precio * item.cantidad
            );


        columnaPrecio.appendChild(precio);


        fila.appendChild(columnaImagen);
        fila.appendChild(informacion);
        fila.appendChild(columnaPrecio);

        producto.appendChild(fila);

        contenedor.appendChild(producto);

    });


    if (subtotalTexto != null) {

        subtotalTexto.innerText =
            formatearPrecio(subtotal);

    }


    actualizarContadorCarrito();

}