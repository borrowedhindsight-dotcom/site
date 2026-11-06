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
NEWSLETTER = 'https://borrowedhindsight.substack.com'
CONTACT_EMAIL = 'hello@borrowedhindsight.org'
PROFILE = INSTAGRAM
E = html.escape
PER_PAGE = 18
BYLINE = 'Borrowed Hindsight editors'   # who is responsible for the stories (shown on every story and in Article schema)

# Google Analytics 4 measurement ID and AdSense publisher ID. Empty = that tag is left out entirely.
# AdSense uses Auto ads: Google chooses ad placement. The AdSense script is left off pages without publisher content
# (contact, legal pages, search, 404), per AdSense policy.
GA_ID = 'G-V6QHHCTWJT'
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
              f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA_ID}');</script>")
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
            f'<details><summary>Categories</summary><div class="menu"><a href="/stories/"><i class="dot" style="--c:#FFD60A"></i>All stories<small>{sum(COUNTS.values())}</small></a>{items}<a class="show-m" href="/about/">About</a></div></details>'
            f'<a class="hide-m" href="/about/">About</a>'
            f'<a class="search" href="/search/" aria-label="Search stories">{SEARCH_ICON}</a>'
            f'<a class="cta hide-m" href="#newsletter">Newsletter</a></nav>')


def page(title, desc, body, path='/', ld=None, og_type='website', extra='', image=None, noindex=False, ads=True, progress=False):
    img = image or f'{SITE}/assets/og.png'
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
<div><h2>Follow</h2><ul><li><a href="{INSTAGRAM}" rel="me noopener">Instagram</a></li><li><a href="{YOUTUBE}" rel="me noopener">YouTube</a></li><li><a href="{FACEBOOK}" rel="me noopener">Facebook</a></li><li><a href="{NEWSLETTER}" rel="me noopener">Newsletter</a></li></ul></div>
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


def write(rel, content):
    p = OUT / rel; p.parent.mkdir(parents=True, exist_ok=True)
    (p.write_bytes if isinstance(content, bytes) else p.write_text)(content)


