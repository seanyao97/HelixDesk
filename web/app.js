// ====== Data Layer ======
const DB = {
    _get(k) { try { return JSON.parse(localStorage.getItem("hx_"+k))||[]; } catch { return []; } },
    _set(k, d) { localStorage.setItem("hx_"+k, JSON.stringify(d)); },
    _uid() { return Date.now().toString(36)+Math.random().toString(36).slice(2,8); },
    _today() { return new Date().toISOString().slice(0,10); },
    listProjects() { return this._get("projects"); },
    createProject(n, d) { const p={id:this._uid(),name:n,description:d||"",created_at:this._today()}; const a=this.listProjects(); a.push(p); this._set("projects",a); return p; },
    deleteProject(id) { this._set("projects",this.listProjects().filter(p=>p.id!==id)); this._set("experiments",this.listExperiments().filter(e=>e.project_id!==id)); },
    listExperiments(pid) { let a=this._get("experiments"); if(pid) a=a.filter(e=>e.project_id===pid); return a.sort((a,b)=>(b.date||"").localeCompare(a.date||"")); },
    createExperiment(pid,t,p,d,l) { const e={id:this._uid(),project_id:pid,title:t,purpose:p||"",date:d||this._today(),location:l||"",status:"draft",steps:[],results:[],parameters:[],run_logs:[]}; const a=this.listExperiments(); a.push(e); this._set("experiments",a); return e; },
    getExperiment(id) { return this.listExperiments().find(e=>e.id===id)||null; },
    updateExperiment(id,f) { const a=this.listExperiments(); const i=a.findIndex(e=>e.id===id); if(i<0) return null; Object.assign(a[i],f); this._set("experiments",a); return a[i]; },
    deleteExperiment(id) { this._set("experiments",this.listExperiments().filter(e=>e.id!==id)); },
    addStep(eid,t,c) { const a=this.listExperiments(); const e=a.find(x=>x.id===eid); if(!e) return; if(!e.steps) e.steps=[]; const s={id:this._uid(),title:t,content:c||"",order_num:e.steps.length}; e.steps.push(s); this._set("experiments",a); return s; },
    deleteStep(eid,sid) { const a=this.listExperiments(); const e=a.find(x=>x.id===eid); if(!e) return; e.steps=(e.steps||[]).filter(s=>s.id!==sid); this._set("experiments",a); },
    addResult(eid,c,t) { const a=this.listExperiments(); const e=a.find(x=>x.id===eid); if(!e) return; if(!e.results) e.results=[]; e.results.push({id:this._uid(),content:c,type:t||"text"}); this._set("experiments",a); },
    deleteResult(eid,rid) { const a=this.listExperiments(); const e=a.find(x=>x.id===eid); if(!e) return; e.results=(e.results||[]).filter(r=>r.id!==rid); this._set("experiments",a); },
    listPlans(d) { let a=this._get("plans"); if(d) a=a.filter(p=>p.date===d); return a.sort((a,b)=>a.date.localeCompare(b.date)); },
    addPlan(d,t,eid) { const p={id:this._uid(),date:d,title:t,experiment_id:eid||null,done:false}; const a=this.listPlans(); a.push(p); this._set("plans",a); return p; },
    togglePlan(id) { const a=this.listPlans(); const p=a.find(x=>x.id===id); if(p){p.done=!p.done;this._set("plans",a);} },
    deletePlan(id) { this._set("plans",this.listPlans().filter(p=>p.id!==id)); },
    listMaterials() { return this._get("materials"); },
    createMaterial(n,t) { const m={id:this._uid(),name:n,type:t||""}; const a=this.listMaterials(); a.push(m); this._set("materials",a); return m; },
    addRunLog(eid,o,d,c,v) { const a=this.listExperiments(); const e=a.find(x=>x.id===eid); if(!e) return; if(!e.run_logs) e.run_logs=[]; e.run_logs.push({id:this._uid(),version:v||1,run_date:this._today(),observations:o,deviations:d,conclusion:c}); this._set("experiments",a); },
    deleteRunLog(eid,lid) { const a=this.listExperiments(); const e=a.find(x=>x.id===eid); if(!e) return; e.run_logs=(e.run_logs||[]).filter(l=>l.id!==lid); this._set("experiments",a); },
    addParam(eid,n,v,u) { const a=this.listExperiments(); const e=a.find(x=>x.id===eid); if(!e) return; if(!e.parameters) e.parameters=[]; e.parameters.push({id:this._uid(),name:n,value:v||"",unit:u||""}); this._set("experiments",a); },
    deleteParam(eid,pid) { const a=this.listExperiments(); const e=a.find(x=>x.id===eid); if(!e) return; e.parameters=(e.parameters||[]).filter(p=>p.id!==pid); this._set("experiments",a); },
    search(q) { q=q.toLowerCase(); return {experiments:this.listExperiments().filter(e=>(e.title||"").toLowerCase().includes(q)||(e.purpose||"").toLowerCase().includes(q)),materials:this.listMaterials().filter(m=>(m.name||"").toLowerCase().includes(q))}; }
};

