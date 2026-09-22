<!DOCTYPE html>
<html lang="es">

<head>

    <title>Menú - Tokyo Noodles</title>

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


<body onload="cargarProductos(); actualizarContadorCarrito();">


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
                        class="nav-link nav-activo px-4"
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
                    class="nav-link"
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


<main class="container py-4">

    <h1 class="titulo-seccion">
        MENÚ
    </h1>


    <h2 class="titulo-seccion">
        RAMEN
    </h2>


    <div
        class="row g-4"
        id="productos-ramen"
    >
    </div>


    <h2 class="titulo-seccion mt-5">
        BARRA
    </h2>


    <div
        class="row g-4"
        id="productos-barra"
    >
    </div>

</main>


<footer class="container-fluid footer-tokyo mt-5">

    <div class="row g-3 text-center">

        <div class="col-12 col-sm-6 col-lg">

            <a href="index.php">
                CONÓCENOS
            </a>

        </div>


        <div class="col-12 col-sm-6 col-lg">
            CONTACTO
        </div>


        <div class="col-12 col-sm-6 col-lg text-center">

            <img
                src="img/logo.png"
                alt="Tokyo Noodles"
                class="logo-footer"
            >

        </div>


        <div class="col-12 col-sm-6 col-lg">
            HORARIO
        </div>


        <div class="col-12 col-sm-6 col-lg">
            UBICACIÓN
        </div>

    </div>

</footer>


</body>

</html>