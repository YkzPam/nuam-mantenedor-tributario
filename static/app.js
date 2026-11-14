'use strict';
const $ = id => document.getElementById(id);
let csrf=document.body.dataset.csrf, me=null, currentPage=1, lastBatch=null, deleteRecord=null, catalog=[];
const element=(tag,attributes={},...children)=>{
  const node=document.createElement(tag);
  for(const [key,value] of Object.entries(attributes)){
    if(key==='text') node.textContent=value;
    else if(key==='class') node.className=value;
    else node.setAttribute(key,value);
  }
  for(const child of children) node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  return node;
};
function notify(text,error=false){
  const box=$('message')||$('login-message'); box.textContent=text; box.hidden=false;
  if(box.id==='message')box.className='message'+(error?' error':'');
}
const run=fn=>async event=>{if(event)event.preventDefault();try{await fn(event);}catch(error){notify(error.message,true);}};
async function api(path,method='GET',body=null){
  const options={method,headers:{'X-CSRF-Token':csrf},credentials:'same-origin'};
  if(body instanceof FormData) options.body=body;
  else if(body!==null){options.headers['Content-Type']='application/json';options.body=JSON.stringify(body);}
  const response=await fetch('/api/'+path,options);
  let data;try{data=await response.json();}catch{throw Error('Respuesta no disponible. Recargar la página.');}
  if(!response.ok) throw Error(data.error||'Operación no disponible.');
  return data;
}
function action(label,fn,style='secondary'){
  const button=element('button',{type:'button',class:style,text:label});button.addEventListener('click',run(fn));return button;
}
function fillBrokers(select,blank=false){
  select.replaceChildren();if(blank)select.append(element('option',{value:'',text:'Todos los autorizados'}));
  for(const b of me.brokers)select.append(element('option',{value:b.id,text:b.codigo+' · '+b.nombre}));
}
async function loadRatings(){
  const params=new URLSearchParams({page:currentPage});
  for(const [id,name] of [['filter-broker','broker'],['filter-market','market'],['filter-period','period'],['filter-origin','origin'],['filter-query','q']])if($(id).value)params.set(name,$(id).value);
  const data=await api('ratings?'+params);$('rating-rows').replaceChildren();
  for(const row of data.items){
    const inst=element('td',{'data-label':'Instrumento'},row.instrumento,element('br'),element('span',{class:'badge',text:row.inscrito?'Inscrito':'No inscrito'}));
    const buttons=element('td',{'data-label':'Acciones'},action('Detalle',()=>showDetail(row.id)),action('Modificar',()=>editRating(row.id)),action('Desactivar',()=>openDelete(row)));
    const bolsa=row.origen==='bolsa-DEMO', origin=element('td',{'data-label':'Origen'},row.origen);
    if(bolsa)origin.append(element('br'),element('span',{class:'badge',text:'Prioridad Bolsa'}));
    if(bolsa&&me.user.rol!=='supervisor')for(const button of [...buttons.children].slice(1)){button.disabled=true;button.title='Regla DEMO-3: solo el supervisor cambia registros informados por Bolsa.';}
    $('rating-rows').append(element('tr',{},inst,element('td',{'data-label':'Corredor / mercado'},row.corredor+' / '+row.mercado),element('td',{'data-label':'Período'},row.periodo),element('td',{'data-label':'Calificación'},row.calificacion),element('td',{'data-label':'Factor'},row.factor),origin,buttons));
  }
  if(!data.items.length)$('rating-rows').append(element('tr',{},element('td',{colspan:7,text:'Sin registros que coincidan con los filtros.'})));
  $('count').textContent=data.total+' registro(s) · Página '+data.page+' de '+data.pages;
  $('previous').disabled=data.page<=1;$('next').disabled=data.page>=data.pages;
}
function catalogMatch(){
  const code=$('rating-instrument').value.trim().toUpperCase(), market=$('rating-market').value;
  const entry=catalog.find(item=>item.codigo===code&&item.mercado===market);
  if(!code){$('catalog-hint').textContent='';return;}
  if(!entry){$('catalog-hint').textContent='No figura en el catálogo: solo se admite como no inscrito (DEMO-2).';$('rating-registered').value='0';return;}
  $('rating-registered').value=String(entry.inscrito);
  $('catalog-hint').textContent='Catálogo: '+(entry.inscrito?'inscrito':'no inscrito')+' · '+(entry.habilitado?'habilitado':'deshabilitado, no admite registros (DEMO-2)');
}
async function loadCatalog(){
  const params=new URLSearchParams();
  if($('catalog-market').value)params.set('market',$('catalog-market').value);if($('catalog-query').value)params.set('q',$('catalog-query').value);
  const data=await api('instruments?'+params);
  if(!params.toString()){catalog=data.items;$('instrument-options').replaceChildren(...catalog.filter(item=>item.habilitado).map(item=>element('option',{value:item.codigo,label:item.mercado+' · '+(item.inscrito?'inscrito':'no inscrito')})));}
  $('catalog-rows').replaceChildren();
  for(const item of data.items){
    const actions=element('td',{});
    if(me.user.rol==='supervisor')actions.append(action(item.habilitado?'Deshabilitar':'Habilitar',async()=>{await api('instruments/'+item.id,'PUT',{enabled:!item.habilitado,version:item.version});notify('Catálogo actualizado y registrado en bitácora.');await loadCatalog();}));
    else actions.append(element('span',{class:'hint',text:'Solo consulta'}));
    $('catalog-rows').append(element('tr',{},element('td',{text:item.mercado}),element('td',{text:item.codigo}),element('td',{text:item.inscrito?'Inscrito':'No inscrito'}),element('td',{text:item.habilitado?'Habilitado':'Deshabilitado'}),actions));
  }
  if(!data.items.length)$('catalog-rows').append(element('tr',{},element('td',{colspan:5,text:'Sin instrumentos que coincidan con la búsqueda.'})));
  $('catalog-count').textContent=data.total+' instrumento(s)'+(data.total>data.items.length?' · se muestran los primeros '+data.items.length:'')+'. '+data.rule;
}
// H-03: nombres legibles de las entidades de la bitácora.
const ENTITY_LABELS={calificacion:'calificación',carga:'carga',archivo:'archivo',instrumento:'instrumento',usuario:'usuario',seguridad:'seguridad'};
function ratingMode(){
  const direct=$('rating-mode').value==='factor';$('rating-factor').disabled=!direct;$('rating-factor').required=direct;
  $('rating-amount').disabled=direct;$('rating-base').disabled=direct;$('rating-amount').required=!direct;$('rating-base').required=!direct;
}
function newRating(){
  $('rating-form').reset();for(const c of $('rating-form').querySelectorAll('[aria-invalid]'))c.removeAttribute('aria-invalid');$('rating-id').value='';$('rating-version').value='';$('rating-broker').disabled=false;$('rating-title').textContent='Crear calificación';$('form-error').textContent='';$('catalog-hint').textContent='';ratingMode();$('edit-dialog').showModal();
}
async function editRating(id){
  const {item}=await api('ratings/'+id);$('rating-title').textContent='Modificar calificación';$('rating-id').value=id;$('rating-version').value=item.version;
  for(const [field,key] of [['broker','corredor_id'],['market','mercado'],['period','periodo'],['instrument','instrumento'],['name','calificacion'],['registered','inscrito'],['amount','monto'],['base','base'],['factor','factor']])$('rating-'+field).value=item[key]??'';
  $('rating-mode').value=item.monto!==null?'monto':'factor';$('rating-broker').disabled=true;$('form-error').textContent='';$('catalog-hint').textContent='';ratingMode();$('edit-dialog').showModal();
}
async function showDetail(id){
  const {item}=await api('ratings/'+id);$('detail-fields').replaceChildren();
  for(const [label,key] of [['ID','id'],['Corredor','corredor_id'],['Mercado','mercado'],['Período','periodo'],['Instrumento','instrumento'],['Calificación','calificacion'],['Inscrito (1/0)','inscrito'],['Monto ficticio','monto'],['Base ficticia','base'],['Factor','factor'],['Origen','origen'],['Versión registro','version'],['Regla ilustrativa','regla_id'],['Actualizado (UTC)','actualizado']])$('detail-fields').append(element('dt',{text:label}),element('dd',{text:item[key]??'No aplica'}));
  $('detail-dialog').showModal();
}
function openDelete(row){
  deleteRecord=row;
  $('delete-description').textContent='Se desactivará la calificación «'+row.calificacion+'» del instrumento '+row.instrumento+', período '+row.periodo+', corredor '+row.corredor+'.';
  $('delete-dialog').showModal();
  $('cancel-delete').focus();
}
// H-07: validación propia en español que indica todos los campos pendientes de una vez.
function formProblems(form){
  const problems=[];
  for(const control of form.querySelectorAll('input,select')){
    control.removeAttribute('aria-invalid');
    if(control.disabled||control.type==='hidden'||control.checkValidity())continue;
    const label=form.querySelector('label[for="'+control.id+'"]');
    const reason=control.validity.valueMissing?'falta completar':'formato no válido';
    control.setAttribute('aria-invalid','true');
    problems.push({control,text:(label?label.textContent:control.id)+' ('+reason+')'});
  }
  return problems;
}
async function saveRating(event){
  event.preventDefault();
  const problems=formProblems($('rating-form'));
  if(problems.length){$('form-error').textContent='Revisa estos campos: '+problems.map(p=>p.text).join(', ')+'.';problems[0].control.focus();return;}
  const payload={};for(const [field,key] of [['broker','broker'],['market','market'],['period','period'],['instrument','instrument'],['name','rating'],['registered','registered'],['mode','mode'],['amount','amount'],['base','base'],['factor','factor'],['version','version']])payload[key]=$('rating-'+field).value;
  const id=$('rating-id').value;
  try{await api(id?'ratings/'+id:'ratings',id?'PUT':'POST',payload);$('edit-dialog').close();notify(id?'Calificación modificada y registrada en bitácora.':'Calificación creada y registrada en bitácora.');await loadRatings();await loadCatalog();}
  catch(error){$('form-error').textContent=error.message;}
}
async function uploadExample(invalid){
  const mode=$('batch-kind').value==='DJ1948-DEMO'?'monto':'factor', instrument=($('batch-kind').value==='bolsa-DEMO'?'DEMO-BOLSA-':'DEMO-CARGA-')+Date.now();
  const row=['SCL','2026-10',instrument,'Tributaria demo',mode,mode==='monto'?'250':'',mode==='monto'?'1000':'',mode==='factor'?'0.25':'','0'].join(',');
  let content='market,period,instrument,rating,mode,amount,base,factor,registered\n'+row+'\n';
  if(invalid){content+=row+'\n';content+='SCL,2026-99,DEMO-ERROR,Tributaria demo,'+mode+',-1,0,2,0\n';}
  const body=new FormData();body.append('broker',$('batch-broker').value);body.append('kind',$('batch-kind').value);body.append('file',new Blob([content],{type:'text/csv'}),invalid?'ejemplo-errores.csv':'ejemplo-valido.csv');
  await preview(body);
}
async function preview(body){
  const data=await api('batches/preview','POST',body);lastBatch=data.id;$('preview').hidden=false;$('preview-rows').replaceChildren();
  $('preview-count').textContent='Carga '+data.id+': '+data.total+' fila(s), '+data.valid+' válida(s), '+data.invalid+' con errores'+(data.replacements?', '+data.replacements+' reemplazo(s) por prioridad Bolsa':'')+'. '+(data.invalid?'Rechazo total: ninguna fila se incorporará.':'Lista para confirmación explícita.');
  for(const row of data.rows)$('preview-rows').append(element('tr',{},element('td',{text:row.number}),element('td',{text:row.raw.instrument}),element('td',{text:row.errors.length?'Rechazada':(row.notice?'Válida · reemplaza':'Válida')}),element('td',{text:row.errors.length?row.errors.join(' · '):row.clean.factor+(row.notice?' · '+row.notice:'')})));
  $('confirm-batch').disabled=!data.can_confirm;notify('Prevalidación terminada. Revisar el resultado por fila.');await loadBatches();
}
async function loadBatches(){
  const {items}=await api('batches');$('batch-history').replaceChildren();
  for(const row of items){
    const box=element('div',{class:'audit-card'},element('h3',{text:'Carga '+row.id+' · '+row.tipo+' · '+row.estado}),element('p',{text:row.total+' fila(s): '+row.validas+' válida(s), '+row.invalidas+' inválida(s) · '+row.creado}));
    for(const file of row.files)box.append(element('p',{},element('a',{href:'/api/files/'+file.id,text:'Descargar '+file.clase+' ('+file.bytes+' bytes)'}),element('br'),element('small',{text:'SHA-256: '+file.sha256})));
    box.append(action('Consultar documento TinyDB',async()=>{const data=await api('documents/'+row.id);$('document-content').textContent=JSON.stringify(data.document,null,2);$('document-dialog').showModal();}));
    $('batch-history').append(box);
  }
  if(!items.length)$('batch-history').append(element('p',{text:'Todavía no hay cargas en el ámbito autorizado.'}));
}
async function loadAudit(){
  const data=await api('audit');$('audit-integrity').textContent=data.integrity?'Integridad verificada: cadena HMAC y referencias anteriores correctas.':'Advertencia: la cadena de integridad no coincide.';$('audit-items').replaceChildren();
  for(const row of data.items){
    const detail=element('details',{},element('summary',{text:'Ver valores anteriores y nuevos'}),element('p',{text:'Antes'}),element('pre',{text:row.antes_json?JSON.stringify(JSON.parse(row.antes_json),null,2):'No aplica'}),element('p',{text:'Después'}),element('pre',{text:row.despues_json?JSON.stringify(JSON.parse(row.despues_json),null,2):'No aplica'}));
    $('audit-items').append(element('article',{class:'audit-card'},element('h3',{text:'#'+row.id+' · '+row.accion+' · '+(ENTITY_LABELS[row.entidad]||row.entidad)}),element('p',{text:row.fecha+' · Usuario '+(row.usuario_login??row.usuario_id??'no autenticado')+' · Corredor '+(row.corredor_codigo??row.corredor_id??'evento técnico')+' · '+row.resultado}),detail));
  }
  if(!data.items.length)$('audit-items').append(element('p',{text:'No hay eventos dentro del ámbito autorizado.'}));
}
async function loadUsers(){
  const data=await api('users');$('user-items').replaceChildren();
  for(const user of data.items){
    const role=element('select',{'aria-label':'Perfil de '+user.login});for(const name of ['operador','supervisor','administrador'])role.append(element('option',{value:name,text:name}));role.value=user.rol;
    const active=element('input',{type:'checkbox','aria-label':'Usuario activo '+user.login});active.checked=!!user.activo;
    const checks=data.brokers.map(b=>{const input=element('input',{type:'checkbox',value:b.id});input.checked=user.brokers.includes(b.id);return {broker:b.id,input,label:element('label',{class:'check-label'},input,b.codigo)};});
    const fields=element('div',{class:'two-col'},element('div',{},element('label',{text:'Perfil'}),role),element('label',{class:'check-label'},active,'Usuario activo'));
    const box=element('article',{class:'user-card'},element('h2',{text:user.nombre+' · '+user.login}),fields,element('p',{text:'Corredores autorizados:'}),...checks.map(c=>c.label));
    const save=action('Guardar perfil',async()=>{await api('users/'+user.id,'PUT',{role:role.value,active:active.checked,brokers:checks.filter(c=>c.input.checked).map(c=>c.broker),version:user.version});notify('Perfil actualizado y registrado en bitácora.');await loadUsers();});
    if(user.id===me.user.id){save.disabled=true;role.disabled=true;active.disabled=true;checks.forEach(c=>c.input.disabled=true);}
    box.append(element('div',{class:'actions'},save));$('user-items').append(box);
  }
}
async function switchView(view){
  // H-01: el aviso de la acción anterior no se arrastra a otra vista.
  const notice=$('message');if(notice)notice.hidden=true;
  for(const section of document.querySelectorAll('.view'))section.hidden=section.id!==view;
  for(const button of document.querySelectorAll('.nav-button'))button.classList.toggle('active',button.dataset.view===view);
  if(view==='consulta')await loadRatings();if(view==='carga')await loadBatches();if(view==='catalogo')await loadCatalog();if(view==='auditoria')await loadAudit();if(view==='usuarios')await loadUsers();
}
async function start(){
  me=await api('me');csrf=me.csrf;
  if($('login-form')){$('login-form').addEventListener('submit',run(async()=>{await api('login','POST',{login:$('login').value,password:$('password').value});location.reload();}));return;}
  $('logout').addEventListener('click',run(async()=>{await api('logout','POST',{});location.reload();}));
  for(const button of document.querySelectorAll('.nav-button'))button.addEventListener('click',run(()=>switchView(button.dataset.view)));
  $('refresh-audit').addEventListener('click',run(loadAudit));
  if(me.user.rol==='administrador'){await loadAudit();return;}
  fillBrokers($('filter-broker'),true);fillBrokers($('rating-broker'));fillBrokers($('batch-broker'));
  $('search-form').addEventListener('submit',run(async()=>{currentPage=1;await loadRatings();}));
  $('clear-filter').addEventListener('click',run(async()=>{$('search-form').reset();currentPage=1;await loadRatings();}));
  $('previous').addEventListener('click',run(async()=>{currentPage--;await loadRatings();}));$('next').addEventListener('click',run(async()=>{currentPage++;await loadRatings();}));
  $('new-rating').addEventListener('click',newRating);$('rating-mode').addEventListener('change',ratingMode);$('rating-form').addEventListener('submit',saveRating);
  $('rating-instrument').addEventListener('change',catalogMatch);$('rating-market').addEventListener('change',catalogMatch);
  $('catalog-form').addEventListener('submit',run(loadCatalog));
  if($('instrument-form'))$('instrument-form').addEventListener('submit',run(async()=>{await api('instruments','POST',{market:$('instrument-market').value,code:$('instrument-code').value,registered:$('instrument-registered').value});$('instrument-form').reset();notify('Instrumento agregado al catálogo y registrado en bitácora.');await loadCatalog();}));
  document.querySelectorAll('.close-dialog').forEach(b=>b.addEventListener('click',()=>$('edit-dialog').close()));document.querySelectorAll('.close-detail').forEach(b=>b.addEventListener('click',()=>$('detail-dialog').close()));
  document.querySelectorAll('.close-document').forEach(b=>b.addEventListener('click',()=>$('document-dialog').close()));
  $('cancel-delete').addEventListener('click',()=>$('delete-dialog').close());$('accept-delete').addEventListener('click',run(async()=>{await api('ratings/'+deleteRecord.id,'DELETE',{version:deleteRecord.version});$('delete-dialog').close();notify('Calificación desactivada. Sus datos y su historial se conservan.');await loadRatings();}));
  $('upload-form').addEventListener('submit',run(async()=>{if(!$('batch-file').files.length)throw Error('Seleccionar un archivo o usar un ejemplo académico.');const body=new FormData();body.append('broker',$('batch-broker').value);body.append('kind',$('batch-kind').value);body.append('file',$('batch-file').files[0]);await preview(body);}));
  $('example-valid').addEventListener('click',run(()=>uploadExample(false)));$('example-invalid').addEventListener('click',run(()=>uploadExample(true)));
  $('confirm-batch').addEventListener('click',run(async()=>{
    const batchId=lastBatch;
    const data=await api('batches/'+batchId+'/confirm','POST',{});
    if(lastBatch===batchId){
      $('preview-count').textContent='Carga '+batchId+' confirmada: '+data.inserted+' registro(s) incorporado(s). No hay una nueva confirmación pendiente.'+(data.replaced?' '+data.replaced+' reemplazo(s) por prioridad Bolsa (DEMO-3).':'');
      $('confirm-batch').disabled=true;
    }
    notify(data.inserted+' registro(s) incorporado(s). Reintentos no duplican la carga.');await loadBatches();await loadCatalog();
  }));
  $('factor-form').addEventListener('submit',run(async()=>{const data=await api('factor/preview','POST',{amount:$('factor-amount').value,base:$('factor-base').value});$('factor-result').textContent='Factor de prueba: '+data.factor+' · '+data.rule;}));
  await loadCatalog();await loadRatings();
}
start().catch(error=>notify(error.message,true));