// ====== UI Layer ======
let currentView = "plan";
let currentProject = null;
let currentExpId = null;
let calYear = new Date().getFullYear();
let calMonth = new Date().getMonth();
const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);
function esc(s) { const d=document.createElement("div"); d.textContent=s; return d.innerHTML; }

$$(".nav-tab").forEach(tab => tab.addEventListener("click", () => switchView(tab.dataset.view)));

function switchView(view) {
    currentView = view;
    $$(".nav-tab").forEach(t => t.classList.toggle("active", t.dataset.view === view));
    loadProjects();
    if (view === "plan") renderCalendar();
    else if (view === "experiments") renderExperiments();
    else if (view === "materials") renderMaterials();
    else if (view === "settings") renderSettings();
}

function loadProjects() {
    const list = document.getElementById("project-list");
    if (!list) return;
    list.innerHTML = "<li class=\"" + (!currentProject?"active":"") + "\" onclick=\"selectProject(null)\">\ud83d\udcc2 所有实验</li>";
    DB.listProjects().forEach(p => {
        list.innerHTML += "<li class=\"" + (p.id===currentProject?"active":"") + "\" onclick=\"selectProject('" + p.id + "')\">\ud83d\udcc1 " + esc(p.name) + "</li>";
    });
}

function selectProject(id) { currentProject = id; loadProjects(); if (currentView==="experiments") renderExperiments(); }

// Calendar
function renderCalendar() {
    const y=calYear, m=calMonth;
    const first=new Date(y,m,1).getDay(), days=new Date(y,m+1,0).getDate();
    const months=["一月","二月","三月","四月","五月","六月","七月","八月","九月","十月","十一月","十二月"];
    const dnames=["日","一","二","三","四","五","六"];
    const today=DB._today();
    const ms=y+"-"+String(m+1).padStart(2,"0");
    const allExps=DB.listExperiments(), allPlans=DB.listPlans();
    const dd={};
    for (let d=1; d<=days; d++) dd[ms+"-"+String(d).padStart(2,"0")]={exps:[],todos:[],dones:[]};
    allExps.forEach(e=>{if(e.date&&dd[e.date]) dd[e.date].exps.push(e);});
    allPlans.forEach(p=>{if(p.date&&dd[p.date]){if(p.done)dd[p.date].dones.push(p);else dd[p.date].todos.push(p);}});

    let html="<div class=\"cal-header\"><h2>\ud83d\udcc5 计划表</h2><div class=\"cal-nav\">"+
        "<button onclick=\"calNav(-1)\">\u2039</button>"+
        "<span class=\"cal-month\">"+y+"年 "+months[m]+"</span>"+
        "<button onclick=\"calNav(1)\">\u203a</button>"+
        "<button class=\"btn-s\" onclick=\"calToday()\" style=\"margin-left:4px\">今天</button></div></div>"+
        "<div class=\"cal-grid\">";
    dnames.forEach(d=>{html+="<div class=\"cal-day-header\">"+d+"</div>";});
    const pd=new Date(y,m,0).getDate();
    for(let i=first-1;i>=0;i--) html+="<div class=\"cal-day other\"><div class=\"cal-day-num\">"+(pd-i)+"</div></div>";
    for(let d=1;d<=days;d++){
        const ds=ms+"-"+String(d).padStart(2,"0");
        const data=dd[ds]||{};
        const is=ds===today;
        html+="<div class=\"cal-day"+(is?" today":"")+"\" onclick=\"addPlanForDate('"+ds+"')\">"+
            "<div class=\"cal-day-num\">"+d+"</div><div class=\"cal-day-items\">";
        data.exps.forEach(e=>{html+="<div class=\"cal-item exp\">"+esc(e.title.slice(0,12))+"</div>";});
        data.todos.forEach(p=>{html+="<div class=\"cal-item todo\">"+esc(p.title.slice(0,12))+"</div>";});
        data.dones.forEach(p=>{html+="<div class=\"cal-item done\">"+esc(p.title.slice(0,12))+"</div>";});
        html+="</div></div>";
    }
    const ep=(7-(first+days)%7)%7;
    for(let i=1;i<=ep;i++) html+="<div class=\"cal-day other\"><div class=\"cal-day-num\">"+i+"</div></div>";
    html+="</div>";
    document.getElementById("view-container").innerHTML=html;
}

