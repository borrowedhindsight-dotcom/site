"""Build borrowedhindsight.org into _site/ from stories.json (anything dated in the future stays hidden).

Blog layout ("highlighter" design, Nov 2026): home (featured story, latest, a wall of borrowed lessons, category rows),
/stories/ (all, paginated), /category/<slug>/ pages with written introductions, /search/, long-form story pages
(answer-first summary, sticky contents, timeline, highlighted lesson, Reel block, share, FAQ, sources, previous/next,
related), plus About, Contact, Editorial standards, Privacy and Terms. Also sitemap.xml, feed.xml, robots.txt, ads.txt,
llms.txt and search.json.

A story is either a Reel story (has "reel") or a website-only article ("kind": "article"). Long-form stories use
"intro" + "sections"; older short stories with only "body" still render.
Images (need Pillow; fall back to the default image):
  assets/thumbs/<slug>.jpg  (+ -640.jpg)  card/cover art: the Reel frame on a blurred backdrop, no text
  assets/og/<slug>.jpg                    social-share card with the title
"""
import json, html, shutil, pathlib, datetime as dt, re, io, math, urllib.parse

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / '_site'
TODAY = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=5, minutes=30)).date().isoformat()
SITE = 'https://www.borrowedhindsight.org'
INSTAGRAM = 'https://www.instagram.com/borrowed.hindsight/'
YOUTUBE = 'https://www.youtube.com/@borrowedhindsight'
FACEBOOK = 'https://www.facebook.com/borrowedhindsight'
NEWSLETTER_URL = 'https://borrowedhindsight.substack.com'  # restore to NEWSLETTER below when the newsletter runs again
NEWSLETTER = ''  # paused 15 Nov 2026: no issues since 21 Oct, so no subscribe prompts
NL_LI = f'<li><a href="{NEWSLETTER}" rel="me noopener">Newsletter</a></li>' if NEWSLETTER else ''
CONTACT_EMAIL = 'hello@borrowedhindsight.org'
PROFILE = INSTAGRAM
# Reels archived on Instagram (Nov 2026). Stories linking to these point to the profile instead, and drop the
# VideoObject schema. Kept here rather than in stories.json because bh-publisher overwrites that file on every sync.
ARCHIVED_REELS = {
    'Des5AIoixAc', 'DewpCmagvx_', 'DezJfq9iGjx', 'De1xO77E0Kh', 'De1b9jZDhvu',
    'De2Cb7Kj9nX', 'De82tyrAEJj', 'De65fgxEQ2m', 'De3rrk-CVVp', 'De3Cq-sgVGt',
    'De6QXaaDSaX', 'De4UpTnEXbp', 'De9jUfnlVdW', 'De_bixbFVO_', 'DfAG8c-FAsd',
    'DfCq_jhlYra', 'DfCBMCElSTk', 'DfFPz1YDPjS', 'DfHKTgqlSHi', 'DfJuEo0FLaN',
    'DfKXdwWFFwF', 'DfM8RvTD5B4', 'DfO4wadibi2', 'DfPjrbbCsI-', 'DfRc5T7CV2z',
    'DfSH5OOAuEP', 'DfUtOUtD_St', 'DfWou5RkwNb', 'DfXR1R9DM3d',
}


def reel_id(url):
    m = re.search(r'/reels?/([^/?#]+)', url or '')
    return m.group(1) if m else ''
E = html.escape
PER_PAGE = 18
MIN_CAT_INDEX = 6   # category pages with fewer stories stay on the site but are hidden from Google (noindex, no ads, not in sitemap)
BYLINE = 'Manisha Aggarwal'   # owner and author: shown on every story, in Article schema and on the author page
AUTHOR_PATH = '/author/manisha-aggarwal/'
CALC_PATH = '/tools/rupee-inflation-calculator/'
CAGR_PATH = '/tools/cagr-calculator/'
TOOLS_PATH = '/tools/'
GOAL_PATH = '/tools/goal-sip-planner/'
AUTHOR_BIO = ('Manisha Aggarwal is an accounting professional based in New Delhi, India. Manisha runs Borrowed Hindsight as a hobby: '
              'to keep learning, to spread awareness, and to share true stories that motivate people to start, or start again.')

