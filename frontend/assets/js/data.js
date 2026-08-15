/* SERGAK AI — Shared mock data (frontend) */

const DEPARTMENTS = [
  {id:1, key:'eritish', name:"Eritish bo'limi", color:'#ef4444', icon:'flame'},
  {id:2, key:'pechka', name:'Pechkaxona', color:'#f97316', icon:'thermometer'},
  {id:3, key:'ombor', name:'Ombor', color:'#3b82f6', icon:'package'},
  {id:4, key:'quyish', name:"Quyish bo'limi", color:'#ec4899', icon:'droplet'},
  {id:5, key:'mexanik', name:'Mexanik ustaxona', color:'#8b5cf6', icon:'wrench'},
  {id:6, key:'ofis', name:'Ofis', color:'#10b981', icon:'briefcase'}
];

// Real factory/industrial photos from Unsplash
const CAM_IMAGES = [
  'https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=800&q=80',
  'https://images.unsplash.com/photo-1581094794329-c8112a89af12?w=800&q=80',
  'https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?w=800&q=80',
  'https://images.unsplash.com/photo-1565793298595-6a879b1d9492?w=800&q=80',
  'https://images.unsplash.com/photo-1581092335397-7c83e9ac82e8?w=800&q=80',
  'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800&q=80',
  'https://images.unsplash.com/photo-1486591038213-cef02f604897?w=800&q=80',
  'https://images.unsplash.com/photo-1581092334651-ddf26d9a09d0?w=800&q=80',
  'https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=800&q=80',
  'https://images.unsplash.com/photo-1553413077-190dd305871c?w=800&q=80',
  'https://images.unsplash.com/photo-1565793298595-6a879b1d9492?w=800&q=80',
  'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80',
  'https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=800&q=80',
  'https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&q=80'
];

const CAMERAS = [
  {id:1, name:'Eritish-1 Kirish', dept:'eritish', loc:"G'arbiy eshik", online:true, modules:['helmet','fire','zone'], alerts:0, img:CAM_IMAGES[0]},
  {id:2, name:'Eritish-2 Asosiy pech', dept:'eritish', loc:'Shimoliy burchak', online:true, modules:['helmet','fire','zone','fall'], alerts:2, hasAlert:true, img:CAM_IMAGES[6]},
  {id:3, name:'Eritish-3 Quyish zonasi', dept:'eritish', loc:'Janub-sharq', online:true, modules:['helmet','fire','fall'], alerts:0, img:CAM_IMAGES[2]},
  {id:4, name:'Pechka-1', dept:'pechka', loc:'Asosiy zal', online:true, modules:['helmet','smoking','fire'], alerts:0, img:CAM_IMAGES[3]},
  {id:5, name:'Pechka-2', dept:'pechka', loc:'Shimoliy', online:true, modules:['helmet','smoking','fire','fall'], alerts:1, hasAlert:true, img:CAM_IMAGES[1]},
  {id:6, name:'Pechka-3', dept:'pechka', loc:'Markaziy', online:true, modules:['helmet','fire'], alerts:0, img:CAM_IMAGES[4]},
  {id:7, name:'Pechka-4 Chiqish', dept:'pechka', loc:'Sharqiy chiqish', online:true, modules:['helmet','fire','zone'], alerts:0, img:CAM_IMAGES[5]},
  {id:8, name:'Ombor-1', dept:'ombor', loc:'Asosiy ombor', online:true, modules:['fall','phone','zone'], alerts:0, img:CAM_IMAGES[8]},
  {id:9, name:'Ombor-2 Yuk maydoni', dept:'ombor', loc:'Yuk eshigi', online:true, modules:['fall','phone'], alerts:0, img:CAM_IMAGES[9]},
  {id:10,name:'Quyish-1', dept:'quyish', loc:'Asosiy', online:true, modules:['helmet','fire','fall'], alerts:0, img:CAM_IMAGES[10]},
  {id:11,name:'Quyish-2', dept:'quyish', loc:'Quyish kanali', online:false, modules:['helmet','fire','zone'], alerts:0, img:CAM_IMAGES[7]},
  {id:12,name:'Mexanik-1', dept:'mexanik', loc:'Ustaxona', online:true, modules:['helmet','phone'], alerts:0, img:CAM_IMAGES[11]},
  {id:13,name:'Mexanik-2', dept:'mexanik', loc:'Stanok zonasi', online:true, modules:['helmet','phone','zone'], alerts:0, img:CAM_IMAGES[12]},
  {id:14,name:'Ofis-Koridor', dept:'ofis', loc:'Asosiy koridor', online:true, modules:['fire'], alerts:0, img:CAM_IMAGES[13]}
];

