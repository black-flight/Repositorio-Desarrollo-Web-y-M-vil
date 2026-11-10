workspace "Tokyo Noodles" "Arquitectura C4 de la plataforma comercial Tokyo Noodles" {

    !identifiers hierarchical

    model {

        visitante = person "Visitante" "Consulta el sitio web, el menu y las promociones."

        cliente = person "Cliente de la API" "Realiza solicitudes autenticadas de catalogo, perfil, pedidos y pagos."

        administrador = person "Administrador" "Utiliza operaciones administrativas protegidas."

        operador = person "Operador tecnico" "Configura el entorno y ejecuta verificaciones HTTP."


        tokyo = softwareSystem "Tokyo Noodles" "Plataforma comercial con frontend responsivo y backend de microservicios." {

            tags "SistemaPrincipal"


            frontend = container "Frontend responsivo" "Interfaz web de catalogo, promociones, carrito y acceso de usuarios. Se conserva como componente independiente del backend." "PHP, HTML, CSS y JavaScript" {
                tags "Frontend"
            }


            gateway = container "API Gateway" "Punto de entrada HTTP en el puerto 8000. Gestiona autenticacion, rutas autorizadas, secretos de integracion y reenvio de solicitudes." "Python, FastAPI y HTTPX" {
                tags "Gateway"

                entrada = component "Entrada HTTP" "Recibe solicitudes REST, autenticacion y consultas GraphQL mediante rutas externas definidas." "FastAPI" {
                    tags "Componente"
                }

                autenticacion = component "Autenticacion" "Valida tokens Bearer mediante introspeccion del Auth Service." "FastAPI y HTTPX" {
                    tags "Componente"
                }

                secretos = component "Cliente Vault" "Recupera las credenciales internas desde el almacenamiento KV v2." "HTTPX" {
                    tags "Componente"
                }

                rutas = component "Politicas de rutas" "Restringe rutas y metodos HTTP segun los roles verificados." "Python" {
                    tags "Componente"
                }

                proxyRest = component "Proxy REST" "Reenvia las operaciones permitidas hacia los servicios de negocio con identidad y credencial interna." "HTTPX" {
                    tags "Componente"
                }

                proxyGraphql = component "Proxy GraphQL" "Reenvia consultas autorizadas al GraphQL Gateway con una credencial particular." "HTTPX" {
                    tags "Componente"
                }
            }


            auth = container "Auth Service" "Administra usuarios, credenciales, roles, sesiones, expiracion e introspeccion de tokens." "Python, FastAPI, Motor y MongoDB" {
                tags "Seguridad"
            }


            inventory = container "Inventory" "Administra el catalogo de productos, sus precios, disponibilidad y operaciones de mantenimiento." "Python, FastAPI, Motor y MongoDB" {
                tags "Microservicio"
            }


            clients = container "Clients" "Gestiona los perfiles y datos personales de clientes, con controles de identidad y propiedad del recurso." "Python, FastAPI, Motor y MongoDB" {
                tags "Microservicio"
            }


            orders = container "Orders" "Registra pedidos, consulta los precios oficiales, calcula totales y controla las transiciones de estado." "Python, FastAPI, Motor y MongoDB" {
                tags "Microservicio"
            }


            payments = container "Payments" "Administra solicitudes de pago persistentes y la confirmacion simulada protegida del entorno local." "Python, FastAPI, Motor y MongoDB" {
                tags "Microservicio"
            }


            graphql = container "GraphQL Gateway" "Expone la consulta privada resumenPedido y agrega informacion de Orders e Inventory sin modificar datos transaccionales." "Node.js, Express, Apollo Server y GraphQL" {
                tags "GraphQL"
            }


            mongo = container "MongoDB" "Persiste productos, clientes, pedidos, pagos, usuarios y sesiones en colecciones separadas de tokyo_noodles_eval2." "MongoDB" {
                tags "Datos"
            }


            mensajeria = container "Scripts de mensajeria" "Productor y consumidor STOMP independientes de las operaciones transaccionales del backend." "Python y STOMP" {
                tags "Complementario"
            }
        }


        vault = softwareSystem "HashiCorp Vault" "Administrador de secretos utilizado en el entorno local con KV v2." {
            tags "Infraestructura"
        }


        broker = softwareSystem "ActiveMQ" "Broker utilizado por los scripts independientes de mensajeria STOMP." {
            tags "Infraestructura"
        }


        visitante -> tokyo.frontend "Consulta las pantallas del sitio" "Navegador web"

        cliente -> tokyo.gateway "Realiza solicitudes autenticadas con token Bearer" "HTTP/JSON"

        administrador -> tokyo.gateway "Ejecuta operaciones de administracion autorizadas" "HTTP/JSON"

        operador -> tokyo.gateway "Realiza pruebas y verifica endpoints" "HTTP/JSON"

        operador -> tokyo.mensajeria "Ejecuta scripts de mensajeria" "Terminal"


        tokyo.gateway -> vault "Obtiene secretos de integracion en KV v2" "HTTP"

        tokyo.gateway -> tokyo.auth "Inicia y cierra sesiones; introspecta tokens" "HTTP/JSON"

        tokyo.gateway -> tokyo.inventory "Consulta y administra productos" "HTTP/JSON"

        tokyo.gateway -> tokyo.clients "Gestiona perfiles de clientes mediante rutas autorizadas" "HTTP/JSON"

        tokyo.gateway -> tokyo.orders "Crea y consulta pedidos; solicita anulaciones y cambios administrativos" "HTTP/JSON"

        tokyo.gateway -> tokyo.payments "Inicia y consulta solicitudes de pago" "HTTP/JSON"

        tokyo.gateway -> tokyo.graphql "Reenvia la consulta resumenPedido con identidad validada y secreto de servicio" "HTTP/GraphQL"


        tokyo.orders -> tokyo.inventory "Obtiene productos, precios y disponibilidad para crear pedidos" "HTTP/JSON"

        tokyo.orders -> tokyo.clients "Comprueba los datos del cliente asociado al pedido" "HTTP/JSON"

        tokyo.payments -> tokyo.orders "Consulta importes oficiales y solicita transiciones de pago protegidas" "HTTP/JSON"

        tokyo.graphql -> tokyo.orders "Consulta un pedido bajo control de propiedad" "HTTP/JSON"

        tokyo.graphql -> tokyo.inventory "Consulta el catalogo para incorporar disponibilidad actual" "HTTP/JSON"


        tokyo.auth -> tokyo.mongo "Persiste usuarios y hashes de sesiones" "Motor"

        tokyo.inventory -> tokyo.mongo "Lee y modifica productos" "Motor"

        tokyo.clients -> tokyo.mongo "Lee y modifica perfiles" "Motor"

        tokyo.orders -> tokyo.mongo "Lee y modifica pedidos" "Motor"

        tokyo.payments -> tokyo.mongo "Lee y modifica solicitudes de pago" "Motor"


        tokyo.mensajeria -> broker "Publica y consume mensajes de ejemplo" "STOMP"


        tokyo.gateway.entrada -> tokyo.gateway.autenticacion "Deriva solicitudes que necesitan identidad"

        tokyo.gateway.autenticacion -> tokyo.gateway.secretos "Solicita la credencial de introspeccion"

        tokyo.gateway.secretos -> vault "Recupera valores de secretos" "HTTP"

        tokyo.gateway.autenticacion -> tokyo.auth "Comprueba el estado del token" "HTTP/JSON"

        tokyo.gateway.autenticacion -> tokyo.gateway.rutas "Entrega identidad y roles verificados"

        tokyo.gateway.rutas -> tokyo.gateway.proxyRest "Autoriza operaciones REST"

        tokyo.gateway.rutas -> tokyo.gateway.proxyGraphql "Autoriza consultas GraphQL"

        tokyo.gateway.proxyRest -> tokyo.inventory "Reenvia solicitudes de catalogo" "HTTP/JSON"

        tokyo.gateway.proxyRest -> tokyo.clients "Reenvia solicitudes de perfiles" "HTTP/JSON"

        tokyo.gateway.proxyRest -> tokyo.orders "Reenvia solicitudes de pedidos" "HTTP/JSON"

        tokyo.gateway.proxyRest -> tokyo.payments "Reenvia solicitudes de pago" "HTTP/JSON"

        tokyo.gateway.proxyGraphql -> tokyo.graphql "Reenvia consultas agregadas" "HTTP/GraphQL"
    }


    views {

        systemContext tokyo "Contexto" {
            include *
            autoLayout lr
        }


        container tokyo "Contenedores" {
            include *
            autoLayout lr
        }


        component tokyo.gateway "ComponentesGateway" {
            include *
            autoLayout lr
        }


        styles {

            element "Person" {
                shape Person
                background #31465B
                color #FFFFFF
            }

            element "SistemaPrincipal" {
                background #243F5C
                color #FFFFFF
            }

            element "Frontend" {
                background #456C96
                color #FFFFFF
            }

            element "Gateway" {
                background #3564A0
                color #FFFFFF
            }

            element "Seguridad" {
                background #986B3E
                color #FFFFFF
            }

            element "Microservicio" {
                background #32765E
                color #FFFFFF
            }

            element "GraphQL" {
                background #685C96
                color #FFFFFF
            }

            element "Datos" {
                background #5E6878
                color #FFFFFF
            }

            element "Complementario" {
                background #66798C
                color #FFFFFF
            }

            element "Infraestructura" {
                background #777777
                color #FFFFFF
            }

            element "Componente" {
                background #315B80
                color #FFFFFF
            }
        }
    }
}