# Goal SIP planner (runs in the browser): a step-by-step journey. Kept out of the f-strings so its braces need no escaping.
GOAL_JS = r'''(function(){
var Y0=new Date().getFullYear(),KEY='bh-goal-plan-v2',W=document.getElementById('gw');if(!W)return;
var T={home:{e:'🏠',l:'Buy a home',d:'A place that is yours',i:7,a:80},
edu:{e:'🎓',l:"Children's education",d:'The course they dream of',i:10,a:50,age:18,ch:1},
mar:{e:'💍',l:"Children's wedding",d:'Their big day, your way',i:7,a:30,age:25,ch:1},
car:{e:'🚗',l:'Buy a car',d:'Paid for, not on EMI',i:6,a:12},
fi:{e:'🌴',l:'Financial freedom',d:'Work because you want to',i:6,a:100000},
oth:{e:'✨',l:'Something else',d:'A world trip, a business, a parent\'s care',i:6,a:10}};
var ORDER=['home','edu','mar','car','fi','oth'];
function fresh(){return {v:2,at:0,name:'',age:30,kids:[],sel:{},g:[],s:0,c:0,r:10,u:10};}
var S=fresh();
try{var h=location.hash.match(/^#p=(.+)$/);if(h){var o=JSON.parse(decodeURIComponent(escape(atob(decodeURIComponent(h[1])))));if(o&&o.v==2&&o.g){S=o;S.at=steps().length-1;}}
else{var ls=JSON.parse(localStorage.getItem(KEY)||'null');if(ls&&ls.v==2)S=ls;}}catch(e){}
function save(){try{localStorage.setItem(KEY,JSON.stringify(S));}catch(e){}}
function num(v,d){v=parseFloat(v);return isFinite(v)?v:d;}
function inr(x){return '₹'+Math.round(x).toLocaleString('en-IN');}
function big(x){var a=Math.abs(x);if(a>=1e7)return '₹'+(a/1e7).toFixed(2)+' crore';if(a>=1e5)return '₹'+(a/1e5).toFixed(2)+' lakh';return inr(a);}
function esc(t){return String(t==null?'':t).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function age(){return Math.round(num(S.age,30));}
function kid(g){return S.kids[g.c]||{n:'',b:Y0};}
function kname(g){var k=kid(g);return k.n||('Child '+(g.c+1));}
function gname(g){if(g.t=='edu')return kname(g)+'’s education';if(g.t=='mar')return kname(g)+'’s wedding';if(g.t=='fi')return 'Financial freedom at '+Math.round(num(g.k,50));return g.n||T[g.t].l;}
function steps(){var a=['you','kids','pick'];S.g.forEach(function(g,i){a.push(i);});a.push('money','plan');return a;}
function sync(){var out=[];S.kids=S.kids.filter(function(k){return k;});
ORDER.forEach(function(t){if(!S.sel[t])return;var ex=S.g.filter(function(g){return g.t==t;});
if(T[t].ch)S.kids.forEach(function(k,ci){var f=ex.filter(function(g){return g.c==ci;})[0];out.push(f||{t:t,c:ci,a:T[t].a,k:T[t].age,d:1,i:T[t].i,n:''});});
else if(ex.length)out=out.concat(ex);
else out.push(t=='fi'?{t:t,a:T.fi.a,k:Math.max(50,age()+5),e:85,p:8,i:6}:{t:t,a:T[t].a,y:Y0+5,pp:100,i:T[t].i,n:''});});S.g=out;}
/* ---- maths ---- */
function sipFactor(n,mr,s){var N=n*12,f=0;for(var j=0;j<N;j++)f+=Math.pow(1+s,Math.floor(j/12))*Math.pow(1+mr,N-j);return f;}
function rates(){var r=num(S.r,10)/100;return {r:r,s:Math.max(0,num(S.u,0))/100,mr:Math.pow(1+r,1/12)-1};}
function pays(g){var y,cnt=1,i=num(g.i,0)/100,a=Math.max(0,num(g.a,0)),x={P:[]};
if(g.t=='fi')y=Y0+Math.round(num(g.k,50))-age();else if(T[g.t].ch)y=Math.round(num(kid(g).b,Y0)+num(g.k,18));else y=Math.round(num(g.y,Y0+5));
if(g.t=='edu')cnt=Math.round(Math.min(10,Math.max(1,num(g.d,1))));
var n=y-Y0;x.y=y;x.y2=y+cnt-1;x.n=n;
if(!isFinite(y)){x.err='Fill in when you need this.';return x;}if(n<0){x.err='That date has already passed. Pick a later one.';return x;}if(n>80){x.err='Pick a date within the next 80 years.';return x;}
if(g.t=='fi'){var E=a*Math.pow(1+i,n),L=Math.round(Math.min(60,Math.max(1,num(g.e,85)-num(g.k,50)))),rp=Math.pow(1+num(g.p,8)/100,1/12)-1,gi=Math.pow(1+i,1/12)-1,c=0;
for(var q=0;q<L*12;q++)c+=E*Math.pow((1+gi)/(1+rp),q);x.E=E;x.L=L;x.P.push({y:y,fv:c});}
else{var pp=g.t=='home'?Math.min(100,Math.max(0,num(g.pp,100)))/100:1;for(var j=0;j<cnt;j++)x.P.push({y:y+j,fv:a*1e5*pp/cnt*Math.pow(1+i,n+j)});}
return x;}
function solo(g){var x=pays(g),R=rates(),o={x:x,fv:0,f:0,st:0};x.P.forEach(function(p){var n=p.y-Y0;o.fv+=p.fv;if(n>=1){o.f+=p.fv/sipFactor(n,R.mr,0);o.st+=p.fv/sipFactor(n,R.mr,R.s);}});return o;}
function plan(){var R=rates(),goals=[],P=[];
S.g.forEach(function(g,ix){var x=pays(g);if(x.err)return;var G={g:g,ix:ix,nm:gname(g),y:x.y,y2:x.y2,n:x.n,E:x.E,L:x.L,fv:0,gap:0,f:0,st:0,bcf:null};goals.push(G);x.P.forEach(function(p){P.push({G:G,y:p.y,fv:p.fv});});});
P.sort(function(a,b){return a.y-b.y||a.G.ix-b.G.ix;});
var bal=Math.max(0,num(S.s,0))*1e5,last=Y0,o={goals:goals,P:P,F:0,ST:0,need:0,cov:0,late:0,R:R};
P.forEach(function(p){var G=p.G,n=p.y-Y0;bal*=Math.pow(1+R.r,p.y-last);last=p.y;if(G.bcf===null)G.bcf=bal;var use=Math.min(bal,p.fv),gap=p.fv-use;bal-=use;
G.fv+=p.fv;G.gap+=gap;o.need+=p.fv;o.cov+=use;p.f=p.st=0;if(gap>0.5){if(n>=1){p.f=gap/sipFactor(n,R.mr,0);p.st=gap/sipFactor(n,R.mr,R.s);}else o.late+=gap;}
G.f+=p.f;G.st+=p.st;o.F+=p.f;o.ST+=p.st;});
goals.sort(function(a,b){return a.y-b.y||a.ix-b.ix;});return o;}
/* ---- building blocks ---- */
function inp(attr,v,o){o=o||{};return '<span class="wz-in">'+(o.pre?'<b>'+o.pre+'</b>':'')+'<input '+attr+' type="'+(o.text?'text':'number')+'"'+(o.text?' maxlength="40"':' inputmode="decimal" step="any"')+(o.ph?' placeholder="'+esc(o.ph)+'"':'')+' value="'+esc(v)+'">'+(o.suf?'<i>'+o.suf+'</i>':'')+'</span>';}
function q(label,field,help){return '<div class="wz-q"><label><span class="wz-ql">'+label+'</span>'+field+'</label>'+(help?'<p class="wz-help">'+help+'</p>':'')+'</div>';}
function G(ix,k){return 'data-g="'+ix+'" data-k="'+k+'"';}
function slider(ix,k,min,max,v){return '<div class="wz-slide"><input type="range" '+G(ix,k)+' min="'+min+'" max="'+max+'" step="1" value="'+v+'"><output id="wz-when" aria-live="polite"></output></div>';}
function adv(inner){return '<details class="wz-adv"><summary>Fine-tune the assumptions</summary>'+inner+'</details>';}
/* ---- steps ---- */
function stepYou(){return '<p class="wz-kick">Step 1 · You</p><h2>First, a little about you.</h2><p class="wz-lead">Your age lets us show how old you will be when each goal arrives.</p>'
+q('What should we call you? <em>(optional)</em>',inp('data-s="name"',S.name,{text:1,ph:'Your first name'}),'Used only to title your plan when you share it.')
+q('How old are you today?',inp('data-s="age"',S.age,{suf:'years'}));}
function stepKids(){var r='';S.kids.forEach(function(k,i){r+='<div class="wz-kid"><span class="wz-in"><input data-kid="'+i+'" data-k="n" type="text" maxlength="30" placeholder="Child '+(i+1)+'’s name" value="'+esc(k.n)+'"></span><span class="wz-in"><input data-kid="'+i+'" data-k="b" type="number" inputmode="numeric" aria-label="Birth year" value="'+esc(k.b)+'"><i>born</i></span><button type="button" class="wz-x" data-delkid="'+i+'" aria-label="Remove child">×</button></div>';});
return '<p class="wz-kick">Step 2 · Family</p><h2>Do you have children, or plan to?</h2><p class="wz-lead">Add each child with the year they were born. Planning one? Add the year you expect. Their biggest money moments, school and a wedding, are timed from it.</p>'
+r+'<button type="button" class="wz-add" data-addkid>+ Add '+(S.kids.length?'another':'a')+' child</button>'+(S.kids.length?'':'<p class="wz-help">No children, or not planning yet? Just press Next.</p>');}
function stepPick(){var t='';ORDER.forEach(function(k){var x=T[k],off=x.ch&&!S.kids.length;t+='<button type="button" class="wz-tile'+(S.sel[k]&&!off?' on':'')+'" data-tile="'+k+'"'+(off?' disabled':'')+' aria-pressed="'+(S.sel[k]&&!off?'true':'false')+'"><span class="wz-emo">'+x.e+'</span><b>'+x.l+'</b><small>'+(off?'Add a child in step 2 first':x.ch?x.d+' (for each child)':x.d)+'</small></button>';});
return '<p class="wz-kick">Step 3 · Dreams</p><h2>What must your money make possible?</h2><p class="wz-lead">Picture the next 20 years. The home, the school fees, the wedding, the day you stop working because you choose to. Tap everything that matters to you.</p><div class="wz-tiles">'+t+'</div><p class="wz-err" id="wz-err" hidden>Choose at least one goal to plan.</p>';}
function stepGoal(ix){var g=S.g[ix],x=T[g.t],nG=S.g.length,head='<p class="wz-kick">Goal '+(ix+1)+' of '+nG+' · '+x.e+' '+esc(x.l)+'</p>',b='',pr=adv(q('How fast will this cost rise?',inp(G(ix,'i'),g.i,{suf:'% a year'}),'Our starting point: '+x.i+'% a year. Education costs in India have usually risen faster than everyday prices.'));
var yn=Math.max(1,Math.min(40,num(g.y,Y0+5)-Y0));
if(g.t=='home')b='<h2>Picture your home.</h2><p class="wz-lead">Not any house. Yours. The more real you make it, the more real your plan becomes.</p>'
+q('What kind of home, and where?',inp(G(ix,'n'),g.n,{text:1,ph:'e.g. 3BHK in Whitefield, Bengaluru'}))
+q('What does a home like that cost there today?',inp(G(ix,'a'),g.a,{pre:'₹',suf:'lakh'}),'Look at 3 or 4 real listings in that area on a property website, or ask a local broker. Use today’s price; we add the future price rise for you.')
+q('How much of the price will you pay yourself?',inp(G(ix,'pp'),g.pp,{suf:'%'}),'100% if you will buy without a loan. If you will take a home loan, enter your down payment, usually 20%.')
+q('When do you want to move in?',slider(ix,'yn',1,40,yn))+pr;
else if(g.t=='car')b='<h2>Which car is in your future?</h2><p class="wz-lead">Buy it with money you saved, not with an EMI that eats next year’s salary.</p>'
+q('Which car?',inp(G(ix,'n'),g.n,{text:1,ph:'e.g. a family SUV'}))+q('Its on-road price today',inp(G(ix,'a'),g.a,{pre:'₹',suf:'lakh'}),'Include registration and insurance. A dealer quote or the maker’s website will tell you.')
+q('When do you want to drive it home?',slider(ix,'yn',1,40,yn))+pr;
else if(g.t=='oth')b='<h2>What else is on your list?</h2><p class="wz-lead">A world trip, your own business, your parents’ care. If it matters, it deserves a plan.</p>'
+q('What is the goal?',inp(G(ix,'n'),g.n,{text:1,ph:'e.g. Europe trip with the family'}))+q('What would it cost if you paid for it today?',inp(G(ix,'a'),g.a,{pre:'₹',suf:'lakh'}))
+q('When?',slider(ix,'yn',1,40,yn))+pr;
else if(g.t=='edu'){var kn=esc(kname(g));b='<h2>Dream big for '+kn+'.</h2><p class="wz-lead">Pilot, doctor, engineer, an MBA abroad: the right course costs more each year you wait. What do you see '+kn+' becoming?</p>'
+q('The dream course',inp(G(ix,'n'),g.n,{text:1,ph:'e.g. Commercial pilot training'}))
+q('What do the full fees cost today?',inp(G(ix,'a'),g.a,{pre:'₹',suf:'lakh'}),'Check today’s fees on the college website and add hostel and living costs. A commercial pilot licence in India costs about ₹1 crore today.')
+q('At what age will '+kn+' start it?',inp(G(ix,'k'),g.k,{suf:'years old'}),'Most degrees and pilot training start at 17 or 18, right after Class 12. A master’s usually starts around 22.')
+q('Fees are paid over',inp(G(ix,'d'),g.d||1,{suf:'years'}),'Enter 1 if you will pay it all at once.')+pr;}
else if(g.t=='mar'){var kn2=esc(kname(g));b='<h2>'+kn2+'’s wedding day.</h2><p class="wz-lead">Imagine '+kn2+' is getting married today. Think of a wedding you attended whose scale and budget you liked: the venue, the food, the clothes, the jewellery. What would a wedding like that cost this year?</p>'
+q('That wedding, at today’s prices',inp(G(ix,'a'),g.a,{pre:'₹',suf:'lakh'}),'Ask the family who hosted it, or add up quotes for venue, catering, clothes, jewellery and gifts.')
+q('At what age do you see '+kn2+' getting married?',inp(G(ix,'k'),g.k,{suf:'years old'}))+pr;}
else if(g.t=='fi')b='<h2>The day work becomes optional.</h2><p class="wz-lead">Financial freedom means your investments pay the monthly bills, so you work only because you want to. Most people never put a number on it. You are about to.</p>'
+q('At what age do you want to be financially free?',slider(ix,'k',Math.min(75,age()+1),75,Math.round(num(g.k,50))))
+q('What does your household spend each month today?',inp(G(ix,'a'),g.a,{pre:'₹',suf:'a month'}),'Rent, groceries, bills, school fees, travel, help at home. Leave out EMIs and SIPs that will have ended by then.')
+q('Plan for the money to last until age',inp(G(ix,'e'),g.e,{suf:'years old'}),'People are living longer. 85 or 90 is a safe planning age.')
+adv(q('Prices rise by',inp(G(ix,'i'),g.i,{suf:'% a year'}),'Our starting point: 6%, close to India’s long-run average.')+q('Your money earns, after you stop working',inp(G(ix,'p'),g.p,{suf:'% a year'}),'Usually lower than while you are working, because more of it sits in safer investments.'));
return head+b+'<div class="wz-live" id="wz-live" aria-live="polite"></div>';}
function stepMoney(){return '<p class="wz-kick">Almost there · What you have</p><h2>Now, what you already have.</h2><p class="wz-lead">Money you have already invested keeps growing and pays for your earliest goals first. That lowers what you need to save from now on.</p>'
+q('Savings already invested for these goals',inp('data-s="s"',S.s,{pre:'₹',suf:'lakh'}),'Mutual funds, shares, PF, FDs. Leave out your emergency fund.')
+q('SIP you already do each month <em>(optional)</em>',inp('data-s="c"',S.c||'',{pre:'₹'}),'We will tell you if it is enough.')
+q('What do you expect your investments to earn?',inp('data-s="r"',S.r,{suf:'% a year'}),'Be honest, not hopeful. Many planners use 10% to 12% for long-term equity funds, and less for money you need within a few years.')
+q('Can you raise your SIP every year?',inp('data-s="u"',S.u,{suf:'% a year'}),'A step-up SIP rises with your salary, so you can start smaller. Enter 0 to see a fixed SIP only.');}
function stepPlan(){var o=plan(),R=o.R,nm=S.name?esc(S.name)+'’s':'Your',h,c=Math.max(0,num(S.c,0)),tl='';
o.goals.forEach(function(G){var x=T[G.g.t],yr=G.y2>G.y?G.y+'–'+String(G.y2).slice(2):G.y,a=age()+G.n;
tl+='<li><span class="wz-yr">'+yr+'</span><div class="wz-tc"><b>'+x.e+' '+esc(G.nm)+'</b><span class="wz-meta">'+(G.n==0?'This year':'In '+G.n+' year'+(G.n==1?'':'s'))+' · you will be '+a+'</span>'
+'<span>Needed then: <strong>'+big(G.fv)+'</strong>'+(G.E?' (₹'+Math.round(G.E).toLocaleString('en-IN')+' a month for '+G.L+' years)':'')+'</span>'
+(G.gap<=0.5?'<span class="wz-ok">Paid for by your savings</span>':G.f<0.5?'<span class="wz-bad">'+big(G.gap)+' needed now, not covered</span>':'<span>SIP: <strong>'+inr(G.f)+'</strong> fixed'+(R.s>0?' or <strong>'+inr(G.st)+'</strong> step-up':'')+'</span>')
+'</div><button type="button" class="wz-edit" data-goto="'+(3+G.ix)+'">Edit</button></li>';});
if(!o.goals.length)h='<h2>Add a goal to see your plan.</h2>';
else if(o.F<0.5&&o.late<0.5)h='<h2>Your savings already pay for this future.</h2><p class="wz-lead">At '+(R.r*100).toFixed(0)+'% a year, what you have invested covers all '+o.goals.length+' goals. Keep it invested.</p>';
else h='<h2>Your future costs <mark>'+big(o.need)+'</mark>.<br>Here’s how you pay for it.</h2><div class="wz-opts"><div><small>Fixed SIP</small><b>'+inr(o.F)+'</b><em>a month, every month</em></div>'+(R.s>0?'<div class="best"><small>Step-up SIP</small><b>'+inr(o.ST)+'</b><em>a month to start, then '+(R.s*100).toFixed(0)+'% more each year</em></div>':'')+'</div>'
+'<p class="wz-lead">Start this month. Every year you wait makes each goal more expensive and leaves fewer months to save.'+(o.cov>0.5?' Your savings already cover '+big(o.cov)+'.':'')+'</p>'
+(o.late>0.5?'<p class="wz-bad">'+big(o.late)+' is needed this year and is not covered by your savings.</p>':'')
+(c>0?(c>=(R.s>0?o.ST:o.F)-0.5?'<p class="wz-ok">Your current SIP of '+inr(c)+' is enough'+(R.s>0?' if you step it up every year':'')+'. Well done.</p>':'<p class="wz-bad">You invest '+inr(c)+' a month now: '+inr((R.s>0?o.ST:o.F)-c)+' a month short'+(R.s>0?' of the step-up plan':'')+'.</p>'):'');
var ys=[];o.P.forEach(function(p){if(p.f&&ys.indexOf(p.y)<0)ys.push(p.y);});ys.sort(function(a,b){return a-b;});
var sh='',from=Y0;ys.forEach(function(y){var a=0,b=0,nmz=[];o.P.forEach(function(p){if(p.f&&p.y>from){a+=p.f;b+=p.st;if(nmz.indexOf(p.G.nm)<0)nmz.push(p.G.nm);}});
sh+='<tr><th scope="row">'+(from==Y0?'Now':from)+'–'+y+'</th><td>'+inr(a)+'</td>'+(R.s>0?'<td>'+inr(b*Math.pow(1+R.s,from-Y0))+(y-1>from?' → '+inr(b*Math.pow(1+R.s,y-1-Y0)):'')+'</td>':'')+'<td>'+nmz.map(esc).join(', ')+'</td></tr>';from=y;});
var tb='';o.goals.forEach(function(G){tb+='<tr><th scope="row">'+esc(G.nm)+'</th><td>'+(G.y2>G.y?G.y+'–'+G.y2:G.y)+'</td><td>'+G.n+'</td><td>'+big(G.bcf||0)+'</td><td>'+big(G.fv)+'</td><td>'+big(G.gap)+'</td><td>'+(G.f?inr(G.f):'–')+'</td>'+(R.s>0?'<td>'+(G.st?inr(G.st):'–')+'</td>':'')+'</tr>';});
return '<p class="wz-kick">'+nm+' plan</p>'+h+(tl?'<h3>Your journey, goal by goal</h3><ol class="wz-tl">'+tl+'</ol>':'')
+'<button type="button" class="wz-add" data-addgoal>+ Add another goal</button>'
+(ys.length>1?'<details class="wz-more"><summary>How your SIP changes as goals are reached</summary><div class="tablewrap"><table class="ctable"><thead><tr><th>Years</th><th>Fixed SIP</th>'+(R.s>0?'<th>Step-up SIP</th>':'')+'<th>Paying for</th></tr></thead><tbody>'+sh+'</tbody></table></div></details>':'')
+(tb?'<details class="wz-more"><summary>See the full calculation</summary><div class="tablewrap"><table class="ctable gtab"><thead><tr><th>Goal</th><th>Year</th><th>Years left</th><th>Savings carried forward</th><th>Needed on the day</th><th>Gap after savings</th><th>Fixed SIP</th>'+(R.s>0?'<th>Step-up SIP (start)</th>':'')+'</tr></thead><tbody>'+tb+'</tbody></table></div><p class="wz-help">Assumes '+(R.r*100).toFixed(1)+'% a year on your investments. Savings pay for the earliest goals first; what is left carries forward.</p></details>':'')
+'<div class="wz-sharebox"><h3>Share it with the people it’s for</h3><p>Your spouse, your parents, your children. The link opens this plan with your numbers, so they can see it and try their own.</p><div class="wz-shares"><button type="button" class="wz-btn wa" data-share="wa">Share on WhatsApp</button><button type="button" class="wz-btn" data-share="native" hidden>Share…</button><button type="button" class="wz-btn ghost" data-share="copy">Copy link</button></div></div>'
+'<p class="wz-restart"><button type="button" class="wz-link" data-restart>Start a new plan</button></p>';}
/* ---- render and navigation ---- */
function render(){var st=steps();if(S.at>=st.length)S.at=st.length-1;if(S.at<0)S.at=0;var s=st[S.at],body;
body=s=='you'?stepYou():s=='kids'?stepKids():s=='pick'?stepPick():s=='money'?stepMoney():s=='plan'?stepPlan():stepGoal(s);
var pct=Math.round(S.at/(st.length-1)*100);
W.innerHTML='<div class="wz-bar"><span style="width:'+pct+'%"></span></div><div class="wz-step">'+body+'</div>'
+(s=='plan'?'<div class="wz-nav"><button type="button" class="wz-btn ghost" data-nav="-1">← Back</button></div>':'<div class="wz-nav">'+(S.at>0?'<button type="button" class="wz-btn ghost" data-nav="-1">← Back</button>':'<span></span>')+'<button type="button" class="wz-btn" data-nav="1">'+(st[S.at+1]=='plan'?'See my plan →':'Next →')+'</button></div>');
if(s=='plan'){var nb=W.querySelector('[data-share=native]');if(nb&&navigator.share)nb.hidden=false;}
live();save();}
function live(){var st=steps()[S.at];if(typeof st!='number')return;var g=S.g[st],o=solo(g),R=rates(),el=document.getElementById('wz-live'),w=document.getElementById('wz-when');
if(w){if(g.t=='fi'){var n=Math.round(num(g.k,50))-age();w.innerHTML='At <b>'+Math.round(num(g.k,50))+'</b> · in '+(Y0+n)+', '+n+' years from now';}else{var yn=Math.round(num(g.y,Y0+5)-Y0);w.innerHTML='In <b>'+Math.round(num(g.y,Y0+5))+'</b> · '+yn+' year'+(yn==1?'':'s')+' from now, you will be '+(age()+yn);}}
if(!el)return;if(o.x.err){el.innerHTML='<p class="wz-bad">'+o.x.err+'</p>';return;}
var when=o.x.y2>o.x.y?'from '+o.x.y+' to '+o.x.y2:'in '+o.x.y;
el.innerHTML='<p class="wz-lk">Your answer</p><p>'+(g.t=='fi'?'To be free at '+Math.round(num(g.k,50))+' you will need about <b>'+big(o.fv)+'</b> invested by '+o.x.y+'. By then your monthly spending will be about '+inr(o.x.E)+'.':'This will cost about <b>'+big(o.fv)+'</b> '+when+(g.t=='edu'&&o.x.y2>o.x.y?' in all':'')+'.')+'</p>'
+(o.f>0.5?'<p>Start saving <b>'+inr(o.f)+'</b> a month from now'+(R.s>0?', or <b>'+inr(o.st)+'</b> a month rising '+(R.s*100).toFixed(0)+'% every year':'')+'.</p><p class="wz-help">Before counting savings you already have; we add those at the end.</p>':o.x.n<1?'<p class="wz-help">This is due this year, so a SIP is too late for it. It must come from savings.</p>':'');}
function go(n){S.at=n;render();var t=W.getBoundingClientRect().top;if(t<0||t>window.innerHeight*0.6)W.scrollIntoView({behavior:'smooth',block:'start'});var h2=W.querySelector('h2');if(h2){h2.setAttribute('tabindex','-1');h2.focus({preventScroll:true});}}
W.addEventListener('input',function(e){var t=e.target,k=t.getAttribute('data-k'),v=t.value;
if(t.hasAttribute('data-s'))S[t.getAttribute('data-s')]=v;
else if(t.hasAttribute('data-kid'))S.kids[+t.getAttribute('data-kid')][k]=v;
else if(t.hasAttribute('data-g')){var g=S.g[+t.getAttribute('data-g')];if(k=='yn')g.y=Y0+(+v);else g[k]=v;}
live();save();});
W.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;var st=steps(),cur=st[S.at];
if(b.hasAttribute('data-nav')){var d=+b.getAttribute('data-nav');if(d>0){if(cur=='you'&&!(num(S.age,0)>=16&&num(S.age,0)<=85)){alert('Please enter your age.');return;}
if(cur=='kids'||cur=='pick')sync();if(cur=='pick'&&!S.g.length){document.getElementById('wz-err').hidden=false;return;}}go(S.at+d);}
else if(b.hasAttribute('data-addkid')){S.kids.push({n:'',b:Y0});render();var r=W.querySelectorAll('.wz-kid input[data-k=n]');if(r.length)r[r.length-1].focus();}
else if(b.hasAttribute('data-delkid')){S.kids.splice(+b.getAttribute('data-delkid'),1);S.g=S.g.filter(function(g){return !T[g.t].ch;});render();}
else if(b.hasAttribute('data-tile')){var k=b.getAttribute('data-tile');S.sel[k]=!S.sel[k];b.classList.toggle('on',!!S.sel[k]);b.setAttribute('aria-pressed',S.sel[k]?'true':'false');var er=document.getElementById('wz-err');if(er)er.hidden=true;save();}
else if(b.hasAttribute('data-goto'))go(+b.getAttribute('data-goto'));
else if(b.hasAttribute('data-addgoal')){S.sel.oth=true;S.g.push({t:'oth',a:10,y:Y0+5,i:6,n:''});go(3+S.g.length-1);}
else if(b.hasAttribute('data-restart')){if(confirm('Clear this plan and start again?')){S=fresh();history.replaceState(null,'',location.pathname);go(0);}}
else if(b.hasAttribute('data-share'))share(b.getAttribute('data-share'),b);});
function link(){var u=location.origin+location.pathname+'#p='+encodeURIComponent(btoa(unescape(encodeURIComponent(JSON.stringify(S)))));history.replaceState(null,'',u);return u;}
function msg(){var o=plan(),R=o.R;return (S.name?S.name+'’s':'Our')+' family plan: '+o.goals.length+' goals, '+big(o.need)+' needed in all. Monthly SIP: '+inr(o.F)+(R.s>0?' fixed, or '+inr(o.ST)+' rising '+(R.s*100).toFixed(0)+'% a year':'')+'. See it and try your own numbers:';}
function share(how,b){var u=link();if(how=='wa')window.open('https://wa.me/?text='+encodeURIComponent(msg()+' '+u),'_blank','noopener');
else if(how=='native')navigator.share({title:'Our family goal plan',text:msg(),url:u}).catch(function(){});
else{var ok=function(){b.textContent='Link copied';setTimeout(function(){b.textContent='Copy link';},2000);};if(navigator.clipboard)navigator.clipboard.writeText(u).then(ok,function(){prompt('Copy this link:',u);});else prompt('Copy this link:',u);}}
document.querySelectorAll('[data-start]').forEach(function(b){b.addEventListener('click',function(){W.scrollIntoView({behavior:'smooth',block:'start'});var i=W.querySelector('input');if(i)i.focus({preventScroll:true});});});
if(S.at>0){var c=document.querySelector('[data-start]');if(c)c.textContent='Continue your plan →';}
render();})();'''