const MODULE_DEFS = {
  helmet:{name:'Kaska', icon:'hard-hat', color:'#3b82f6'},
  phone:{name:'Telefon', icon:'smartphone', color:'#8b5cf6'},
  smoking:{name:'Chekish', icon:'cigarette-off', color:'#ec4899'},
  fall:{name:'Yiqilish', icon:'user-x', color:'#f59e0b'},
  fire:{name:"Yong'in", icon:'flame', color:'#ef4444'},
  zone:{name:'Zona', icon:'shield-x', color:'#06b6d4'},
  twoperson:{name:'2-kishi', icon:'users-2', color:'#10b981'}
};

const RECENT_ALERTS = [
  {id:1, dept:'eritish', cam:'Eritish-2 Asosiy pech', module:'fire', msg:"Yong'in belgilari aniqlandi", time:'14:32:15', critical:true},
  {id:2, dept:'pechka', cam:'Pechka-2', module:'smoking', msg:'Chekish aniqlandi', time:'14:18:42', critical:true},
  {id:3, dept:'eritish', cam:'Eritish-2 Asosiy pech', module:'helmet', msg:'Kaska kiyilmagan', time:'13:54:11', critical:false},
  {id:4, dept:'pechka', cam:'Pechka-2', module:'helmet', msg:'Kaska kiyilmagan', time:'13:42:08', critical:false},
  {id:5, dept:'ombor', cam:'Ombor-1', module:'phone', msg:'Telefon ishlatish', time:'13:31:55', critical:false},
  {id:6, dept:'eritish', cam:'Eritish-3 Quyish zonasi', module:'zone', msg:'Cheklangan zonaga kirish', time:'13:15:23', critical:true},
  {id:7, dept:'mexanik', cam:'Mexanik-2', module:'helmet', msg:'Kaska kiyilmagan', time:'12:58:40', critical:false},
  {id:8, dept:'pechka', cam:'Pechka-1', module:'helmet', msg:'Kaska kiyilmagan', time:'12:45:12', critical:false}
];

const USERS = [
  {name:'Mardonbek Sulaymonqulov', email:'mardonbeksulaymonqulov156@gmail.com', role:'admin', dept:"Hamma bo'limlar", status:'online', lastSeen:'Hozir onlayn', seed:'Mardonbek', color:'3b82f6'},
  {name:'Akmal Karimov', email:'a.karimov@bekobod-zavod.uz', role:'admin', dept:"Hamma bo'limlar", status:'online', lastSeen:'5 daqiqa oldin', seed:'Akmal', color:'ef4444'},
  {name:'Dilshod Rahimov', email:'d.rahimov@bekobod-zavod.uz', role:'manager', dept:"Eritish bo'limi", status:'online', lastSeen:'12 daqiqa oldin', seed:'Dilshod', color:'8b5cf6'},
  {name:'Sherzod Yusupov', email:'s.yusupov@bekobod-zavod.uz', role:'manager', dept:'Pechkaxona', status:'online', lastSeen:'28 daqiqa oldin', seed:'Sherzod', color:'10b981'},
  {name:"Bobur Olimov", email:'b.olimov@bekobod-zavod.uz', role:'manager', dept:'Ombor', status:'offline', lastSeen:'2 soat oldin', seed:'Bobur', color:'f97316'},
  {name:'Jasur Toshpulatov', email:'j.toshpulatov@bekobod-zavod.uz', role:'operator', dept:'Eritish (smena 1)', status:'online', lastSeen:'Hozir onlayn', seed:'Jasur', color:'06b6d4'},
  {name:'Nodira Karimova', email:'n.karimova@bekobod-zavod.uz', role:'operator', dept:'TB xona', status:'online', lastSeen:'2 daqiqa oldin', seed:'Nodira', color:'ec4899'},
  {name:"Ulug'bek Murodov", email:'u.murodov@bekobod-zavod.uz', role:'operator', dept:'Pechkaxona (smena 2)', status:'offline', lastSeen:'8 soat oldin', seed:'Ulugbek', color:'22c55e'},
  {name:'Zafar Abdullayev', email:'audit@bekobod-zavod.uz', role:'auditor', dept:'Read-only · hammasi', status:'online', lastSeen:'1 soat oldin', seed:'Zafar', color:'8b5cf6'}
];

window.SergakData = { DEPARTMENTS, CAMERAS, MODULE_DEFS, RECENT_ALERTS, USERS, CAM_IMAGES };
