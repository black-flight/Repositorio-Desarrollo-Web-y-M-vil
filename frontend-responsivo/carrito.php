<!DOCTYPE html>
<html lang="es">

<head>

    <title>Carrito - Tokyo Noodles</title>

    <meta charset="utf-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

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
                Ingresa tu dirección o selecciona
                un local para continuar
            </button>

        </div>

    </div>

</main>


<div
    class="modal fade"
    id="modalPedido"
    tabindex="-1"
>

    <div class="modal-dialog modal-lg modal-dialog-centered">

        <div class="modal-content">

            <div class="modal-header border-0">

                <h2 class="modal-title w-100 text-center">

                    ¿Cómo quieres tu pedido?

                </h2>


                <button
                    type="button"
                    class="btn-close btn-close-white"
                    data-bs-dismiss="modal"
                >
                </button>

            </div>


            <div class="modal-body p-4">

                <div class="row opcion-pedido mb-4">

                    <div class="col-6">

                        <button
                            class="btn btn-dorado w-100"
                            type="button"
                        >
                            Delivery
                        </button>

                    </div>


                    <div class="col-6">

                        <button
                            class="btn btn-secondary w-100"
                            type="button"
                        >
                            Retiro
                        </button>

                    </div>

                </div>


                <div class="row">

                    <div class="col-12">

                        <label
                            for="direccion"
                            class="form-label"
                        >
                            Dirección
                        </label>


                        <input
                            type="text"
                            class="form-control direccion"
                            id="direccion"
                            placeholder="Ingresa tu dirección"
                        >

                    </div>

                </div>


                <div class="row mt-4">

                    <div class="col-12">

                        <div class="local-retiro">

                            <strong>
                                Maipú
                            </strong>

                            <br>

                            Maipú 1234

                        </div>

                    </div>

                </div>

            </div>

        </div>

    </div>

</div>


</body>

</html>