function calNav(d){calMonth+=d;if(calMonth>11){calMonth=0;calYear++;}else if(calMonth<0){calMonth=11;calYear--;}renderCalendar();}
function calToday(){const n=new Date();calYear=n.getFullYear();calMonth=n.getMonth();renderCalendar();}
function addPlanForDate(ds){showForm("添加事项 - "+ds,[{label:"事项",type:"text",id:"plan-title",required:true}],()=>{const t=document.getElementById("plan-title").value.trim();if(!t)return;DB.addPlan(ds,t);closeModal();renderCalendar();});}

// Experiments
function renderExperiments(){
    const projects=DB.listProjects(), exps=DB.listExperiments(currentProject);
    let html="<div class=\"exp-header\"><h2>\ud83e\uddea 实验</h2><div>"+
        "<button class=\"btn-s\" onclick=\"showNewProject()\" style=\"margin-right:6px\">+ 新建项目</button>"+
        "<button class=\"btn-p\" onclick=\"showNewExperiment()\">+ 新建实验</button></div></div>"+
        "<div class=\"project-filter\"><button class=\""+(!currentProject?"active":"")+"\" onclick=\"filterExp(null)\">全部</button>";
    projects.forEach(p=>{html+="<button class=\""+(p.id===currentProject?"active":"")+"\" onclick=\"filterExp('"+p.id+"')\">"+esc(p.name)+"</button>";});
    html+="</div>";
    if(exps.length===0) html+="<div class=\"empty-state\"><div class=\"empty-icon\">\ud83e\uddea</div><p>暂无实验记录</p></div>";
    else{
        html+="<div class=\"exp-grid\">";
        exps.forEach(e=>{
            const label={draft:"草稿",submitted:"已提交",archived:"已归档"}[e.status]||e.status;
            html+="<div class=\"exp-card\" onclick=\"openDetail('"+e.id+"')\"><div class=\"exp-title\">"+esc(e.title)+"</div>"+
                "<div class=\"exp-meta\"><span>"+(e.date||"")+"</span><span class=\"badge badge-"+e.status+"\">"+label+"</span></div>"+
                (e.purpose?"<div class=\"exp-desc\">"+esc(e.purpose)+"</div>":"")+"</div>";
        });
        html+="</div>";
    }
    document.getElementById("view-container").innerHTML=html;
}
function filterExp(pid){currentProject=pid;renderExperiments();}

