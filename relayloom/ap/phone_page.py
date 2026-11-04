"""The phone alert page, in English, Tamil and Hindi. One self contained page: no outside fonts, scripts or requests."""
import json

from .i18n import LANGUAGES, STRINGS

TEMPLATE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Relayloom alerts</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}
body{margin:0;background:#0b0d10;color:#e7eaee;font:16px/1.5 Candara,Calibri,"Segoe UI","Nirmala UI","Noto Sans Tamil","Noto Sans Devanagari",system-ui,sans-serif}
header{position:sticky;top:0;background:#0b0d10;border-bottom:1px solid #23282f;padding:14px 16px}
.row{display:flex;align-items:center;justify-content:space-between;gap:12px}
h1{margin:0;font-size:17px}#state{margin:2px 0 0;font-size:13px;color:#8a939e}
select{min-height:44px;background:#12151a;color:#e7eaee;border:1px solid #2f353d;border-radius:8px;padding:0 10px;font:inherit}
main{padding:12px 16px 40px;display:grid;gap:10px}
.empty{color:#8a939e;font-size:14px;padding:24px 0}
.card{background:#12151a;border:1px solid #23282f;border-radius:12px;padding:14px}
.card.needs_owner{border-color:#f5b54480}.card.injection,.card.readback{border-color:#ff6b6b80}
.card b{display:block;font-size:16px}.card span{display:block;margin-top:4px;color:#b8c0c9;font-size:14px}
.card small{display:block;margin-top:8px;color:#8a939e;font:12px ui-monospace,monospace}
button{min-height:44px;margin-top:6px;background:#12151a;color:#e7eaee;border:1px solid #2f353d;border-radius:8px;padding:0 14px;font:inherit}
input{width:100%;min-height:44px;margin-top:8px;background:#0b0d10;color:#e7eaee;border:1px solid #2f353d;border-radius:8px;padding:0 12px;font:inherit}
.unchecked{text-decoration:underline dotted #f5b544;text-underline-offset:3px}
</style></head><body>
<header><div class="row"><h1 data-i="p.title">Relayloom alerts</h1>
<label class="row" style="gap:8px"><span data-i="p.language" style="font-size:13px;color:#8a939e">Language</span><select id="lang" aria-label="Language"></select></label></div>
<p id="state">Connecting</p></header>
<section class="card" style="margin:12px 16px 0"><b data-i="p.count_title">Count a delivery</b>
<span data-i="p.count_hint">Take a photo of the goods. The laptop counts them and the result appears below.</span>
<input id="word" value="box" data-aria="p.word_label" aria-label="What to count">
<input id="shot" type="file" accept="image/*" capture="environment" style="display:none">
<button id="take" type="button" data-i="p.take">Take dock photo</button><small id="up"></small></section>
<main id="list"><p class="empty" id="empty" data-i="p.empty">No alerts yet. This page lights up when a delivery needs you.</p></main>
<script>
var S=__STRINGS__,LANGS=S.languages,ST=S.strings,REVIEW=location.search.indexOf("review=1")>=0;
var token=new URLSearchParams(location.search).get("t")||"",last=0,ALL=[],stateKey="p.connecting",stateParams={};
var lang=(function(){var l="";try{l=localStorage.getItem("relayloom-lang")||""}catch(e){}
 if(!LANGS[l]){l=((navigator.language||"en")+"").slice(0,2)}return LANGS[l]?l:"en"})();
function t(key,params){var e=ST[key];if(!e)return key;var s=e[lang]||e.en,p={},k;params=params||{};
 for(k in params){if(/_key$/.test(k)){var name=k.slice(0,-4);if(ST[params[k]])p[name]=t(params[k]);else if(!(name in params))p[name]=params[k]}else p[k]=params[k]}
 return s.replace(/\{(\w+)\}/g,function(m,n){return n in p?p[n]:m})}
function mark(el,key){if(REVIEW&&ST[key]&&!ST[key].checked)el.classList.add("unchecked");else el.classList.remove("unchecked")}
var list=document.getElementById("list"),state=document.getElementById("state"),up=document.getElementById("up");
function setState(key,params){stateKey=key;stateParams=params||{};state.textContent=t(key,stateParams);mark(state,key)}
function build(a){var d=document.createElement("div");d.className="card "+a.kind;
 var b=document.createElement("b"),s=document.createElement("span"),m=document.createElement("small");
 b.textContent=a.key?t(a.key+".title",a.params):a.title;s.textContent=a.key?t(a.key+".body",a.params):a.body;
 if(a.key){mark(b,a.key+".title")}
 m.textContent=a.time+(a.case?" · "+a.case:"");d.append(b,s,m);return d}
function draw(){list.querySelectorAll(".card").forEach(function(c){c.remove()});
 var e=document.getElementById("empty");if(e)e.style.display=ALL.length?"none":"";
 ALL.slice().reverse().forEach(function(a){list.append(build(a))})}
function apply(){document.documentElement.lang=lang;
 document.querySelectorAll("[data-i]").forEach(function(el){var k=el.getAttribute("data-i");el.textContent=t(k);mark(el,k)});
 document.querySelectorAll("[data-aria]").forEach(function(el){el.setAttribute("aria-label",t(el.getAttribute("data-aria")))});
 document.title=t("p.title");setState(stateKey,stateParams);draw();
 var n=document.getElementById("allow");if(n){n.textContent=t("p.allow");mark(n,"p.allow")}}
var sel=document.getElementById("lang");
Object.keys(LANGS).forEach(function(c){var o=document.createElement("option");o.value=c;o.textContent=LANGS[c];sel.append(o)});
sel.value=lang;sel.onchange=function(){lang=sel.value;try{localStorage.setItem("relayloom-lang",lang)}catch(e){}apply()};
function add(a){ALL.push(a);draw();if(navigator.vibrate)navigator.vibrate([120,60,120]);
 if(window.Notification&&Notification.permission==="granted")new Notification(a.key?t(a.key+".title",a.params):a.title,{body:a.key?t(a.key+".body",a.params):a.body})}
function poll(){fetch("alerts?t="+encodeURIComponent(token)+"&after="+last).then(function(r){
 if(r.status===403){setState("p.invalid");return null}
 return r.json()}).then(function(j){if(!j)return;setState("p.waiting");
 j.forEach(function(a){last=Math.max(last,a.id);add(a)});poll()}).catch(function(){
 setState("p.reconnecting");setTimeout(poll,2000)})}
if(window.Notification&&Notification.permission==="default"){var n=document.createElement("button");n.id="allow";
 n.onclick=function(){Notification.requestPermission();n.remove()};document.querySelector("header").append(n)}
document.getElementById("take").onclick=function(){document.getElementById("shot").click()};
document.getElementById("shot").onchange=function(){var f=this.files[0];if(!f)return;
 up.textContent=t("p.sending",{kb:Math.round(f.size/1024)});
 fetch("photo?t="+encodeURIComponent(token)+"&word="+encodeURIComponent(document.getElementById("word").value),{method:"POST",headers:{"Content-Type":f.type||"image/jpeg"},body:f})
 .then(function(r){return r.json().then(function(j){up.textContent=r.ok?t("p.received"):(j.error||t("p.not_accepted"))})}).catch(function(){up.textContent=t("p.unreachable")});this.value=""};
apply();poll();
</script></body></html>"""


def page() -> str:
    """The page with the strings of all three languages inside it. `</` is escaped so no string can end the script."""
    payload = json.dumps({"languages": LANGUAGES, "strings": STRINGS}, ensure_ascii=False).replace("</", "<\\/")
    return TEMPLATE.replace("__STRINGS__", payload)
