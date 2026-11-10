const responseAPI = {
    "status": 200,
    "message": "Productos Obtenidos",
    "data": [

        {
            "id": "1",
            "nombre": "Shio Ramen",
            "descripcion": "Caldo ligero a base de almeja y pollo con aceite de camarón, chashu de cerdo, ajitama, wakame, nori, cebollín, sésamo y noodles.",
            "precio": 13800,
            "imagen": "img/shio.png",
            "categoria": "ramen"
        },

        {
            "id": "2",
            "nombre": "Miso Ramen",
            "descripcion": "Caldo consistente de miso, pollo y almeja, chashu de cerdo, ajitama, choclo, nori, cebollín, sésamo y noodles.",
            "precio": 14200,
            "imagen": "img/miso.png",
            "categoria": "ramen"
        },

        {
            "id": "3",
            "nombre": "Tantan Ramen",
            "descripcion": "Caldo de miso picante, pollo y almeja con sésamo, pulpa de cerdo molido picante, karaage, ajitama, nori y noodles.",
            "precio": 14900,
            "imagen": "img/tantan.png",
            "categoria": "ramen"
        },

        {
            "id": "4",
            "nombre": "Veggie Miso Especial",
            "descripcion": "Caldo de miso y verduras con aceite de hongos, tofu, shiitake grillado, choclo, kikurage, nori y fideos de la casa.",
            "precio": 15510,
            "imagen": "img/veggie-miso.png",
            "categoria": "ramen"
        },

        {
            "id": "5",
            "nombre": "Coca Cola Zero",
            "descripcion": "Coca Cola Zero",
            "precio": 2900,
            "imagen": "img/coca-zero.png",
            "categoria": "barra"
        },

        {
            "id": "6",
            "nombre": "Aka Natsu",
            "descripcion": "Syrup de betarraga, pulpa de maracuyá y jugo fresco de naranja en un mocktail dulce y cítrico.",
            "precio": 7800,
            "imagen": "img/aka-natsu.png",
            "categoria": "barra"
        },

        {
            "id": "7",
            "nombre": "Natsu No Hikari",
            "descripcion": "Cóctel refrescante con tamarindo, sake y pisco, equilibrado con goma y zumo de limón.",
            "precio": 9900,
            "imagen": "img/natsu-hikari.png",
            "categoria": "barra"
        },

        {
            "id": "8",
            "nombre": "Soukai",
            "descripcion": "Sake, vodka, kiwi, esferas de kiwi, pomelo, limón y syrup.",
            "precio": 9400,
            "imagen": "img/soukai.png",
            "categoria": "barra"
        },

        {
            "id": "9",
            "nombre": "Tokyo Classic",
            "descripcion": "Shio Ramen acompañado de una bebida clásica.",
            "precio": 15500,
            "imagen": "img/shio.png",
            "categoria": "promocion"
        },

        {
            "id": "10",
            "nombre": "Tokyo Experience",
            "descripcion": "Tantan Ramen acompañado de un Aka Natsu.",
            "precio": 20500,
            "imagen": "img/tantan.png",
            "categoria": "promocion"
        }

    ]
};


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

        if (prod.id == id) {

            productoEncontrado = prod;

        }

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


    if (ramen == null || barra == null) {

        return;

    }


    responseAPI.data.forEach((prod) => {

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

        boton.innerText = "+";


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


    if (contenedor == null) {

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


        if (prod == null) {

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