function showNewExperiment(){
    const projects=DB.listProjects();
    if(projects.length===0){alert("请先创建项目");return;}
    let opts="";
    projects.forEach(p=>{opts+="<option value=\""+p.id+"\""+(p.id===currentProject?" selected":"")+">"+esc(p.name)+"</option>";});
    showForm("新建实验",[
        {label:"标题",type:"text",id:"exp-title",required:true},
        {label:"目的",type:"textarea",id:"exp-purpose"},
        {label:"日期",type:"date",id:"exp-date",value:DB._today()},
        {label:"地点",type:"text",id:"exp-location"},
        {label:"项目",type:"select",id:"exp-project",options:opts}
    ],()=>{
        const t=document.getElementById("exp-title").value.trim();
        if(!t)return alert("请输入标题");
        const pid=document.getElementById("exp-project").value;
        DB.createExperiment(pid,t,document.getElementById("exp-purpose").value.trim(),document.getElementById("exp-date").value,document.getElementById("exp-location").value.trim());
        closeModal();renderExperiments();
    });
}

// Detail Panel
function openDetail(eid) {
    currentExpId=eid;
    const exp=DB.getExperiment(eid);
    if(!exp)return;
    const steps=exp.steps||[], results=exp.results||[], params=exp.parameters||[], logs=exp.run_logs||[];
    const label={draft:"草稿",submitted:"已提交",archived:"已归档"}[exp.status]||exp.status;
    document.querySelector(".detail-panel")?.remove();
    document.querySelector(".detail-overlay")?.remove();

    let h="<div class=\"detail-panel open\" id=\"dp\"><div class=\"dp-header\"><h2>"+esc(exp.title)+"</h2><button class=\"modal-close\" onclick=\"closeDetail()\">\u2715</button></div><div class=\"dp-body\">"+
        "<div class=\"dp-meta\"><span>\ud83d\udcc5 "+(exp.date||"")+"</span><span>\ud83d\udccd "+esc(exp.location||"未指定")+"</span><span class=\"badge badge-"+exp.status+"\">"+label+"</span></div>"+
        (exp.purpose?"<div class=\"dp-purpose\">\ud83c\udfaf "+esc(exp.purpose)+"</div>":"")+

        "<div class=\"dp-section\"><div class=\"dp-section-title\"><span>\ud83d\udccb 步骤 ("+steps.length+")</span><button class=\"btn-s\" onclick=\"showAddStep('"+eid+"')\">+ 添加</button></div>";
    if(steps.length>0) steps.forEach((s,i)=>{h+="<div class=\"step-item\"><div class=\"step-title\"><span>"+(i+1)+". "+esc(s.title)+"</span><button class=\"btn-d\" onclick=\"deleteStep('"+eid+"','"+s.id+"')\">删除</button></div>"+(s.content?"<div class=\"step-desc\">"+esc(s.content)+"</div>":"")+"</div>";});
    else h+="<div style=\"text-align:center;padding:12px;color:var(--text-m);font-size:12px\">暂无步骤</div>";
    h+="</div>";

    h+="<div class=\"dp-section\"><div class=\"dp-section-title\"><span>\ud83d\udcca 结果 ("+results.length+")</span><button class=\"btn-s\" onclick=\"showAddResult('"+eid+"')\">+ 记录</button></div>";
    if(results.length>0) results.forEach(r=>{h+="<div style=\"padding:8px 12px;background:#fafbfc;border:1px dashed var(--bd);border-radius:6px;margin-bottom:4px;font-size:12px;display:flex;justify-content:space-between\"><span>"+esc(r.content)+"</span><button class=\"btn-d\" onclick=\"deleteResult('"+eid+"','"+r.id+"')\">\u2715</button></div>";});
    else h+="<div style=\"text-align:center;padding:12px;color:var(--text-m);font-size:12px\">暂无结果</div>";
    h+="</div>";

    h+="<div class=\"dp-section\"><div class=\"dp-section-title\"><span>\u2699\ufe0f 参数 ("+params.length+")</span><button class=\"btn-s\" onclick=\"showAddParam('"+eid+"')\">+ 添加</button></div>";
    if(params.length>0) params.forEach(p=>{h+="<div style=\"padding:6px 10px;background:var(--primary-l);border-radius:6px;margin-bottom:4px;font-size:12px;display:flex;justify-content:space-between\"><span>"+esc(p.name)+" = "+esc(p.value)+" "+esc(p.unit)+"</span><button class=\"btn-d\" onclick=\"DB.deleteParam('"+eid+"','"+p.id+"');openDetail('"+eid+"')\">\u2715</button></div>";});
    else h+="<div style=\"text-align:center;padding:12px;color:var(--text-m);font-size:12px\">暂无参数</div>";
    h+="</div>";

    h+="<div class=\"dp-section\"><div class=\"dp-section-title\"><span>\ud83d\udcdd 运行日志 ("+logs.length+")</span><button class=\"btn-s\" onclick=\"showAddLog('"+eid+"')\">+ 添加</button></div>";
    if(logs.length>0) logs.forEach(l=>{h+="<div style=\"padding:8px 12px;background:var(--card);border:1px solid var(--bd);border-radius:6px;margin-bottom:6px;font-size:12px\"><div style=\"font-weight:600\">v"+l.version+" - "+(l.run_date||"")+"</div>"+(l.observations?"<div>观察："+esc(l.observations)+"</div>":"")+(l.deviations?"<div>偏差："+esc(l.deviations)+"</div>":"")+(l.conclusion?"<div style=\"color:var(--green)\">结论："+esc(l.conclusion)+"</div>":"")+"<button class=\"btn-d\" onclick=\"DB.deleteRunLog('"+eid+"','"+l.id+"');openDetail('"+eid+"')\">删除</button></div>";});
    else h+="<div style=\"text-align:center;padding:12px;color:var(--text-m);font-size:12px\">暂无日志</div>";
    h+="</div>";

    h+="<div class=\"dp-section\"><div class=\"dp-section-title\">状态</div><select onchange=\"updateStatus('"+eid+"',this.value)\" style=\"padding:6px;border:1px solid var(--bd);border-radius:6px;font-size:13px;width:100%\">"+
        "<option value=\"draft\""+(exp.status==="draft"?" selected":"")+">草稿</option>"+
        "<option value=\"submitted\""+(exp.status==="submitted"?" selected":"")+">已提交</option>"+
        "<option value=\"archived\""+(exp.status==="archived"?" selected":"")+">已归档</option></select></div>";
    h+="</div></div>";

    const ov=document.createElement("div"); ov.className="detail-overlay"; ov.style.display="block"; ov.onclick=closeDetail;
    document.body.appendChild(ov);
    const div=document.createElement("div"); div.innerHTML=h;
    document.body.appendChild(div.firstElementChild);
}