# Google Analytics 4 measurement ID and AdSense publisher ID. Empty = that tag is left out entirely.
# AdSense uses Auto ads: Google chooses ad placement. The AdSense script is left off pages without publisher content
# (contact, legal pages, search, 404), per AdSense policy.
GA_ID = 'G-V6QHHCTWJT'
# Google Analytics events, marked as key events in GA: story_read (reader reached the lesson), video_click (to Instagram/
# YouTube), share (share buttons and Copy link), calculator_use (first edit on a calculator page). One script, all pages.
GA_EVENTS = '''<script>document.addEventListener('DOMContentLoaded',function(){
var path=location.pathname;function ev(n,p){try{gtag('event',n,p)}catch(e){}}
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a,button');if(!a)return;var h=a.getAttribute('href')||'';
if(a.closest('.share')){ev('share',{method:a.tagName==='BUTTON'?'copy_link':a.textContent.trim().toLowerCase(),content_type:'story',item_id:path});return}
if(/instagram\\.com|youtube\\.com/.test(h)){ev('video_click',{platform:/youtube/.test(h)?'youtube':'instagram',link_location:a.closest('.reel')?'story_video':a.closest('.reelmini')?'story_video_mini':a.closest('footer')?'footer':a.closest('header.top')?'header':'other',page_path:path})}},true);
var l=document.getElementById('lesson');if(l&&'IntersectionObserver' in window){var o=new IntersectionObserver(function(x){if(x[0].isIntersecting){ev('story_read',{page_path:path});o.disconnect()}});o.observe(l)}
var c=document.getElementById('calc');if(c){var d=0;c.addEventListener('input',function(){if(d)return;d=1;ev('calculator_use',{calculator:/cagr/.test(path)?'cagr':/goal/.test(path)?'goal':'inflation'})})}});</script>'''
ADSENSE_CLIENT = 'ca-pub-8424876803254841'

# Parent category: Stories. Child categories: slug -> (name, one-line description, colour, written introduction).
CATS = {
    'zero-to-empire': ('Zero to Empire', 'Founders who started with almost nothing and built companies millions of people use.', '#5B2EFF', [
        'Most of the companies in this collection began with less than a typical monthly salary: a few thousand rupees, a borrowed room, one product nobody had asked for yet. These are the stories of how they grew into names people use every day.',
        'We focus on the early years, when the outcome was far from certain. Each story covers what the founder actually had at the start, the moment it nearly ended, and the decision that kept it going, with every figure checked against at least two published sources.',
        'Read them for the pattern rather than the fame: start smaller than feels respectable, solve a problem you can see in front of you, and keep going long enough for the work to compound.']),
    'small-start-big-result': ('Small Start, Big Result', 'Tiny first steps: a few rupees, one product, one room, and what they grew into.', '#E8A600', [
        'Every big result in this collection started with a step that looked too small to matter: a rooftop kitchen, one shop counter, a first sale at a weekend market, a single free lesson posted online.',
        'These stories are about the size of the first step, not the size of the dream. We look at what each person started with, why they began anyway, and how a modest routine turned into something much larger over years rather than weeks. Every number is verified in at least two sources, and each story lists them.',
        'If you have been waiting for the right moment or enough money to begin, these are the stories to read first.']),
    'rejected-then-won': ('Rejected, Then Won', 'People who were told no, turned away or laughed at, and kept going.', '#FF4FA3', [
        'Rejection is the most common chapter in success stories and the one people skip when they retell them. This collection keeps it in: the job interviews that went nowhere, the publishers and record labels that passed, the coaches and experts who said it would not work.',
        'We report each rejection as it happened, using contemporary sources where possible, and we judge the people who said no fairly, by what they knew at the time. Then we follow what the rejected person did next, and what finally changed.',
        'The lesson is rarely "never give up". More often it is: get specific feedback, change one thing, and try a different door.']),
    'late-starter': ('Late Starters', 'Proof that 40, 50, 65 or even 90 is not too late to begin.', '#13A89E', [
        'These are true stories of people who started the thing they are known for at an age when most people are told it is too late: a first company at 40, a career restart at 65, a first earned income in their nineties.',
        'Each story covers what the person did before, why they began when they did, and how earlier experience turned out to be an advantage rather than a delay. Dates and ages are checked against at least two published sources.',
        'If you are wondering whether you have missed your chance, start here.']),
    'comeback': ('Comebacks', 'People and companies that lost almost everything and came back stronger.', '#FF6B2C', [
        'A comeback story needs a real low point: a bankruptcy, a business destroyed, a career that seemed finished. This collection follows people and companies through that low point and out the other side.',
        'We pay most attention to what changed between the fall and the return: the new idea, the hard decision, the help that arrived. Every figure is verified in at least two sources, and we avoid turning anyone\'s hardship into entertainment.',
        'Read these when something has gone wrong and you need evidence that it does not have to be the end of the story.']),
    'human-limits': ('Human Limits', 'Athletes and explorers who did what experts said could not be done.', '#2E8BFF', [
        'For years, experts said a four-minute mile, a two-hour marathon or a new way of jumping could not work. This collection tells the stories of the people who proved otherwise, and of the preparation behind each record.',
        'We report times, distances and dates from official records and reputable sports reporting, checked in at least two sources, and we explain what made each breakthrough possible: training, technique, teamwork or a different way of thinking about the problem.',
        'The borrowed lesson is usually about limits we accept without testing them.']),
    'big-decisions': ('Big Decisions', 'Famous decisions, judged by what people knew at the time, not by hindsight.', '#1E1640', [
        'Turning down Netflix, passing on the Beatles, selling a stake in Apple for a few hundred dollars: these decisions look obvious now. This collection asks how they looked at the time.',
        'Each story sets out what the decision-makers knew, what they could not have known, and how the alternative would have played out on the information available then. We also test popular claims and statistics against the original research, and say so when a well-known story turns out to be wrong.',
        'It is the most direct use of borrowed hindsight: learning to judge a decision by the reasoning behind it, not only by how it turned out.']),
    'lists': ('Lists & Roundups', 'Researched collections of true stories, every one sourced.', '#8A5CFF', [
        'Researched collections of true stories around one theme, each entry sourced like a full story.']),
}
LEGACY_TAG = {  # older stories without a "category" field
    'small start, big result': 'small-start-big-result', 'zero to empire': 'zero-to-empire', 'rejected, then won': 'rejected-then-won',
    'rejected then won': 'rejected-then-won', 'human limits': 'human-limits', 'late starter': 'late-starter', 'comeback': 'comeback',
}


def cat_of(s):
    c = s.get('category') or LEGACY_TAG.get((s.get('tag') or '').strip().lower(), 'big-decisions')
    return c if c in CATS else 'big-decisions'


def tracking(ads=True):
    t = ''
    if GA_ID:
        t += (f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>'
              f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA_ID}');</script>"
              + GA_EVENTS)
    if ADSENSE_CLIENT:
        t += f'<meta name="google-adsense-account" content="{ADSENSE_CLIENT}">'
        if ads:
            t += f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT}" crossorigin="anonymous"></script>'
    return t


FONTS = ('<link rel="preload" href="/assets/webfonts/bricolage-grotesque-latin-opsz-normal.woff2" as="font" type="font/woff2" crossorigin>'
         '<link rel="preload" href="/assets/webfonts/newsreader-latin-opsz-normal.woff2" as="font" type="font/woff2" crossorigin>')
SEARCH_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m20 20-4.6-4.6"/></svg>'
SCRIPT = '''<script>
(function(){
  document.querySelectorAll('[data-copy]').forEach(function(b){b.addEventListener('click',function(){
    if(navigator.share&&matchMedia('(pointer:coarse)').matches){navigator.share({title:document.title,url:b.dataset.copy}).catch(function(){});return;}
    if(navigator.clipboard){navigator.clipboard.writeText(b.dataset.copy);b.textContent='Link copied';}});});
  document.addEventListener('click',function(e){document.querySelectorAll('.nav details[open]').forEach(function(d){if(!d.contains(e.target))d.removeAttribute('open');});});
  var art=document.querySelector('.prose');if(!art)return;
  var bar=document.querySelector('.progress');
  var links=[].slice.call(document.querySelectorAll('.aside .toc a'));
  var heads=links.map(function(a){return document.getElementById(a.getAttribute('href').slice(1));});
  function onScroll(){
    var r=art.getBoundingClientRect(),h=r.height-innerHeight*0.6;
    if(bar)bar.style.width=Math.max(0,Math.min(1,-r.top/h))*100+'%';
    var cur=-1;heads.forEach(function(el,i){if(el&&el.getBoundingClientRect().top<140)cur=i;});
    links.forEach(function(a,i){a.classList.toggle('on',i===cur);});
  }
  addEventListener('scroll',onScroll,{passive:true});onScroll();
})();
</script>'''


def nav_html():
    items = ''.join(f'<a href="/category/{c}/"><i class="dot" style="--c:{v[2]}"></i>{E(v[0])}<small>{COUNTS.get(c, 0)}</small></a>'
                    for c, v in CATS.items() if c in LIVE_CATS)
    return (f'<nav class="nav" aria-label="Main"><a class="hide-m" href="/stories/">Stories</a>'
            f'<details><summary>Categories</summary><div class="menu"><a href="/stories/"><i class="dot" style="--c:#FFD60A"></i>All stories<small>{sum(COUNTS.values())}</small></a>{items}<a class="show-m" href="{TOOLS_PATH}">Calculators</a><a class="show-m" href="/about/">About</a></div></details>'
            f'<a class="hide-m" href="{TOOLS_PATH}">Calculators</a><a class="hide-m" href="/about/">About</a>'
            f'<a class="search" href="/search/" aria-label="Search stories">{SEARCH_ICON}</a>'
            + (f'<a class="cta hide-m" href="#newsletter">Newsletter</a>' if NEWSLETTER else '') + '</nav>')


def page(title, desc, body, path='/', ld=None, og_type='website', extra='', image=None, noindex=False, ads=True, progress=False):
    img = image or f'{SITE}/assets/og.png'
    # Google shows about 60 characters of a title: drop the brand suffix rather than have the topic cut off.
    if title.endswith(' | Borrowed Hindsight') and len(title) > 60: title = title[:-len(' | Borrowed Hindsight')]
    # Descriptions: Google shows about 155 characters; cut long ones at a word boundary.
    if len(desc) > 158: desc = desc[:155].rsplit(' ', 1)[0].rstrip(',;:') + '…'
    ld_html = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    robots = 'noindex,follow' if noindex else 'index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1'
    cats = ''.join(f'<li><a href="/category/{c}/">{E(v[0])}</a></li>' for c, v in CATS.items() if c in LIVE_CATS)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">
