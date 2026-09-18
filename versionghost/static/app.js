const $ = (id) => document.getElementById(id);
const stages = ['queued','analyzing','contracting','patching','verifying','repairing','complete'];
const stageLabels = {queued:'Queue',analyzing:'Impact',contracting:'Contract',patching:'Patch',verifying:'Verify',repairing:'Repair',complete:'Packet'};
let currentRun = null;
let timer = null;

function esc(s){return String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
async function getJSON(url, options){const r=await fetch(url,options);if(!r.ok) throw new Error(`${r.status} ${await r.text()}`);return r.json();}
async function loadDemo(){const data=await getJSON('/api/demo/request');$('requestText').value=data.request_text;}
function renderStages(stage){const index=stages.indexOf(stage), finished=stage==='complete';$('stageTrack').innerHTML=stages.map((s,i)=>`<div class="stage ${finished||i<index?'done':''} ${!finished&&i===index?'active':''}"><b>${stageLabels[s]}</b>${finished||i<index?'complete':i===index?'running':'pending'}</div>`).join('');}
async function run(){
  $('runBtn').disabled=true;$('runBtn').textContent='Starting…';
  try{
    const body={request_text:$('requestText').value,provider:$('provider').value,scenario:'streak-bonus-compatibility'};
    const data=await getJSON('/api/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    currentRun=data.id;$('runArea').classList.remove('hidden');$('runId').textContent=currentRun;renderStages('queued');
    clearInterval(timer);await poll();timer=setInterval(poll,700);
  }catch(e){alert(e.message);$('runBtn').disabled=false;$('runBtn').innerHTML='Run compatibility pipeline <span>→</span>';}
}
async function poll(){if(!currentRun)return;try{const r=await getJSON(`/api/runs/${currentRun}`);render(r);if(['complete','failed'].includes(r.stage)){clearInterval(timer);$('runBtn').disabled=false;$('runBtn').innerHTML='Run compatibility pipeline <span>→</span>';}}catch(e){console.error(e)}}
function render(r){
  renderStages(r.stage);$('runStatus').textContent=r.status_message;
  const v=$('verdict');if(r.packet){v.textContent=r.packet.verdict.replaceAll('_',' ');v.className=`verdict ${r.packet.verdict==='ready_with_evidence'?'good':'bad'}`;}else{v.textContent=r.stage;v.className='verdict neutral';}
  $('events').innerHTML=(r.events||[]).slice().reverse().map(e=>`<div class="event"><time>${new Date(e.at).toLocaleTimeString()}</time><div><b>${esc(e.stage)}</b> · ${esc(e.message)}</div></div>`).join('');
  if(!r.packet)return;
  const p=r.packet, final=p.attempts[p.attempts.length-1];
  $('replayCount').textContent=`${final.replay.filter(x=>x.status==='pass').length}/${final.replay.length} pass`;
  $('matrix').className='matrix';$('matrix').innerHTML=final.replay.map(c=>`<div class="matrix-row"><strong>${esc(c.client_version)}</strong><span>${esc(c.case_id)}</span><i class="pill ${c.status}">${c.status}</i></div>`).join('');
  $('attempts').innerHTML=p.attempts.map(a=>{const fails=a.replay.filter(x=>x.status==='fail').length;return `<div class="attempt"><h4>Attempt ${a.attempt} · ${a.passed?'accepted':'rejected'}</h4><p>${esc(a.patch_summary)}</p><p>${a.changed_files.map(esc).join(' · ')}</p><p>${fails?`${fails} compatibility probe(s) failed`:'all verification surfaces passed'}</p></div>`}).join('');
  const ev={};p.requirement_evidence.forEach(x=>ev[x.requirement_id]=x);
  $('requirements').innerHTML=p.contract.requirements.map(q=>{const e=ev[q.id]||{status:'unproven',evidence:[]};return `<div class="req"><code>${esc(q.id)}</code><div><p>${esc(q.text)}</p><small>${esc((e.evidence||[]).join(' · '))}</small></div><span class="state ${e.status}">${e.status}</span></div>`}).join('');
  $('impact').innerHTML=`<div class="statline"><div><b>${p.impact.nodes.length}</b><span>nodes</span></div><div><b>${p.impact.edges.length}</b><span>resolved edges</span></div><div><b>${p.impact.uncertainty.length}</b><span>uncertainties</span></div></div><ul>${p.impact.touched_candidates.slice(0,6).map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`;
  $('packetMeta').innerHTML=`<div class="statline"><div><b>${p.metrics.pipeline_ms}</b><span>pipeline ms</span></div><div><b>${p.metrics.attempt_count}</b><span>attempts</span></div><div><b>${p.metrics.final_replay_passes}</b><span>replay passes</span></div></div><ul><li>route: ${esc(p.model_route)}</li><li>changed: ${p.changed_files.map(esc).join(', ')}</li><li>${esc(p.limitations[0])}</li></ul>`;
}
$('runBtn').addEventListener('click',run);$('loadDemo').addEventListener('click',loadDemo);loadDemo();getJSON('/api/health').then(()=>{$('serviceStatus').textContent='service ready'}).catch(()=>{$('serviceStatus').textContent='service unavailable'});
