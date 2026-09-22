<!DOCTYPE html>
<html lang="es">

<head>

    <title>Iniciar Sesión - Tokyo Noodles</title>

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

                <a class="nav-link nav-activo"
                   href="login.php">
                    Usuario
                </a>

            </div>

        </div>

    </div>

</nav>


<main class="container py-5">

    <div class="form-login">

        <h1 class="titulo-seccion">
            INICIAR SESIÓN EN TOKYO NOODLES
        </h1>


        <form>

            <div class="mb-4">

                <label
                    for="usuario"
                    class="form-label fs-4"
                >
                    Nombre de usuario o correo electrónico principal
                </label>

                <input
                    type="text"
                    class="form-control form-control-lg"
                    id="usuario"
                >

            </div>


            <div class="mb-2">

                <label
                    for="password"
                    class="form-label fs-4"
                >
                    Contraseña
                </label>

                <input
                    type="password"
                    class="form-control form-control-lg"
                    id="password"
                >

            </div>


            <div class="text-end mb-5">

                <a
                    href="#"
                    class="text-decoration-none"
                    style="color: #da8442;"
                >
                    ¿Olvidó su contraseña?
                </a>

            </div>


            <div class="row justify-content-center">

                <div class="col-12 col-md-7">

                    <button
                        type="button"
                        class="btn btn-tokyo w-100 py-3"
                    >
                        Iniciar Sesión
                    </button>

                </div>

            </div>


            <div class="text-center mt-5 fs-5">

                <span>
                    ¿Aún no tiene una cuenta?
                </span>

                <a
                    href="#"
                    class="text-decoration-none ms-2"
                    style="color: #da8442;"
                >
                    Regístrese ahora
                </a>

            </div>

        </form>

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