function closeDetail(){
    const dp=document.querySelector(".detail-panel");
    if(dp){dp.classList.remove("open");setTimeout(()=>dp.remove(),300);}
    document.querySelector(".detail-overlay")?.remove();
}
function updateStatus(eid,s){DB.updateExperiment(eid,{status:s});openDetail(eid);}

function showAddStep(eid){showForm("添加步骤",[{label:"标题",type:"text",id:"step-title",required:true},{label:"说明",type:"textarea",id:"step-content"}],()=>{const t=document.getElementById("step-title").value.trim();if(!t)return;DB.addStep(eid,t,document.getElementById("step-content").value.trim());closeModal();openDetail(eid);});}
function deleteStep(eid,sid){if(!confirm("确定删除？"))return;DB.deleteStep(eid,sid);openDetail(eid);}
function showAddResult(eid){showForm("记录结果",[{label:"内容",type:"textarea",id:"result-content",required:true}],()=>{const c=document.getElementById("result-content").value.trim();if(!c)return;DB.addResult(eid,c);closeModal();openDetail(eid);});}
function deleteResult(eid,rid){if(!confirm("确定删除？"))return;DB.deleteResult(eid,rid);openDetail(eid);}
function showAddParam(eid){showForm("添加参数",[{label:"名称",type:"text",id:"param-name",required:true},{label:"值",type:"text",id:"param-value"},{label:"单位",type:"text",id:"param-unit"}],()=>{const n=document.getElementById("param-name").value.trim();if(!n)return;DB.addParam(eid,n,document.getElementById("param-value").value.trim(),document.getElementById("param-unit").value.trim());closeModal();openDetail(eid);});}
function showAddLog(eid){showForm("添加运行日志",[{label:"观察",type:"textarea",id:"log-obs"},{label:"偏差",type:"textarea",id:"log-dev"},{label:"结论",type:"textarea",id:"log-con"}],()=>{const exp=DB.getExperiment(eid);if(!exp)return;const ver=(exp.run_logs||[]).length+1;DB.addRunLog(eid,document.getElementById("log-obs").value.trim(),document.getElementById("log-dev").value.trim(),document.getElementById("log-con").value.trim(),ver);closeModal();openDetail(eid);});}

