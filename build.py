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
AUTHOR_BIO = ('Manisha Aggarwal is an accounting professional based in New Delhi, India. Manisha runs Borrowed Hindsight as a hobby: '
              'to keep learning, to spread awareness, and to share true stories that motivate people to start, or start again.')

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

    # ---------- tools index ----------
    tools_body = f"""<h1>Money calculators</h1>
<p class="lead">Simple, free calculators that put the numbers in our stories into perspective.</p>
<p class="mby">By <a href="{AUTHOR_PATH}" rel="author">{E(BYLINE)}</a>, accounting professional</p>
<h2><a href="{CALC_PATH}">Rupee inflation calculator</a></h2><p>What is a rupee amount from any year between {y0} and {y1} worth in another year? Uses the World Bank consumer price index for India.</p>
<h2><a href="{CAGR_PATH}">CAGR calculator</a></h2><p>Find the average yearly growth rate between a starting value and an ending value, with a growth table and examples.</p>"""
    write(TOOLS_PATH.strip('/') + '/index.html', page('Money calculators: inflation and CAGR | Borrowed Hindsight', 'Free money calculators from Borrowed Hindsight: a rupee inflation calculator (1960 to 2025) and a CAGR growth-rate calculator.',
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
            ('/privacy/', None, '0.2'), ('/terms/', None, '0.2'), (AUTHOR_PATH, None, '0.4'), (CALC_PATH, None, '0.8'), (CAGR_PATH, None, '0.8'), (TOOLS_PATH, None, '0.6')] + \
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
