<!DOCTYPE html>
<html lang="es">

<head>

    <title>Menú - Tokyo Noodles</title>

    <meta charset="utf-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1">

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

</head>


<body>


<!-- NAVBAR -->

<nav class="navbar navbar-expand-md navbar-dark tn-navbar">

    <div class="container-fluid">

        <a class="navbar-brand me-5"
           href="index.php">
            LOGO
        </a>

        <button
            class="navbar-toggler"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#navbarTokyo"
        >
            <span class="navbar-toggler-icon"></span>
        </button>


        <div class="collapse navbar-collapse"
             id="navbarTokyo">

            <ul class="navbar-nav me-auto">

                <li class="nav-item">
                    <a class="nav-link px-4"
                       href="index.php">
                        Inicio
                    </a>
                </li>

                <li class="nav-item">
                    <a class="nav-link nav-activo px-4"
                       href="menu.php">
                        Menú
                    </a>
                </li>

                <li class="nav-item">
                    <a class="nav-link px-4"
                       href="promociones.php">
                        Promociones
                    </a>
                </li>

            </ul>


            <div class="d-flex flex-column flex-md-row gap-3 align-items-md-center">

                <a class="nav-link"
                   href="#">
                    Buscar
                </a>

                <a class="nav-link"
                   href="carrito.php">
                    Carrito
                </a>

                <a class="nav-link"
                   href="login.php">
                    Usuario
                </a>

            </div>

        </div>

    </div>

</nav>