ORG = {'@type': 'Organization', '@id': f'{SITE}/#org', 'name': 'Borrowed Hindsight', 'url': SITE + '/',
       'description': 'An independent publisher of true, sourced stories of people who started with almost nothing.',
       'logo': {'@type': 'ImageObject', 'url': f'{SITE}/assets/apple-touch-icon.png', 'width': 180, 'height': 180},
       'sameAs': [INSTAGRAM, YOUTUBE, FACEBOOK, NEWSLETTER], 'email': CONTACT_EMAIL,
       'publishingPrinciples': f'{SITE}/editorial-standards/', 'correctionsPolicy': f'{SITE}/editorial-standards/#corrections',
       'contactPoint': {'@type': 'ContactPoint', 'contactType': 'editorial', 'email': CONTACT_EMAIL, 'url': f'{SITE}/contact/'}}


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
    if tl: toc_items.append(('timeline', 'Timeline'))
    toc_items.append(('lesson', 'The borrowed hindsight'))
    if s.get('faq'): toc_items.append(('faq', 'Questions people ask'))
    toc_items.append(('sources', 'Sources'))
    toc_li = ''.join(f'<li><a href="#{i}">{E(h)}</a></li>' for i, h in toc_items)
    toc_m = f'<details class="toc-m"><summary>In this story</summary><ol>{toc_li}</ol></details>'
    tl_html = ('<section class="timeline" id="timeline"><h2>Timeline</h2><ol>' + ''.join(f'<li><b>{E(str(y))}</b>{E(ev)}</li>' for y, ev in tl) + '</ol></section>') if tl else ''
    photo = s.get('photo')
    photo_html = (f'<figure class="photo"><img src="{E(photo["url"])}" alt="{E(s["title"])}" loading="lazy"><figcaption>Photo: '
                  f'<a href="{E(photo["page"])}" rel="nofollow noopener">{E(photo.get("credit") or "Wikimedia Commons")}</a>, {E(photo.get("license", ""))}, via Wikimedia Commons</figcaption></figure>') if photo else ''
    checks = ''.join(f'<li>{E(x)}</li>' for x in s.get('check', []))
    nsrc = len(s['sources'])
    srcs = ''.join(f'<li>{f"<a href={chr(34)}{E(u)}{chr(34)} rel=\"nofollow noopener\">{E(t)}</a>" if u else E(t)}</li>' for t, u in s['sources'])
    faq = s.get('faq', [])
    faq_html = ('<section class="faq" id="faq"><h2>Questions people ask</h2>' + ''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in faq) + '</section>') if faq else ''
    has_reel = bool(s.get('reel')) and s['reel'] != PROFILE
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
    body = f'''<main class="wrap">{crumbs_html([("Home", "/"), ("Stories", "/stories/"), (cname, f"/category/{c}/"), (s["title"], url)])}
<article>
<header class="story-head">{kicker(c, True)}<h1>{E(s["title"])}</h1><p class="lead">{E(s["summary"])}</p>
<div class="byline"><img src="/assets/logo.svg" alt="" width="42" height="42"><div><b>{E(BYLINE)}</b><div class="facts"><time datetime="{s["date"]}">{fmt_date(s["date"])}</time>{upd}<span>{rt} min read</span><span>Checked against {nsrc} sources</span></div></div></div></header>
<figure class="cover">{img_tag(s, "(max-width:1240px) 100vw, 1200px", eager=True)}</figure>{f'<p class="figcap">{E(caption_of(s))}</p>' if caption_of(s) else ''}
<div class="layout"><div class="prose">
{toc_m}{intro}{secs}{photo_html}{tl_html}
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
           'author': {'@type': 'Organization', 'name': BYLINE, 'url': SITE + '/about/'}, 'publisher': ORG,
           'image': [{'@type': 'ImageObject', 'url': img, 'width': 1200, 'height': 675, 'caption': alt_of(s), 'contentUrl': img}], 'mainEntityOfPage': SITE + url, 'articleSection': cname, 'inLanguage': 'en', 'wordCount': words_of(s),
           'keywords': ', '.join(s.get('keywords', [])) or None, 'citation': [u for _, u in s['sources'] if u] or None,
           'abstract': s['lesson'], 'isAccessibleForFree': True,
           'speakable': {'@type': 'SpeakableSpecification', 'cssSelector': ['.story-head .lead', '.lesson p']}}
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


def list_pages(base, items, title, desc, heading, head_html, crumb_items, below=''):
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
        write(path.lstrip('/') + 'index.html', page(title + (f' (page {n})' if n > 1 else ''), desc, body, path, ld=ld, noindex=n > 1, ads=n == 1))


def main():
    global THUMBS
    shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir()
    shutil.copytree(ROOT / 'assets', OUT / 'assets', ignore=shutil.ignore_patterns('fonts')); shutil.copy(ROOT / 'CNAME', OUT / 'CNAME')
    stories = sorted([s for s in json.load(open(ROOT / 'stories.json')) if s['date'] <= TODAY], key=lambda s: (s['date'], s['slug']), reverse=True)
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
    watched = [s for s in popular if POP.get(s['slug'], 0) > 0][:4]   # the top story stays in Most watched even when it is also featured (Deepak, 6 Nov)
    most_html = (f'<section class="block"><div class="shead"><h2>Most watched</h2><a class="all" href="{INSTAGRAM}" rel="noopener">Watch on Instagram</a></div>'
                 f'<p class="sdesc">The stories people watched most on Instagram. Read the full, sourced version here.</p>'
                 f'<div class="row">{"".join(card(s, summary=False) for s in watched)}</div></section>') if len(watched) >= 3 else ''
    wall = [s for s in stories if s.get('lesson')][:9]
    wall_html = ''.join(f'<a class="quote" href="/stories/{s["slug"]}/"><q>{E(s["lesson"])}</q><span>{E(s["title"])}</span></a>' for s in wall)
    rows = ''.join(
        f'<section class="block"><div class="shead"><h2><a href="/category/{c}/">{E(v[0])}</a></h2><a class="all" href="/category/{c}/">All {len(by_cat[c])}</a></div>'
        f'<p class="sdesc">{E(v[1])}</p><div class="row">{"".join(card(s, summary=False) for s in ([x for x in by_cat[c] if x not in shown] + [x for x in by_cat[c] if x in shown])[:4])}</div></section>'
        for c, v in CATS.items() if by_cat[c])
    home = f'''<main>
