# Checklist del video — 5 componentes obligatorios

- [ ] Contenedores reales `docker compose ps` (13 servicios, verificar estado; `vault-init` finalizado).
- [ ] Versión/commit anotado, navegador, fecha hora, tamaño viewport, datos ficticios y RUN.
- [ ] F12 Network: `POST /api/orders`, resultado HTTP, `ORD-...`, `X-Operacion`; **no mostrar token Bearer**.
- [ ] Gateway: mismo `operacion_id`, lectura KV de Vault y ruta a Orders.
- [ ] Auth: mismo `operacion_id`, resultado de introspección/rol sin token.
- [ ] Backend Orders: mismo `operacion_id`, `secret_check=ok` y lectura de Clients/Inventory.
- [ ] Persistencia: `db=mongo action=insert_order` con igual ID y lectura independiente de ORD desde Mongo.
- [ ] Repetición del mismo `codigo_compra` sin duplicar; payload distinto 409; prueba concurrencia P39.
- [ ] Pago simulado protegido, posterior evento `order.paid`, consumidor registrado una vez; si falla, mostrar reintento controlado.
- [ ] Correo demo claramente no enviado, o API externa real + código recibido (si existe proveedor).
- [ ] Delivery 3 km, comprobante no tributario y reportes admin.
- [ ] GraphQL privado agrega Orders + Inventory y maneja error.
- [ ] Ejecutar al menos 2 RUN independientes, escritorio y móvil emulado; conservar logs y fallos sin modificar.
- [ ] No grabar contraseñas, cookies, tokens, secretos, `.env` ni información personal real.

**Guion sugerido:** 1) versión/arquitectura; 2) login y carrito en navegador; 3) F12 y `X-Operacion`; 4) Gateway Vault/Auth, Orders secret y Mongo; 5) pago demo, STOMP/consumer y comprobante; 6) rechazo/reintento; 7) limitaciones y conclusiones según RUN real. **Sin pruebas Docker no grabar afirmando éxito.**