<link rel="canonical" href="{SITE}{path}"><link rel="icon" href="/assets/favicon.png"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<meta name="google-site-verification" content="Z8IjOXiZKp3AtpkbKtGYkweQgaNV6yic2UDtFgTTYyk"><meta name="robots" content="{robots}"><meta name="theme-color" content="#1E1640">
<link rel="alternate" type="application/rss+xml" title="Borrowed Hindsight" href="/feed.xml">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="Borrowed Hindsight"><meta property="og:locale" content="en_IN">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:image" content="{img}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="675"><meta property="og:url" content="{SITE}{path}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{E(title)}"><meta name="twitter:description" content="{E(desc)}"><meta name="twitter:image" content="{img}">{extra}{ld_html}
{FONTS}<link rel="stylesheet" href="/assets/style.css?v={VERSION}">{tracking(ads)}</head><body>
<a class="skip" href="#main">Skip to content</a>{'<div class="progress" aria-hidden="true"></div>' if progress else ''}
<header class="top"><div class="wrap"><a class="brand" href="/"><img src="/assets/logo.svg" alt="" width="38" height="38"><span>Borrowed Hindsight</span></a>{nav_html()}</div></header>
<div id="main">{body}</div>
<footer><div class="wrap"><div class="fgrid">
<div><div class="fbrand"><img src="/assets/logo.svg" alt="" width="38" height="38">Borrowed Hindsight</div>
<p>True, sourced stories of people who started with almost nothing, and one lesson to borrow from each.</p></div>
<div><h2>Stories</h2><ul><li><a href="/stories/">All stories</a></li>{cats}</ul></div>
<div><h2>Follow</h2><ul><li><a href="{INSTAGRAM}" rel="me noopener">Instagram</a></li><li><a href="{YOUTUBE}" rel="me noopener">YouTube</a></li><li><a href="{FACEBOOK}" rel="me noopener">Facebook</a></li>{NL_LI}</ul></div>
<div><h2>About</h2><ul><li><a href="/about/">About us</a></li><li><a href="/editorial-standards/">Editorial standards</a></li><li><a href="/contact/">Contact</a></li><li><a href="/privacy/">Privacy policy</a></li><li><a href="/terms/">Terms of use</a></li></ul></div></div>
<p class="fine">© {dt.date.today().year} Borrowed Hindsight. General education, not personal or financial advice. Our videos are animated and narrated with an AI voice; every story is checked against its sources. Our publishing tool uses YouTube API Services: see our <a href="/privacy/">privacy policy</a> and the <a href="https://www.youtube.com/t/terms">YouTube Terms of Service</a>.</p></div></footer>
{SCRIPT}</body></html>'''


def signup(where='home'):
    if not NEWSLETTER:
        return ''
    head = 'One borrowed lesson, every Sunday' if where == 'home' else 'Get a story like this every Sunday'
    return f'''<section class="signup" id="newsletter"><div><h2>{head}</h2>
<p>One true story a week of someone who started small, and the one line of hindsight worth keeping. Free, and you can unsubscribe anytime.</p></div>
<div><iframe src="{NEWSLETTER}/embed" title="Subscribe to the Borrowed Hindsight newsletter" scrolling="no" loading="lazy"></iframe>
<p class="note">Prefer Substack? <a href="{NEWSLETTER}/subscribe" rel="noopener">Subscribe there</a>.</p></div></section>'''


def site_data():
    if not (GA_ID or ADSENSE_CLIENT):
        return ('<p>borrowedhindsight.org does not use cookies, analytics, advertising trackers or sign-up forms. We do not collect personal information from visitors.</p>')
    t = '<p>We do not ask visitors for personal information.</p>'
    if GA_ID:
        t += ('<p><b>Analytics.</b> We use Google Analytics to understand how many people visit, which stories they read and where they came from '
              '(for example Instagram, YouTube or a search engine). Google Analytics uses cookies and collects data such as pages viewed, approximate location, '
              'device and browser. We see only aggregate reports and never use it to identify you. See '
              '<a href="https://policies.google.com/technologies/partner-sites">how Google uses data from sites that use its services</a>. '
              'You can opt out with the <a href="https://tools.google.com/dlpage/gaoptout">Google Analytics opt-out add-on</a>.</p>')
    if ADSENSE_CLIENT:
        t += ('<p><b>Advertising.</b> This site shows ads served by Google AdSense. Google and its partners use cookies to show ads based on your visits '
              'to this and other websites. You can turn off personalised ads in <a href="https://adssettings.google.com">Google Ads Settings</a>, or opt out of '
              "third-party vendors' cookies at <a href=\"https://www.aboutads.info/choices/\">aboutads.info</a>. We do not choose or endorse the products in these ads, "
              'and nothing in them is advice from us.</p>')
    return t

REDIRECTS = {
    'lego-comeback-from-near-bankruptcy-back-to-the-brick': 'biggest-business-comebacks-in-history-apple-lego-marvel',
    'steve-sasson-kodak-first-digital-camera-1975': 'steve-sasson-kodak-first-digital-camera-shelved-story',
}


def write(rel, content):
    p = OUT / rel; p.parent.mkdir(parents=True, exist_ok=True)
    (p.write_bytes if isinstance(content, bytes) else p.write_text)(content)


ORG = {'@type': 'Organization', '@id': f'{SITE}/#org', 'name': 'Borrowed Hindsight', 'url': SITE + '/',
       'description': 'An independent publisher of true, sourced stories of people who started with almost nothing.',
       'logo': {'@type': 'ImageObject', 'url': f'{SITE}/assets/apple-touch-icon.png', 'width': 180, 'height': 180},
       'sameAs': [u for u in (INSTAGRAM, YOUTUBE, FACEBOOK, NEWSLETTER) if u], 'email': CONTACT_EMAIL,
       'publishingPrinciples': f'{SITE}/editorial-standards/', 'correctionsPolicy': f'{SITE}/editorial-standards/#corrections',
       'contactPoint': {'@type': 'ContactPoint', 'contactType': 'editorial', 'email': CONTACT_EMAIL, 'url': f'{SITE}/contact/'},
       'founder': {'@id': f'{SITE}{AUTHOR_PATH}#person'}}
PERSON = {'@type': 'Person', '@id': f'{SITE}{AUTHOR_PATH}#person', 'name': BYLINE, 'url': SITE + AUTHOR_PATH,
          'jobTitle': 'Accounting professional', 'description': AUTHOR_BIO, 'homeLocation': {'@type': 'Place', 'name': 'New Delhi, India'}}


def crumbs(items):
    return {'@type': 'BreadcrumbList', '@context': 'https://schema.org', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + u} for i, (n, u) in enumerate(items)]}


def crumbs_html(items):
    parts = [f'<a href="{u}">{E(n)}</a>' for n, u in items[:-1]] + [f'<span aria-current="page">{E(items[-1][0])}</span>']
    return '<nav class="crumbs" aria-label="Breadcrumb">' + '<span aria-hidden="true">/</span>'.join(parts) + '</nav>'


# ---------- images ----------
def hex_rgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def make_images(stories):
    """Per story: a text-free 16:9 cover (Reel frame on its own blurred backdrop, or Mirro on the category colour)
    at 1200 and 640 px wide, and a 1200x675 social card with the title."""
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print('Pillow not installed: images skipped'); return set()
    fdir = ROOT / 'assets' / 'fonts'
    disp = lambda n: ImageFont.truetype(str(fdir / 'BH-Display.ttf'), n)
    sans = ImageFont.truetype(str(fdir / 'BH-SansSemi.ttf'), 26)
    mirro = Image.open(ROOT / 'assets' / 'social' / 'profile.png').convert('RGBA')
    W, H = 1200, 675
    made = set()

    def rounded(im, r):
        m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
        out = Image.new('RGBA', im.size); out.paste(im, (0, 0), m); return out

    def save(im, rel, q=82):
        buf = io.BytesIO(); im.convert('RGB').save(buf, 'JPEG', quality=q, optimize=True, progressive=True); write(rel, buf.getvalue())

    for s in stories:
        frame_p = ROOT / 'assets' / 'reels' / f'{s["slug"]}.jpg'
        col = hex_rgb(CATS[cat_of(s)][2])
        ill_p = ROOT / 'assets' / 'covers' / f'{s["slug"]}.png'
        if ill_p.exists():   # illustrated cover drawn with the animation kit (bh-publisher scripts/covers.py)
            cover = Image.open(ill_p).convert('RGBA').resize((W, H), Image.LANCZOS)
            save(cover, f'assets/thumbs/{s["slug"]}.jpg', 86)
            save(cover.resize((640, 360), Image.LANCZOS), f'assets/thumbs/{s["slug"]}-640.jpg', 82)
            save(cover, f'assets/og/{s["slug"]}.jpg', 86)
            made.add(s['slug']); continue
        if frame_p.exists():
            f = Image.open(frame_p).convert('RGB')
            bg = f.resize((W, int(f.height * W / f.width))); top = (bg.height - H) // 2
            bg = bg.crop((0, top, W, top + H)).filter(ImageFilter.GaussianBlur(38))
            bg = Image.blend(bg, Image.new('RGB', (W, H), (30, 22, 64)), 0.18)
            crop = f.crop((0, int(f.height * 0.055), f.width, int(f.height * 0.73)))
            ch = H - 70; cw = int(crop.width * ch / crop.height)
            crop = rounded(crop.resize((cw, ch), Image.LANCZOS), 26)
            shadow = Image.new('RGBA', (cw + 80, ch + 80), (0, 0, 0, 0))
            ImageDraw.Draw(shadow).rounded_rectangle((40, 52, cw + 40, ch + 52), 26, fill=(20, 12, 50, 110))
            shadow = shadow.filter(ImageFilter.GaussianBlur(18))
            cover = bg.convert('RGBA'); x = (W - cw) // 2
            cover.alpha_composite(shadow, (x - 40, 35 - 40)); cover.alpha_composite(crop, (x, 35))
        else:
            cover = Image.new('RGBA', (W, H), col + (255,)); d = ImageDraw.Draw(cover)
            d.ellipse((W - 520, -300, W + 220, 440), fill=tuple(min(255, c + 28) for c in col))
            d.ellipse((-260, H - 260, 340, H + 340), fill=tuple(max(0, c - 22) for c in col))
            m = mirro.resize((360, 360), Image.LANCZOS); cover.alpha_composite(m, ((W - 360) // 2, (H - 360) // 2))
        save(cover, f'assets/thumbs/{s["slug"]}.jpg')
        save(cover.resize((640, 360), Image.LANCZOS), f'assets/thumbs/{s["slug"]}-640.jpg', 80)

        # social card: title on white, cover art on the right
        og = Image.new('RGB', (W, H), (255, 255, 255)); d = ImageDraw.Draw(og)
        art = cover.convert('RGB').crop((322, 12, 878, 663)).resize((480, 562))
        og.paste(rounded(art, 28), (W - 480 - 50, 56), rounded(art, 28))
        cname = CATS[cat_of(s)][0]
        d.ellipse((60, 78, 78, 96), fill=col)
        d.text((92, 72), cname, font=sans, fill=(30, 22, 64))
        title = s['title']; maxw = W - 480 - 50 - 60 - 40
        for size in (62, 56, 50, 46, 42, 38, 34):
            font = disp(size); lines = []; cur = ''
            for w in title.split():
                t = (cur + ' ' + w).strip()
                if d.textlength(t, font=font) <= maxw: cur = t
                else: lines.append(cur); cur = w
            lines.append(cur)
            if len(lines) * size * 1.12 <= H - 260: break
        y = 140
        for ln in lines:
            d.text((60, y), ln, font=font, fill=(30, 22, 64)); y += int(size * 1.12)
        d.rectangle((60, H - 92, 60 + 54, H - 86), fill=(255, 214, 10))
        d.text((60, H - 74), 'borrowedhindsight.org', font=sans, fill=(75, 68, 102))
        buf = io.BytesIO(); og.save(buf, 'JPEG', quality=84, optimize=True, progressive=True)
        write(f'assets/og/{s["slug"]}.jpg', buf.getvalue())
        made.add(s['slug'])
    return made


# ---------- helpers ----------
def words_of(s):
    if s.get('sections'):
        txt = ' '.join(s.get('intro', [])) + ' ' + ' '.join(p for sec in s['sections'] for p in sec['paras'])
    else:
        txt = ' '.join(s.get('body', []))
    return len(txt.split())


def slugify(t):
    return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')[:60]


VERSION = dt.datetime.now().strftime('%Y%m%d%H%M')
THUMBS = set()
TITLES = {}
LIVE_CATS = set()   # categories that have at least one published story
COUNTS = {}
COVER_META = json.load(open(ROOT / 'covers.json')) if (ROOT / 'covers.json').exists() else {}
POP = json.load(open(ROOT / 'popularity.json')) if (ROOT / 'popularity.json').exists() else {}   # Instagram views per story, from bh-publisher
LINK_RE = re.compile(r'https?://(?:www\.)?borrowedhindsight\.org/stories/([a-z0-9-]+)/?')


def para(text):
    """Escape a paragraph and turn links to our own stories into titled internal links."""
    out = E(text)
    def repl(m):
        slug = m.group(1)
        return f'<a href="/stories/{slug}/">{E(TITLES.get(slug, slug.replace("-", " ")))}</a>'
    return LINK_RE.sub(repl, out)


def thumb(s, small=False):
    if s['slug'] in THUMBS:
        return f'/assets/thumbs/{s["slug"]}{"-640" if small else ""}.jpg'
    return '/assets/og.png'


def og_img(s):
    return f'/assets/og/{s["slug"]}.jpg' if s['slug'] in THUMBS else '/assets/og.png'


def alt_of(s):
    if s['slug'] in COVER_META:
        return COVER_META[s['slug']]['alt']
    if (ROOT / 'assets' / 'reels' / f'{s["slug"]}.jpg').exists():
        return f'Illustration from our animated video: {s["title"]}'
    return f'Borrowed Hindsight illustration: {s["title"]}'


def caption_of(s):
    if s['slug'] in COVER_META:
        return COVER_META[s['slug']]['caption']
    return f'Illustration from the Borrowed Hindsight video about this story.' if (ROOT / 'assets' / 'reels' / f'{s["slug"]}.jpg').exists() else ''


def img_tag(s, sizes, eager=False, alt=None):
    alt = alt_of(s) if alt is None else alt
    src = thumb(s)
    srcset = f' srcset="{thumb(s, True)} 640w, {src} 1200w" sizes="{sizes}"' if s['slug'] in THUMBS else ''
    load = ' fetchpriority="high"' if eager else ' loading="lazy" decoding="async"'
    return f'<img src="{src}"{srcset} alt="{E(alt)}" width="1200" height="675"{load}>'


def kicker(c, link=False):
    n, _, col, _ = CATS[c]
    inner = f'<i class="dot" style="--c:{col}"></i>{E(n)}'
    return f'<a class="kicker" href="/category/{c}/">{inner}</a>' if link else f'<span class="kicker">{inner}</span>'


def mins(s):
    return max(1, round(words_of(s) / 220))


def card(s, summary=True):
    return (f'<a class="card" href="/stories/{s["slug"]}/"><div class="pic">{img_tag(s, "(max-width:720px) 92vw, 380px")}</div>'
            f'{kicker(cat_of(s))}<h3>{E(s["title"])}</h3>' + (f'<p>{E(s["summary"])}</p>' if summary else '') +
            f'<span class="rt">{mins(s)} min read</span></a>')


def grid(items):
    return '<div class="grid">' + ''.join(card(s) for s in items) + '</div>' if items else ''


def pager(base, n, total):
    if total <= 1:
        return ''
    links = []
    for i in range(1, total + 1):
        u = base if i == 1 else f'{base}page/{i}/'
        links.append(f'<span class="cur" aria-current="page">{i}</span>' if i == n else f'<a href="{u}">{i}</a>')
    return '<nav class="pager" aria-label="Pages">' + ''.join(links) + '</nav>'


def share(url, title):
    u = urllib.parse.quote(SITE + url, safe=''); t = urllib.parse.quote(title, safe='')
    return (f'<div class="share"><span>Send this to someone</span>'
            f'<a href="https://wa.me/?text={t}%20{u}" rel="noopener">WhatsApp</a>'
            f'<a href="https://www.facebook.com/sharer/sharer.php?u={u}" rel="noopener">Facebook</a>'
            f'<a href="https://twitter.com/intent/tweet?text={t}&url={u}" rel="noopener">X</a>'
            f'<a href="https://www.linkedin.com/sharing/share-offsite/?url={u}" rel="noopener">LinkedIn</a>'
            f'<button type="button" data-copy="{E(SITE + url)}">Copy link</button></div>')


def fmt_date(iso):
    return dt.date.fromisoformat(iso).strftime('%-d %B %Y')


# ---------- pages ----------
def story_page(s, prev_s, next_s, related):
    url = f'/stories/{s["slug"]}/'; c = cat_of(s); cname = CATS[c][0]
    mod = s.get('updated', s['date']); rt = mins(s)
    is_article = s.get('kind') == 'article'
    toc_items = []
    if s.get('sections'):
        intro = ''.join(f'<p>{para(p)}</p>' for p in s.get('intro', []))
        ids = [slugify(sec['h']) for sec in s['sections']]
        toc_items = list(zip(ids, [sec['h'] for sec in s['sections']]))
        secs = ''.join(f'<h2 id="{i}">{E(sec["h"])}</h2>' + ''.join(f'<p>{para(p)}</p>' for p in sec['paras']) for i, sec in zip(ids, s['sections']))
    else:
        intro = ''; secs = '<h2 id="the-story">The story</h2>' + ''.join(f'<p>{para(p)}</p>' for p in s.get('body', []))
        toc_items = [('the-story', 'The story')]
    tl = s.get('timeline') or []
    money = s.get('money')
    if money: toc_items.append(('money', money.get('h', 'The money behind it')))
    if tl: toc_items.append(('timeline', 'Timeline'))
    toc_items.append(('lesson', 'The borrowed hindsight'))
    if s.get('faq'): toc_items.append(('faq', 'Questions people ask'))
    toc_items.append(('sources', 'Sources'))
    toc_li = ''.join(f'<li><a href="#{i}">{E(h)}</a></li>' for i, h in toc_items)
    toc_m = f'<details class="toc-m"><summary>In this story</summary><ol>{toc_li}</ol></details>'
    tl_html = ('<section class="timeline" id="timeline"><h2>Timeline</h2><ol>' + ''.join(f'<li><b>{E(str(y))}</b>{E(ev)}</li>' for y, ev in tl) + '</ol></section>') if tl else ''
    money_html = ''
    if money:
        rows = ''.join(f'<tr><th scope="row">{E(a)}</th><td>{E(b)}</td></tr>' for a, b in money.get('table', []))
        money_html = (f'<section class="money" id="money"><h2>{E(money.get("h", "The money behind it"))}</h2>'
                      f'<p class="mby">By <a href="{AUTHOR_PATH}" rel="author">{E(BYLINE)}</a>, accounting professional</p>'
                      + ''.join(f'<p>{para(x)}</p>' for x in money.get('paras', []))
                      + (f'<table><tbody>{rows}</tbody></table>' if rows else '')
                      + (f'<p class="mnote">{E(money["note"])}</p>' if money.get('note') else '')
                      + f'<p class="mtry">Try it yourself: <a href="{CALC_PATH}">inflation calculator</a> · <a href="{CAGR_PATH}">growth-rate (CAGR) calculator</a></p></section>')
    photo = s.get('photo')
    photo_html = (f'<figure class="photo"><img src="{E(photo["url"])}" alt="{E(s["title"])}" loading="lazy"><figcaption>Photo: '
                  f'<a href="{E(photo["page"])}" rel="nofollow noopener">{E(photo.get("credit") or "Wikimedia Commons")}</a>, {E(photo.get("license", ""))}, via Wikimedia Commons</figcaption></figure>') if photo else ''
    checks = ''.join(f'<li>{E(x)}</li>' for x in s.get('check', []))
    nsrc = len(s['sources'])
    srcs = ''.join(f'<li>{f"<a href={chr(34)}{E(u)}{chr(34)} rel=\"nofollow noopener\">{E(t)}</a>" if u else E(t)}</li>' for t, u in s['sources'])
    faq = s.get('faq', [])
    faq_html = ('<section class="faq" id="faq"><h2>Questions people ask</h2>' + ''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in faq) + '</section>') if faq else ''
    has_reel = bool(s.get('reel')) and s['reel'] != PROFILE and reel_id(s['reel']) not in ARCHIVED_REELS
    reel_url = s['reel'] if has_reel else PROFILE
    frame = (ROOT / 'assets' / 'reels' / f'{s["slug"]}.jpg').exists()
    reel_html = '' if is_article else (
        '<section class="reel">'
        + (f'<a class="rthumb" href="{E(reel_url)}" rel="noopener" aria-label="Watch the video"><img src="/assets/reels/{s["slug"]}.jpg" alt="" loading="lazy" width="540" height="960"><span></span></a>' if frame else '')
        + f'<div><h2>{"Watch this story in under a minute" if has_reel else "Watch our story videos"}</h2><p>Animated, narrated, and sourced like this page.</p>'
        f'<p class="btns"><a class="btn" href="{E(reel_url)}" rel="noopener">{"Watch on Instagram" if has_reel else "Follow on Instagram"}</a><a class="btn ghost" href="{YOUTUBE}" rel="noopener">YouTube</a></p></div></section>')
    reelmini = '' if is_article or not frame else (
        f'<a class="reelmini" href="{E(reel_url)}" rel="noopener"><img src="/assets/reels/{s["slug"]}.jpg" alt="" loading="lazy" width="540" height="960">'
        f'<div><b>Watch the video</b><span>Under a minute, on Instagram</span></div></a>')
    nav = '<nav class="prevnext" aria-label="More stories">' + (f'<a class="prev" href="/stories/{prev_s["slug"]}/"><span>Previous story</span>{E(prev_s["title"])}</a>' if prev_s else '<span></span>') + \
          (f'<a class="next" href="/stories/{next_s["slug"]}/"><span>Next story</span>{E(next_s["title"])}</a>' if next_s else '<span></span>') + '</nav>'
    rel_html = ('<section class="related block"><div class="shead"><h2>Keep reading</h2><a class="all" href="/stories/">All stories</a></div>' + grid(related) + '</section>') if related else ''
    upd = f'<span>Updated {fmt_date(mod)}</span>' if mod != s['date'] else ''
    answer_html = (f'<div class="answer"><b>Quick answer</b>' + (f'<p class="aq">{E(s["answer_q"])}</p>' if s.get('answer_q') else '')
                   + f'<p>{E(s["answer"])}</p></div>') if s.get('answer') else ''
    body = f'''<main class="wrap">{crumbs_html([("Home", "/"), ("Stories", "/stories/"), (cname, f"/category/{c}/"), (s["title"], url)])}
