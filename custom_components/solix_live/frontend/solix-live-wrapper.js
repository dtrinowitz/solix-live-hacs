import '/solix_live/solix-live-panel.js';
const Panel=customElements.get('solix-live-panel');
const originalConnected=Panel.prototype.connectedCallback;
const originalRefresh=Panel.prototype.refresh;
// Resolve a dashboard metric to the actual Home Assistant entity before opening more-info.
// Home Assistant may assign an entity_id different from the integration's suggested name.
const METRIC_NAMES={solarleistung:'Solarleistung',ausgangsleistung:'Ausgangsleistung',hausverbrauch:'Hausverbrauch',hauseinspeisung:'Hauseinspeisung',ladestand:'Ladestand',betriebszustand:'Betriebszustand',systemdetails:'Systemdetails'};
Panel.prototype._metricEntity=function(key){
  const states=this._hass?.states||{};
  const preferred='sensor.solix_live_'+key;
  if(states[preferred]&&!['unknown','unavailable'].includes(String(states[preferred].state).toLowerCase()))return states[preferred];
  const expected=METRIC_NAMES[key];
  if(!expected)return null;
  const matches=Object.values(states).filter(s=>{
    if(!s.entity_id?.startsWith('sensor.'))return false;
    const label=String(s.attributes?.friendly_name||'');
    return (s.entity_id.startsWith('sensor.solix_live_')||/SOLIX Live/i.test(label)) &&
      (label===expected||label==='SOLIX Live '+expected||label.endsWith(' '+expected)) &&
      !s.attributes?.read_only_mirror;
  });
  return matches.length===1?matches[0]:null;
};
Panel.prototype.openDetails=function(kind){
  const key={pv:'solarleistung',battery:'ladestand',home:'hausverbrauch',export:'hauseinspeisung'}[kind];
  const target=key&&this._metricEntity(key);
  if(!target){this._openSolixDetail(kind);return;}
  this._openSolixDetail(kind);
  /*this.dispatchEvent(new CustomEvent('hass-more-info',{bubbles:true,composed:true,detail:{entityId:target.entity_id}}));*/
};
Panel.prototype._openSolixDetail=function(kind){const section=this.shadowRoot.querySelector('.details');if(!section)return;section.scrollIntoView({behavior:'smooth',block:'start'});section.querySelectorAll('details').forEach(el=>{el.open=(kind==='pv');});};
Panel.prototype._translateStatus=function(value){
 const labels={discharge:'Entladen',charge:'Laden',charging:'Laden',discharging:'Entladen',detection:'Erkennung',standby:'Bereitschaft',full_bypass:'Direktversorgung',bypass:'Direktversorgung',idle:'Leerlauf'};
 return String(value||'Unbekannt').split('/').map(part=>labels[part.trim().toLowerCase()]||part).join(' / ');
};
Panel.prototype._updateVisualLabels=function(){
 const view=this.$('view');if(!view)return;
 const svgNS='http://www.w3.org/2000/svg';
 let badge=view.querySelector('#solix-title-badge');
 if(!badge){
  const candidates=[...view.querySelectorAll('text')];
  const heading=candidates.find(el=>el.textContent?.trim()==='SOLIX Energy Center');
  if(heading){
   const group=heading.parentElement;
   if(group){
    group.id='solix-title-badge';
    const subtitle=[...group.querySelectorAll('text')].find(el=>el!==heading);
    subtitle?.remove();
    const rect=group.querySelector('rect');
    if(rect){rect.setAttribute('x','1128');rect.setAttribute('y','25');rect.setAttribute('width','492');rect.setAttribute('height','83');}
    heading.setAttribute('x','1152');heading.setAttribute('y','78');heading.setAttribute('font-size','37');
   }
  }
 }
 const card=this.$('batteryCard');
 const rect=card?.querySelector('rect');if(rect){rect.setAttribute('width','490');rect.setAttribute('x','560');rect.setAttribute('height','100');rect.setAttribute('y','753');}
 const lines=card?.querySelectorAll('text');
 if(lines?.length>=2){lines[0].setAttribute('x','580');lines[0].setAttribute('y','789');lines[0].setAttribute('font-size','29');lines[1].setAttribute('x','580');lines[1].setAttribute('y','828');lines[1].setAttribute('font-size','28');}
};
Panel.prototype._installMetricDetailRouting=function(){
  if(this._metricDetailRoutingInstalled)return;
  this._metricDetailRoutingInstalled=true;
  this.addEventListener('hass-more-info',event=>{
    const id=event.detail?.entityId;
    const match=/^sensor\\.solix_live_(solarleistung|ausgangsleistung|hausverbrauch|hauseinspeisung|ladestand|betriebszustand|systemdetails)$/.exec(id||'');
    if(!match)return;
    const target=this._metricEntity(match[1]);
    if(!target||target.entity_id===id)return;
    event.stopImmediatePropagation();
    event.stopPropagation();
    this.dispatchEvent(new CustomEvent('hass-more-info',{detail:{entityId:target.entity_id},bubbles:true,composed:true}));
  },true);
};

