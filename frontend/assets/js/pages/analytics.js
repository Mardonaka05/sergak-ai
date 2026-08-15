/* Analytics page logic */

function initAnalytics(){
  renderHeatmap();
  initAnalyticsCharts();
  if(window.lucide) lucide.createIcons();
}

function renderHeatmap(){
  const days = ['Du','Se','Ch','Pa','Ju','Sh','Ya'];
  const grid = document.getElementById('heatmapGrid');
  const hours = document.getElementById('heatmapHours');
  if(!grid) return;
  hours.innerHTML = '<span></span>'+Array.from({length:24},(_,i)=>`<span>${i}</span>`).join('');
  let html = '';
  days.forEach(d=>{
    html += `<div class="heatmap-label">${d}</div>`;
    for(let h=0;h<24;h++){
      let v = Math.random()*0.3;
      if(h>=8&&h<=18) v += Math.random()*0.5;
      if(h>=14&&h<=15&&d==='Se') v += 0.5;
      if(h>=10&&h<=11) v += 0.2;
      if(d==='Ya'||d==='Sh') v *= 0.4;
      let bg = '#1a2238';
      if(v>0.7) bg = 'rgba(239,68,68,.85)';
      else if(v>0.5) bg = 'rgba(239,68,68,.5)';
      else if(v>0.3) bg = 'rgba(59,130,246,.5)';
      else if(v>0.1) bg = 'rgba(59,130,246,.25)';
      const count = Math.floor(v*8);
      html += `<div class="heatmap-cell" style="background:${bg}" title="${d} ${h}:00 — ${count} ta hodisa"></div>`;
    }
  });
  grid.innerHTML = html;
}

function initAnalyticsCharts(){
  Chart.defaults.color = '#8d9bb8';
  Chart.defaults.borderColor = '#252e48';

  // Accuracy
  new Chart(document.getElementById('chartAccuracy'),{
    type:'line',
    data:{
      labels:Array.from({length:14},(_,i)=>`${i+1}`),
      datasets:[
        {label:'Kaska',data:[94.2,94.8,95.1,95.5,95.3,95.8,96.0,96.2,96.4,96.5,96.7,96.6,96.8,96.8],borderColor:'#3b82f6',tension:.4,borderWidth:2,pointRadius:0},
        {label:"Yong'in",data:[97.1,97.3,97.5,97.4,97.6,97.8,97.9,98.0,98.1,98.2,98.2,98.1,98.2,98.2],borderColor:'#ef4444',tension:.4,borderWidth:2,pointRadius:0},
        {label:'Telefon',data:[91.0,91.5,92.0,92.2,92.5,92.8,93.0,93.1,93.0,93.2,93.2,93.3,93.2,93.2],borderColor:'#8b5cf6',tension:.4,borderWidth:2,pointRadius:0},
        {label:'Yiqilish',data:[92.5,93.0,93.5,93.8,94.0,94.2,94.3,94.5,94.6,94.7,94.7,94.8,94.7,94.7],borderColor:'#f59e0b',tension:.4,borderWidth:2,pointRadius:0}
      ]
    },
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'bottom',labels:{boxWidth:10,padding:10,font:{size:10}}}},
      scales:{y:{min:88,max:100,grid:{color:'#252e48'},ticks:{callback:v=>v+'%'}},x:{grid:{display:false}}}}
  });

  // Radar
  new Chart(document.getElementById('chartRadar'),{
    type:'radar',
    data:{labels:['Kaska',"Yong'in",'Telefon','Yiqilish','Zona'],
      datasets:[
        {label:'Eritish',data:[18,8,2,5,9],borderColor:'#ef4444',backgroundColor:'rgba(239,68,68,.15)',borderWidth:2,pointBackgroundColor:'#ef4444'},
        {label:'Pechkaxona',data:[12,3,5,2,6],borderColor:'#f97316',backgroundColor:'rgba(249,115,22,.15)',borderWidth:2,pointBackgroundColor:'#f97316'},
        {label:'Ombor',data:[4,1,8,1,2],borderColor:'#3b82f6',backgroundColor:'rgba(59,130,246,.15)',borderWidth:2,pointBackgroundColor:'#3b82f6'}
      ]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{position:'bottom',labels:{boxWidth:10,padding:10,font:{size:10}}}},
      scales:{r:{grid:{color:'#252e48'},angleLines:{color:'#252e48'},pointLabels:{font:{size:10},color:'#8d9bb8'},ticks:{display:false}}}}
  });

  // Hourly
  const data = Array.from({length:24},(_,i)=>{
    let v = 1;
    if(i>=8&&i<=18) v = 4+Math.random()*4;
    if(i>=13&&i<=15) v = 8+Math.random()*4;
    if(i>=22||i<=5) v = Math.random()*1.5;
    return Math.round(v);
  });
  new Chart(document.getElementById('chartHourly'),{
    type:'bar',
    data:{labels:Array.from({length:24},(_,i)=>i+':00'),
      datasets:[{data,backgroundColor:data.map(v=>v>8?'#ef4444':v>4?'#3b82f6':'#252e48'),borderRadius:4}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},
      scales:{y:{grid:{color:'#252e48'}},x:{grid:{display:false},ticks:{font:{size:9},maxRotation:0,autoSkip:true,maxTicksLimit:12}}}}
  });
}
