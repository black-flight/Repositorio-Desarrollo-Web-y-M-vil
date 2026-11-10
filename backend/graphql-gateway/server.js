const express = require('express');
const crypto = require('crypto');
const { ApolloServer, gql, ForbiddenError } = require('apollo-server-express');
const { parse } = require('graphql');

const app = express();

const GRAPHQL_GATEWAY_SECRET = process.env.GRAPHQL_GATEWAY_SECRET;
const INTERNAL_GATEWAY_SECRET = process.env.INTERNAL_GATEWAY_SECRET;
const ORDERS_URL = process.env.ORDERS_URL || 'http://127.0.0.1:9002';
const INVENTORY_URL = process.env.INVENTORY_URL || 'http://127.0.0.1:9001';

if (!GRAPHQL_GATEWAY_SECRET || !INTERNAL_GATEWAY_SECRET) {
    throw new Error('Configurar GRAPHQL_GATEWAY_SECRET e INTERNAL_GATEWAY_SECRET');
}

const typeDefs = gql`
    type DetallePedido {
        productId: ID!
        nombre: String!
        cantidad: Int!
        precioUnitario: Int!
        subtotal: Int!
        disponibleActual: Boolean
    }

    type ResumenPedido {
        id: ID!
        estado: String!
        total: Int!
        modalidad: String!
        items: [DetallePedido!]!
        advertencias: [String!]!
    }

    type Query {
        resumenPedido(id: ID!): ResumenPedido
    }
`;

function comparar(a, b) {
    const primero = Buffer.from(a || '');
    const segundo = Buffer.from(b || '');

    return primero.length === segundo.length &&
        crypto.timingSafeEqual(primero, segundo);
}

async function consultar(url, headers) {
    return fetch(url, {
        headers,
        signal: AbortSignal.timeout(4000)
    });
}

const resolvers = {
    Query: {
        async resumenPedido(_, { id }, { identidad }) {
            const headers = {
                'X-Gateway-Secret': INTERNAL_GATEWAY_SECRET,
                'X-Authenticated-Client': identidad.id,
                'X-Authenticated-Roles': identidad.roles
            };

            let respuestaPedido;

            try {
                respuestaPedido = await consultar(
                    `${ORDERS_URL}/orders/${encodeURIComponent(id)}`,
                    headers
                );
            } catch {
                throw new Error('Orders no disponible');
            }

            if (respuestaPedido.status === 403) {
                throw new ForbiddenError('Pedido no autorizado');
            }

            if (respuestaPedido.status === 404) {
                return null;
            }

            if (!respuestaPedido.ok) {
                throw new Error('No fue posible consultar el pedido');
            }

            const pedido = await respuestaPedido.json();
            let productos = [];
            const advertencias = [];

            try {
                const respuestaCatalogo = await consultar(
                    `${INVENTORY_URL}/products`,
                    headers
                );

                if (!respuestaCatalogo.ok) {
                    throw new Error('Catalogo no disponible');
                }

                const catalogo = await respuestaCatalogo.json();
                productos = catalogo.products || [];
            } catch {
                advertencias.push('No se pudo consultar la disponibilidad actual');
            }

            const porId = new Map(
                productos.map(p => [String(p.id), p])
            );

            const items = pedido.items.map(item => {
                const producto = porId.get(String(item.product_id));

                return {
                    productId: item.product_id,
                    nombre: item.nombre,
                    cantidad: item.cantidad,
                    precioUnitario: item.precio_unitario,
                    subtotal: item.subtotal,
                    disponibleActual: producto ? producto.available : null
                };
            });

            return {
                id: pedido.id,
                estado: pedido.estado,
                total: pedido.total,
                modalidad: pedido.modalidad,
                items,
                advertencias
            };
        }
    }
};

function revisarConsulta(query) {
    if (typeof query !== 'string' || query.length > 2000) {
        return false;
    }

    let documento;

    try {
        documento = parse(query);
    } catch {
        return false;
    }

    if (documento.definitions.length !== 1) {
        return false;
    }

    const operacion = documento.definitions[0];

    if (
        operacion.kind !== 'OperationDefinition' ||
        operacion.operation !== 'query'
    ) {
        return false;
    }

    let cantidad = 0;
    let valido = true;

    function recorrer(selecciones, profundidad) {
        if (profundidad > 5) {
            valido = false;
        }

        for (const campo of selecciones.selections) {
            if (
                campo.kind !== 'Field' ||
                campo.name.value.startsWith('__')
            ) {
                valido = false;
                continue;
            }

            cantidad++;

            if (cantidad > 25) {
                valido = false;
            }

            if (campo.selectionSet) {
                recorrer(campo.selectionSet, profundidad + 1);
            }
        }
    }

    recorrer(operacion.selectionSet, 1);

    return valido && cantidad > 0;
}

app.get('/health', (req, res) => {
    res.json({
        status: 'OK',
        service: 'GraphQL Gateway privado'
    });
});

app.use('/graphql', express.json({ limit: '8kb' }), (req, res, next) => {
    if (req.method !== 'POST') {
        return res.status(405).json({
            error: 'Metodo no permitido'
        });
    }

    if (!comparar(req.header('X-Graphql-Secret'), GRAPHQL_GATEWAY_SECRET)) {
        return res.status(403).json({
            error: 'Gateway no autorizado'
        });
    }

    const id = req.header('X-Authenticated-Client');

    if (!id) {
        return res.status(401).json({
            error: 'Identidad requerida'
        });
    }

    if (!revisarConsulta(req.body?.query)) {
        return res.status(400).json({
            error: 'Consulta GraphQL fuera de los limites permitidos'
        });
    }

    req.identidad = {
        id,
        roles: req.header('X-Authenticated-Roles') || ''
    };

    next();
});

async function iniciar() {
    const servidor = new ApolloServer({
        typeDefs,
        resolvers,
        introspection: false,
        context: ({ req }) => ({
            identidad: req.identidad
        })
    });

    await servidor.start();

    servidor.applyMiddleware({
        app,
        path: '/graphql',
        cors: false,
        bodyParserConfig: false
    });

    app.listen(8090, '127.0.0.1', () => {
        console.log('GraphQL privado iniciado en 8090');
    });
}

iniciar();