Panel.prototype.connectedCallback=function(){originalConnected.call(this);this._installMetricDetailRouting();if(this.shadowRoot.getElementById('solix-tools'))return;
const css=document.createElement('style');css.textContent=`.solix-tools{display:flex;flex-wrap:wrap;align-items:center;gap:9px;padding:12px;background:#112b3d;border-radius:12px;margin-bottom:12px}.solix-tools button,.solix-tools input{padding:9px;border:1px solid #60889b;border-radius:8px;background:#16374b;color:#fff}.solix-tools input{min-width:170px;flex:1}.solix-entities{max-height:60vh;overflow:auto}.solix-entities table{width:100%;border-collapse:collapse;font-size:13px}.solix-entities td,.solix-entities th{padding:7px;border-bottom:1px solid #31506a;text-align:left;overflow-wrap:anywhere}.solix-entities th{position:sticky;top:0;background:#112b3d}.solix-entities .muted{color:#aac3d0}`;this.shadowRoot.append(css);
const bar=document.createElement('div');bar.id='solix-tools';bar.className='solix-tools';bar.innerHTML='<button type="button" id="solix-menu" aria-label="Home Assistant Menü öffnen">☰ Menü</button><a href="/lovelace" style="color:#fff;padding:9px">Übersicht</a><a href="/config" style="color:#fff;padding:9px">Einstellungen</a><button type="button" id="solix-entities-toggle">Alle Entitäten anzeigen</button><span id="solix-count"></span>';this.shadowRoot.querySelector('.wrap').prepend(bar);
bar.querySelector('#solix-menu').addEventListener('click',()=>{const root=document.querySelector('home-assistant');if(root){root.dispatchEvent(new Event('hass-toggle-menu',{bubbles:true,composed:true}));}else{this.dispatchEvent(new Event('hass-toggle-menu',{bubbles:true,composed:true}));}});
const section=document.createElement('section');section.id='solix-entity-section';section.className='details';section.hidden=true;section.innerHTML='<h2>Home Assistant · Entitätenübersicht</h2><p>Alle aktuell geladenen Home-Assistant-Entitäten. Suche nach SOLIX, Anker, Gerätenamen oder Entity-ID.</p><div class="solix-tools"><input id="solix-search" aria-label="Entitäten suchen" placeholder="Entitäten suchen …"><label><input type="checkbox" id="solix-only" checked> Nur Anker / SOLIX</label></div><p id="solix-result-count"></p><div class="solix-entities"><table><thead><tr><th>Entität</th><th>Zustand</th><th>Einheit</th></tr></thead><tbody id="solix-rows"></tbody></table></div>';this.shadowRoot.querySelector('.wrap').append(section);
bar.querySelector('#solix-entities-toggle').addEventListener('click',()=>{section.hidden=!section.hidden;bar.querySelector('#solix-entities-toggle').textContent=section.hidden?'Alle Entitäten anzeigen':'Entitäten ausblenden';if(!section.hidden)this.renderEntityCatalog();});
section.querySelector('#solix-search').addEventListener('input',()=>this.renderEntityCatalog());section.querySelector('#solix-only').addEventListener('change',()=>this.renderEntityCatalog());this.refresh();};
Panel.prototype._solixEntity=function(id){const states=this._hass?.states||{};if(states[id])return states[id];const suffix=id.replace(/^sensor\.solix_live_/, '').replace(/_/g,' ');const candidates=Object.values(states).filter(s=>s.entity_id?.startsWith('sensor.')&&s.entity_id.includes('solix_live')&&(s.entity_id.endsWith('_'+suffix.replace(/ /g,'_'))||String(s.attributes?.friendly_name||'').toLowerCase().endsWith(suffix)));return candidates.length===1?candidates[0]:null;};
Panel.prototype._num=function(id){const state=this._solixEntity(id);if(!state||['unknown','unavailable','none',''].includes(String(state.state).toLowerCase()))return null;const n=Number(state.state);return Number.isFinite(n)?n:null;};
Panel.prototype.refresh=function(){if(!this._ready||!this._hass)return;originalRefresh.call(this);const pre='sensor.solix_live_';const state=this._solixEntity(pre+'betriebszustand')?.state||'Unbekannt';const card=this.$('batteryCard');const t=card?.querySelectorAll('text');if(t?.length)t[0].textContent='⚡ '+this._translateStatus(state);this._updateVisualLabels();const details=this._solixEntity(pre+'systemdetails');if(details?.attributes){this._solixDetails=details.attributes;this.renderDetails();}if(this.shadowRoot.getElementById('solix-entity-section')?.hidden===false)this.renderEntityCatalog();};
Panel.prototype.renderDetails=function(){const attrs=this._solixEntity('sensor.solix_live_systemdetails')?.attributes||{};const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const fmt=(v,u)=>v==null||!Number.isFinite(Number(v))?'Nicht verfügbar':Number(v).toLocaleString('de-DE',{maximumFractionDigits:1})+' '+u;const devices=this.$('deviceDetails');if(devices)devices.innerHTML=(attrs.devices||[]).map(d=>`<div class="detail-tile"><strong>${esc(d.name)}</strong><p>🌡 Temperatur: ${fmt(d.temp,'°C')}</p><p>🔋 Ladestand: ${fmt(d.soc,'%')}</p><p>⚡ Lade-/Entladeleistung: ${fmt(d.power,'W')}</p></div>`).join('')||'<p>Gerätewerte bitte in den Integrationsoptionen zuordnen.</p>';const mppts=this.$('mpptDetails');if(mppts)mppts.innerHTML=(attrs.mppts||[]).map(d=>`<div class="detail-tile"><strong>System ${esc(d.system)} · MPPT ${esc(d.index)}</strong><p>${fmt(d.power,'W')}</p></div>`).join('');const plugs=this.$('plugDetails');if(plugs)plugs.innerHTML=(attrs.plugs||[]).map(d=>`<div class="detail-tile"><strong>${esc(d.name)}</strong><p>${fmt(d.power,'W')}</p></div>`).join('');};
Panel.prototype.renderEntityCatalog=function(){const root=this.shadowRoot;if(!root||!this._hass)return;const search=(root.getElementById('solix-search')?.value||'').toLocaleLowerCase();const only=root.getElementById('solix-only')?.checked;const states=Object.values(this._hass.states||{});const relevant=s=>/anker|solix|solarbank|e1600|system_sb_/i.test([s.entity_id,s.attributes?.friendly_name,s.attributes?.device_class].join(' '));const found=states.filter(s=>(!only||relevant(s))&&(!search||[s.entity_id,s.attributes?.friendly_name,s.state,s.attributes?.unit_of_measurement].join(' ').toLocaleLowerCase().includes(search))).sort((a,b)=>a.entity_id.localeCompare(b.entity_id));root.getElementById('solix-result-count').textContent=`${found.length} von ${states.length} verfügbaren Entitäten · keine Duplikate angelegt`;const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));root.getElementById('solix-rows').innerHTML=found.map(s=>`<tr><td><strong>${esc(s.attributes?.friendly_name||s.entity_id)}</strong><div class="muted">${esc(s.entity_id)}</div></td><td>${esc(s.state)}</td><td>${esc(s.attributes?.unit_of_measurement||'')}</td></tr>`).join('')||'<tr><td colspan="3">Keine passenden Entitäten gefunden.</td></tr>';root.getElementById('solix-count').textContent=`${states.length} HA-Entitäten`;};