<article>
<header class="story-head">{kicker(c, True)}<h1>{E(s["title"])}</h1><p class="lead">{E(s["summary"])}</p>{answer_html}
<div class="byline"><img src="/assets/logo.svg" alt="" width="42" height="42"><div><b><a href="{AUTHOR_PATH}" rel="author">{E(BYLINE)}</a></b><div class="facts"><time datetime="{s["date"]}">{fmt_date(s["date"])}</time>{upd}<span>{rt} min read</span><span>Checked against {nsrc} sources</span></div></div></div></header>
<figure class="cover">{img_tag(s, "(max-width:1240px) 100vw, 1200px", eager=True)}</figure>{f'<p class="figcap">{E(caption_of(s))}</p>' if caption_of(s) else ''}
<div class="layout"><div class="prose">
{toc_m}{intro}{secs}{photo_html}{money_html}{tl_html}
<section class="lesson" id="lesson"><small>The borrowed hindsight</small><p><span class="hl">{E(s["lesson"])}</span></p></section>
{f'<div class="check"><h3>{E(s.get("check_title", "Ask yourself"))}</h3><ul>{checks}</ul></div>' if checks else ''}
{reel_html}{share(url, s["title"])}{faq_html}
<section class="sources" id="sources"><h2>Sources</h2><ol>{srcs}</ol><p>Every fact on this page comes from the sources above, and every number is checked in at least two. General education, not personal or financial advice. Spotted an error? <a href="/contact/">Tell us</a> and we will correct it. Read our <a href="/editorial-standards/">editorial standards</a>.</p></section>
{nav}</div>
<aside class="aside"><div class="stick"><nav class="toc" aria-label="In this story"><h2>In this story</h2><ol>{toc_li}</ol></nav>{reelmini}
<div><h2>Share</h2><button class="btn ghost" type="button" data-copy="{E(SITE + url)}">Copy link</button></div></div></aside></div>
</article>{rel_html}{signup('story')}</main>'''
    img = SITE + thumb(s)
    art = {'@context': 'https://schema.org', '@type': 'Article', '@id': SITE + url + '#article', 'headline': s['title'][:110], 'description': s['summary'],
           'datePublished': f'{s["date"]}T19:30:00+05:30', 'dateModified': f'{mod}T19:30:00+05:30',
           'author': PERSON, 'publisher': ORG,
           'image': [{'@type': 'ImageObject', 'url': img, 'width': 1200, 'height': 675, 'caption': alt_of(s), 'contentUrl': img}], 'mainEntityOfPage': SITE + url, 'articleSection': cname, 'inLanguage': 'en', 'wordCount': words_of(s),
           'keywords': ', '.join(s.get('keywords', [])) or None, 'citation': [u for _, u in s['sources'] if u] or None,
           'abstract': s['lesson'], 'isAccessibleForFree': True,
           'speakable': {'@type': 'SpeakableSpecification', 'cssSelector': ['.story-head .lead', '.answer p', '.lesson p']}}
    if has_reel:
        art['video'] = {'@type': 'VideoObject', 'name': s['title'], 'description': s['summary'], 'thumbnailUrl': SITE + f'/assets/reels/{s["slug"]}.jpg',
                        'uploadDate': f'{s["date"]}T19:30:00+05:30', 'url': reel_url} if frame else None
    art = {k: v for k, v in art.items() if v is not None}
    ld = [art, crumbs([('Home', '/'), ('Stories', '/stories/'), (cname, f'/category/{c}/'), (s['title'], url)])]
    if faq:
        ld.append({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]})
    extra = (f'<meta property="article:published_time" content="{s["date"]}T19:30:00+05:30"><meta property="article:modified_time" content="{mod}T19:30:00+05:30">'
             f'<meta property="article:section" content="{E(cname)}">'
             f'<link rel="preload" as="image" href="{thumb(s)}" imagesrcset="{thumb(s, True)} 640w, {thumb(s)} 1200w" imagesizes="(max-width:1240px) 100vw, 1200px">')
    title = s.get('seo_title') or s['title']
    write(f'stories/{s["slug"]}/index.html', page(f'{title} | Borrowed Hindsight', s['summary'], body, url, ld=ld, og_type='article', extra=extra,
                                                  image=SITE + og_img(s), progress=True))


def chips_html(by_cat, current=None):
    out = '<nav class="chips" aria-label="Categories">' + (f'<a href="/stories/"{" aria-current=page" if current == "all" else ""}>All stories</a>')
    for c, v in CATS.items():
        if by_cat[c]:
            out += f'<a href="/category/{c}/"{" aria-current=page" if current == c else ""}><i class="dot" style="--c:{v[2]}"></i>{E(v[0])}<small>{len(by_cat[c])}</small></a>'
    return out + '</nav>'


def list_pages(base, items, title, desc, heading, head_html, crumb_items, below='', hide=False):
    total = max(1, math.ceil(len(items) / PER_PAGE))
    for n in range(1, total + 1):
        chunk = items[(n - 1) * PER_PAGE: n * PER_PAGE]
        path = base if n == 1 else f'{base}page/{n}/'
        body = (f'<main class="wrap">{crumbs_html(crumb_items)}<header class="phead"><h1>{E(heading)}{f" (page {n})" if n > 1 else ""}</h1>{head_html if n == 1 else ""}</header>'
                f'{grid(chunk)}{pager(base, n, total)}{below}</main>')
        ld = [crumbs([(n_, u) for n_, u in crumb_items]),
              {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': heading, 'url': SITE + path, 'description': desc, 'publisher': ORG,
               'mainEntity': {'@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': f'{SITE}/stories/{s["slug"]}/', 'name': s['title']} for i, s in enumerate(chunk)]}}]
        # page 2+ of a list: crawlable for links, kept out of the index (thin list pages)
        write(path.lstrip('/') + 'index.html', page(title + (f' (page {n})' if n > 1 else ''), desc, body, path, ld=ld, noindex=hide or n > 1, ads=n == 1 and not hide))


def main():
    global THUMBS
    shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir()
    shutil.copytree(ROOT / 'assets', OUT / 'assets', ignore=shutil.ignore_patterns('fonts')); shutil.copy(ROOT / 'CNAME', OUT / 'CNAME')
    stories = sorted([s for s in json.load(open(ROOT / 'stories.json')) if s['date'] <= TODAY], key=lambda s: (s['date'], s['slug']), reverse=True)
    # Site-side edits (search titles, quick answers) that bh-publisher must not overwrite: overrides.json, keyed by slug.
    ovr = json.load(open(ROOT / 'overrides.json')) if (ROOT / 'overrides.json').exists() else {}
    for s in stories:
        s.update(ovr.get(s['slug'], {}))
    THUMBS = make_images(stories)
    TITLES.update({s['slug']: s['title'] for s in stories})
    popular = sorted(stories, key=lambda s: (POP.get(s['slug'], 0), s['date']), reverse=True)   # most-watched first, then newest
    by_cat = {c: [s for s in popular if cat_of(s) == c] for c in CATS}
    LIVE_CATS.update(c for c in CATS if by_cat[c])
    COUNTS.update({c: len(v) for c, v in by_cat.items()})

    # ---------- home ----------
    feat = stories[0]; fc = cat_of(feat)
    latest = stories[1:7]
    shown = stories[:7]
    watched = [s for s in popular if POP.get(s['slug'], 0) > 0][:4]   # the top story stays in Most watched even when it is also featured (owner's request, 6 Nov)
    most_html = (f'<section class="block"><div class="shead"><h2>Most watched</h2><a class="all" href="{INSTAGRAM}" rel="noopener">Watch on Instagram</a></div>'
                 f'<p class="sdesc">The stories people watched most on Instagram. Read the full, sourced version here.</p>'
                 f'<div class="row">{"".join(card(s, summary=False) for s in watched)}</div></section>') if len(watched) >= 3 else ''
    wall = [s for s in stories if s.get('lesson')][:9]
    wall_html = ''.join(f'<a class="quote" href="/stories/{s["slug"]}/"><q>{E(s["lesson"])}</q><span>{E(s["title"])}</span></a>' for s in wall)
    rows = ''.join(
        f'<section class="block"><div class="shead"><h2><a href="/category/{c}/">{E(v[0])}</a></h2><a class="all" href="/category/{c}/">All {len(by_cat[c])}</a></div>'
        f'<p class="sdesc">{E(v[1])}</p><div class="row">{"".join(card(s, summary=False) for s in ([x for x in by_cat[c] if x not in shown] + [x for x in by_cat[c] if x in shown])[:4])}</div></section>'
        for c, v in CATS.items() if by_cat[c])
    mpick = [x for x in (next((s for s in stories if s['slug'] == k), None) for k in (
        'lijjat-papad-seven-women-80-rupees-story', 'how-infosys-started-with-10000-rupees-sudha-murty-1981', 'ronald-wayne-apple-800')) if x and x.get('money')]
    money_home = ('<section class="block mhome"><div class="shead"><h2>The money behind the stories</h2><a class="all" href="' + TOOLS_PATH + '">Calculators</a></div>'
                  f'<p class="sdesc">{E(BYLINE)}, an accounting professional, works out what the famous numbers really mean: in today\'s money, as yearly growth, and what they leave out.</p>'
                  '<div class="mgrid">' + ''.join(
                      f'<a class="mcard" href="/stories/{s["slug"]}/#money"><span class="mfig">{E(s["money"]["table"][0][1])}</span>'
                      f'<span class="mlab">{E(s["money"]["table"][0][0])}</span><b>{E(s["title"])}</b></a>' for s in mpick)
                  + f'<a class="mcard tool" href="{CALC_PATH}"><span class="mfig">₹ → today</span><span class="mlab">What is any amount from 1960 to 2025 worth now?</span><b>Rupee inflation calculator</b></a>'
                  + f'<a class="mcard tool" href="{CAGR_PATH}"><span class="mfig">% a year</span><span class="mlab">The steady growth rate between two numbers</span><b>CAGR calculator</b></a>'
                  + '</div></section>') if mpick else ''
    home = f'''<main>
