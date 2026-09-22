<!DOCTYPE html>
<html lang="es">

<head>

    <title>Carrito - Tokyo Noodles</title>

    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <link
        rel="icon"
        type="image/png"
        href="img/favicon.png"
    >

    <link
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css"
        rel="stylesheet"
    >

    <link
        rel="stylesheet"
        href="estilos.css"
    >

    <script
        src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js">
    </script>

    <script src="productos.js"></script>

</head>


<body onload="cargarCarrito(); actualizarContadorCarrito();">


<!-- NAVBAR -->

<nav class="navbar navbar-expand-md navbar-dark tn-navbar">

    <div class="container-fluid">

        <a
            class="navbar-brand me-5"
            href="index.php"
        >

            <img
                src="img/logo.png"
                alt="Tokyo Noodles"
                class="logo-navbar"
            >

        </a>


        <button
            class="navbar-toggler"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#navbarTokyo"
        >

            <span class="navbar-toggler-icon"></span>

        </button>


        <div
            class="collapse navbar-collapse"
            id="navbarTokyo"
        >

            <ul class="navbar-nav me-auto">

                <li class="nav-item">

                    <a
                        class="nav-link px-4"
                        href="index.php"
                    >
                        Inicio
                    </a>

                </li>


                <li class="nav-item">

                    <a
                        class="nav-link px-4"
                        href="menu.php"
                    >
                        Menú
                    </a>

                </li>


                <li class="nav-item">

                    <a
                        class="nav-link px-4"
                        href="promociones.php"
                    >
                        Promociones
                    </a>

                </li>

            </ul>


            <div class="d-flex flex-column flex-md-row gap-3 align-items-md-center">

                <button
                    class="btn nav-link"
                    type="button"
                    data-bs-toggle="collapse"
                    data-bs-target="#buscadorTokyo"
                >
                    🔍 Buscar
                </button>


                <a
                    class="nav-link nav-activo"
                    href="carrito.php"
                >
                    🛒 Carrito
                    (<span id="contador-carrito">0</span>)
                </a>


                <a
                    class="nav-link"
                    href="login.php"
                >
                    Usuario
                </a>

            </div>

        </div>

    </div>

</nav>


<!-- BUSCADOR -->

<div
    class="collapse"
    id="buscadorTokyo"
>

    <div class="container-fluid buscador-tokyo p-3">

        <input
            type="text"
            class="form-control"
            placeholder="Buscar ramen, bebidas o promociones..."
        >

    </div>

</div>


<!-- CARRITO -->

<main class="container py-5">

    <div class="carrito-contenedor">

        <h1 class="titulo-carrito">

            TU CARRITO
            (<span id="cantidad-carrito-titulo">0</span>)

        </h1>


        <div id="lista-carrito">
        </div>


        <div class="subtotal">

            <div class="row">

                <div class="col-6">

                    <h3>
                        Subtotal
                    </h3>

                </div>


                <div class="col-6 text-end">

                    <h3 id="subtotal-carrito">
                        $0
                    </h3>

                </div>

            </div>

        </div>


        <div class="text-center mt-5">

            <button
                type="button"
                class="btn-continuar"
                data-bs-toggle="modal"
                data-bs-target="#modalPedido"
            >
                Continuar con el pedido
            </button>

        </div>

    </div>

</main>


<!-- MODAL PEDIDO -->

<div
    class="modal fade"
    id="modalPedido"
    tabindex="-1"
    aria-hidden="true"
