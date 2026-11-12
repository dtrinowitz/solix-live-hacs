import '/solix_live/solix-live-panel.js';
const Panel=customElements.get('solix-live-panel');
if (!Panel) throw new Error('SOLIX panel not registered');
const originalConnected=Panel.prototype.connectedCallback;
const originalRefresh=Panel.prototype.refresh;
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
Panel.prototype._solixEntity=function(id){
 const states=this._hass?.states||{};
 if(states[id])return states[id];
 const suffix=id.replace(/^sensor\.solix_live_/,'');
 const candidates=Object.values(states).filter(s=>s.entity_id?.startsWith('sensor.')&&s.entity_id.includes('solix_live')&&(s.entity_id.endsWith('_'+suffix)||String(s.attributes?.friendly_name||'').toLowerCase().endsWith(suffix.replace(/_/g,' '))));
 return candidates.length===1?candidates[0]:null;
};
Panel.prototype._num=function(id){
 const s=this._solixEntity(id);
 if(!s||['unknown','unavailable','none',''].includes(String(s.state).toLowerCase()))return null;
 const n=Number(s.state);return Number.isFinite(n)?n:null;
};
Panel.prototype.connectedCallback=function(){
 originalConnected.call(this);
 if(!this.shadowRoot||this.shadowRoot.getElementById('solix-tools'))return;
 const wrap=this.shadowRoot.querySelector('.wrap');if(!wrap)return;
 const css=document.createElement('style');
 css.textContent='.solix-tools{display:flex;flex-wrap:wrap;align-items:center;gap:9px;padding:12px;background:#112b3d;border-radius:12px;margin-bottom:12px}.solix-tools button,.solix-tools input{padding:9px;border:1px solid #60889b;border-radius:8px;background:#16374b;color:#fff}.solix-tools input[type=checkbox]{min-width:0}.solix-search{min-width:170px;flex:1}.solix-entities{max-height:60vh;overflow:auto}.solix-entities table{width:100%;border-collapse:collapse;font-size:13px}.solix-entities td,.solix-entities th{padding:7px;border-bottom:1px solid #31506a;text-align:left;overflow-wrap:anywhere}.solix-entities th{position:sticky;top:0;background:#112b3d}.solix-entities .muted{color:#aac3d0}';
 this.shadowRoot.append(css);
 const bar=document.createElement('div');bar.id='solix-tools';bar.className='solix-tools';
 bar.innerHTML='<button type="button" id="solix-menu">☰ Home Assistant</button><button type="button" id="solix-entities-toggle">Alle Entitäten anzeigen</button><span id="solix-count"></span>';
 wrap.prepend(bar);
 bar.querySelector('#solix-menu').addEventListener('click',()=>this.dispatchEvent(new Event('hass-toggle-menu',{bubbles:true,composed:true})));
 const section=document.createElement('section');section.id='solix-entity-section';section.className='details';section.hidden=true;
 section.innerHTML='<h2>Home Assistant · Entitätenübersicht</h2><p>Alle aktuell geladenen Home-Assistant-Entitäten. Suche nach SOLIX, Anker, Gerätenamen oder Entity-ID.</p><div class="solix-tools"><input class="solix-search" id="solix-search" aria-label="Entitäten suchen" placeholder="Entitäten suchen …"><label><input type="checkbox" id="solix-only" checked> Nur Anker / SOLIX</label></div><p id="solix-result-count"></p><div class="solix-entities"><table><thead><tr><th>Entität</th><th>Zustand</th><th>Einheit</th></tr></thead><tbody id="solix-rows"></tbody></table></div>';
 wrap.append(section);
 bar.querySelector('#solix-entities-toggle').addEventListener('click',()=>{section.hidden=!section.hidden;bar.querySelector('#solix-entities-toggle').textContent=section.hidden?'Alle Entitäten anzeigen':'Entitäten ausblenden';if(!section.hidden)this.renderEntityCatalog();});
 section.querySelector('#solix-search').addEventListener('input',()=>this.renderEntityCatalog());
 section.querySelector('#solix-only').addEventListener('change',()=>this.renderEntityCatalog());
 this.renderEntityCatalog();
 this.refresh();
};
Panel.prototype.refresh=function(){
 if(!this._ready||!this._hass)return;
 originalRefresh.call(this);
 const state=this._solixEntity('sensor.solix_live_betriebszustand')?.state||'Unbekannt';
 const card=this.$('batteryCard');const t=card?.querySelectorAll('text');if(t?.length)t[0].textContent='⚡ '+state;
 const details=this._solixEntity('sensor.solix_live_systemdetails');
 if(details?.attributes){this._solixDetails=details.attributes;this.renderDetails();}
 if(this.shadowRoot?.getElementById('solix-entity-section')?.hidden===false)this.renderEntityCatalog();
};
Panel.prototype.renderDetails=function(){
 const attrs=this._solixEntity('sensor.solix_live_systemdetails')?.attributes||{};
 const fmt=(v,u)=>v==null||!Number.isFinite(Number(v))?'Nicht verfügbar':Number(v).toLocaleString('de-DE',{maximumFractionDigits:1})+' '+u;
 const devices=this.$('deviceDetails');
 if(devices)devices.innerHTML=(attrs.devices||[]).map(d=>'<div class="detail-tile"><strong>'+esc(d.name)+'</strong><p>🌡 Temperatur: '+fmt(d.temp,'°C')+'</p><p>🔋 Ladestand: '+fmt(d.soc,'%')+'</p><p>⚡ Lade-/Entladeleistung: '+fmt(d.power,'W')+'</p></div>').join('')||'<p>Gerätewerte bitte in den Integrationsoptionen zuordnen.</p>';
 const mppts=this.$('mpptDetails');
 if(mppts)mppts.innerHTML=(attrs.mppts||[]).map(d=>'<div class="detail-tile"><strong>System '+esc(d.system)+' · MPPT '+esc(d.index)+'</strong><p>'+fmt(d.power,'W')+'</p></div>').join('');
 const plugs=this.$('plugDetails');
 if(plugs)plugs.innerHTML=(attrs.plugs||[]).map(d=>'<div class="detail-tile"><strong>'+esc(d.name)+'</strong><p>'+fmt(d.power,'W')+'</p></div>').join('');
};
Panel.prototype.renderEntityCatalog=function(){
 const root=this.shadowRoot;if(!root||!this._hass)return;
 const search=(root.getElementById('solix-search')?.value||'').toLocaleLowerCase();
 const only=root.getElementById('solix-only')?.checked;
 const states=Object.values(this._hass.states||{});
 const relevant=s=>/anker|solix|solarbank|e1600|system_sb_/i.test([s.entity_id,s.attributes?.friendly_name,s.attributes?.device_class].join(' '));
 const found=states.filter(s=>(!only||relevant(s))&&(!search||[s.entity_id,s.attributes?.friendly_name,s.state,s.attributes?.unit_of_measurement].join(' ').toLocaleLowerCase().includes(search))).sort((a,b)=>a.entity_id.localeCompare(b.entity_id));
 root.getElementById('solix-result-count').textContent=found.length+' von '+states.length+' verfügbaren Entitäten · keine Duplikate angelegt';
 root.getElementById('solix-rows').innerHTML=found.map(s=>'<tr><td><strong>'+esc(s.attributes?.friendly_name||s.entity_id)+'</strong><div class="muted">'+esc(s.entity_id)+'</div></td><td>'+esc(s.state)+'</td><td>'+esc(s.attributes?.unit_of_measurement||'')+'</td></tr>').join('')||'<tr><td colspan="3">Keine passenden Entitäten gefunden.</td></tr>';
 root.getElementById('solix-count').textContent=states.length+' HA-Entitäten';
};