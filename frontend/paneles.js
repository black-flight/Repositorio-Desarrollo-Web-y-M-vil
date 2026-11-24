/* Vistas comerciales: datos desde servicios reales, DOM construido sin HTML de usuario. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const clp = v => '$' + Number(v || 0).toLocaleString('es-CL');
  const text = (tag, value, className) => {
    const e = document.createElement(tag);
    e.textContent = String(value == null ? '' : value);
    if (className) e.className = className;
    return e;
  };
  const button = (label, onClick, style='btn btn-outline-secondary btn-sm') => {
    const b = text('button', label, style);
    b.type = 'button'; b.onclick = async () => {
      b.disabled = true;
      try { await onClick(); } catch (err) { alert(err.message); }
      finally { b.disabled = false; }
    };
    return b;
  };
  const status = (id, msg, success = false) => {
    const e = $(id); if (!e) return;
    e.textContent = msg; e.className = 'tn-status alert ' + (success ? 'alert-success' : 'alert-warning');
  };
  const item = title => {const e=text('div','', 'tn-item');e.append(text('h3',title,'h6'));return e;};
  async function ensureAuth() {
    if (!TokyoAPI.getToken()) { location.assign('login.php?return=menu.php'); throw Error('Inicia sesión'); }
    return TokyoAPI.getCurrentUser();
  }
  function error(id, e) {status(id, e.status === 401 ? 'La sesión expiró. Inicia sesión.' : e.message);}

  async function registro() {
    const form=$('registroForm');
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const b=form.querySelector('button[type=submit]');b.disabled=true;
      const datos=Object.fromEntries(new FormData(form));
      try {
        const r=await TokyoAPI.register(datos);
        form.reset();
        sessionStorage.setItem('tn_pending_verification',r.user_id);
        const ev=r.verificacion_correo || {};
        if(ev.codigo_demo) sessionStorage.setItem('tn_email_demo_code',ev.codigo_demo);
        const txt=`Cuenta ${r.username} creada (${r.user_id}). Notificación: ${ev.estado||'sin resultado'}. `+
          (ev.codigo_demo?'Código DEMO (NO enviado a correo): '+ev.codigo_demo+'. ':'')+
          'Inicia sesión y entra en Verificar correo. Sin proveedor HTTP no se acredita existencia de la casilla.';
        status('registroStatus',txt,true);
        const link=text('a','Iniciar sesión y verificar correo','btn btn-outline-primary mt-2');
        link.href='login.php?return=verificar-correo.php'; $('registroStatus').append(link);
      } catch(err) {error('registroStatus',err);} finally{b.disabled=false;}
    });
  }
  async function verificarCorreo() {
    const form=$('verificarCorreoForm'); if(!form)return;
    try {
      const me=await ensureAuth();
      const id=me.user_id;
      const profile=await TokyoAPI.getMyProfile();
      $('correoVerificacionDestino').textContent='Cuenta '+id+' · correo '+profile.correo+
        ' · verificado externamente: '+Boolean(profile.correo_verificado);
      const demo=sessionStorage.getItem('tn_email_demo_code');
      if(demo){$('codigoCorreo').value=demo;status('verificarCorreoStatus','Código de DEMOSTRACIÓN local: NO entregado por email. Verificarlo NO prueba existencia de la casilla.');}
      form.addEventListener('submit',async e=>{
        e.preventDefault();const b=form.querySelector('[type=submit]');b.disabled=true;
        try {
          const r=await TokyoAPI.verifyEmailCode(id,$('codigoCorreo').value.trim());
          status('verificarCorreoStatus','Estado: '+r.estado+'; correo verificado externamente: '+r.correo_verificado,r.correo_verificado);
          if(r.correo_verificado)sessionStorage.removeItem('tn_email_demo_code');
        }catch(err){error('verificarCorreoStatus',err);}finally{b.disabled=false;}
      });
      $('reenviarCodigo').onclick=async()=>{
        const b=$('reenviarCodigo');b.disabled=true;
        try{const r=await TokyoAPI.sendEmailCode(id);
          if(r.codigo_demo){$('codigoCorreo').value=r.codigo_demo;sessionStorage.setItem('tn_email_demo_code',r.codigo_demo);}
          status('verificarCorreoStatus',r.estado+': '+r.detalle+(r.codigo_demo?' Código DEMO '+r.codigo_demo:''));
        }catch(e){error('verificarCorreoStatus',e);}finally{b.disabled=false;}
      };
    }catch(e){error('verificarCorreoStatus',e);}
  }
  async function perfil() {
    try {
      const me=await ensureAuth();
      const d=await TokyoAPI.getMyProfile();
      status('perfilStatus',`Perfil ${me.user_id} validado por Auth y Clients`,true);
      const holder=$('perfilDatos');holder.replaceChildren();
      for(const key of ['id','nombre','run','correo','telefono','direccion','comuna','provincia','region','activo']) {
        holder.append(text('p',key+': '+String(d[key] ?? 'No informado')));
      }
    } catch(e) {error('perfilStatus',e);}
  }
  const estadosPagados = new Set(['pagado','en_preparacion','listo','en_reparto','entregado','anulacion_solicitada']);
  function renderPedido(p, admin=false) {
    const d=item(`Pedido ${p.id}`);
    d.append(text('p',`Estado: ${p.estado} · ${p.modalidad} · Total ${clp(p.total)} · ${p.fecha}`));
    d.append(text('p','Productos: '+p.items.map(x=>x.nombre+' ×'+x.cantidad).join(', ')));
    if(p.modalidad==='delivery') d.append(text('p',`Distancia calculada: ${p.delivery_distance_km ?? 'sin dato'} km en línea recta`));
    const actions=text('div','', 'd-flex gap-2 flex-wrap align-items-center');
    if (estadosPagados.has(p.estado)) {
      const link=text('a','Ver comprobante comercial','btn btn-outline-secondary btn-sm');
      link.href='comprobante.php?id='+encodeURIComponent(p.id); actions.append(link);
    }
    if (!admin && ['pendiente_pago','pagado'].includes(p.estado)) {
      actions.append(button('Solicitar anulación',async () => {
        const motivo=prompt('Motivo de la anulación (mínimo 5 caracteres):');
        if (motivo===null) return;
        if(motivo.trim().length<5) throw Error('Motivo demasiado corto');
        const actualizado=await TokyoAPI.cancelOrder(p.id,motivo.trim());
        status('pedidosStatus','Pedido '+actualizado.id+' → '+actualizado.estado,true);
        await cargarPedidos();
      },'btn btn-outline-danger btn-sm'));
    }
    d.append(actions);return d;
  }
  async function cargarPedidos() {
    try {
      await ensureAuth();
      const r=await TokyoAPI.getOrders();
      const e=$('pedidosLista');e.replaceChildren();
      if(!r.orders?.length)e.append(text('p','No hay pedidos registrados para esta cuenta.'));
      for(const p of r.orders || []) e.append(renderPedido(p));
      status('pedidosStatus',`${(r.orders||[]).length} pedido(s) consultado(s) desde Orders`,true);
    } catch(e) {error('pedidosStatus',e);}
  }
  const transitions = {
    pagado: ['en_preparacion'],en_preparacion:['listo'],listo:['en_reparto','entregado'],en_reparto:['entregado']
  };
  async function panelGestion() {
    let me;
    try {me=await ensureAuth();}catch(e){error('gestionStatus',e);return;}
    const admin=me.roles.includes('admin'),staff=me.roles.includes('staff');
    if(!admin && !staff){status('gestionStatus','Se requiere rol admin o staff. Esta cuenta solo puede gestionar pedidos propios.');return;}
    $('gestionIdentidad').replaceChildren(text('p',`Operador ${me.username}; roles: ${me.roles.join(', ')}`));
    if(admin) $('panelAdministracion').hidden=false;
    const cargar=async()=>{
      try {
        const r=await TokyoAPI.getOrders();const e=$('gestionPedidos');e.replaceChildren();
        for(const p of r.orders||[]) {
          const card=renderPedido(p,true);
          const next=transitions[p.estado]||[];
          const allowed=next.filter(x=>p.modalidad==='delivery' || x!=='en_reparto');
          for(const estado of allowed) card.append(button('Cambiar a '+estado,async()=>{
            if(!confirm(`¿Cambiar ${p.id} a ${estado}?`))return;
            await TokyoAPI.updateOrderStatus(p.id,estado);await cargar();
          }));
          if(admin && p.estado==='pendiente_pago'){
            const div=text('div','', 'mt-2');
            div.append(button('Consultar y confirmar pago DE PRUEBA', async()=>{
              const pago=await TokyoAPI.getPaymentForOrder(p.id);
              if(!confirm(`Confirmar PAGO SIMULADO ${pago.id} (${clp(pago.monto)})? No es transacción real.`))return;
              const resultado=await TokyoAPI.confirmTestPayment(pago.id);
              status('gestionStatus',`Pago demo ${resultado.id}: ${resultado.estado}; email: ${resultado.email_status||'desconocido'}`,true);
              await cargar();
            },'btn btn-warning btn-sm'));
            card.append(div);
          }
          if((admin || staff) && p.event_status==='fallido'){
            card.append(button('Reintentar evento STOMP de pago',async()=>{
              const z=await TokyoAPI.retryOrderEvent(p.id);
              status('gestionStatus','Evento pedido '+p.id+': '+z.event_status,true);
              await cargar();
            },'btn btn-outline-warning btn-sm'));
          }
          e.append(card);
        }
        if(!(r.orders||[]).length)e.append(text('p','Sin pedidos para gestionar'));
        status('gestionStatus',`${(r.orders||[]).length} pedido(s); vista consultada a través del API Gateway`,true);
        if(admin)await cargarAdmin();
      }catch(e){error('gestionStatus',e);}
    };
    async function cargarAdmin() {
      try {
        const catalogo=await TokyoAPI.request('/products');
        const div=$('adminCatalogo');div.replaceChildren();
        for(const product of catalogo.products){
          const line=text('div','', 'tn-item d-flex justify-content-between flex-wrap align-items-center');
          line.append(text('span',`${product.nombre} · ${clp(product.precio)} · ${product.available?'Activo':'Desactivado'}`));
          line.append(button(product.available?'Desactivar':'Activar',async()=>{
            await TokyoAPI.updateProduct(product.id,{...product, available:!product.available});
            await cargarAdmin();
          }));div.append(line);
        }
        $('estadoMensajeria').textContent=JSON.stringify(await TokyoAPI.getEventStatus(),null,2);
      }catch(e){error('gestionStatus',e);}
    }
    $('actualizarGestion').addEventListener('click',cargar);
    if(admin){
      const today=new Date().toISOString().slice(0,10);
      $('ventasHasta').value=today;
      $('ventasDesde').value=today.slice(0,7)+'-01';
      $('ventasForm').addEventListener('submit',async event=>{
        event.preventDefault();
        try {$('ventasResultado').textContent=JSON.stringify(await TokyoAPI.getSalesReport($('ventasDesde').value,$('ventasHasta').value),null,2);}
        catch(e){error('gestionStatus',e);}
      });
    }
    await cargar();
  }
  async function comprobante() {
    const id=new URLSearchParams(location.search).get('id');
    if(!/^ORD-[\w-]+$/.test(id||'')){status('comprobanteStatus','Falta un identificador de pedido válido.');return;}
    try {
      await ensureAuth();
      const p=await TokyoAPI.getReceipt(id);
      const d=$('comprobanteContenido');d.replaceChildren();
      for(const k of ['pedido_id','cliente_id','fecha','modalidad','estado','referencia_pago'])d.append(text('p',`${k}: ${p[k]}`));
      const t=document.createElement('table');t.className='table table-striped';
      const h=document.createElement('thead');const hr=document.createElement('tr');
      ['Artículo','Cantidad','Precio unitario','Subtotal'].forEach(x=>hr.append(text('th',x)));h.append(hr);t.append(h);
      const b=document.createElement('tbody');
      p.items.forEach(x=>{const r=document.createElement('tr');[x.nombre,x.cantidad,clp(x.precio_unitario),clp(x.subtotal)].forEach(v=>r.append(text('td',v)));b.append(r);});
      t.append(b);d.append(t);d.append(text('h2',`Total: ${clp(p.total_clp)}`));
      d.append(text('p',p.leyenda,'text-danger fw-bold'));
      status('comprobanteStatus','Comprobante comercial consultado desde Orders (no tributario)',true);
    }catch(e){error('comprobanteStatus',e);}
    $('imprimirComprobante').addEventListener('click',()=>window.print());
  }
  document.addEventListener('DOMContentLoaded',()=>{
    if($('registroForm'))registro();
    if($('verificarCorreoForm'))verificarCorreo();
    if($('perfilDatos'))perfil();
    if($('pedidosLista')){$('recargarPedidos').addEventListener('click',cargarPedidos);cargarPedidos();}
    if($('gestionPedidos'))panelGestion();
    if($('comprobanteContenido'))comprobante();
  });
})();