>

    <div class="modal-dialog modal-dialog-centered modal-lg">

        <div class="modal-content modal-tokyo">


            <!-- CABECERA -->

            <div class="modal-header modal-tokyo-header border-0">

                <div class="w-100 text-center">

                    <h2 class="modal-tokyo-title mb-2">
                        ¿Cómo quieres tu pedido?
                    </h2>

                    <p class="modal-tokyo-subtitle mb-0">
                        Elige delivery o retiro en nuestro local de Maipú.
                    </p>

                </div>


                <button
                    type="button"
                    class="btn-close btn-close-white"
                    data-bs-dismiss="modal"
                    aria-label="Cerrar"
                >
                </button>

            </div>


            <!-- CONTENIDO -->

            <div class="modal-body modal-tokyo-body">


                <!-- DELIVERY / RETIRO -->

                <div class="pedido-switch mb-4">

                    <button
                        type="button"
                        id="btnDelivery"
                        class="pedido-switch-btn activo"
                        onclick="mostrarDelivery()"
                    >
                        Delivery
                    </button>


                    <button
                        type="button"
                        id="btnRetiro"
                        class="pedido-switch-btn"
                        onclick="mostrarRetiro()"
                    >
                        Retiro
                    </button>

                </div>


                <!-- DELIVERY -->

                <div id="bloqueDelivery">

                    <div class="row g-3">

                        <div class="col-12">

                            <label
                                for="direccion"
                                class="form-label modal-label"
                            >
                                Dirección
                            </label>


                            <input
                                type="text"
                                class="form-control input-tokyo"
                                id="direccion"
                                placeholder="Ej: Av. Pajaritos 2450"
                                autocomplete="off"
                            >

                        </div>


                        <div class="col-12 col-md-6">

                            <label
                                for="depto"
                                class="form-label modal-label"
                            >
                                Depto / Casa / Oficina
                            </label>


                            <input
                                type="text"
                                class="form-control input-tokyo"
                                id="depto"
                                placeholder="Ej: Depto 403"
                                autocomplete="off"
                            >

                        </div>


                        <div class="col-12 col-md-6">

                            <label
                                for="referencia"
                                class="form-label modal-label"
                            >
                                Referencia
                            </label>


                            <input
                                type="text"
                                class="form-control input-tokyo"
                                id="referencia"
                                placeholder="Ej: Frente a la plaza"
                                autocomplete="off"
                            >

                        </div>

                    </div>


                    <div class="aviso-entrega mt-4">

                        <span class="aviso-entrega-icono">
                            📍
                        </span>

                        Verifica tu dirección antes de continuar
                        con el pedido.

                    </div>

                </div>


                <!-- RETIRO -->

                <div
                    id="bloqueRetiro"
                    style="display: none;"
                >

                    <p class="modal-label mb-3">
                        Tu pedido estará disponible para retiro en:
                    </p>


                    <div class="local-card selected">

                        <span class="local-badge">
                            Disponible
                        </span>


                        <h4>
                            Tokyo Noodles Maipú
                        </h4>


                        <p class="mb-1">
                            Maipú 1234
                        </p>


                        <small>
                            Retiro en local
                        </small>

                    </div>


                    <div class="aviso-entrega mt-4">

                        <span class="aviso-entrega-icono">
                            🥡
                        </span>

                        Te avisaremos cuando tu pedido esté listo
                        para retirar.

                    </div>

                </div>

            </div>


            <!-- BOTONES INFERIORES -->

            <div class="modal-footer modal-tokyo-footer border-0">

                <button
                    type="button"
                    class="btn-modal-secundario"
                    data-bs-dismiss="modal"
                >
                    Volver
                </button>


                <button
                    type="button"
                    class="btn-modal-principal"
                >
                    Continuar
                </button>

            </div>

        </div>

    </div>

</div>


<!-- CAMBIO DELIVERY / RETIRO -->

<script>

    function mostrarDelivery() {

        document.getElementById(
            "bloqueDelivery"
        ).style.display = "block";


        document.getElementById(
            "bloqueRetiro"
        ).style.display = "none";


        document.getElementById(
            "btnDelivery"
        ).classList.add("activo");


        document.getElementById(
            "btnRetiro"
        ).classList.remove("activo");

    }


    function mostrarRetiro() {

        document.getElementById(
            "bloqueDelivery"
        ).style.display = "none";


        document.getElementById(
            "bloqueRetiro"
        ).style.display = "block";


        document.getElementById(
            "btnRetiro"
        ).classList.add("activo");


        document.getElementById(
            "btnDelivery"
        ).classList.remove("activo");

    }

</script>


</body>

</html>