// Materials
function renderMaterials(){
    const mats=DB.listMaterials();
    let h="<div class=\"exp-header\"><h2>\ud83e\uddeb 材料库</h2><button class=\"btn-p\" onclick=\"showAddMaterial()\">+ 添加材料</button></div>";
    if(mats.length===0) h+="<div class=\"empty-state\"><div class=\"empty-icon\">\ud83e\uddeb</div><p>材料库为空</p></div>";
    else{h+="<div class=\"mat-grid\">";mats.forEach(m=>{h+="<span class=\"mat-tag\" title=\""+esc(m.type)+"\">"+esc(m.name)+"</span>";});h+="</div>";}
    document.getElementById("view-container").innerHTML=h;
}
function showAddMaterial(){showForm("添加材料",[{label:"名称",type:"text",id:"mat-name",required:true},{label:"类型",type:"text",id:"mat-type",placeholder:"抗体/试剂/细胞系"}],()=>{const n=document.getElementById("mat-name").value.trim();if(!n)return;DB.createMaterial(n,document.getElementById("mat-type").value.trim());closeModal();renderMaterials();});}

// Settings
function renderSettings(){
    const p=DB.listProjects(), e=DB.listExperiments(), m=DB.listMaterials();
    let h="<div class=\"exp-header\"><h2>\u2699\ufe0f 设置</h2></div>"+
        "<div class=\"set-card\"><h3>数据存储</h3><div class=\"set-row\"><span class=\"set-label\">存储方式</span><span>浏览器本地存储</span></div>"+
        "<div class=\"set-row\"><span class=\"set-label\">数据备份</span><button class=\"btn-s\" onclick=\"exportData()\">导出数据</button><button class=\"btn-s\" onclick=\"importData()\" style=\"margin-left:6px\">导入数据</button></div>"+
        "<div style=\"margin-top:8px;font-size:12px;color:var(--text-m)\">导出为 JSON 文件，导入可恢复数据。</div></div>"+
        "<div class=\"set-card\"><h3>关于</h3><div class=\"set-row\"><span class=\"set-label\">版本</span><span>v2.0 Web</span></div>"+
        "<div class=\"set-row\"><span class=\"set-label\">技术栈</span><span>HTML/CSS/JS + localStorage</span></div></div>"+
        "<div class=\"set-card\"><h3>数据统计</h3><div class=\"set-row\"><span class=\"set-label\">项目</span><span>"+p.length+"</span></div>"+
        "<div class=\"set-row\"><span class=\"set-label\">实验</span><span>"+e.length+"</span></div>"+
        "<div class=\"set-row\"><span class=\"set-label\">材料</span><span>"+m.length+"</span></div></div>";
    document.getElementById("view-container").innerHTML=h;
}

