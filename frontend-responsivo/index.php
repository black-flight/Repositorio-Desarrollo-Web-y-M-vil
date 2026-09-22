<!DOCTYPE html>
<html lang="es">

<head>

    <title>Tokyo Noodles</title>

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
                    <a class="nav-link nav-activo px-4"
                       href="index.php">
                        Inicio
                    </a>
                </li>

                <li class="nav-item">
                    <a class="nav-link px-4"
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


<!-- PORTADA -->

<div class="container-fluid">

    <div class="row">

        <section class="col-12 col-lg-8 hero-texto">

            <h1>
                ¿PREPARADO PARA VIAJAR A TRAVÉS DEL SABOR?
            </h1>

            <p class="mt-4">
                Descubre sabores únicos inspirados en la esencia de Japón
            </p>

        </section>


        <section class="col-12 col-lg-4 hero-imagen">

            <a href="menu.php">
                PIDE AQUÍ
            </a>

        </section>

    </div>

</div>


<!-- FOOTER -->

<footer class="container-fluid footer-tokyo">

    <div class="row g-4 text-center text-md-start">

        <div class="col-12 col-sm-6 col-lg">

            <h4>
                CONÓCENOS
            </h4>

            <p>
                Tokyo Noodles nació con una idea simple:
                traer un pedacito de Tokio a tu mesa.
            </p>

            <p>
                Mezclamos tradición japonesa, sabores únicos
                y ramen hecho con personalidad.
            </p>

        </div>


        <div class="col-12 col-sm-6 col-lg">

            <h4>
                CONTACTO
            </h4>

            <p>Whatsapp</p>
            <p>Instagram</p>
            <p>Facebook</p>
            <p>TikTok</p>

        </div>


        <div class="col-12 col-sm-6 col-lg text-center">

            <span class="footer-logo">
                LOGO
            </span>

        </div>


        <div class="col-12 col-sm-6 col-lg">

            <h4>
                HORARIO
            </h4>

            <p>
                Lunes - Martes<br>
                12:00 - 01:00
            </p>

            <p>
                Miércoles - Sábado<br>
                12:00 - 02:00
            </p>

        </div>


        <div class="col-12 col-sm-6 col-lg">

            <h4>
                UBICACIÓN
            </h4>

            <p>
                Maipú 1234
            </p>

        </div>

    </div>

</footer>


</body>

</html>