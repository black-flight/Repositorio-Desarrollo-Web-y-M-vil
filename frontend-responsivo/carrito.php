<!DOCTYPE html>
<html lang="es">

<head>

    <title>Carrito - Tokyo Noodles</title>

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

                <a class="nav-link"
                   href="login.php">
                    Usuario
                </a>

            </div>

        </div>

    </div>

</nav>


<main class="container py-5">

    <div class="carrito-contenedor">

        <h1 class="titulo-carrito">
            TU CARRITO (3)
        </h1>


        <!-- SHIO -->

        <div class="carrito-producto">

            <div class="row align-items-center g-3">

                <div class="col-4 col-md-3">

                    <img src="img/shio.png"
                         alt="Shio Ramen">

                </div>

                <div class="col-8 col-md-6">

                    <h3>
                        Shio Ramen
                    </h3>

                    <p>
                        • Classic
                    </p>

                    <span class="cantidad">
                        − &nbsp; 1 &nbsp; +
                    </span>

                </div>

                <div class="col-12 col-md-3 text-md-end">

                    <span class="precio">
                        $13.800
                    </span>

                </div>

            </div>

        </div>


        <!-- COCA -->

        <div class="carrito-producto">

            <div class="row align-items-center g-3">

                <div class="col-4 col-md-3">

                    <img src="img/coca-zero.png"
                         alt="Coca Cola Zero">

                </div>

                <div class="col-8 col-md-6">

                    <h3>
                        Coca Cola Zero
                    </h3>

                    <p>
                        • Coca Cola Zero
                    </p>

                    <span class="cantidad">
                        − &nbsp; 2 &nbsp; +
                    </span>

                </div>

                <div class="col-12 col-md-3 text-md-end">

                    <span class="precio">
                        $5.800
                    </span>

                </div>

            </div>

        </div>


        <!-- SUBTOTAL -->

        <div class="subtotal">

            <div class="row">

                <div class="col-6">

                    <h3>
                        Subtotal
                    </h3>

                </div>

                <div class="col-6 text-end">

                    <h3>
                        $19.600
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


<!-- MODAL -->

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