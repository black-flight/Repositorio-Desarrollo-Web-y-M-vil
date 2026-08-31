<html>
    <head>
        <title>Servicios</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>     
    </head>
    <body>
        <!==Navbar==>
        <nav class="navbar navbar-expand-sm bg-dark navbar-dark">
            <div class="container-fluid">
                <a class="navbar-brand" href="index.php">Mi Empresa</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#collapsibleNavbar">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="collapsibleNavbar">
                    <ul class="navbar-nav">
                        <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">Empresa</a>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="empresa.php">Quienes somos</a></li>
                            <li><a class="dropdown-item" href="#">Nuestro Equipo</a></li>
                            <li><a class="dropdown-item" href="#">Misión</a></li>
                        </ul>
                        </li>   

                        <li class="nav-item">
                            <a class="nav-link" href="servicios.php">Servicios</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="productos.php">Productos</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="contacto.php">Contactos</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>

        <!==Container==>
    
        <div class="container-fluid bg-warning p-4">

            <h1>Nuestros Servicios</h1>

            <p>
                En Mi Empresa contamos con distintos servicios pensados para
                ayudar a nuestros clientes y entregar soluciones de acuerdo
                a sus necesidades.
            </p>

            <h4>Asesoría</h4>

            <p>
                Entregamos orientación y apoyo a nuestros clientes para que
                puedan encontrar las mejores alternativas para sus proyectos.
            </p>

            <h4>Soporte</h4>

            <p>
                Contamos con atención para resolver dudas, problemas o
                requerimientos relacionados con nuestros productos y servicios.
            </p>

            <h4>Soluciones para empresas</h4>

            <p>
                Trabajamos con empresas de distintos tamaños, entregando
                soluciones que pueden adaptarse a sus necesidades y objetivos.
            </p>

            <h4>Atención personalizada</h4>

            <p>
                Nuestro equipo busca entregar una atención cercana y mantener
                una comunicación constante con cada cliente.
            </p>

            <a href="index.php">Volver</a>

        </div>

        <!==Footer==>
        <div class="container-fuid bg-dark">
            <div class="row">
                <div class="col-4"></div>
                <div class="col-4" style="color:white"><strong>MiEmpresa@2026</strong></div>
                <div class="col-4"></div>
            </div>
        </div>
        <!==Modal==>
    </body>
</html>