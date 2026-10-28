const labels = [];
const genData = [];
const conData = [];
for (let i = 0; i < 18; i++) {
  labels.push(new Date(Date.now() - (17-i)*60000).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}));
  genData.push(Number((5.2 + Math.sin(i*1.1)*0.35 + (Math.random()-.5)*.18).toFixed(2)));
  conData.push(Number((3.55 + Math.sin(i*1.4)*0.35 + (Math.random()-.5)*.22).toFixed(2)));
}
const ctx = document.getElementById('energyChart');
const chart = new Chart(ctx, {
  type:'line',
  data:{labels,datasets:[
    {label:'Generation (kWh)',data:genData,borderColor:'#22c55e',backgroundColor:'#22c55e',borderWidth:3,pointRadius:3,tension:.28},
    {label:'Consumption (kWh)',data:conData,borderColor:'#ef4444',backgroundColor:'#ef4444',borderWidth:3,pointRadius:3,tension:.25}
  ]},
  options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
    plugins:{legend:{labels:{color:'#a3adbc',usePointStyle:true}},title:{display:true,text:'Live Energy Metrics',color:'#a3adbc',padding:{bottom:18}}},
    scales:{x:{ticks:{color:'#8994a4',maxRotation:50,minRotation:35},grid:{color:'#ffffff08'}},
      y:{min:2.5,max:6.5,ticks:{color:'#8994a4'},grid:{color:'#ffffff0c'}}}}
});

async function api(url, options={}) {
  const response = await fetch(url,{headers:{'Content-Type':'application/json'},...options});
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Request failed');
  return data;
}
function notice(message, bad=false) {
  const el=document.getElementById('notice'); el.textContent=message;
  el.style.color=bad?'#fca5a5':'#86efac';
}
async function refreshMetrics(){
  try {
    const m=await api('/api/metrics');
    document.getElementById('generation').textContent=Number(m.generation).toFixed(1);
    document.getElementById('consumption').textContent=Number(m.consumption).toFixed(1);
    document.getElementById('balance').textContent=m.balance;
    document.getElementById('modeLabel').textContent=`${m.mode==='blockchain'?'Blockchain mode':'Demo telemetry · simulated data'} · surplus ${m.surplus} kWh`;
    genData.push(m.generation); conData.push(m.consumption);
    labels.push(new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'}));
    if(genData.length>18){genData.shift();conData.shift();labels.shift();}
    chart.update('none');
  } catch(e){console.error(e);}
}
async function refreshOrders(){
  try {
    const result=await api('/api/orders');
    const list=document.getElementById('ordersList');
    list.innerHTML='';
    if(!result.orders.length){list.textContent='No active orders.';return;}
    result.orders.forEach(o=>{
      const el=document.createElement('div');el.className='order';
      el.textContent=`Order #${o.id} · ${o.energy_kwh} kWh · ${o.price_per_kwh} AGNI/kWh · ${o.source}`;
      list.appendChild(el);
    });
  }catch(e){document.getElementById('ordersList').textContent=e.message;}
}
document.getElementById('sellButton').addEventListener('click',async()=>{
  const button=document.getElementById('sellButton');button.disabled=true;
  try{
    const m=await api('/api/metrics');
    const data=await api('/api/orders/sell',{method:'POST',body:JSON.stringify({energy_kwh:Math.max(.1,m.surplus),price_per_kwh:12.5})});
    notice(data.message+(data.tx_hash?` · Tx: ${data.tx_hash}`:''));
    await refreshOrders();
  }catch(e){notice(e.message,true)}finally{button.disabled=false;}
});
document.getElementById('buyButton').addEventListener('click',async()=>{
  const button=document.getElementById('buyButton');button.disabled=true;
  try{
    const data=await api('/api/orders/1/buy',{method:'POST',body:'{}'});
    notice(data.message+(data.tx_hash?` · Tx: ${data.tx_hash}`:''));
    await refreshOrders();
  }catch(e){notice(e.message,true)}finally{button.disabled=false;}
});
refreshMetrics();refreshOrders();setInterval(refreshMetrics,3000);setInterval(refreshOrders,15000);