<main class="container py-4">

    <h1 class="titulo-seccion">
        MENÚ
    </h1>

    <h2 class="titulo-seccion">
        RAMEN
    </h2>


    <div class="row g-4">


        <!-- SHIO -->

        <div class="col-12 col-lg-6">

            <div class="tarjeta-producto">

                <div class="row align-items-center">

                    <div class="col-12 col-sm-5">

                        <img src="img/shio.png"
                             alt="Shio Ramen">

                    </div>

                    <div class="col-12 col-sm-7 mt-3 mt-sm-0">

                        <h3>
                            Shio Ramen
                        </h3>

                        <p>
                            Caldo ligero a base de almeja y pollo con aceite de
                            camarón, chashu de cerdo, ajitama, wakame, nori,
                            cebollín, sésamo y noodles.
                        </p>

                        <div class="d-flex justify-content-between align-items-center">

                            <span class="precio">
                                $13.800
                            </span>

                            <a href="carrito.php"
                               class="btn btn-dorado">
                                +
                            </a>

                        </div>

                    </div>

                </div>

            </div>

        </div>


        <!-- MISO -->

        <div class="col-12 col-lg-6">

            <div class="tarjeta-producto">

                <div class="row align-items-center">

                    <div class="col-12 col-sm-5">

                        <img src="img/miso.png"
                             alt="Miso Ramen">

                    </div>

                    <div class="col-12 col-sm-7 mt-3 mt-sm-0">

                        <h3>
                            Miso Ramen
                        </h3>

                        <p>
                            Caldo consistente de miso, pollo y almeja,
                            chashu de cerdo, ajitama, choclo, nori,
                            cebollín, sésamo y noodles.
                        </p>

                        <div class="d-flex justify-content-between align-items-center">

                            <span class="precio">
                                $14.200
                            </span>

                            <a href="carrito.php"
                               class="btn btn-dorado">
                                +
                            </a>

                        </div>

                    </div>

                </div>

            </div>

        </div>


        <!-- TANTAN -->

        <div class="col-12 col-lg-6">

            <div class="tarjeta-producto">

                <div class="row align-items-center">

                    <div class="col-12 col-sm-5">

                        <img src="img/tantan.png"
                             alt="Tantan Ramen">

                    </div>

                    <div class="col-12 col-sm-7 mt-3 mt-sm-0">

                        <h3>
                            Tantan Ramen
                        </h3>

                        <p>
                            Caldo de miso picante, pollo y almeja con
                            sésamo, pulpa de cerdo molido picante,
                            karaage, ajitama, nori y noodles.
                        </p>

                        <div class="d-flex justify-content-between align-items-center">

                            <span class="precio">
                                $14.900
                            </span>

                            <a href="carrito.php"
                               class="btn btn-dorado">
                                +
                            </a>

                        </div>

                    </div>

                </div>

            </div>

        </div>


        <!-- VEGGIE -->

        <div class="col-12 col-lg-6">

            <div class="tarjeta-producto">

                <div class="row align-items-center">

                    <div class="col-12 col-sm-5">

                        <img src="img/veggie-miso.png"
                             alt="Veggie Miso Especial">

                    </div>

                    <div class="col-12 col-sm-7 mt-3 mt-sm-0">

                        <h3>
                            Veggie Miso Especial
                        </h3>

                        <p>
                            Caldo de miso y verduras con aceite de hongos,
                            tofu, shiitake grillado, choclo, kikurage,
                            nori y fideos de la casa.
                        </p>

                        <div class="d-flex justify-content-between align-items-center">

                            <span class="precio">
                                $15.510
                            </span>

                            <a href="carrito.php"
                               class="btn btn-dorado">
                                +
                            </a>

                        </div>

                    </div>

                </div>

            </div>

        </div>

    </div>


    <h2 class="titulo-seccion mt-5">
        BARRA
    </h2>


    <div class="row g-4">


        <!-- COCA ZERO -->

        <div class="col-12 col-lg-6">

            <div class="tarjeta-producto">

                <div class="row align-items-center">

                    <div class="col-12 col-sm-5">

                        <img src="img/coca-zero.png"
                             alt="Coca Cola Zero">

                    </div>

                    <div class="col-12 col-sm-7 mt-3 mt-sm-0">

                        <h3>
                            Coca Cola Zero
                        </h3>

                        <p>
                            Coca Cola Zero
                        </p>

                        <div class="d-flex justify-content-between align-items-center">

                            <span class="precio">
                                $2.900
                            </span>

                            <a href="carrito.php"
                               class="btn btn-dorado">
                                +
                            </a>

                        </div>

                    </div>

                </div>

            </div>

        </div>


        <!-- AKA NATSU -->

        <div class="col-12 col-lg-6">

            <div class="tarjeta-producto">

                <div class="row align-items-center">

                    <div class="col-12 col-sm-5">

                        <img src="img/aka-natsu.png"
                             alt="Aka Natsu">

                    </div>

                    <div class="col-12 col-sm-7 mt-3 mt-sm-0">

                        <h3>
                            Aka Natsu
                        </h3>

                        <p>
                            Syrup de betarraga, pulpa de maracuyá
                            y jugo fresco de naranja en un mocktail
                            dulce y cítrico.
                        </p>

                        <div class="d-flex justify-content-between align-items-center">

                            <span class="precio">
                                $7.800
                            </span>

                            <a href="carrito.php"
                               class="btn btn-dorado">
                                +
                            </a>

                        </div>

                    </div>

                </div>

            </div>

        </div>


        <!-- NATSU NO HIKARI -->

        <div class="col-12 col-lg-6">

            <div class="tarjeta-producto">

                <div class="row align-items-center">

                    <div class="col-12 col-sm-5">

                        <img src="img/natsu-hikari.png"
                             alt="Natsu No Hikari">

                    </div>

                    <div class="col-12 col-sm-7 mt-3 mt-sm-0">

                        <h3>
                            Natsu No Hikari
                        </h3>

                        <p>
                            Cóctel refrescante con tamarindo,
                            sake y pisco, equilibrado con goma
                            y zumo de limón.
                        </p>

                        <div class="d-flex justify-content-between align-items-center">

                            <span class="precio">
                                $9.900
                            </span>

                            <a href="carrito.php"
                               class="btn btn-dorado">
                                +
                            </a>

                        </div>

                    </div>

                </div>

            </div>

        </div>


        <!-- SOUKAI -->

        <div class="col-12 col-lg-6">

            <div class="tarjeta-producto">

                <div class="row align-items-center">

                    <div class="col-12 col-sm-5">

                        <img src="img/soukai.png"
                             alt="Soukai">

                    </div>

                    <div class="col-12 col-sm-7 mt-3 mt-sm-0">

                        <h3>
                            Soukai
                        </h3>

                        <p>
                            Sake, vodka, kiwi, esferas de kiwi,
                            pomelo, limón y syrup.
                        </p>

                        <div class="d-flex justify-content-between align-items-center">

                            <span class="precio">
                                $9.400
                            </span>

                            <a href="carrito.php"
                               class="btn btn-dorado">
                                +
                            </a>

                        </div>

                    </div>

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

        <div class="col-12 col-sm-6 col-lg footer-logo">
            LOGO
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