<div class="wrap"><section class="intro"><div class="intro-row"><h1>True stories of people who started with almost nothing</h1>
<p class="lead">Founders, late starters, comebacks and record-breakers: the low point, the climb, the money behind it, and one line of hindsight you can borrow. Every story is researched, sourced and checked twice.</p></div></section>
<a class="feature" href="/stories/{feat["slug"]}/"><div class="pic">{img_tag(feat, "(max-width:900px) 100vw, 690px", eager=True)}</div>
<div>{kicker(fc)}<h2>{E(feat["title"])}</h2><p>{E(feat["summary"])}</p><blockquote><span class="hl">{E(feat["lesson"])}</span></blockquote><span class="more">Read the story ({mins(feat)} min)</span></div></a>
{money_home}{most_html}<section class="block"><div class="shead"><h2>Latest stories</h2><a class="all" href="/stories/">All {len(stories)} stories</a></div>{grid(latest)}</section></div>
<section class="wall"><div class="wrap"><h2>Lines worth borrowing</h2><p class="sub">Every story ends with one line of hindsight. Here are the latest. Tap one to read the story behind it.</p><div class="quotes">{wall_html}</div></div></section>
<div class="wrap"><section class="block"><div class="shead"><h2>Browse by category</h2></div>{chips_html(by_cat)}</section>
{rows}{signup('home')}</div></main>'''
    home_ld = [{'@context': 'https://schema.org', '@graph': [ORG, {'@type': 'WebSite', '@id': f'{SITE}/#site', 'url': SITE + '/', 'name': 'Borrowed Hindsight',
               'description': 'True, sourced stories of people who started small and built something big, with one lesson to borrow.', 'publisher': {'@id': f'{SITE}/#org'}, 'inLanguage': 'en',
               'potentialAction': {'@type': 'SearchAction', 'target': {'@type': 'EntryPoint', 'urlTemplate': f'{SITE}/search/?q={{search_term_string}}'}, 'query-input': 'required name=search_term_string'}},
               {'@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': f'{SITE}/stories/{s["slug"]}/'} for i, s in enumerate(stories[:20])]}]}]
    write('index.html', page('Borrowed Hindsight: true stories of people who started small', 'True, sourced stories of founders, late starters and comebacks, the money behind them worked out by an accountant, and free inflation and CAGR calculators.', home, ld=home_ld,
                             extra=f'<link rel="preload" as="image" href="{thumb(feat)}" imagesrcset="{thumb(feat, True)} 640w, {thumb(feat)} 1200w" imagesizes="(max-width:900px) 100vw, 690px">'))

    # ---------- all stories + categories ----------
    list_pages('/stories/', stories, 'All stories | Borrowed Hindsight', 'Every Borrowed Hindsight story: true, sourced stories of people who started small and built something big.',
               'All stories', f'<p class="lead">{len(stories)} true stories, newest first. Every one is researched, sourced and checked against at least two sources.</p>{chips_html(by_cat, "all")}',
               [('Home', '/'), ('Stories', '/stories/')])
    for c, (n, dsc, col, intro) in CATS.items():
        if by_cat[c]:
            head = (f'<div class="catintro">{"".join(f"<p>{E(p)}</p>" for p in intro)}</div>{chips_html(by_cat, c)}')
            list_pages(f'/category/{c}/', by_cat[c], f'{n}: true stories | Borrowed Hindsight', dsc if len(dsc) >= 90 else dsc + ' True, sourced stories, each with one lesson you can borrow.', n, head,
                       [('Home', '/'), ('Stories', '/stories/'), (n, f'/category/{c}/')], hide=len(by_cat[c]) < MIN_CAT_INDEX)

    # ---------- search ----------
    write('search.json', json.dumps([{'u': f'/stories/{s["slug"]}/', 't': s['title'], 's': s['summary'], 'c': CATS[cat_of(s)][0],
                                      'k': ' '.join(s.get('keywords', [])), 'i': thumb(s, True), 'm': mins(s)} for s in stories], ensure_ascii=False))
    search_body = f'''<main class="wrap">{crumbs_html([("Home", "/"), ("Search", "/search/")])}<header class="phead"><h1>Search stories</h1></header>
