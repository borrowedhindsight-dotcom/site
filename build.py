"""Build borrowedhindsight.org into _site/ from stories.json (anything dated in the future stays hidden).

Blog layout: home with story cards, /stories/ (all, paginated), /category/<slug>/ pages, long-form story pages
with thumbnail, table of contents, timeline, Reel block, share buttons, FAQ, sources, previous/next and related
stories, plus About, Contact, Editorial standards, Privacy and Terms.

A story is either a Reel story (has "reel") or a website-only article ("kind": "article"). Long-form stories use
"intro" + "sections"; older short stories with only "body" still render.
Thumbnails: assets/reels/<slug>.jpg (a frame from the Reel, copied by bh-publisher's site sync) or a free-licence
"photo" are turned into 1200x675 branded cards at build time (needs Pillow; falls back to the default image).
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
CONTACT_EMAIL = 'borrowedhindsight@gmail.com'
PROFILE = INSTAGRAM
E = html.escape
PER_PAGE = 18

# Google Analytics 4 measurement ID and AdSense publisher ID. Empty = that tag is left out entirely.
# AdSense uses Auto ads: Google chooses ad placement (AdSense > Ads > By site).
GA_ID = 'G-V6QHHCTWJT'
ADSENSE_CLIENT = 'ca-pub-8424876803254841'

# Parent category: Stories. Child categories (slug -> name, one-line description used on category pages).
CATS = {
    'zero-to-empire': ('Zero to Empire', 'Founders who started with almost nothing and built companies millions of people use.'),
    'small-start-big-result': ('Small Start, Big Result', 'Tiny first steps: a few rupees, one product, one room, and what they grew into.'),
    'rejected-then-won': ('Rejected, Then Won', 'People who were told no, turned away or laughed at, and kept going.'),
    'late-starter': ('Late Starters', 'Proof that 40, 50, 65 or even 90 is not too late to begin.'),
    'comeback': ('Comebacks', 'People and companies that lost almost everything and came back stronger.'),
    'human-limits': ('Human Limits', 'Athletes and explorers who did what experts said could not be done.'),
    'big-decisions': ('Big Decisions', 'Famous decisions, judged by what people knew at the time, not by hindsight.'),
    'lists': ('Lists & Roundups', 'Researched collections of true stories, every one sourced.'),
}
LEGACY_TAG = {  # older stories without a "category" field
    'small start, big result': 'small-start-big-result', 'zero to empire': 'zero-to-empire', 'rejected, then won': 'rejected-then-won',
    'rejected then won': 'rejected-then-won', 'human limits': 'human-limits', 'late starter': 'late-starter', 'comeback': 'comeback',
}


def cat_of(s):
    c = s.get('category') or LEGACY_TAG.get((s.get('tag') or '').strip().lower(), 'big-decisions')
    return c if c in CATS else 'big-decisions'


def tracking():
    t = ''
    if GA_ID:
        t += (f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>'
              f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA_ID}');</script>")
    if ADSENSE_CLIENT:
        t += (f'<meta name="google-adsense-account" content="{ADSENSE_CLIENT}">'
              f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT}" crossorigin="anonymous"></script>')
    return t


FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Caveat+Brush&family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">')


def page(title, desc, body, path='/', ld=None, og_type='website', extra='', image=None, noindex=False):
    img = image or f'{SITE}/assets/og.png'
    ld_html = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    robots = 'noindex' if noindex else 'index,follow,max-image-preview:large,max-snippet:-1'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">
<link rel="canonical" href="{SITE}{path}"><link rel="icon" href="/assets/favicon.png"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<meta name="google-site-verification" content="Z8IjOXiZKp3AtpkbKtGYkweQgaNV6yic2UDtFgTTYyk"><meta name="robots" content="{robots}"><meta name="theme-color" content="#FFE14D">
<link rel="alternate" type="application/rss+xml" title="Borrowed Hindsight" href="/feed.xml">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="Borrowed Hindsight"><meta property="og:locale" content="en_US">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:image" content="{img}"><meta property="og:url" content="{SITE}{path}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{E(title)}"><meta name="twitter:description" content="{E(desc)}"><meta name="twitter:image" content="{img}">{extra}{ld_html}
{FONTS}<link rel="stylesheet" href="/assets/style.css">{tracking()}</head><body>
<header class="top"><div class="wrap wide"><img src="/assets/logo.svg" alt="" width="46" height="46"><a class="brand" href="/">Borrowed Hindsight</a>
<nav><a href="/stories/">Stories</a><a href="/stories/#categories">Categories</a><a href="/#newsletter">Newsletter</a><a href="/about/">About</a><a class="ext" href="{INSTAGRAM}">Instagram</a><a class="ext" href="{YOUTUBE}">YouTube</a></nav></div></header>
{body}
<footer><div class="wrap wide"><div class="fcols">
<div><b>Borrowed Hindsight</b><p>True, sourced stories of people who started with almost nothing, and one lesson to borrow from each.</p>
<p><a href="{INSTAGRAM}">Instagram</a> · <a href="{YOUTUBE}">YouTube</a> · <a href="{FACEBOOK}">Facebook</a> · <a href="{NEWSLETTER}">Newsletter</a></p></div>
<div><b>Stories</b><p>{" · ".join(f'<a href="/category/{c}/">{E(n)}</a>' for c, (n, _) in CATS.items() if c in LIVE_CATS)}</p></div>
<div><b>About</b><p><a href="/about/">About us</a> · <a href="/editorial-standards/">Editorial standards</a> · <a href="/contact/">Contact</a> · <a href="/privacy/">Privacy</a> · <a href="/terms/">Terms</a></p></div></div>
<p class="fine">© {dt.date.today().year} Borrowed Hindsight. General education, not personal or financial advice. Videos are animated and AI-narrated. Our publishing tool uses YouTube API Services: see our <a href="/privacy/">Privacy policy</a> and the <a href="https://www.youtube.com/t/terms">YouTube Terms of Service</a>.</p></div></footer>
<script>document.querySelectorAll('[data-copy]').forEach(b=>b.addEventListener('click',()=>{{navigator.clipboard&&navigator.clipboard.writeText(b.dataset.copy);b.textContent='Link copied';}}));</script>
</body></html>'''


def signup(where='home'):
    if not NEWSLETTER:
        return ''
    head = 'Get one borrowed lesson a week' if where == 'home' else 'Liked this? Get one like it every week'
    return f'''<section class="signup" id="newsletter"><div><h2>{head}</h2>
<p>One true story a week of someone who started small and built something big, and the one lesson you can borrow from it. Free. Unsubscribe anytime.</p></div>
<div><iframe src="{NEWSLETTER}/embed" title="Subscribe to the Borrowed Hindsight newsletter" scrolling="no" loading="lazy"></iframe>
<p class="note"><a href="{NEWSLETTER}/subscribe" rel="noopener">Or subscribe on Substack →</a></p></div></section>'''


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
       'logo': {'@type': 'ImageObject', 'url': f'{SITE}/assets/apple-touch-icon.png'},
       'sameAs': [INSTAGRAM, YOUTUBE, FACEBOOK, NEWSLETTER], 'email': CONTACT_EMAIL}


def crumbs(items):
    return {'@type': 'BreadcrumbList', '@context': 'https://schema.org', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + u} for i, (n, u) in enumerate(items)]}


def crumbs_html(items):
    parts = [f'<a href="{u}">{E(n)}</a>' for n, u in items[:-1]] + [f'<span>{E(items[-1][0])}</span>']
    return '<nav class="crumbs" aria-label="Breadcrumb">' + ' › '.join(parts) + '</nav>'


# ---------- thumbnails ----------
def make_thumbs(stories):
    """1200x675 branded card per story: title + category on yellow, Reel frame (or Mirro) on the right."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print('Pillow not installed: thumbnails skipped'); return set()
    fdir = ROOT / 'assets' / 'fonts'
    disp = lambda n: ImageFont.truetype(str(fdir / 'BH-Display.ttf'), n)
    sans = ImageFont.truetype(str(fdir / 'BH-SansSemi.ttf'), 26)
    made = set()
    mirro = Image.open(ROOT / 'assets' / 'social' / 'profile.png').convert('RGBA')
    for s in stories:
        W, H = 1200, 675
        im = Image.new('RGB', (W, H), (255, 214, 10)); d = ImageDraw.Draw(im)
        d.ellipse((W - 420, -260, W + 260, 420), fill=(255, 200, 0))
        frame = ROOT / 'assets' / 'reels' / f'{s["slug"]}.jpg'
        right_x = 720
        if frame.exists():
            f = Image.open(frame).convert('RGB')
            fw = 420; fh = int(f.height * fw / f.width); f = f.resize((fw, fh))
            top = max(0, (fh - (H - 70)) // 2); f = f.crop((0, top, fw, top + H - 70))
            box = Image.new('RGB', (fw + 12, f.height + 12), (20, 20, 20)); box.paste(f, (6, 6))
            im.paste(box, (W - fw - 52, 29))
            right_x = W - fw - 80
        else:
            m = mirro.resize((330, 330)); im.paste(m, (W - 400, (H - 330) // 2), m)
            right_x = W - 430
        # category pill
        cname = CATS[cat_of(s)][0].upper()
        tw = d.textlength(cname, font=sans)
        d.rounded_rectangle((56, 56, 56 + tw + 36, 56 + 46), 23, fill=(20, 20, 20))
        d.text((56 + 18, 56 + 8), cname, font=sans, fill=(255, 255, 255))
        # title, wrapped to fit
        title = s['title']; maxw = right_x - 56 - 30
        for size in (64, 58, 52, 46, 42, 38):
            font = disp(size); words = title.split(); lines = []; cur = ''
            for w in words:
                t = (cur + ' ' + w).strip()
                if d.textlength(t, font=font) <= maxw: cur = t
                else: lines.append(cur); cur = w
            lines.append(cur)
            if len(lines) * size * 1.12 <= H - 230: break
        y = 140
        for ln in lines:
            d.text((56, y), ln, font=font, fill=(20, 20, 20)); y += int(size * 1.12)
        d.text((56, H - 70), 'borrowedhindsight.org', font=sans, fill=(20, 20, 20))
        buf = io.BytesIO(); im.save(buf, 'JPEG', quality=84, optimize=True, progressive=True)
        write(f'assets/thumbs/{s["slug"]}.jpg', buf.getvalue()); made.add(s['slug'])
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


THUMBS = set()
TITLES = {}
LIVE_CATS = set()   # categories that have at least one published story
LINK_RE = re.compile(r'https?://(?:www\.)?borrowedhindsight\.org/stories/([a-z0-9-]+)/?')


def para(text):
    """Escape a paragraph and turn links to our own stories into titled internal links."""
    out = E(text)
    def repl(m):
        slug = m.group(1)
        return f'<a href="/stories/{slug}/">{E(TITLES.get(slug, slug.replace("-", " ")))}</a>'
    return LINK_RE.sub(repl, out)


def thumb(s):
    return f'/assets/thumbs/{s["slug"]}.jpg' if s['slug'] in THUMBS else '/assets/og.png'


def card(s, big=False):
    c = cat_of(s)
    return (f'<a class="card{" big" if big else ""}" href="/stories/{s["slug"]}/"><img src="{thumb(s)}" alt="" loading="lazy" width="1200" height="675">'
            f'<div class="cbody"><span class="tag">{E(CATS[c][0])}</span><h3>{E(s["title"])}</h3><p>{E(s["summary"])}</p>'
            f'<span class="rt">{max(1, round(words_of(s) / 220))} min read</span></div></a>')


def grid(items, big_first=False):
    if not items:
        return '<p>Stories coming soon.</p>'
    return '<div class="grid">' + ''.join(card(s, big_first and i == 0) for i, s in enumerate(items)) + '</div>'


def pager(base, n, total):
    if total <= 1:
        return ''
    links = []
    for i in range(1, total + 1):
        u = base if i == 1 else f'{base}page/{i}/'
        links.append(f'<span class="cur">{i}</span>' if i == n else f'<a href="{u}">{i}</a>')
    return '<nav class="pager" aria-label="Pages">' + ''.join(links) + '</nav>'


def share(url, title):
    u = urllib.parse.quote(SITE + url, safe=''); t = urllib.parse.quote(title, safe='')
    return (f'<div class="share"><b>Share this story</b>'
            f'<a href="https://wa.me/?text={t}%20{u}" rel="noopener">WhatsApp</a>'
            f'<a href="https://www.facebook.com/sharer/sharer.php?u={u}" rel="noopener">Facebook</a>'
            f'<a href="https://twitter.com/intent/tweet?text={t}&url={u}" rel="noopener">X</a>'
            f'<a href="https://www.linkedin.com/sharing/share-offsite/?url={u}" rel="noopener">LinkedIn</a>'
            f'<button type="button" data-copy="{E(SITE + url)}">Copy link</button></div>')


# ---------- pages ----------
def story_page(s, prev_s, next_s, related):
    url = f'/stories/{s["slug"]}/'; c = cat_of(s); cname = CATS[c][0]
    d = dt.date.fromisoformat(s['date']); dtxt = d.strftime('%-d %B %Y')
    mod = s.get('updated', s['date']); rt = max(1, round(words_of(s) / 220))
    is_article = s.get('kind') == 'article'
    if s.get('sections'):
        intro = ''.join(f'<p>{para(p)}</p>' for p in s.get('intro', []))
        ids = [slugify(sec['h']) for sec in s['sections']]
        toc = '<nav class="toc"><b>In this story</b><ol>' + ''.join(f'<li><a href="#{i}">{E(sec["h"])}</a></li>' for i, sec in zip(ids, s['sections'])) + '</ol></nav>'
        secs = ''.join(f'<h2 id="{i}">{E(sec["h"])}</h2>' + ''.join(f'<p>{para(p)}</p>' for p in sec['paras']) for i, sec in zip(ids, s['sections']))
        main_html = intro + toc + secs
    else:
        main_html = '<h2>The story</h2>' + ''.join(f'<p>{E(p)}</p>' for p in s.get('body', []))
    tl = s.get('timeline') or []
    tl_html = ('<section class="timeline"><h2>Timeline</h2><ol>' + ''.join(f'<li><b>{E(str(y))}</b><span>{E(ev)}</span></li>' for y, ev in tl) + '</ol></section>') if tl else ''
    photo = s.get('photo')
    photo_html = (f'<figure class="photo"><img src="{E(photo["url"])}" alt="{E(s["title"])}" loading="lazy"><figcaption>Photo: '
                  f'<a href="{E(photo["page"])}" rel="nofollow noopener">{E(photo.get("credit") or "Wikimedia Commons")}</a>, {E(photo.get("license", ""))}, via Wikimedia Commons</figcaption></figure>') if photo else ''
    checks = ''.join(f'<li>{E(x)}</li>' for x in s.get('check', []))
    srcs = ''.join(f'<li>{f"<a href={chr(34)}{E(u)}{chr(34)} rel=\"nofollow noopener\">{E(t)}</a>" if u else E(t)}</li>' for t, u in s['sources'])
    faq = s.get('faq', [])
    faq_html = ('<section class="faq"><h2>Questions people ask</h2>' + ''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in faq) + '</section>') if faq else ''
    has_reel = bool(s.get('reel')) and s['reel'] != PROFILE
    reel_url = s['reel'] if has_reel else PROFILE
    frame = (ROOT / 'assets' / 'reels' / f'{s["slug"]}.jpg').exists()
    main_btn = (f'<a class="btn" href="{E(reel_url)}">Watch on Instagram</a>' if has_reel
                else f'<a class="btn" href="{INSTAGRAM}">Follow on Instagram</a>')
    reel_html = '' if is_article else (
        '<section class="reel">'
        + (f'<a class="rthumb" href="{E(reel_url)}" rel="noopener"><img src="/assets/reels/{s["slug"]}.jpg" alt="Frame from the video" loading="lazy"><span>▶</span></a>' if frame else '')
        + f'<div><b>{"Watch this story in 40 seconds" if has_reel else "Watch our story videos"}</b><p>Animated, AI-narrated, and sourced like this page.</p>'
        f'<p class="btns">{main_btn}<a class="btn alt" href="{YOUTUBE}">YouTube</a><a class="btn alt" href="{FACEBOOK}">Facebook</a></p></div></section>')
    nav = '<nav class="prevnext">' + (f'<a class="prev" href="/stories/{prev_s["slug"]}/"><span>← Previous story</span>{E(prev_s["title"])}</a>' if prev_s else '<span></span>') + \
          (f'<a class="next" href="/stories/{next_s["slug"]}/"><span>Next story →</span>{E(next_s["title"])}</a>' if next_s else '<span></span>') + '</nav>'
    rel_html = ('<section class="related"><h2>More borrowed hindsight</h2>' + grid(related) + '</section>') if related else ''
    body = f'''<main class="wrap">{crumbs_html([("Home", "/"), ("Stories", "/stories/"), (cname, f"/category/{c}/"), (s["title"], url)])}
<article><span class="meta"><a href="/category/{c}/">{E(cname)}</a> · <time datetime="{s["date"]}">{dtxt}</time> · {rt} min read · By the Borrowed Hindsight team</span>
<h1>{E(s["title"])}</h1><p class="lead">{E(s["summary"])}</p>
<img class="hero-img" src="{thumb(s)}" alt="{E(s["title"])}" width="1200" height="675">
{main_html}{photo_html}{tl_html}
<div class="lesson"><b>The borrowed hindsight</b>{E(s["lesson"])}</div>
{f'<div class="check"><h3>{E(s.get("check_title", "Ask yourself"))}</h3><ul>{checks}</ul></div>' if checks else ''}
{reel_html}{share(url, s["title"])}{faq_html}
<div class="sources"><h2>Sources</h2><ol>{srcs}</ol><p class="note">Every fact on this page comes from the sources above; numbers are checked in at least two. General education, not personal or financial advice. Spotted an error? <a href="/contact/">Tell us</a> and we'll correct it. <a href="/editorial-standards/">Our editorial standards</a>.</p></div>
{nav}</article>{signup('story')}{rel_html}</main>'''
    img = SITE + thumb(s)
    art = {'@context': 'https://schema.org', '@type': 'Article', 'headline': s['title'][:110], 'description': s['summary'],
           'datePublished': f'{s["date"]}T19:30:00+05:30', 'dateModified': f'{mod}T19:30:00+05:30',
           'author': {'@type': 'Organization', 'name': 'Borrowed Hindsight', 'url': SITE + '/about/'}, 'publisher': ORG,
           'image': [img], 'mainEntityOfPage': SITE + url, 'articleSection': cname, 'inLanguage': 'en', 'wordCount': words_of(s),
           'keywords': ', '.join(s.get('keywords', [])) or None, 'citation': [u for _, u in s['sources'] if u] or None}
    art = {k: v for k, v in art.items() if v is not None}
    ld = [art, crumbs([('Home', '/'), ('Stories', '/stories/'), (cname, f'/category/{c}/'), (s['title'], url)])]
    if faq:
        ld.append({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]})
    extra = (f'<meta property="article:published_time" content="{s["date"]}T19:30:00+05:30"><meta property="article:modified_time" content="{mod}T19:30:00+05:30">'
             f'<meta property="article:section" content="{E(cname)}">')
    title = s.get('seo_title') or s['title']
    write(f'stories/{s["slug"]}/index.html', page(f'{title} | Borrowed Hindsight', s['summary'], body, url, ld=ld, og_type='article', extra=extra, image=img))


def list_pages(base, items, title, desc, heading, intro_html, crumb_items):
    total = max(1, math.ceil(len(items) / PER_PAGE))
    for n in range(1, total + 1):
        chunk = items[(n - 1) * PER_PAGE: n * PER_PAGE]
        path = base if n == 1 else f'{base}page/{n}/'
        body = (f'<main class="wrap wide">{crumbs_html(crumb_items)}<h1 class="ptitle">{E(heading)}</h1>{intro_html}'
                f'{grid(chunk)}{pager(base, n, total)}</main>')
        ld = [crumbs([(n_, u) for n_, u in crumb_items]),
              {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': heading, 'url': SITE + path, 'publisher': ORG}]
        write(path.lstrip('/') + 'index.html', page(title + (f' (page {n})' if n > 1 else ''), desc, body, path, ld=ld))


def main():
    global THUMBS
    shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir()
    shutil.copytree(ROOT / 'assets', OUT / 'assets', ignore=shutil.ignore_patterns('fonts')); shutil.copy(ROOT / 'CNAME', OUT / 'CNAME')
    stories = sorted([s for s in json.load(open(ROOT / 'stories.json')) if s['date'] <= TODAY], key=lambda s: (s['date'], s['slug']), reverse=True)
    THUMBS = make_thumbs(stories)
    TITLES.update({s['slug']: s['title'] for s in stories})
    by_cat = {c: [s for s in stories if cat_of(s) == c] for c in CATS}
    LIVE_CATS.update(c for c in CATS if by_cat[c])

    # home
    cat_blocks = ''.join(
        f'<section class="catblock"><div class="cathead"><h2><a href="/category/{c}/">{E(n)}</a></h2><a class="more" href="/category/{c}/">See all {len(by_cat[c])} →</a></div>'
        f'<p class="catdesc">{E(dsc)}</p>{grid(by_cat[c][:3])}</section>' for c, (n, dsc) in CATS.items() if by_cat[c])
    chips = '<div class="chips" id="categories">' + ''.join(f'<a href="/category/{c}/">{E(n)} <small>{len(by_cat[c])}</small></a>' for c, (n, _) in CATS.items() if by_cat[c]) + '</div>'
    home = f'''<section class="hero"><div class="wrap wide"><h1>They started with almost nothing. Their hindsight is yours to <span class="script">borrow</span>.</h1>
<p class="lead">True, sourced stories of founders, late starters, comebacks and record-breakers: the low point, the climb, and one lesson you can use in your own life.</p>
<div class="btns"><a class="btn" href="/stories/">Read the stories</a><a class="btn alt" href="{INSTAGRAM}">Follow on Instagram</a></div></div></section>
<main class="wrap wide"><h2 id="stories">Latest stories</h2>{grid(stories[:7], big_first=True)}<p><a class="btn" href="/stories/">All {len(stories)} stories →</a></p>
<h2>Browse by category</h2>{chips}{cat_blocks}
{signup('home')}<p class="note">Every story is researched and sourced, and every number is checked in at least two sources. Videos are animated and AI-narrated. Nothing here is personal or financial advice. <a href="/editorial-standards/">Our editorial standards</a>.</p></main>'''
    home_ld = [{'@context': 'https://schema.org', '@graph': [ORG, {'@type': 'WebSite', '@id': f'{SITE}/#site', 'url': SITE + '/', 'name': 'Borrowed Hindsight',
               'description': 'True, sourced stories of people who started small and built something big, with one lesson to borrow.', 'publisher': {'@id': f'{SITE}/#org'}, 'inLanguage': 'en'},
               {'@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': f'{SITE}/stories/{s["slug"]}/'} for i, s in enumerate(stories[:20])]}]}]
    write('index.html', page('Borrowed Hindsight: true stories of people who started from nothing', 'True, sourced stories of founders, late starters, comebacks and record-breakers, and one lesson you can borrow from each.', home, ld=home_ld))

    # all stories + categories
    list_pages('/stories/', stories, 'All stories | Borrowed Hindsight', 'Every Borrowed Hindsight story: true, sourced stories of people who started small and built something big.',
               'All stories', f'<p class="lead">{len(stories)} true stories, newest first. Every one is researched and sourced.</p>{chips}', [('Home', '/'), ('Stories', '/stories/')])
    for c, (n, dsc) in CATS.items():
        if by_cat[c]:
            list_pages(f'/category/{c}/', by_cat[c], f'{n}: true stories | Borrowed Hindsight', dsc, n, f'<p class="lead">{E(dsc)}</p>',
                       [('Home', '/'), ('Stories', '/stories/'), (n, f'/category/{c}/')])

    # story pages: previous = older, next = newer
    chrono = list(reversed(stories))
    for i, s in enumerate(chrono):
        prev_s = chrono[i - 1] if i > 0 else None
        next_s = chrono[i + 1] if i + 1 < len(chrono) else None
        same = [r for r in stories if r is not s and cat_of(r) == cat_of(s)]
        other = [r for r in stories if r is not s and cat_of(r) != cat_of(s)]
        story_page(s, prev_s, next_s, (same + other)[:3])

    # static pages
    about = f'''<h1>About Borrowed Hindsight</h1>
<p class="lead">They started with almost nothing. Their hindsight is yours to borrow.</p>
<p>Borrowed Hindsight tells true stories of people who started with very little, were told no, or started late, and built something remarkable anyway: the low point, the choice, the climb, and one line of hindsight you can borrow for your own life.</p>
<p>We publish short animated videos on <a href="{INSTAGRAM}">Instagram</a>, <a href="{YOUTUBE}">YouTube</a> and <a href="{FACEBOOK}">Facebook</a>, a weekly <a href="{NEWSLETTER}">newsletter</a>, and the full, sourced version of every story here.</p>
<h2>How we research</h2><p>Every story is built from primary or reputable sources: company and official records, major newspapers and magazines, books, peer-reviewed studies and official statistics. Every number is checked in at least two independent sources, and each page lists its sources. If a popular story or statistic can't be traced to a real source, we say so instead of repeating it. Read our full <a href="/editorial-standards/">editorial standards</a>.</p>
<h2>How the videos are made</h2><p>Our short videos are animated and narrated with an AI voice. Scripts are researched and checked before publishing.</p>
<h2>What we don't do</h2><p>We don't give personal financial, investment, legal or career advice, and we don't recommend products, stocks or apps. We don't publish political or religious content, and we never mock anyone. We judge decisions by what was known at the time, not by how they turned out.</p>
<h2>Contact</h2><p>Corrections, story suggestions or partnership questions: see our <a href="/contact/">contact page</a>.</p>'''
    write('about/index.html', page('About Borrowed Hindsight: who we are and how we research', 'Who we are, how every Borrowed Hindsight story is researched and sourced, and how to reach us.',
          f'<main class="wrap legal">{crumbs_html([("Home", "/"), ("About", "/about/")])}{about}</main>', '/about/', ld=[{'@context': 'https://schema.org', '@type': 'AboutPage', 'url': SITE + '/about/', 'publisher': ORG}]))

    contact = f'''<h1>Contact us</h1>
<p class="lead">We read every message. The fastest way to reach us is email.</p>
<p class="big-mail"><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
<h2>What to write to us about</h2><ul>
<li><b>Corrections.</b> Found a mistake? Send the page link and what's wrong, with a source if you have one. We check every report and correct confirmed errors, usually within 48 hours. See our <a href="/editorial-standards/#corrections">corrections policy</a>.</li>
<li><b>Story suggestions.</b> Know a true story of someone who started small or came back from a setback? Tell us, with a link to where it was reported.</li>
<li><b>Partnerships and press.</b> Brands, publishers and educators: tell us what you have in mind.</li>
<li><b>Privacy requests.</b> See our <a href="/privacy/">privacy policy</a>.</li></ul>
<h2>Find us elsewhere</h2><p><a href="{INSTAGRAM}">Instagram</a> · <a href="{YOUTUBE}">YouTube</a> · <a href="{FACEBOOK}">Facebook</a> · <a href="{NEWSLETTER}">Newsletter</a></p>
<p class="note">We usually reply within two working days (India time). We never ask for passwords, payments or personal documents.</p>'''
    write('contact/index.html', page('Contact Borrowed Hindsight', 'How to reach Borrowed Hindsight for corrections, story suggestions, partnerships and privacy requests.',
          f'<main class="wrap legal">{crumbs_html([("Home", "/"), ("Contact", "/contact/")])}{contact}</main>', '/contact/',
          ld=[{'@context': 'https://schema.org', '@type': 'ContactPage', 'url': SITE + '/contact/', 'publisher': ORG}]))

    corr = json.load(open(ROOT / 'corrections.json')) if (ROOT / 'corrections.json').exists() else []
    corr_html = ('<ul class="corrections">' + ''.join(f'<li><b>{E(c["date"])}</b> · <a href="/stories/{E(c["slug"])}/">{E(c.get("title", c["slug"]))}</a>: {E(c["what"])}</li>' for c in corr) + '</ul>') if corr else '<p>No corrections yet. When we correct a published fact, it will be listed here with the date.</p>'
    ed = f'''<h1>Editorial standards</h1>
<p class="lead">Our promise: every story is true, every number is checked, and every source is shown.</p>
<h2>What we publish</h2><p>True stories of people and companies that started small, faced rejection or setbacks, and built something remarkable, plus researched roundups of such stories. Each story ends with one practical lesson (the "borrowed hindsight") and a question to ask yourself.</p>
<h2>How we check facts</h2><ul>
<li>We use primary and reputable sources: official and company records, major newspapers and magazines, books, peer-reviewed research and official statistics.</li>
<li>Every number, date and claim is checked in at least two independent sources. When good sources disagree, we say so.</li>
<li>We only quote people when a reputable source published the quote. We never invent dialogue.</li>
<li>Wikipedia can point us to sources, but it is never our only source.</li>
<li>Every page lists the sources we used, with links.</li></ul>
<h2>How we use AI</h2><p>Our videos are animated and narrated with an AI voice, and we use AI tools to help research and draft. Every story is checked against its sources before publishing, and a person is responsible for what we publish. We never use AI to create fake photos of real people.</p>
<h2>Images</h2><p>We use our own illustrations and video frames, or photos with free licences (such as Creative Commons) credited to their authors.</p>
<h2>What we don't publish</h2><p>No political or religious content, nothing that mocks people or groups, no tragedy for entertainment, and no personal financial, investment, legal or career advice. We judge decisions by what was known at the time.</p>
<h2>Independence and advertising</h2><p>This site shows ads served by Google AdSense. Advertisers have no say in what we write, and we don't accept payment to feature people or companies. If we ever publish sponsored content, it will be clearly labelled.</p>
<h2 id="corrections">Corrections</h2><p>If we get something wrong, we fix it and record the change here. Report an error on our <a href="/contact/">contact page</a>.</p>{corr_html}'''
    write('editorial-standards/index.html', page('Editorial standards | Borrowed Hindsight', 'How Borrowed Hindsight researches, checks and corrects its stories, how we use AI, and how advertising works on this site.',
          f'<main class="wrap legal">{crumbs_html([("Home", "/"), ("Editorial standards", "/editorial-standards/")])}{ed}</main>', '/editorial-standards/'))

    for name in ('privacy', 'terms'):
        body = (ROOT / f'{name}.html').read_text().replace('<!--SITE-DATA-->', site_data())
        title = 'Privacy policy' if name == 'privacy' else 'Terms of use'
        write(f'{name}/index.html', page(f'{title} | Borrowed Hindsight', f'{title} for borrowedhindsight.org and the Borrowed Hindsight channels.', f'<main class="wrap legal">{body}</main>', f'/{name}/'))
    write('404.html', page('Not found | Borrowed Hindsight', 'Page not found', f'<main class="wrap legal"><h1>Not found</h1><p>That page doesn\'t exist. Try the <a href="/stories/">full list of stories</a>.</p></main>', noindex=True))

    newest = stories[0]['date'] if stories else TODAY
    urls = [('/', newest, '1.0'), ('/stories/', newest, '0.9'), ('/about/', None, '0.5'), ('/contact/', None, '0.4'), ('/editorial-standards/', None, '0.4'),
            ('/privacy/', None, '0.2'), ('/terms/', None, '0.2')] + \
           [(f'/category/{c}/', by_cat[c][0]['date'], '0.7') for c in CATS if by_cat[c]] + \
           [(f'/stories/{s["slug"]}/', s.get('updated', s['date']), '0.8') for s in stories]
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(
        f'<url><loc>{SITE}{u}</loc>{f"<lastmod>{m}</lastmod>" if m else ""}<priority>{pr}</priority></url>' for u, m, pr in urls) + '</urlset>')
    if ADSENSE_CLIENT:
        write('ads.txt', f'google.com, {ADSENSE_CLIENT.replace("ca-", "")}, DIRECT, f08c47fec0942fa0\n')
    write('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n')
    items = ''.join(f'<item><title>{E(s["title"])}</title><link>{SITE}/stories/{s["slug"]}/</link><guid>{SITE}/stories/{s["slug"]}/</guid>'
                    f'<pubDate>{dt.datetime.fromisoformat(s["date"] + "T14:00:00+00:00").strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate><description>{E(s["summary"])}</description></item>' for s in stories[:50])
    write('feed.xml', f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Borrowed Hindsight</title><link>{SITE}/</link>'
          f'<description>True stories of people who started from nothing, and the lesson to borrow.</description><language>en</language>{items}</channel></rss>')
    print('built', len(stories), 'stories,', len(THUMBS), 'thumbnails,', sum(1 for c in CATS if by_cat[c]), 'categories')


if __name__ == '__main__':
    main()
