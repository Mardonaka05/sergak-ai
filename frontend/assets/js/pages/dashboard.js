/* Dashboard page logic */

function initDashboard(){
  // Live cameras (4)
  const live = SergakData.CAMERAS.filter(c=>c.online).slice(0,4);
  document.getElementById('liveCameras').innerHTML = live.map(renderLiveCameraTile).join('');

  // Alerts list
  document.getElementById('alertsList').innerHTML = SergakData.RECENT_ALERTS.map(renderAlertItem).join('');

  if(window.lucide) lucide.createIcons();
  initDashboardCharts();

  // Welcome toast + simulated alerts
  setTimeout(()=>SergakApp.showToast('success','Xush kelibsiz!','Sergak AI tizimi muvaffaqiyatli ishga tushdi'), 500);
  setInterval(()=>{
    if(Math.random()>0.7){
      const a = SergakData.RECENT_ALERTS[Math.floor(Math.random()*SergakData.RECENT_ALERTS.length)];
      SergakApp.showToast('error','Yangi qoidabuzarlik!', a.msg+' — '+a.cam);
    }
  }, 25000);
}

function initDashboardCharts(){
  Chart.defaults.color = '#8d9bb8';
  Chart.defaults.borderColor = '#252e48';
  Chart.defaults.font.family = 'Inter';

  new Chart(document.getElementById('chartTimeline'), {
    type:'line',
    data:{
      labels:['Du','Se','Ch','Pa','Ju','Sh','Ya'],
      datasets:[
        {label:'Kaska', data:[12,15,11,18,14,9,8], borderColor:'#3b82f6', backgroundColor:'rgba(59,130,246,.1)', tension:.4, fill:true, borderWidth:2, pointRadius:3, pointBackgroundColor:'#3b82f6'},
        {label:"Yong'in", data:[2,1,3,2,4,1,2], borderColor:'#ef4444', backgroundColor:'rgba(239,68,68,.1)', tension:.4, fill:true, borderWidth:2, pointRadius:3, pointBackgroundColor:'#ef4444'},
        {label:'Telefon', data:[8,7,9,11,6,5,4], borderColor:'#8b5cf6', backgroundColor:'rgba(139,92,246,.05)', tension:.4, fill:true, borderWidth:2, pointRadius:3, pointBackgroundColor:'#8b5cf6'}
      ]
    },
    options:{responsive:true, maintainAspectRatio:false,
      plugins:{legend:{position:'bottom', labels:{boxWidth:12, padding:14, font:{size:11}}}},
      scales:{y:{beginAtZero:true, grid:{color:'#252e48'}}, x:{grid:{display:false}}}
    }
  });

  new Chart(document.getElementById('chartDept'), {
    type:'doughnut',
    data:{labels:['Eritish','Pechkaxona','Ombor','Quyish','Mexanik','Ofis'],
      datasets:[{data:[42,28,15,8,5,2], backgroundColor:['#ef4444','#f97316','#3b82f6','#ec4899','#8b5cf6','#10b981'], borderColor:'#131a2c', borderWidth:3}]
    },
    options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{position:'bottom', labels:{boxWidth:10, padding:8, font:{size:10}}}}, cutout:'68%'}
  });

  new Chart(document.getElementById('chartModule'), {
    type:'bar',
    data:{labels:['Kaska',"Yong'in",'Telefon','Yiqil.','Zona','Chekish','2-kishi'],
      datasets:[{data:[68,12,38,8,15,11,4], backgroundColor:['#3b82f6','#ef4444','#8b5cf6','#f59e0b','#06b6d4','#ec4899','#10b981'], borderRadius:6, borderSkipped:false}]
    },
    options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}},
      scales:{y:{beginAtZero:true, grid:{color:'#252e48'}}, x:{grid:{display:false}, ticks:{font:{size:10}}}}
    }
  });
}
