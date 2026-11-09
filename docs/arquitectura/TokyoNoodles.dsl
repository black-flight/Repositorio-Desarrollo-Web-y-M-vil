workspace "Tokyo Noodles" "Modelo C4 del sitio web y los servicios backend del proyecto." {

    !identifiers hierarchical

    model {
        visitante = person "Visitante" "Persona que navega el sitio web de Tokyo Noodles."
        usuario = person "Usuario de pruebas" "Persona que utiliza los endpoints de autenticacion y consulta del backend."
        desarrollador = person "Desarrollador" "Persona que ejecuta los scripts de mensajeria durante las pruebas."

        sistema = softwareSystem "Tokyo Noodles" "Sitio web y servicios backend del proyecto Tokyo Noodles." {
            tags "SistemaEvaluado"

            frontend = container "Sitio web" "Presenta el menu, las promociones y el carrito de compras. En esta version no consume las APIs del backend." "PHP, HTML, CSS, JavaScript y Bootstrap" {
                tags "Frontend"
            }

            apiGateway = container "API Gateway" "Punto de entrada para las solicitudes de productos y pedidos. Valida tokens, obtiene secretos y enruta las solicitudes." "FastAPI" {
                tags "Gateway"

                httpEntry = component "Entrada HTTP" "Recibe solicitudes en la ruta /api/{path}." "FastAPI"
                vaultClient = component "Cliente de Vault" "Obtiene los secretos configurados para las comunicaciones del Gateway." "HTTP/JSON"
                tokenValidator = component "Validador de token" "Solicita al Auth Service la introspeccion del token Bearer." "HTTP/JSON"
                routeDispatcher = component "Enrutador de solicitudes" "Dirige las solicitudes a la API de productos o a la API de pedidos." "FastAPI"
                responseHandler = component "Manejador de respuestas" "Devuelve al cliente la respuesta recibida desde el backend." "FastAPI"
            }

            authService = container "Auth Service" "Gestiona el inicio de sesion, la introspeccion de tokens y el cierre de sesiones." "FastAPI" {
                tags "Seguridad"

                identityApi = component "API de identidad" "Atiende las operaciones /login, /introspect y /logout." "FastAPI"
                credentialVerifier = component "Verificador de credenciales" "Comprueba las credenciales contra los usuarios definidos en el servicio." "Python"
                tokenManager = component "Gestor de tokens" "Genera tokens opacos y controla su vigencia." "Python"
                sessionStore = component "Almacen de sesiones" "Mantiene las sesiones en memoria durante la ejecucion del servicio." "Python"
            }

            apiProductos = container "API de productos" "Entrega el listado de productos y verifica que las solicitudes provengan del API Gateway." "FastAPI" {
                tags "Backend"

                productsEndpoint = component "Endpoint de productos" "Atiende las solicitudes GET /products." "FastAPI"
                productsSecretVerifier = component "Verificador de secreto" "Compara el secreto recibido desde el Gateway con el valor configurado en el servicio." "Python"
                productCatalog = component "Catalogo de productos" "Entrega la lista de productos definida en el codigo del servicio." "Python"
            }

            apiPedidos = container "API de pedidos" "Entrega el listado de pedidos de ejemplo y verifica que las solicitudes provengan del API Gateway." "FastAPI" {
                tags "Backend"

                ordersEndpoint = component "Endpoint de pedidos" "Atiende las solicitudes GET /orders." "FastAPI"
                ordersSecretVerifier = component "Verificador de secreto" "Compara el secreto recibido desde el Gateway con el valor configurado en el servicio." "Python"
                ordersList = component "Listado de pedidos" "Entrega los pedidos de ejemplo definidos en el codigo del servicio." "Python"
            }

            graphqlApi = container "API GraphQL de usuarios" "Expone consultas y mutaciones para crear, consultar, actualizar y eliminar usuarios." "Node.js, Express, Apollo Server y Mongoose" {
                tags "Backend"

                graphqlEndpoint = component "Endpoint GraphQL" "Recibe las operaciones GraphQL." "Apollo Server"
                graphqlSchema = component "Esquema GraphQL" "Define los tipos Usuario, UsuarioInput, Alert, Query y Mutation." "GraphQL"
                graphqlResolvers = component "Resolvers" "Ejecuta las consultas y mutaciones sobre los usuarios." "JavaScript"
                usuarioModel = component "Modelo Usuario" "Define el modelo de usuario utilizado por Mongoose." "Mongoose"
            }

            mensajeria = container "Scripts de mensajeria" "Contiene los scripts independientes que envian y reciben mensajes de pedidos mediante STOMP." "Python y STOMP" {
                tags "Mensajeria"

                productor = component "Productor" "Serializa un pedido de ejemplo como JSON y lo envia a la cola pedidos." "Python"
                consumidor = component "Consumidor" "Recibe mensajes de la cola, deserializa el JSON y muestra sus campos." "Python"
            }

            mongoDb = container "MongoDB" "Almacena los registros de usuarios utilizados por la API GraphQL en la base de datos bdunab2." "MongoDB" {
                tags "BaseDatos"
            }

            secretManager = container "HashiCorp Vault" "Almacena los secretos que consulta el API Gateway en la ruta secret/data/gateway." "Vault" {
                tags "Seguridad"
            }

            activeMq = container "ActiveMQ" "Broker que recibe y entrega mensajes mediante STOMP en la cola pedidos." "ActiveMQ y STOMP" {
                tags "Mensajeria"
            }
        }

        visitante -> sistema.frontend "Navega el sitio y consulta el menu y las promociones" "Navegador web"
        desarrollador -> sistema.mensajeria "Ejecuta los scripts de productor y consumidor" "Terminal"
        usuario -> sistema.authService "Envia credenciales a POST /login" "HTTP/JSON"
        sistema.authService -> usuario "Devuelve un token opaco" "HTTP/JSON"
        usuario -> sistema.apiGateway "Consulta /api/products o /api/orders con un token Bearer" "HTTP/JSON"
        sistema.apiGateway -> usuario "Devuelve la respuesta de la API solicitada" "HTTP/JSON"
        usuario -> sistema.graphqlApi "Ejecuta consultas y mutaciones GraphQL de usuarios" "HTTP/GraphQL"
        sistema.graphqlApi -> usuario "Devuelve el resultado de la operacion GraphQL" "HTTP/GraphQL"
        sistema.apiGateway -> sistema.secretManager "Obtiene los secretos configurados" "HTTP"
        sistema.secretManager -> sistema.apiGateway "Entrega los secretos solicitados" "HTTP"
        sistema.apiGateway -> sistema.authService "Solicita la introspeccion del token" "HTTP/JSON"
        sistema.authService -> sistema.apiGateway "Devuelve el estado y la identidad de la sesion" "HTTP/JSON"
        sistema.apiGateway -> sistema.apiProductos "Enruta solicitudes de productos" "HTTP/JSON"
        sistema.apiProductos -> sistema.apiGateway "Devuelve el listado de productos" "HTTP/JSON"
        sistema.apiGateway -> sistema.apiPedidos "Enruta solicitudes de pedidos" "HTTP/JSON"
        sistema.apiPedidos -> sistema.apiGateway "Devuelve el listado de pedidos" "HTTP/JSON"
        sistema.graphqlApi -> sistema.mongoDb "Consulta y modifica usuarios mediante Mongoose" "MongoDB"
        sistema.mongoDb -> sistema.graphqlApi "Devuelve los registros consultados" "MongoDB"
        desarrollador -> sistema.mensajeria.productor "Ejecuta productor.py" "Terminal"
        sistema.mensajeria.productor -> sistema.activeMq "Envia un mensaje JSON a la cola /queue/pedidos" "STOMP"
        sistema.activeMq -> sistema.mensajeria.consumidor "Entrega el mensaje publicado en la cola" "STOMP"
        sistema.mensajeria.consumidor -> desarrollador "Muestra los datos del pedido recibido" "Consola"

        sistema.apiGateway.httpEntry -> sistema.apiGateway.vaultClient "Solicita los secretos necesarios"
        sistema.apiGateway.vaultClient -> sistema.secretManager "Consulta secret/data/gateway" "HTTP"
        sistema.apiGateway.vaultClient -> sistema.apiGateway.tokenValidator "Entrega los secretos obtenidos"
        sistema.apiGateway.httpEntry -> sistema.apiGateway.tokenValidator "Solicita validar el token recibido"
        sistema.apiGateway.tokenValidator -> sistema.authService.identityApi "Envia el token para introspeccion" "HTTP/JSON"
        sistema.authService.identityApi -> sistema.apiGateway.tokenValidator "Devuelve el estado de la sesion" "HTTP/JSON"
        sistema.apiGateway.tokenValidator -> sistema.apiGateway.routeDispatcher "Entrega la identidad validada"
        sistema.apiGateway.routeDispatcher -> sistema.apiProductos.productsEndpoint "Enruta GET /products" "HTTP/JSON"
        sistema.apiGateway.routeDispatcher -> sistema.apiPedidos.ordersEndpoint "Enruta GET /orders" "HTTP/JSON"
        sistema.apiProductos.productsEndpoint -> sistema.apiGateway.responseHandler "Devuelve el resultado de productos"
        sistema.apiPedidos.ordersEndpoint -> sistema.apiGateway.responseHandler "Devuelve el resultado de pedidos"
        sistema.apiGateway.responseHandler -> sistema.apiGateway.httpEntry "Entrega la respuesta HTTP"

        sistema.authService.identityApi -> sistema.authService.credentialVerifier "Solicita comprobar las credenciales"
        sistema.authService.credentialVerifier -> sistema.authService.tokenManager "Entrega la identidad validada"
        sistema.authService.tokenManager -> sistema.authService.sessionStore "Registra el token y su vigencia"
        sistema.authService.identityApi -> sistema.authService.sessionStore "Consulta o elimina una sesion"
        sistema.authService.sessionStore -> sistema.authService.identityApi "Devuelve los datos de la sesion"

        sistema.apiProductos.productsEndpoint -> sistema.apiProductos.productsSecretVerifier "Verifica el secreto del Gateway"
        sistema.apiProductos.productsSecretVerifier -> sistema.apiProductos.productCatalog "Permite entregar el catalogo"
        sistema.apiPedidos.ordersEndpoint -> sistema.apiPedidos.ordersSecretVerifier "Verifica el secreto del Gateway"
        sistema.apiPedidos.ordersSecretVerifier -> sistema.apiPedidos.ordersList "Permite entregar los pedidos de ejemplo"

        sistema.graphqlApi.graphqlEndpoint -> sistema.graphqlApi.graphqlSchema "Procesa la operacion recibida"
        sistema.graphqlApi.graphqlSchema -> sistema.graphqlApi.graphqlResolvers "Invoca el resolver correspondiente"
        sistema.graphqlApi.graphqlResolvers -> sistema.graphqlApi.usuarioModel "Consulta o modifica usuarios"
        sistema.graphqlApi.usuarioModel -> sistema.mongoDb "Lee y escribe registros de usuarios" "MongoDB"

        local = deploymentEnvironment "Desarrollo_Local" {
            deploymentNode "Equipo de desarrollo" "Equipo local utilizado para ejecutar y probar los componentes del proyecto." "Estacion de trabajo" {
                tags "ZonaLocal"

                deploymentNode "Servidor web XAMPP" "Ejecuta el sitio web PHP." "Servidor web" {
                    containerInstance sistema.frontend
                }

                deploymentNode "Procesos FastAPI" "Ejecuta el API Gateway, el Auth Service y las APIs de productos y pedidos." "Procesos Python" {
                    containerInstance sistema.apiGateway
                    containerInstance sistema.authService
                    containerInstance sistema.apiProductos
                    containerInstance sistema.apiPedidos
                }

                deploymentNode "Proceso Node.js" "Ejecuta el servidor GraphQL." "Proceso Node.js" {
                    containerInstance sistema.graphqlApi
                }

                deploymentNode "Scripts Python" "Ejecuta el productor y el consumidor de mensajes." "Procesos Python" {
                    containerInstance sistema.mensajeria
                }

                deploymentNode "Servicios locales" "Agrupa los servicios externos requeridos durante la ejecucion local." "Servicios locales" {
                    containerInstance sistema.mongoDb
                    containerInstance sistema.secretManager
                    containerInstance sistema.activeMq
                }
            }
        }
    }

    views {

        systemContext sistema "C1_Contexto" "Contexto del sitio web y los servicios backend de Tokyo Noodles." {
            title "C1 - Contexto de Tokyo Noodles"
            include *
            autoLayout lr
        }

        container sistema "C2_Contenedores" "Aplicaciones, servicios y almacenes utilizados por Tokyo Noodles." {
            title "C2 - Contenedores de Tokyo Noodles"
            include *
            autoLayout lr
        }

        container sistema "C2_Backend" "Servicios de autenticacion, enrutamiento y consulta de productos y pedidos." {
            include usuario sistema.apiGateway sistema.authService sistema.apiProductos sistema.apiPedidos sistema.secretManager
            autoLayout lr
        }

        container sistema "C2_GraphQL_Mensajeria" "Servicios de usuarios y mensajeria utilizados en el proyecto." {
            include usuario desarrollador sistema.graphqlApi sistema.mongoDb sistema.mensajeria sistema.activeMq
            autoLayout lr
        }

        component sistema.apiGateway "C3_API_Gateway" "Componentes internos del API Gateway." {
            title "C3 - API Gateway"
            include *
            autoLayout lr
        }

        component sistema.authService "C3_Auth_Service" "Componentes internos del servicio de autenticacion." {
            title "C3 - Auth Service"
            include *
            autoLayout lr
        }

        component sistema.apiProductos "C3_API_Productos" "Componentes internos de la API de productos." {
            title "C3 - API de productos"
            include *
            autoLayout lr
        }

        component sistema.apiPedidos "C3_API_Pedidos" "Componentes internos de la API de pedidos." {
            title "C3 - API de pedidos"
            include *
            autoLayout lr
        }

        component sistema.graphqlApi "C3_GraphQL_Usuarios" "Componentes internos de la API GraphQL de usuarios." {
            title "C3 - GraphQL de usuarios"
            include *
            autoLayout lr
        }

        component sistema.mensajeria "C3_Mensajeria" "Componentes internos de los scripts de mensajeria." {
            title "C3 - Mensajeria"
            include *
            autoLayout lr
        }

        dynamic sistema "D_F01_Productos" "Consulta de productos mediante autenticacion, API Gateway y API de productos." {
            title "F01 - Consulta de productos"
            1: usuario -> sistema.authService "Envia credenciales a POST /login" "HTTP/JSON"
            2: sistema.authService -> usuario "Devuelve token opaco" "HTTP/JSON"
            3: usuario -> sistema.apiGateway "Solicita GET /api/products con token Bearer" "HTTP/JSON"
            4: sistema.apiGateway -> sistema.secretManager "Obtiene los secretos de Gateway" "HTTP"
            5: sistema.secretManager -> sistema.apiGateway "Devuelve los secretos configurados" "HTTP"
            6: sistema.apiGateway -> sistema.authService "Solicita POST /introspect" "HTTP/JSON"
            7: sistema.authService -> sistema.apiGateway "Devuelve el estado de la sesion" "HTTP/JSON"
            8: sistema.apiGateway -> sistema.apiProductos "Envia GET /products y el secreto interno" "HTTP/JSON"
            9: sistema.apiProductos -> sistema.apiGateway "Devuelve el catalogo definido en el servicio" "HTTP/JSON"
            10: sistema.apiGateway -> usuario "Devuelve la respuesta de productos" "HTTP/JSON"
            autoLayout lr
        }

        dynamic sistema "D_F02_Pedidos" "Consulta de pedidos mediante autenticacion, API Gateway y API de pedidos." {
            title "F02 - Consulta de pedidos"
            1: usuario -> sistema.authService "Envia credenciales a POST /login" "HTTP/JSON"
            2: sistema.authService -> usuario "Devuelve token opaco" "HTTP/JSON"
            3: usuario -> sistema.apiGateway "Solicita GET /api/orders con token Bearer" "HTTP/JSON"
            4: sistema.apiGateway -> sistema.secretManager "Obtiene los secretos de Gateway" "HTTP"
            5: sistema.secretManager -> sistema.apiGateway "Devuelve los secretos configurados" "HTTP"
            6: sistema.apiGateway -> sistema.authService "Solicita POST /introspect" "HTTP/JSON"
            7: sistema.authService -> sistema.apiGateway "Devuelve el estado de la sesion" "HTTP/JSON"
            8: sistema.apiGateway -> sistema.apiPedidos "Envia GET /orders y el secreto interno" "HTTP/JSON"
            9: sistema.apiPedidos -> sistema.apiGateway "Devuelve los pedidos de ejemplo" "HTTP/JSON"
            10: sistema.apiGateway -> usuario "Devuelve la respuesta de pedidos" "HTTP/JSON"
            autoLayout lr
        }

        dynamic sistema "D_F03_GraphQL" "Consulta o modificacion de usuarios mediante GraphQL y MongoDB." {
            title "F03 - Operaciones GraphQL de usuarios"
            1: usuario -> sistema.graphqlApi "Envia una consulta o mutacion GraphQL" "HTTP/GraphQL"
            2: sistema.graphqlApi -> sistema.mongoDb "Consulta o modifica registros de usuarios mediante Mongoose" "MongoDB"
            3: sistema.mongoDb -> sistema.graphqlApi "Devuelve los registros solicitados" "MongoDB"
            4: sistema.graphqlApi -> usuario "Devuelve el resultado GraphQL" "HTTP/GraphQL"
            autoLayout lr
        }

        dynamic sistema.mensajeria "D_F04_Mensajeria" "Envio y recepcion de un mensaje JSON mediante ActiveMQ y STOMP." {
            title "F04 - Mensajeria de pedidos"
            1: desarrollador -> sistema.mensajeria.productor "Ejecuta productor.py" "Terminal"
            2: sistema.mensajeria.productor -> sistema.activeMq "Envia JSON a /queue/pedidos" "STOMP"
            3: sistema.activeMq -> sistema.mensajeria.consumidor "Entrega el mensaje de la cola" "STOMP"
            4: sistema.mensajeria.consumidor -> desarrollador "Muestra los datos del pedido recibido" "Consola"
            autoLayout lr
        }

        deployment sistema local "DEP_Local" "Distribucion de los componentes en el entorno de desarrollo local." {
            title "Despliegue - Desarrollo local"
            include *
            autoLayout lr
        }

        styles {
            element "Deployment Node" {
                background #E9EFF5
                color #213F56
                stroke #8FA5B7
            }
            element "Infrastructure Node" {
                shape roundedbox
                background #EDF0F3
                color #334454
            }
            element "ZonaLocal" {
                background #F0F3F6
                color #243F56
            }
            element "Person" {
                shape person
                background #56718A
                color #FFFFFF
            }
            element "Software System" {
                shape roundedbox
                background #0C527A
                color #FFFFFF
            }
            element "SistemaEvaluado" {
                background #173B5D
                color #FFFFFF
            }
            element "Container" {
                shape roundedbox
                background #E3ECF5
                color #173B5D
            }
            element "Frontend" {
                shape webbrowser
                background #CDE5F7
                color #153E5B
            }
            element "Gateway" {
                background #2B6289
                color #FFFFFF
            }
            element "Seguridad" {
                background #3F6171
                color #FFFFFF
            }
            element "Backend" {
                background #D5E8EF
                color #173B5D
            }
            element "Mensajeria" {
                background #E9E2F2
                color #4A3666
            }
            element "BaseDatos" {
                shape cylinder
                background #E5EAF0
                color #243F56
            }
            element "Component" {
                shape roundedbox
                background #EDF3F7
                color #173B5D
            }
            relationship "Relationship" {
                color #60758A
                thickness 2
            }
        }
    }
}