<div class="wrap"><section class="intro"><div class="intro-row"><h1>True stories of people who started with almost nothing</h1>
<p class="lead">Founders, late starters, comebacks and record-breakers: the low point, the climb, and one line of hindsight you can borrow. Every story is researched, sourced and checked twice.</p></div></section>
<a class="feature" href="/stories/{feat["slug"]}/"><div class="pic">{img_tag(feat, "(max-width:900px) 100vw, 690px", eager=True)}</div>
<div>{kicker(fc)}<h2>{E(feat["title"])}</h2><p>{E(feat["summary"])}</p><blockquote><span class="hl">{E(feat["lesson"])}</span></blockquote><span class="more">Read the story ({mins(feat)} min)</span></div></a>
{most_html}<section class="block"><div class="shead"><h2>Latest stories</h2><a class="all" href="/stories/">All {len(stories)} stories</a></div>{grid(latest)}</section></div>
<section class="wall"><div class="wrap"><h2>Lines worth borrowing</h2><p class="sub">Every story ends with one line of hindsight. Here are the latest. Tap one to read the story behind it.</p><div class="quotes">{wall_html}</div></div></section>
<div class="wrap"><section class="block"><div class="shead"><h2>Browse by category</h2></div>{chips_html(by_cat)}</section>
{rows}{signup('home')}</div></main>'''
    home_ld = [{'@context': 'https://schema.org', '@graph': [ORG, {'@type': 'WebSite', '@id': f'{SITE}/#site', 'url': SITE + '/', 'name': 'Borrowed Hindsight',
               'description': 'True, sourced stories of people who started small and built something big, with one lesson to borrow.', 'publisher': {'@id': f'{SITE}/#org'}, 'inLanguage': 'en',
               'potentialAction': {'@type': 'SearchAction', 'target': {'@type': 'EntryPoint', 'urlTemplate': f'{SITE}/search/?q={{search_term_string}}'}, 'query-input': 'required name=search_term_string'}},
               {'@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': f'{SITE}/stories/{s["slug"]}/'} for i, s in enumerate(stories[:20])]}]}]
    write('index.html', page('Borrowed Hindsight: true stories of people who started from nothing', 'True, sourced stories of founders, late starters, comebacks and record-breakers, and one lesson you can borrow from each.', home, ld=home_ld,
                             extra=f'<link rel="preload" as="image" href="{thumb(feat)}" imagesrcset="{thumb(feat, True)} 640w, {thumb(feat)} 1200w" imagesizes="(max-width:900px) 100vw, 690px">'))

    # ---------- all stories + categories ----------
    list_pages('/stories/', stories, 'All stories | Borrowed Hindsight', 'Every Borrowed Hindsight story: true, sourced stories of people who started small and built something big.',
               'All stories', f'<p class="lead">{len(stories)} true stories, newest first. Every one is researched, sourced and checked against at least two sources.</p>{chips_html(by_cat, "all")}',
               [('Home', '/'), ('Stories', '/stories/')])
    for c, (n, dsc, col, intro) in CATS.items():
        if by_cat[c]:
            head = (f'<div class="catintro">{"".join(f"<p>{E(p)}</p>" for p in intro)}</div>{chips_html(by_cat, c)}')
            list_pages(f'/category/{c}/', by_cat[c], f'{n}: true stories | Borrowed Hindsight', dsc, n, head,
                       [('Home', '/'), ('Stories', '/stories/'), (n, f'/category/{c}/')])

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
<p>We publish short animated videos on <a href="{INSTAGRAM}">Instagram</a>, <a href="{YOUTUBE}">YouTube</a> and <a href="{FACEBOOK}">Facebook</a>, a weekly <a href="{NEWSLETTER}">newsletter</a>, and the full, sourced version of every story here. We are based in New Delhi, India, and write for readers everywhere.</p>
<h2>How we research</h2><p>Every story is built from primary or reputable sources: company and official records, major newspapers and magazines, books, peer-reviewed studies and official statistics. Every number is checked in at least two independent sources, and each page lists its sources. If a popular story or statistic can't be traced to a real source, we say so instead of repeating it. Read our full <a href="/editorial-standards/">editorial standards</a>.</p>
<h2>How we use AI</h2><p>AI tools help us research, draft and narrate. People choose every story, and every fact is checked against its sources before it is published. Our short videos are animated and narrated with an AI voice. We never create fake photos of real people.</p>
<h2>What we don't do</h2><p>We don't give personal financial, investment, legal or career advice, and we don't recommend products, stocks or apps. We don't publish political or religious content, and we never mock anyone. We judge decisions by what was known at the time, not by how they turned out.</p>
<h2>Who publishes this site</h2><p>Borrowed Hindsight is published by Manisha Aggarwal, New Delhi, India. Stories are researched and written by the Borrowed Hindsight editorial team, following our <a href="/editorial-standards/">editorial standards</a>.</p>
<h2>Contact</h2><p>Corrections, story suggestions or partnership questions: email <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a> or see our <a href="/contact/">contact page</a>.</p>'''
    write('about/index.html', page('About Borrowed Hindsight: who we are and how we research', 'Who we are, how every Borrowed Hindsight story is researched and sourced, and how to reach us.',
          f'<main class="wrap narrow legal">{crumbs_html([("Home", "/"), ("About", "/about/")])}{about}</main>', '/about/', ld=[{'@context': 'https://schema.org', '@type': 'AboutPage', 'url': SITE + '/about/', 'about': ORG, 'publisher': ORG}]))

    contact = f'''<h1>Contact us</h1>
<p class="lead">We read every message. The fastest way to reach us is email.</p>
<p class="big-mail"><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
<h2>What to write to us about</h2><ul>
<li><b>Corrections.</b> Found a mistake? Send the page link and what's wrong, with a source if you have one. We check every report and correct confirmed errors, usually within 48 hours. See our <a href="/editorial-standards/#corrections">corrections policy</a>.</li>
<li><b>Story suggestions.</b> Know a true story of someone who started small or came back from a setback? Tell us, with a link to where it was reported.</li>
<li><b>Partnerships and press.</b> Brands, publishers and educators: tell us what you have in mind.</li>
<li><b>Privacy requests.</b> See our <a href="/privacy/">privacy policy</a>.</li></ul>
<h2>Find us elsewhere</h2><p><a href="{INSTAGRAM}">Instagram</a>, <a href="{YOUTUBE}">YouTube</a>, <a href="{FACEBOOK}">Facebook</a> and our <a href="{NEWSLETTER}">newsletter</a>.</p>
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
            ('/privacy/', None, '0.2'), ('/terms/', None, '0.2')] + \
           [(f'/category/{c}/', by_cat[c][0]['date'], '0.7') for c in CATS if by_cat[c]] + \
           [(f'/stories/{s["slug"]}/', s.get('updated', s['date']), '0.8') for s in stories]
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">' + ''.join(
        f'<url><loc>{SITE}{u}</loc>{f"<lastmod>{m}</lastmod>" if m else ""}<priority>{pr}</priority>'
        + (f'<image:image><image:loc>{SITE}/assets/thumbs/{u.split("/")[2]}.jpg</image:loc></image:image>' if u.startswith('/stories/') and len(u) > 9 and u.split('/')[2] in THUMBS else '')
        + '</url>' for u, m, pr in urls) + '</urlset>')
    if ADSENSE_CLIENT:
        write('ads.txt', f'google.com, {ADSENSE_CLIENT.replace("ca-", "")}, DIRECT, f08c47fec0942fa0\n')
    write('robots.txt', f'User-agent: *\nAllow: /\nDisallow: /search/?\n\nSitemap: {SITE}/sitemap.xml\n')
    items = ''.join(f'<item><title>{E(s["title"])}</title><link>{SITE}/stories/{s["slug"]}/</link><guid>{SITE}/stories/{s["slug"]}/</guid>'
                    f'<category>{E(CATS[cat_of(s)][0])}</category>'
                    f'<pubDate>{dt.datetime.fromisoformat(s["date"] + "T14:00:00+00:00").strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate><description>{E(s["summary"])}</description></item>' for s in stories[:50])
    write('feed.xml', f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Borrowed Hindsight</title><link>{SITE}/</link>'
          f'<description>True stories of people who started from nothing, and the lesson to borrow.</description><language>en</language>{items}</channel></rss>')
    llms = [f'# Borrowed Hindsight', '',
            '> True, sourced stories of people who started with almost nothing (founders, late starters, comebacks, record-breakers), each ending with one practical lesson ("the borrowed hindsight"). Every number is checked in at least two sources and every story lists its sources.', '',
            f'Publisher: Borrowed Hindsight, New Delhi, India. Contact: {CONTACT_EMAIL}. Editorial standards: {SITE}/editorial-standards/', '']
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
