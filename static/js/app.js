async function refreshDashboard(){
  const [leadsRes, statsRes] = await Promise.all([fetch('/api/leads'), fetch('/api/stats')]);
  const leadsData = await leadsRes.json();
  const statsData = await statsRes.json();
  const stats = statsData.stats;
  document.getElementById('total').textContent = stats.total;
  document.getElementById('hot').textContent = stats.temperature.Hot || 0;
  document.getElementById('warm').textContent = stats.temperature.Warm || 0;
  document.getElementById('cold').textContent = stats.temperature.Cold || 0;
  const tbody = document.getElementById('leadRows');
  tbody.innerHTML = '';
  if(!leadsData.leads.length){tbody.innerHTML='<tr><td colspan="6">No leads yet. Submit a lead through the API or Google Form.</td></tr>';return;}
  for(const lead of leadsData.leads){
    const tr=document.createElement('tr');
    const safe=(v)=>String(v||'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    tr.innerHTML=`<td><strong>${safe(lead.name)}</strong><br><span class="muted">${safe(lead.email)}</span></td>
      <td>${safe(lead.company)}</td><td>${safe(lead.requirements || lead.message)}</td>
      <td><span class="pill ${safe(lead.temperature)}">${safe(lead.temperature || 'Pending')}</span></td>
      <td>${safe(lead.status)}</td>
      <td><button class="button secondary" data-id="${lead.id}">Analyze</button></td>`;
    tr.querySelector('button').addEventListener('click',()=>analyzeLead(lead.id));
    tbody.appendChild(tr);
  }
}
async function analyzeLead(id){
  const button=event?.target;
  if(button){button.disabled=true;button.textContent='Working…';}
  try{
    const response=await fetch(`/api/leads/${id}/analyze`,{method:'POST'});
    const data=await response.json();
    if(!response.ok) alert(data.message || 'Analysis failed');
  }catch(e){alert('Could not reach the API');}
  await refreshDashboard();
}
document.getElementById('refresh').addEventListener('click',refreshDashboard);
refreshDashboard();
