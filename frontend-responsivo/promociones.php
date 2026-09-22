<!DOCTYPE html>
<html lang="es">

<head>

    <title>Promociones - Tokyo Noodles</title>

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


<body onload="actualizarContadorCarrito();">


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
                        class="nav-link nav-activo px-4"
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


<main class="container py-5">

    <h1 class="titulo-seccion">
        PROMOCIONES
    </h1>


    <div class="tarjeta-promocion">

        <div class="row align-items-center g-4">

            <div class="col-12 col-lg-5">

                <div class="row">

                    <div class="col-8">

                        <img
                            src="img/shio.png"
                            class="imagen-promo"
                            alt="Shio Ramen"
                        >

                    </div>


                    <div class="col-4">

                        <img
                            src="img/coca-zero.png"
                            class="imagen-bebida"
                            alt="Coca Cola Zero"
                        >

                    </div>

                </div>

            </div>


            <div class="col-12 col-lg-7">

                <h2>
                    TOKYO CLASSIC
                </h2>

                <p class="mt-4">

                    Elige tu Shio Ramen acompañado
                    de una bebida clásica a elección.

                </p>


                <div class="d-flex justify-content-between align-items-center mt-5">

                    <span class="precio">
                        $15.500
                    </span>


                    <button
                        type="button"
                        class="btn btn-dorado"
                        onclick="agregarProducto('9')"
                    >
                        +
                    </button>

                </div>

            </div>

        </div>

    </div>


    <div class="tarjeta-promocion">

        <div class="row align-items-center g-4">

            <div class="col-12 col-lg-5">

                <div class="row">

                    <div class="col-8">

                        <img
                            src="img/tantan.png"
                            class="imagen-promo"
                            alt="Tantan Ramen"
                        >

                    </div>


                    <div class="col-4">

                        <img
                            src="img/aka-natsu.png"
                            class="imagen-promo"
                            alt="Aka Natsu"
                        >

                    </div>

                </div>

            </div>


            <div class="col-12 col-lg-7">

                <h2>
                    TOKYO EXPERIENCE
                </h2>

                <p class="mt-4">

                    Disfruta nuestro Tantan Ramen
                    junto a un refrescante Aka Natsu.

                </p>


                <div class="d-flex justify-content-between align-items-center mt-5">

                    <span class="precio">
                        $20.500
                    </span>


                    <button
                        type="button"
                        class="btn btn-dorado"
                        onclick="agregarProducto('10')"
                    >
                        +
                    </button>

                </div>

            </div>

        </div>

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