function exportData(){
    const data={};
    for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(k.startsWith("hx_")) data[k]=localStorage.getItem(k);}
    const blob=new Blob([JSON.stringify(data,null,2)],{type:"application/json"});
    const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="helixdesk-"+DB._today()+".json";a.click();
    alert("数据已导出！");
}
function importData(){
    const input=document.createElement("input");input.type="file";input.accept=".json";
    input.onchange=function(e){
        const file=e.target.files[0];if(!file)return;
        const reader=new FileReader();
        reader.onload=function(ev){try{const data=JSON.parse(ev.target.result);for(const k in data){if(k.startsWith("hx_"))localStorage.setItem(k,data[k]);}alert("数据已导入！");location.reload();}catch{alert("文件格式错误");}};
        reader.readAsText(file);
    };
    input.click();
}

// Search
document.getElementById("search-btn").addEventListener("click",doSearch);
document.getElementById("search-input").addEventListener("keydown",e=>{if(e.key==="Enter")doSearch();});
function doSearch(){
    const q=document.getElementById("search-input").value.trim();
    if(!q)return;
    const r=DB.search(q);
    let h="<h3 style=\"margin-bottom:12px\">搜索</h3>";
    if(r.experiments.length){h+="<h4>\ud83e\uddea 实验</h4>";r.experiments.forEach(e=>{h+="<div class=\"exp-card\" onclick=\"switchView('experiments');setTimeout(()=>openDetail('"+e.id+"'),100)\" style=\"margin-bottom:6px\"><div>"+esc(e.title)+"</div></div>";});}
    if(r.materials.length){h+="<h4 style=\"margin:12px 0\">\ud83e\uddeb 材料</h4><div class=\"mat-grid\">";r.materials.forEach(m=>{h+="<span class=\"mat-tag\">"+esc(m.name)+"</span>";});h+="</div>";}
    if(!r.experiments.length&&!r.materials.length)h+="<p style=\"color:var(--text-m)\">未找到结果</p>";
    showCustomModal("\ud83d\udd0d 搜索",h,"<button class=\"btn-flat\" onclick=\"closeModal()\">关闭</button>");
}

// Modal
function showNewProject(){showForm("新建项目",[{label:"名称",type:"text",id:"proj-name",required:true},{label:"描述",type:"textarea",id:"proj-desc"}],()=>{const n=document.getElementById("proj-name").value.trim();if(!n)return alert("请输入名称");DB.createProject(n,document.getElementById("proj-desc").value.trim());closeModal();loadProjects();if(currentView==="experiments")renderExperiments();});}
function showForm(title,fields,onSave){
    let b="";
    fields.forEach(f=>{
        b+="<div class=\"fld\"><label>"+f.label+(f.required?" <span style=\"color:var(--red)\">*</span>":"")+"</label>";
        if(f.type==="textarea") b+="<textarea id=\""+f.id+"\" placeholder=\""+(f.placeholder||"")+"\" rows=\"3\"></textarea>";
        else if(f.type==="select") b+="<select id=\""+f.id+"\">"+(f.options||"")+"</select>";
        else if(f.type==="date") b+="<input type=\"date\" id=\""+f.id+"\" value=\""+(f.value||"")+"\" />";
        else b+="<input type=\"text\" id=\""+f.id+"\" placeholder=\""+(f.placeholder||"")+"\" value=\""+(f.value||"")+"\" />";
        b+="</div>";
    });
    showCustomModal(title,b,"<button class=\"btn-flat\" onclick=\"closeModal()\">取消</button><button class=\"btn-p\" id=\"form-save-btn\">保存</button>");
    setTimeout(()=>{const btn=document.getElementById("form-save-btn");if(btn)btn.onclick=onSave;const fi=document.querySelector("#modal-body input,textarea,select");if(fi)fi.focus();},50);
}
function showCustomModal(title,body,footer){
    document.getElementById("modal-title").textContent=title;
    document.getElementById("modal-body").innerHTML=body;
    document.getElementById("modal-footer").innerHTML=footer;
    document.getElementById("modal-overlay").style.display="block";
    document.getElementById("modal").style.display="flex";
}
function closeModal(){
    document.getElementById("modal-overlay").style.display="none";
    document.getElementById("modal").style.display="none";
}

// Keyboard
document.addEventListener("keydown",e=>{if(e.key==="Escape"){closeModal();closeDetail();}});

// Init
switchView("plan");