<form class="searchbox" role="search" action="/search/"><label class="sr" for="q">Search stories</label><input id="q" name="q" type="search" placeholder="Try a name, a company or an idea: Nirma, rejected, at 65" autocomplete="off"><button class="btn" type="submit">Search</button></form>
<p class="muted" id="status" aria-live="polite"></p><div class="grid" id="results"></div>{chips_html(by_cat)}</main>
<script>
(function(){{var q=document.getElementById('q'),res=document.getElementById('results'),st=document.getElementById('status'),data=null;
function esc(t){{return t.replace(/[&<>"]/g,function(c){{return{{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c];}});}}
function run(){{var v=q.value.trim().toLowerCase();if(!data)return;if(!v){{res.innerHTML='';st.textContent='';return;}}
var terms=v.split(/\\s+/),hits=data.filter(function(d){{var h=(d.t+' '+d.s+' '+d.c+' '+d.k).toLowerCase();return terms.every(function(t){{return h.indexOf(t)>-1;}});}});
st.textContent=hits.length?hits.length+(hits.length==1?' story':' stories')+' found':'No stories match "'+q.value+'". Try one word, like a name or a company.';
res.innerHTML=hits.map(function(d){{return '<a class="card" href="'+d.u+'"><div class="pic"><img src="'+d.i+'" alt="" width="640" height="360" loading="lazy"></div><span class="kicker">'+esc(d.c)+'</span><h3>'+esc(d.t)+'</h3><p>'+esc(d.s)+'</p><span class="rt">'+d.m+' min read</span></a>';}}).join('');}}
fetch('/search.json').then(function(r){{return r.json();}}).then(function(j){{data=j;var p=new URLSearchParams(location.search).get('q');if(p)q.value=p;run();}});
q.addEventListener('input',run);q.focus();}})();
</script>'''
    write('search/index.html', page('Search | Borrowed Hindsight', 'Search every Borrowed Hindsight story by name, company or idea.', search_body, '/search/', noindex=True, ads=False))

    # ---------- story pages: previous = older, next = newer ----------
    chrono = list(reversed(stories))
    for i, s in enumerate(chrono):
        prev_s = chrono[i - 1] if i > 0 else None
        next_s = chrono[i + 1] if i + 1 < len(chrono) else None
        same = [r for r in popular if r is not s and cat_of(r) == cat_of(s)]
        other = [r for r in popular if r is not s and cat_of(r) != cat_of(s)]
        story_page(s, prev_s, next_s, (same[:2] + other[:1] + same[2:])[:3])

    # ---------- static pages ----------
    about = f'''<h1>About Borrowed Hindsight</h1>
<p class="lead">They started with almost nothing. Their hindsight is yours to borrow.</p>
<p>Borrowed Hindsight is an independent publisher of true stories about people who started with very little, were told no, or started late, and built something remarkable anyway. Each story covers the low point, the choice, the climb, and one line of hindsight you can use in your own life.</p>
<p>We publish short animated videos on <a href="{INSTAGRAM}">Instagram</a>, <a href="{YOUTUBE}">YouTube</a> and <a href="{FACEBOOK}">Facebook</a>, and the full, sourced version of every story here. We are based in New Delhi, India, and write for readers everywhere.</p>
<h2>The money behind each story</h2><p>Borrowed Hindsight is run by <a href="{AUTHOR_PATH}">Manisha Aggarwal</a>, an accounting professional. Where a story involves money, such as a first loan, a sale price or a company's growth, Manisha adds a section called "The money behind it". It converts old amounts into today's money using official inflation data, works out growth rates, and points out what headline numbers leave out, such as turnover versus profit, or cash versus shares in a deal. You can run the same sums yourself with our free <a href="{TOOLS_PATH}">calculators</a>.</p>
<h2>How we research</h2><p>Every story is built from primary or reputable sources: company and official records, major newspapers and magazines, books, peer-reviewed studies and official statistics. Every number is checked in at least two independent sources, and each page lists its sources. If a popular story or statistic can't be traced to a real source, we say so instead of repeating it. Read our full <a href="/editorial-standards/">editorial standards</a>.</p>
<h2>How we use AI</h2><p>AI tools help us research, draft and narrate. People choose every story, and every fact is checked against its sources before it is published. Our short videos are animated and narrated with an AI voice. We never create fake photos of real people.</p>
<h2>What we don't do</h2><p>We don't give personal financial, investment, legal or career advice, and we don't recommend products, stocks or apps. We don't publish political or religious content, and we never mock anyone. We judge decisions by what was known at the time, not by how they turned out.</p>
<h2>Who publishes this site</h2><p>Borrowed Hindsight is owned, written and published by <a href="{AUTHOR_PATH}">Manisha Aggarwal</a>, an accounting professional in New Delhi, India, who runs it as a hobby: to keep learning, to spread awareness, and to share stories that motivate. Every story follows our <a href="/editorial-standards/">editorial standards</a>.</p>
<h2>Contact</h2><p>Corrections, story suggestions or partnership questions: email <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a> or see our <a href="/contact/">contact page</a>.</p>'''
    write('about/index.html', page('About Borrowed Hindsight: who we are and how we research', 'Who we are, how every Borrowed Hindsight story is researched and sourced, and how to reach us.',
          f'<main class="wrap narrow legal">{crumbs_html([("Home", "/"), ("About", "/about/")])}{about}</main>', '/about/', ld=[{'@context': 'https://schema.org', '@type': 'AboutPage', 'url': SITE + '/about/', 'about': ORG, 'publisher': ORG}]))

    # ---------- rupee inflation calculator ----------
    cpi_d = json.load(open(ROOT / 'data' / 'india_cpi.json'))
    CPI = {int(k): v for k, v in cpi_d['cpi'].items()}
    y0, y1 = min(CPI), max(CPI)
    def worth(a, fy, ty): return a * CPI[ty] / CPI[fy]
    def inr(x):
        x = round(x)
        s = str(x); head, tail = s[:-3], s[-3:]
        while len(head) > 2: tail = head[-2:] + ',' + tail; head = head[:-2]
        return '₹' + (head + ',' + tail if head else tail)
    avg = (CPI[y1] / CPI[y0]) ** (1 / (y1 - y0)) - 1
    decade_rows = ''.join(f'<tr><th scope="row">₹100 in {y}</th><td>{inr(worth(100, y, y1))}</td><td>{CPI[y1] / CPI[y]:.1f}×</td></tr>'
                          for y in range(1960, y1, 5))
    lj = {x['slug'] for x in stories}
    lij = '/stories/lijjat-papad-seven-women-80-rupees-story/' if 'lijjat-papad-seven-women-80-rupees-story' in lj else None
    opts = ''.join(f'<option{" selected" if y == 1990 else ""}>{y}</option>' for y in range(y0, y1 + 1))
    opts2 = ''.join(f'<option{" selected" if y == y1 else ""}>{y}</option>' for y in range(y0, y1 + 1))
    v1990 = worth(100, 1990, y1)
    faqs = [
        (f'What is ₹100 from 1960 worth today?', f'About {inr(worth(100, 1960, y1))} in {y1} money. Consumer prices in India rose about {CPI[y1] / CPI[1960]:.0f} times between 1960 and {y1}, based on the World Bank consumer price index.'),
        (f'What is ₹100 from 1990 worth today?', f'About {inr(v1990)} in {y1} money. Prices rose about {CPI[y1] / CPI[1990]:.1f} times between 1990 and {y1}.'),
        (f'What has India\'s average inflation rate been since 1960?', f'About {avg * 100:.1f}% a year on average from 1960 to {y1}, measured by the consumer price index. Some decades were much higher, and recent years have been lower.'),
        ('Can I use this to value gold, property or shares?', 'No. This calculator measures the general cost of living (a basket of consumer goods and services). Gold, property and shares have their own price histories and can rise much faster or slower than general inflation.'),
        ('Where does the data come from?', f'From the World Bank\'s consumer price index for India (series FP.CPI.TOTL, {cpi_d["base"]}), covering {y0} to {y1}. It is based on India\'s official consumer price statistics. Values are yearly averages, so results are approximate.'),
    ]
    faq_c = ''.join(f'<h3>{E(q)}</h3><p>{E(a)}</p>' for q, a in faqs)
    calc_body = f"""<h1>Rupee inflation calculator</h1>
<p class="lead">See what any rupee amount from {y0} to {y1} is worth in another year.</p>
<p class="mby">By <a href="{AUTHOR_PATH}" rel="author">{E(BYLINE)}</a>, accounting professional · Data: World Bank consumer price index for India, {y0}–{y1}</p>
<form class="calc" id="calc" onsubmit="return false">
<label>Amount (₹)<input id="amt" type="number" inputmode="decimal" min="0" step="any" value="100"></label>
<label>From year<select id="fy">{opts}</select></label>
<label>To year<select id="ty">{opts2}</select></label>
<output id="out" for="amt fy ty" aria-live="polite"><b>₹100 in 1990 is worth about {inr(v1990)} in {y1}.</b><span>Prices rose {CPI[y1] / CPI[1990]:.1f} times, an average of {((CPI[y1] / CPI[1990]) ** (1 / (y1 - 1990)) - 1) * 100:.1f}% a year.</span></output>
</form>
<script>(function(){{var C={json.dumps(CPI)};var f0=new Intl.NumberFormat('en-IN',{{maximumFractionDigits:0}}),f2=new Intl.NumberFormat('en-IN',{{minimumFractionDigits:2,maximumFractionDigits:2}});function f_(v){{return v<100?f2.format(v):f0.format(v);}}var f={{format:f_}};
function g(i){{return document.getElementById(i);}}
function run(){{var a=parseFloat(g('amt').value),x=+g('fy').value,y=+g('ty').value,o=g('out');
if(!(a>=0)){{o.innerHTML='<b>Enter an amount.</b>';return;}}
var v=a*C[y]/C[x],r=C[y]/C[x],n=Math.abs(y-x),avg=n?(Math.pow(Math.max(r,1/r),1/n)-1)*100:0;
o.innerHTML='<b>₹'+f.format(a)+' in '+x+' is worth about ₹'+f.format(v)+' in '+y+'.</b><span>'+(x===y?'Same year, no change.':r>=1?'Prices rose '+r.toFixed(r<10?2:1)+' times, an average of '+avg.toFixed(1)+'% a year.':'Prices in '+y+' were '+(1/r).toFixed(1/r<10?2:1)+' times lower than in '+x+'.')+'</span>';}}
['amt','fy','ty'].forEach(function(i){{g(i).addEventListener('input',run);}});}})();</script>
<h2>What ₹100 from each year is worth in {y1}</h2>
<div class="tablewrap"><table class="ctable"><thead><tr><th>Amount</th><th>Worth in {y1}</th><th>Prices rose</th></tr></thead><tbody>{decade_rows}</tbody></table></div>
<h2>How this calculator works</h2>
<p>It compares India's consumer price index in the two years you choose. If the index is ten times higher in the later year, ₹100 then buys roughly what ₹1,000 buys later. The index tracks the average price of everyday goods and services, such as food, housing, clothing and transport.</p>
<p>India's prices rose about {CPI[y1] / CPI[y0]:.0f} times between {y0} and {y1}, an average of about {avg * 100:.1f}% a year. That is why old salaries, prices and business figures look tiny today, and why money kept as cash slowly buys less each year.</p>
<h2>Why we built it</h2>
<p>Many of our stories start with a small sum: a ₹80 loan, a ₹10,000 investment, a first salary. Those numbers only make sense when you see them in today's money.{f' In the <a href="{lij}">Lijjat Papad story</a>, for example, the ₹80 the founders borrowed in 1959 is worth only about {inr(worth(80, 1960, y1))} today.' if lij else ''}</p>
<h2>Limits to keep in mind</h2>
<p>Results are approximate. The index uses yearly averages and a national basket of goods, so your own costs, city or lifestyle may have risen faster or slower. The earliest year available is {y0}. This is general education, not financial advice.</p>
<h2>Questions people ask</h2>{faq_c}
<p class="mnote">Source: <a href="{cpi_d['source_url']}" rel="noopener">{E(cpi_d['source'])}</a>, retrieved {cpi_d['retrieved']}.</p>"""
    calc_desc = f'Free rupee inflation calculator for India: see what any amount from {y0} to {y1} is worth today, using official consumer price data. ₹100 in 1990 = {inr(v1990)} in {y1}.'
    write(CALC_PATH.strip('/') + '/index.html', page(f'Rupee inflation calculator: value of ₹ from {y0} to {y1}', calc_desc,
          f'<main class="wrap narrow legal calcpage">{crumbs_html([("Home", "/"), ("Calculators", TOOLS_PATH), ("Rupee inflation calculator", CALC_PATH)])}{calc_body}</main>', CALC_PATH,
          ld=[{'@context': 'https://schema.org', '@type': 'WebApplication', 'name': 'Rupee inflation calculator', 'url': SITE + CALC_PATH, 'applicationCategory': 'FinanceApplication',
               'operatingSystem': 'Any', 'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'INR'}, 'author': PERSON, 'publisher': ORG, 'description': calc_desc},
              {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]},
              crumbs([('Home', '/'), ('Calculators', TOOLS_PATH), ('Rupee inflation calculator', CALC_PATH)])]))

    # ---------- CAGR calculator ----------
    def pct(x): return f'{x * 100:.1f}%'
    ex = []
    if 'lijjat-papad-seven-women-80-rupees-story' in lj: ex.append(('/stories/lijjat-papad-seven-women-80-rupees-story/', 'Lijjat Papad', 'sales from just over ₹6,000 in its first year to about ₹1,600 crore', 6000, 1600e7, 63))
    if 'how-infosys-started-with-10000-rupees-sudha-murty-1981' in lj: ex.append(('/stories/how-infosys-started-with-10000-rupees-sudha-murty-1981/', 'Infosys', 'revenue from US$100 million in 1999 to about US$20 billion', 100e6, 20e9, 26))
    ex_html = ''.join(f'<li><a href="{u}">{E(n)}</a>: {E(d)} over {y} years is about <b>{((b / a) ** (1 / y) - 1) * 100:.0f}% a year</b>.</li>' for u, n, d, a, b, y in ex)
    grid_rows = ''.join('<tr><th scope="row">' + f'{r}% a year' + '</th>' + ''.join(f'<td>{inr(100000 * (1 + r / 100) ** n)}</td>' for n in (5, 10, 20, 30)) + '</tr>' for r in (6, 8, 10, 12, 15, 20))
    cagr_faqs = [
        ('What is CAGR?', 'CAGR, or compound annual growth rate, is the steady yearly rate that would take a value from its starting amount to its ending amount over a given number of years. It smooths out good and bad years into one average.'),
        ('What is the CAGR formula?', 'CAGR = (ending value ÷ starting value)^(1 ÷ number of years) − 1. For example, ₹1 lakh growing to ₹2 lakh in 5 years is (2)^(1/5) − 1, about 14.9% a year.'),
        ('How is CAGR different from average return?', 'A simple average adds each year\'s growth and divides by the number of years, which overstates results when growth goes up and down. CAGR uses only the start, the end and the time, so it shows the rate that really connects them.'),
        ('How long does it take money to double?', 'A quick rule is to divide 72 by the yearly growth rate. At 8% a year, money roughly doubles in 9 years; at 12%, in about 6 years.'),
        ('Can CAGR predict future growth?', 'No. CAGR describes the past. It says nothing about what will happen next, and it hides the ups and downs along the way. This calculator is for education, not investment advice.'),
    ]
    cagr_faq_c = ''.join(f'<h3>{E(q)}</h3><p>{E(a)}</p>' for q, a in cagr_faqs)
    v0 = ((200000 / 100000) ** (1 / 5) - 1)
    cagr_body = f"""<h1>CAGR calculator</h1>
<p class="lead">Find the average yearly growth rate between a starting value and an ending value.</p>
<p class="mby">By <a href="{AUTHOR_PATH}" rel="author">{E(BYLINE)}</a>, accounting professional</p>
<form class="calc" id="calc" onsubmit="return false">
<label>Starting value (₹)<input id="sv" type="number" inputmode="decimal" min="0" step="any" value="100000"></label>
<label>Ending value (₹)<input id="ev" type="number" inputmode="decimal" min="0" step="any" value="200000"></label>
<label>Number of years<input id="ny" type="number" inputmode="decimal" min="0" step="any" value="5"></label>
<output id="out" for="sv ev ny" aria-live="polite"><b>CAGR: about {pct(v0)} a year.</b><span>The value grew 2.0 times in 5 years.</span></output>
</form>
<script>(function(){{function g(i){{return document.getElementById(i);}}
function run(){{var a=parseFloat(g('sv').value),b=parseFloat(g('ev').value),n=parseFloat(g('ny').value),o=g('out');
if(!(a>0)||!(b>=0)||!(n>0)){{o.innerHTML='<b>Enter a starting value above 0, an ending value and the number of years.</b>';return;}}
var r=Math.pow(b/a,1/n)-1,m=b/a;
o.innerHTML='<b>CAGR: about '+(r*100).toFixed(1)+'% a year.</b><span>The value '+(m>=1?'grew ':'shrank to ')+(m<10?m.toFixed(2):new Intl.NumberFormat('en-IN',{{maximumFractionDigits:0}}).format(m))+' times'+(m>=1?'':' its start')+' in '+n+' year'+(n==1?'':'s')+'.</span>';}}
['sv','ev','ny'].forEach(function(i){{g(i).addEventListener('input',run);}});}})();</script>
<h2>What ₹1 lakh grows to at a steady rate</h2>
<div class="tablewrap"><table class="ctable"><thead><tr><th>Growth rate</th><th>5 years</th><th>10 years</th><th>20 years</th><th>30 years</th></tr></thead><tbody>{grid_rows}</tbody></table></div>
<h2>How CAGR works</h2>
<p>CAGR is the single yearly rate that would turn your starting value into your ending value over the years you enter, if growth had been perfectly steady. The formula is: <b>(ending value ÷ starting value)<sup>1 ÷ years</sup> − 1</b>.</p>
<p>Real growth is never that smooth. A business might grow 40% one year and shrink the next. CAGR ignores that path and asks only one question: what steady rate connects the start and the end? That makes it the fairest way to compare growth over different lengths of time.</p>
<h2>Examples from our stories</h2><ul>{ex_html}</ul>
<p>Compare those with the table above. Even 15% a year turns ₹1 lakh into about ₹66 lakh over 30 years, which is why decades of steady growth matter more than any single good year.</p>
<h2>Growth and inflation</h2>
<p>A CAGR in rupees includes inflation. To see real growth, compare it with the rise in prices over the same years using our <a href="{CALC_PATH}">rupee inflation calculator</a>. Indian prices rose about {avg * 100:.1f}% a year on average between {y0} and {y1}.</p>
<h2>Questions people ask</h2>{cagr_faq_c}
<p class="mnote">General education, not investment advice. Past growth does not predict future results.</p>"""
    cagr_desc = 'Free CAGR calculator: find the compound annual growth rate between any starting and ending value, with the formula, a growth table and real examples.'
    write(CAGR_PATH.strip('/') + '/index.html', page('CAGR calculator: compound annual growth rate, with examples', cagr_desc,
          f'<main class="wrap narrow legal calcpage">{crumbs_html([("Home", "/"), ("Calculators", TOOLS_PATH), ("CAGR calculator", CAGR_PATH)])}{cagr_body}</main>', CAGR_PATH,
          ld=[{'@context': 'https://schema.org', '@type': 'WebApplication', 'name': 'CAGR calculator', 'url': SITE + CAGR_PATH, 'applicationCategory': 'FinanceApplication',
               'operatingSystem': 'Any', 'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'INR'}, 'author': PERSON, 'publisher': ORG, 'description': cagr_desc},
              {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in cagr_faqs]},
              crumbs([('Home', '/'), ('Calculators', TOOLS_PATH), ('CAGR calculator', CAGR_PATH)])]))

    # ---------- goal SIP planner ----------
    def sip_needed(fv, n, r, s=0.0):
        mr = (1 + r) ** (1 / 12) - 1
        f = sum((1 + s) ** (j // 12) * (1 + mr) ** (n * 12 - j) for j in range(n * 12))
        return fv / f
    def lakh_cr(x):
        return f'₹{x / 1e7:.2f} crore' if x >= 1e7 else f'₹{x / 1e5:.1f} lakh'
    gy = int(TODAY[:4])
    ex_n = 2024 + 18 - gy
    ex_fv = 1e7 * 1.10 ** ex_n
    ex_sip, ex_sip_up = sip_needed(ex_fv, ex_n, 0.10), sip_needed(ex_fv, ex_n, 0.10, 0.10)
    goal_rates = [('Child\'s education (school fees, college, professional courses)', '8% to 10%'), ('Child\'s marriage', '6% to 8%'),
                  ('Buying a home', '6% to 8%'), ('Buying a car', '5% to 6%'), ('Monthly household expenses (retirement)', '6%')]
    goal_rate_rows = ''.join(f'<tr><th scope="row">{E(a)}</th><td>{b}</td></tr>' for a, b in goal_rates)
    goal_faqs = [
        ('How much SIP do I need for my child\'s education?', f'Start with today\'s cost of the course, then grow it by education inflation until the year your child will start it. For example, a ₹1 crore commercial pilot course for a child born in 2024 who starts at 18 would cost about {lakh_cr(ex_fv)} in {2024 + 18} at 10% a year. At a 10% return, that needs a monthly SIP of about {inr(ex_sip)} from {gy}, or about {inr(ex_sip_up)} to begin with if you raise the SIP by 10% every year.'),
        ('How do I decide what my child\'s wedding will cost?', 'Imagine your child is getting married today. Think of a wedding you attended whose scale and budget you liked, and estimate what a wedding like that would cost this year, including the venue, food, clothes, jewellery and gifts. Enter that amount; the planner adds the price rise until the wedding year.'),
        ('Why does the planner fund the earliest goal first?', 'The money you have already saved is used for goals in date order, the way most families spend it. Whatever is left after one goal stays invested and carries forward to the next. Any gap is covered by a separate SIP that runs only until that goal\'s year.'),
        ('How is the retirement or financial independence amount worked out?', 'Your monthly expenses today are grown by inflation until the year you want to stop working. The planner then finds the fund that can pay that amount every month, rising with inflation, for as many years as you choose, while the rest of the money keeps earning the return you set for those years.'),
        ('What is a step-up SIP?', 'A SIP that you raise by a fixed percentage every year, usually in line with your salary. Starting smaller and stepping up 10% a year can reach the same goal with a much lower first instalment.'),
        ('What return should I assume?', 'Use a rate you can defend, not the best year you remember. Many planners use 10% to 12% a year for long-term equity funds and 6% to 7% for debt. Lower the rate for goals that are only a few years away, because that money should not be in shares.'),
        ('Is this financial advice?', 'No. This planner is for general education. Returns are never guaranteed, and real costs can rise faster or slower than you assume. Speak to a SEBI-registered investment adviser before you invest.'),
    ]
    goal_faq_c = ''.join(f'<h3>{E(q)}</h3><p>{E(a)}</p>' for q, a in goal_faqs)
    goal_body = f"""<section class="wz-hero"><p class="wz-kick">Goal SIP planner</p>
<h1>Plan your future <mark>from here.</mark></h1>
<p>Your home. Your children's dreams. The day you stop working because you want to, not because you have to. Every one of them already has a price tag. Find out what it is, and what to save from this month to pay it.</p>
<button type="button" class="wz-btn big" data-start>Start planning →</button>
<p class="wz-small">About 5 minutes · Free · Nothing you type leaves your browser</p></section>
<div id="gw" class="wz" aria-live="polite"><noscript><p>This planner needs JavaScript turned on.</p></noscript></div>
<script>{GOAL_JS}</script>
<p class="mby">Planner by <a href="{AUTHOR_PATH}" rel="author">{E(BYLINE)}</a>, accounting professional</p>
<h2>How the planner works</h2>
<ol>
<li><b>Cost on the day.</b> Each goal's cost today is grown by its own price rise until the year it is needed: cost today × (1 + price rise)<sup>years left</sup>.</li>
<li><b>Your savings go first.</b> The money you have already invested keeps earning your expected return and is used for goals in date order. What is left after one goal carries forward to the next.</li>
<li><b>A SIP for each gap.</b> Whatever your savings cannot cover is filled by a monthly SIP that runs from now until that goal's year. When a goal is reached, its SIP stops, so your total SIP falls over time.</li>
<li><b>Two ways to pay.</b> A <b>fixed SIP</b> stays the same every month until the goal. A <b>step-up SIP</b> starts lower and rises by the percentage you choose every year, which suits a growing salary. Both reach the same amount.</li>
<li><b>Fees over several years.</b> For a course paid over, say, four years, the fees are split evenly across those years and each year's share grows with inflation until it is due.</li>
<li><b>Retirement.</b> Your monthly expenses today are grown by inflation until the age you stop working. The planner then works out the fund that pays those expenses, still rising with inflation, until the age you plan for.</li>
</ol>
<h2>Example: a pilot course and a ₹1 crore price tag</h2>
<p>A commercial pilot course costs about ₹1 crore today. For a child born in 2024 who starts training after Class 12, at 18, the money is needed in {2024 + 18}, {ex_n} years from now. If course fees rise 10% a year, the same course will cost about <b>{lakh_cr(ex_fv)}</b> by then.</p>
<p>At a 10% yearly return, a monthly SIP of about <b>{inr(ex_sip)}</b> started in {gy} gets there. If you raise the SIP by 10% every year, you can start at about <b>{inr(ex_sip_up)}</b> a month instead.</p>
<h2>Price rise rates people often use</h2>
<p>These are planning assumptions, not official figures. Change them in the planner to suit your own goals.</p>
<div class="tablewrap"><table class="ctable"><thead><tr><th>Goal</th><th>Price rise a year</th></tr></thead><tbody>{goal_rate_rows}</tbody></table></div>
<p>India's general consumer prices rose about {avg * 100:.1f}% a year on average between {y0} and {y1} (see our <a href="{CALC_PATH}">rupee inflation calculator</a>). Education and medical costs have usually risen faster than that.</p>
<h2>Questions people ask</h2>{goal_faq_c}
<p class="mnote">General education, not investment advice. Returns are not guaranteed and the results are estimates based on the rates you enter. Your plan stays in your browser; nothing you type is sent to us.</p>"""
    goal_desc = 'Free goal SIP planner for Indian families: see what your child\'s education and marriage, a home, a car and retirement will cost in the year you need them, and the monthly SIP to start today.'
    write(GOAL_PATH.strip('/') + '/index.html', page('Goal SIP planner: child education, marriage, home and retirement', goal_desc,
          f'<main class="wrap narrow legal calcpage">{crumbs_html([("Home", "/"), ("Calculators", TOOLS_PATH), ("Goal SIP planner", GOAL_PATH)])}{goal_body}</main>', GOAL_PATH,
          ld=[{'@context': 'https://schema.org', '@type': 'WebApplication', 'name': 'Goal SIP planner', 'url': SITE + GOAL_PATH, 'applicationCategory': 'FinanceApplication',
               'operatingSystem': 'Any', 'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'INR'}, 'author': PERSON, 'publisher': ORG, 'description': goal_desc},
              {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in goal_faqs]},
              crumbs([('Home', '/'), ('Calculators', TOOLS_PATH), ('Goal SIP planner', GOAL_PATH)])]))

    # ---------- tools index ----------
    tools_body = f"""<h1>Money calculators</h1>
<p class="lead">Simple, free calculators that put the numbers in our stories into perspective.</p>
<p class="mby">By <a href="{AUTHOR_PATH}" rel="author">{E(BYLINE)}</a>, accounting professional</p>
<h2><a href="{CALC_PATH}">Rupee inflation calculator</a></h2><p>What is a rupee amount from any year between {y0} and {y1} worth in another year? Uses the World Bank consumer price index for India.</p>
<h2><a href="{GOAL_PATH}">Goal SIP planner</a></h2><p>List your goals in today's prices, from your children's education and marriage to a home and retirement. See what each will cost on the day and the monthly SIP to start now.</p>
<h2><a href="{CAGR_PATH}">CAGR calculator</a></h2><p>Find the average yearly growth rate between a starting value and an ending value, with a growth table and examples.</p>"""
    write(TOOLS_PATH.strip('/') + '/index.html', page('Money calculators: goal SIP, inflation and CAGR | Borrowed Hindsight', 'Free money calculators from Borrowed Hindsight: a goal SIP planner for family goals, a rupee inflation calculator (1960 to 2025) and a CAGR growth-rate calculator.',
          f'<main class="wrap narrow legal calcpage">{crumbs_html([("Home", "/"), ("Calculators", TOOLS_PATH)])}{tools_body}</main>', TOOLS_PATH,
          ld=[crumbs([('Home', '/'), ('Calculators', TOOLS_PATH)])]))

    n_auth = len(stories)
    author = f'''<h1>Manisha Aggarwal</h1>
<p class="lead">Owner and author of Borrowed Hindsight.</p>
<p>{E(AUTHOR_BIO)}</p>
<p>Manisha chooses every story on this site and is responsible for what is published. Each story is checked against its sources, following our <a href="/editorial-standards/">editorial standards</a>, and lists those sources at the end.</p>
<h2>Stories by Manisha</h2><p>{n_auth} stories so far, from founders and late starters to comebacks and record-breakers. <a href="/stories/">Read all stories</a>.</p>
<h2>Contact</h2><p>Email <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a> with corrections, story ideas or questions.</p>'''
    write('author/manisha-aggarwal/index.html', page('Manisha Aggarwal, author of Borrowed Hindsight', AUTHOR_BIO,
          f'<main class="wrap narrow legal">{crumbs_html([("Home", "/"), ("About", "/about/"), ("Manisha Aggarwal", AUTHOR_PATH)])}{author}</main>', AUTHOR_PATH,
          ld=[{'@context': 'https://schema.org', '@type': 'ProfilePage', 'url': SITE + AUTHOR_PATH, 'mainEntity': PERSON}]))

    contact = f'''<h1>Contact us</h1>
<p class="lead">We read every message. The fastest way to reach us is email.</p>
<p class="big-mail"><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
<h2>What to write to us about</h2><ul>
<li><b>Corrections.</b> Found a mistake? Send the page link and what's wrong, with a source if you have one. We check every report and correct confirmed errors, usually within 48 hours. See our <a href="/editorial-standards/#corrections">corrections policy</a>.</li>
<li><b>Story suggestions.</b> Know a true story of someone who started small or came back from a setback? Tell us, with a link to where it was reported.</li>
<li><b>Partnerships and press.</b> Brands, publishers and educators: tell us what you have in mind.</li>
<li><b>Privacy requests.</b> See our <a href="/privacy/">privacy policy</a>.</li></ul>
<h2>Find us elsewhere</h2><p><a href="{INSTAGRAM}">Instagram</a>, <a href="{YOUTUBE}">YouTube</a>, <a href="{FACEBOOK}">Facebook</a>.</p>
<p class="note">We usually reply within two working days (India time). We never ask for passwords, payments or personal documents.</p>'''
    write('contact/index.html', page('Contact Borrowed Hindsight', 'How to reach Borrowed Hindsight for corrections, story suggestions, partnerships and privacy requests.',
          f'<main class="wrap narrow legal">{crumbs_html([("Home", "/"), ("Contact", "/contact/")])}{contact}</main>', '/contact/',
          ld=[{'@context': 'https://schema.org', '@type': 'ContactPage', 'url': SITE + '/contact/', 'publisher': ORG}], ads=False))

    corr = json.load(open(ROOT / 'corrections.json')) if (ROOT / 'corrections.json').exists() else []
    corr_html = ('<ul class="corrections">' + ''.join(f'<li><b>{E(c["date"])}</b>: <a href="/stories/{E(c["slug"])}/">{E(c.get("title", c["slug"]))}</a>. {E(c["what"])}</li>' for c in corr) + '</ul>') if corr else '<p>No corrections so far. When we correct a published fact, it is listed here with the date.</p>'
    ed = f'''<h1>Editorial standards</h1>
<p class="lead">Our promise: every story is true, every number is checked, and every source is shown.</p>
<h2>What we publish</h2><p>True stories of people and companies that started small, faced rejection or setbacks, and built something remarkable, plus researched roundups of such stories. Each story ends with one practical lesson (the "borrowed hindsight") and a question to ask yourself.</p>
<h2>How we check facts</h2><ul>
<li>We use primary and reputable sources: official and company records, major newspapers and magazines, books, peer-reviewed research and official statistics.</li>
<li>Every number, date and claim is checked in at least two independent sources. When good sources disagree, we say so.</li>
<li>We only quote people when a reputable source published the quote. We never invent dialogue.</li>
<li>Wikipedia can point us to sources, but it is never our only source.</li>
<li>Every page lists the sources we used, with links, and shows when it was last updated.</li></ul>
<h2>How we use AI</h2><p>AI tools help us research, draft and narrate. People choose every story and are responsible for what we publish, and every fact is checked against its sources before publishing. Our videos are animated and narrated with an AI voice. We never use AI to create fake photos of real people.</p>
<h2>Images</h2><p>We use our own illustrations and video frames, or photos with free licences (such as Creative Commons) credited to their authors.</p>
<h2>What we don't publish</h2><p>No political or religious content, nothing that mocks people or groups, no tragedy for entertainment, and no personal financial, investment, legal or career advice. We judge decisions by what was known at the time.</p>
<h2>Independence and advertising</h2><p>This site shows ads served by Google AdSense. Advertisers have no say in what we write, and we don't accept payment to feature people or companies. If we ever publish sponsored content, it will be clearly labelled.</p>
<h2 id="corrections">Corrections</h2><p>If we get something wrong, we fix it and record the change here. Report an error by emailing <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>{corr_html}'''
    write('editorial-standards/index.html', page('Editorial standards | Borrowed Hindsight', 'How Borrowed Hindsight researches, checks and corrects its stories, how we use AI, and how advertising works on this site.',
          f'<main class="wrap narrow legal">{crumbs_html([("Home", "/"), ("Editorial standards", "/editorial-standards/")])}{ed}</main>', '/editorial-standards/', ads=False))

    for name in ('privacy', 'terms'):
        body = (ROOT / f'{name}.html').read_text().replace('<!--SITE-DATA-->', site_data())
        title = 'Privacy policy' if name == 'privacy' else 'Terms of use'
        write(f'{name}/index.html', page(f'{title} | Borrowed Hindsight', f'{title} for borrowedhindsight.org and the Borrowed Hindsight channels.',
                                         f'<main class="wrap narrow legal">{crumbs_html([("Home", "/"), (title, f"/{name}/")])}{body}</main>', f'/{name}/', ads=False))
    write('404.html', page('Page not found | Borrowed Hindsight', 'Page not found',
          f'<main class="wrap"><header class="phead"><h1>We couldn\'t find that page</h1><p class="lead">The link may be old or mistyped. Search the stories, or start with the latest ones below.</p>'
          f'<p class="btns"><a class="btn" href="/search/">Search stories</a><a class="btn ghost" href="/stories/">All stories</a></p></header>{grid(stories[:3])}</main>', noindex=True, ads=False))

    # ---------- feeds and machine-readable files ----------
    newest = stories[0]['date'] if stories else TODAY
    urls = [('/', newest, '1.0'), ('/stories/', newest, '0.9'), ('/about/', None, '0.5'), ('/contact/', None, '0.4'), ('/editorial-standards/', None, '0.4'),
            ('/privacy/', None, '0.2'), ('/terms/', None, '0.2'), (AUTHOR_PATH, None, '0.4'), (CALC_PATH, None, '0.8'), (CAGR_PATH, None, '0.8'), (GOAL_PATH, None, '0.8'), (TOOLS_PATH, None, '0.6')] + \
           [(f'/category/{c}/', by_cat[c][0]['date'], '0.7') for c in CATS if len(by_cat[c]) >= MIN_CAT_INDEX] + \
           [(f'/stories/{s["slug"]}/', s.get('updated', s['date']), '0.8') for s in stories]
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">' + ''.join(
        f'<url><loc>{SITE}{u}</loc>{f"<lastmod>{m}</lastmod>" if m else ""}<priority>{pr}</priority>'
        + (f'<image:image><image:loc>{SITE}/assets/thumbs/{u.split("/")[2]}.jpg</image:loc></image:image>' if u.startswith('/stories/') and len(u) > 9 and u.split('/')[2] in THUMBS else '')
        + '</url>' for u, m, pr in urls) + '</urlset>')
    if ADSENSE_CLIENT:
        write('ads.txt', f'google.com, {ADSENSE_CLIENT.replace("ca-", "")}, DIRECT, f08c47fec0942fa0\n')
    # Moved pages: Google had seen these URLs, so send visitors and Google to the page that replaced them.
    for old, new in REDIRECTS.items():
        t = f'{SITE}/stories/{new}/'
        write(f'stories/{old}/index.html', f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Moved: Borrowed Hindsight</title>'
              f'<link rel="canonical" href="{t}"><meta http-equiv="refresh" content="0; url={t}"><meta name="robots" content="noindex,follow"></head>'
              f'<body><p>This story moved to <a href="{t}">{t}</a>.</p></body></html>')
    write('robots.txt', f'User-agent: *\nAllow: /\nDisallow: /search/?\n\nSitemap: {SITE}/sitemap.xml\n')
    items = ''.join(f'<item><title>{E(s["title"])}</title><link>{SITE}/stories/{s["slug"]}/</link><guid>{SITE}/stories/{s["slug"]}/</guid>'
                    f'<category>{E(CATS[cat_of(s)][0])}</category>'
                    f'<pubDate>{dt.datetime.fromisoformat(s["date"] + "T14:00:00+00:00").strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate><description>{E(s["summary"])}</description></item>' for s in stories[:50])
    write('feed.xml', f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Borrowed Hindsight</title><link>{SITE}/</link>'
          f'<description>True stories of people who started from nothing, and the lesson to borrow.</description><language>en</language>{items}</channel></rss>')
    llms = [f'# Borrowed Hindsight', '',
            '> True, sourced stories of people who started with almost nothing (founders, late starters, comebacks, record-breakers), each ending with one practical lesson ("the borrowed hindsight"). Every number is checked in at least two sources and every story lists its sources.', '',
            f'Owner and author: Manisha Aggarwal, accounting professional, New Delhi, India ({SITE}{AUTHOR_PATH}). Contact: {CONTACT_EMAIL}. Editorial standards: {SITE}/editorial-standards/', '',
             '## Tools', '', f'- [Rupee inflation calculator]({SITE}{CALC_PATH}): what any rupee amount from 1960 to 2025 is worth in another year, using the World Bank consumer price index for India.',
             f'- [CAGR calculator]({SITE}{CAGR_PATH}): the average yearly growth rate between a starting and ending value, with examples from our stories.', '']
    for c, v in CATS.items():
        if by_cat[c]:
            llms += [f'## {v[0]}', '', v[1], '']
            llms += [f'- [{s["title"]}]({SITE}/stories/{s["slug"]}/): {s["summary"]} Lesson: {s["lesson"]}' for s in by_cat[c]]
            llms.append('')
    llms += ['## About', '', f'- [About]({SITE}/about/)', f'- [Editorial standards]({SITE}/editorial-standards/)', f'- [Contact]({SITE}/contact/)', '']
    write('llms.txt', '\n'.join(llms))
    print('built', len(stories), 'stories,', len(THUMBS), 'images,', sum(1 for c in CATS if by_cat[c]), 'categories')


if __name__ == '__main__':
    main()
