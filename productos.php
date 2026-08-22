<html>
    <head>
        <title>Productos</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            const responseAPI ={
                "status": 200,
                "message": "Productos Obtenidos",
                "data": [
                    {"id":"1","nombre":"Producto Empresarial"},
                    {"id":"2","nombre":"Producto Profesional"},
                    {"id":"3","nombre":"Producto Personal"},
                    {"id":"4","nombre":"Soluciones personalizadas"}
                ]
            };

            function cargarProductos(){
                let cmb = document.getElementById("cmbProducto");

                responseAPI.data.forEach((prod) =>{
                    let opt = document.createElement("option");
                    opt.setAttribute("value", prod.id);
                    opt.innerText = prod.nombre;
                    cmb.appendChild(opt);

                });
            }
        </script>     
    </head>
    <body onload="cargarProductos();">
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

            <h1>Nuestros Productos</h1>

            <p>
                En Mi Empresa contamos con distintos productos orientados
                tanto a clientes particulares como a empresas.
            </p>

            <p>
                Buscamos ofrecer alternativas de buena calidad que puedan
                adaptarse a diferentes necesidades.
            </p>

            <h4>Lineas de productos</h4>
            <p>
                Puedes revisar algunas de las principales lineas de productos que actualmente ofrece Mi Empresa.
            </p>
            
            <div>
                <select id="cmbProducto" name="cmbProducto"></select>
            </div>

            <h4>Producto Empresarial</h4>

            <p>
                Solución pensada para empresas que necesitan mejorar y
                organizar parte de sus procesos de trabajo.
            </p>

            <h4>Producto Profesional</h4>

            <p>
                Alternativa orientada a profesionales que buscan una solución
                sencilla y confiable para sus actividades diarias.
            </p>

            <h4>Producto Personal</h4>

            <p>
                Producto pensado para usuarios que necesitan una opción
                fácil de utilizar y accesible para sus necesidades personales.
            </p>

            <h4>Soluciones personalizadas</h4>

            <p>
                También podemos adaptar nuestros productos dependiendo
                de los requerimientos y objetivos de cada cliente.
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