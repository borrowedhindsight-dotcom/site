"""Build borrowedhindsight.org into _site/ from stories.json (stories dated in the future stay hidden)."""
import json, html, shutil, pathlib, datetime as dt

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / '_site'
TODAY = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=5, minutes=30)).date().isoformat()
SITE = 'https://www.borrowedhindsight.org'
FACEBOOK = 'https://www.facebook.com/borrowedhindsight'
NEWSLETTER = 'https://borrowedhindsight.substack.com'   # Substack address, e.g. 'https://borrowedhindsight.substack.com'. Empty = sign-up hidden.
E = html.escape

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Caveat+Brush&family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">')


def page(title, desc, body, path='/', ld=None, og_type='website', extra=''):
    nl_nav = '<a href="/#newsletter">Newsletter</a>' if NEWSLETTER else ''
    ld_html = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">
<link rel="canonical" href="{SITE}{path}"><link rel="icon" href="/assets/favicon.png"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<meta name="google-site-verification" content="Z8IjOXiZKp3AtpkbKtGYkweQgaNV6yic2UDtFgTTYyk"><meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1"><meta name="theme-color" content="#FFE14D">
<link rel="alternate" type="application/rss+xml" title="Borrowed Hindsight" href="/feed.xml">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="Borrowed Hindsight"><meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{E(title)}"><meta name="twitter:description" content="{E(desc)}"><meta name="twitter:image" content="{SITE}/assets/og.png">{extra}{ld_html}
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:image" content="{SITE}/assets/og.png"><meta property="og:url" content="{SITE}{path}">
{FONTS}<link rel="stylesheet" href="/assets/style.css"></head><body>
<header class="top"><div class="wrap"><img src="/assets/logo.svg" alt=""><a class="brand" href="/">Borrowed Hindsight</a>
<nav><a href="/#stories">Stories</a>{nl_nav}<a href="/about/">About</a><a class="ext" href="https://www.instagram.com/borrowed.hindsight/">Instagram</a><a class="ext" href="https://www.youtube.com/@borrowedhindsight">YouTube</a></nav></div></header>
{body}
<footer><div class="wrap"><span>© {dt.date.today().year} Borrowed Hindsight</span><a href="/about/">About</a><a href="{FACEBOOK}">Facebook</a><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a><a href="mailto:borrowedhindsight@gmail.com">Contact</a>
<span>General education, not personal or financial advice. Our publishing tool uses YouTube API Services: see our <a href="/privacy/">Privacy policy</a> and the <a href="https://www.youtube.com/t/terms">YouTube Terms of Service</a>.</span></div></footer></body></html>'''


def signup(where='home'):
    if not NEWSLETTER:
        return ''
    head = 'Get one borrowed lesson a week' if where == 'home' else 'Liked this? Get one like it every week'
    return f'''<section class="signup" id="newsletter"><div><h2>{head}</h2>
<p>One true story a week of someone who started small and built something big, and the one lesson you can borrow from it. Free. Unsubscribe anytime.</p></div>
<div><iframe src="{NEWSLETTER}/embed" title="Subscribe to the Borrowed Hindsight newsletter" scrolling="no"></iframe>
<p class="note"><a href="{NEWSLETTER}/subscribe" rel="noopener">Or subscribe on Substack →</a></p></div></section>'''


def write(rel, content):
    p = OUT / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content)


ORG = {'@type': 'Organization', '@id': f'{SITE}/#org', 'name': 'Borrowed Hindsight', 'url': SITE + '/',
       'logo': {'@type': 'ImageObject', 'url': f'{SITE}/assets/apple-touch-icon.png'},
       'sameAs': ['https://www.instagram.com/borrowed.hindsight/', 'https://www.youtube.com/@borrowedhindsight', FACEBOOK],
       'email': 'borrowedhindsight@gmail.com'}


def crumbs(items):
    return {'@type': 'BreadcrumbList', '@context': 'https://schema.org', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': SITE + u} for i, (n, u) in enumerate(items)]}


def main():
    shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir()
    shutil.copytree(ROOT / 'assets', OUT / 'assets'); shutil.copy(ROOT / 'CNAME', OUT / 'CNAME')
    stories = sorted([s for s in json.load(open(ROOT / 'stories.json')) if s['date'] <= TODAY], key=lambda s: s['date'], reverse=True)

    cards = ''.join(f'<a class="card" href="/stories/{s["slug"]}/"><span class="tag">{E(s["tag"])}</span><h3>{E(s["title"])}</h3><p>{E(s["summary"])}</p></a>' for s in stories)
    home = f'''<section class="hero"><div class="wrap"><h1>They started with almost nothing. Their hindsight is yours to <span class="script">borrow</span>.</h1>
<p class="lead">True, sourced stories of founders, late starters, comebacks and record-breakers: the low point, the climb, and one lesson you can use in your own life.</p>
<div class="btns"><a class="btn" href="https://www.instagram.com/borrowed.hindsight/">Follow on Instagram</a><a class="btn alt" href="https://www.youtube.com/@borrowedhindsight">Watch on YouTube</a></div></div></section>
<main class="wrap"><h2 id="stories">Latest stories</h2><div class="cards">{cards or "<p>First stories coming soon.</p>"}</div>
{signup('home')}<p class="note">Every story is researched and sourced. Videos are animated and AI-narrated. Nothing here is personal or financial advice. <a href="/about/">How we research our stories</a>.</p></main>'''
    home_ld = [{'@context': 'https://schema.org', '@graph': [ORG, {'@type': 'WebSite', '@id': f'{SITE}/#site', 'url': SITE + '/', 'name': 'Borrowed Hindsight',
               'description': 'True, sourced stories of people who started small and built something big, with one lesson to borrow.', 'publisher': {'@id': f'{SITE}/#org'}, 'inLanguage': 'en'},
               {'@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': f'{SITE}/stories/{s["slug"]}/'} for i, s in enumerate(stories)]}]}]
    write('index.html', page('Borrowed Hindsight: true stories of people who started from nothing', 'True, sourced stories of founders, late starters, comebacks and record-breakers, and one lesson you can borrow from each.', home, ld=home_ld))

    for s in stories:
        url = f'/stories/{s["slug"]}/'
        paras = ''.join(f'<p>{E(p)}</p>' for p in s['body'])
        checks = ''.join(f'<li>{E(c)}</li>' for c in s['check'])
        srcs = ''.join(f'<li>{f"<a href={chr(34)}{E(u)}{chr(34)} rel=\"nofollow noopener\">{E(t)}</a>" if u else E(t)}</li>' for t, u in s['sources'])
        faq = s.get('faq', [])
        faq_html = ('<section class="faq"><h2>Questions people ask</h2>' + ''.join(f'<details><summary>{E(q)}</summary><p>{E(a)}</p></details>' for q, a in faq) + '</section>') if faq else ''
        d = dt.date.fromisoformat(s['date']); dtxt = d.strftime('%-d %B %Y')
        mod = s.get('updated', s['date'])
        related = [r for r in stories if r is not s][:3]
        rel_html = ('<section class="related"><h2>More borrowed hindsight</h2><div class="cards">' + ''.join(
            f'<a class="card" href="/stories/{r["slug"]}/"><span class="tag">{E(r["tag"])}</span><h3>{E(r["title"])}</h3></a>' for r in related) + '</div></section>') if related else ''
        body = f'''<main class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> › <a href="/#stories">Stories</a> › <span>{E(s["title"])}</span></nav>
<article><span class="meta">{E(s["tag"])} · <time datetime="{s["date"]}">{dtxt}</time> · By Borrowed Hindsight</span><h1>{E(s["title"])}</h1>
<p class="lead">{E(s["summary"])}</p><h2>The story</h2>{paras}
<div class="lesson"><b>The borrowed hindsight</b>{E(s["lesson"])}</div>
<div class="check"><h3>{E(s["check_title"])}</h3><ul>{checks}</ul></div>
<p><a class="btn" href="{E(s["reel"])}">Watch the video</a></p>{signup('story')}{faq_html}
<div class="sources"><h2>Sources</h2><ol>{srcs}</ol><p class="note">General education, not personal or financial advice. Spotted an error? Email borrowedhindsight@gmail.com and we'll correct it. <a href="/about/">How we research</a>.</p></div></article>{rel_html}</main>'''
        art = {'@context': 'https://schema.org', '@type': 'Article', 'headline': s['title'][:110], 'description': s['summary'],
               'datePublished': f'{s["date"]}T19:30:00+05:30', 'dateModified': f'{mod}T19:30:00+05:30',
               'author': {'@type': 'Organization', 'name': 'Borrowed Hindsight', 'url': SITE + '/about/'}, 'publisher': ORG,
               'image': [f'{SITE}/assets/og.png'], 'mainEntityOfPage': SITE + url, 'articleSection': s['tag'], 'inLanguage': 'en',
               'keywords': ', '.join(s.get('keywords', [])) or None,
               'citation': [u for _, u in s['sources'] if u] or None}
        art = {k: v for k, v in art.items() if v is not None}
        ld = [art, crumbs([('Home', '/'), ('Stories', '/#stories'), (s['title'], url)])]
        if faq:
            ld.append({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
                {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]})
        extra = f'<meta property="article:published_time" content="{s["date"]}T19:30:00+05:30"><meta property="article:modified_time" content="{mod}T19:30:00+05:30"><meta property="article:section" content="{E(s["tag"])}">'
        title = s.get('seo_title') or s['title']
        write(f'stories/{s["slug"]}/index.html', page(f'{title} | Borrowed Hindsight', s['summary'], body, url, ld=ld, og_type='article', extra=extra))

    about = '''<h1>About Borrowed Hindsight</h1>
<p>Borrowed Hindsight tells true stories of people who started with very little, or were told no, or started late, and built something remarkable anyway: the low point, the choice, the climb, and one line of hindsight you can borrow for your own life.</p>
<h2>How we research</h2><p>Every story is built from primary or reputable sources: court and company records, peer-reviewed studies, official statistics, and major publications quoting primary sources. Each story page lists its sources. If a popular statistic or story can't be traced to a real source, we say so instead of repeating it.</p>
<h2>How the videos are made</h2><p>Our short videos are animated and narrated with an AI voice. Scripts are researched and checked before publishing.</p>
<h2>What we don't do</h2><p>We don't give personal financial, investment, legal or career advice, and we don't recommend products, stocks or apps. We judge decisions by what was known at the time, not by how they turned out.</p>
<h2>Corrections</h2><p>Found an error? Email <a href="mailto:borrowedhindsight@gmail.com">borrowedhindsight@gmail.com</a> and we'll check it and correct the page.</p>'''
    write('about/index.html', page('About Borrowed Hindsight: how we research our stories', 'Who we are, how every Borrowed Hindsight story is researched and sourced, and our corrections policy.',
          f'<main class="wrap legal">{about}</main>', '/about/', ld=[{'@context': 'https://schema.org', '@type': 'AboutPage', 'url': SITE + '/about/', 'publisher': ORG}]))

    for name in ('privacy', 'terms'):
        body = (ROOT / f'{name}.html').read_text()
        title = 'Privacy policy' if name == 'privacy' else 'Terms of use'
        write(f'{name}/index.html', page(f'{title} | Borrowed Hindsight', f'{title} for borrowedhindsight.org and the Borrowed Hindsight channels.', f'<main class="wrap legal">{body}</main>', f'/{name}/'))
    write('404.html', page('Not found | Borrowed Hindsight', 'Page not found', '<main class="wrap legal"><h1>Not found</h1><p><a href="/">Back to the stories</a></p></main>').replace('index,follow', 'noindex'))

    newest = stories[0]['date'] if stories else TODAY
    urls = [('/', newest, '1.0'), ('/about/', newest, '0.5'), ('/privacy/', None, '0.2'), ('/terms/', None, '0.2')] + \
           [(f'/stories/{s["slug"]}/', s.get('updated', s['date']), '0.8') for s in stories]
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(
        f'<url><loc>{SITE}{u}</loc>{f"<lastmod>{m}</lastmod>" if m else ""}<priority>{pr}</priority></url>' for u, m, pr in urls) + '</urlset>')
    write('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n')
    items = ''.join(f'<item><title>{E(s["title"])}</title><link>{SITE}/stories/{s["slug"]}/</link><guid>{SITE}/stories/{s["slug"]}/</guid>'
                    f'<pubDate>{dt.datetime.fromisoformat(s["date"] + "T14:00:00+00:00").strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate><description>{E(s["summary"])}</description></item>' for s in stories)
    write('feed.xml', f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Borrowed Hindsight</title><link>{SITE}/</link>'
          f'<description>True stories of people who started from nothing, and the lesson to borrow.</description><language>en</language>{items}</channel></rss>')
    print('built', len(stories), 'stories')

if __name__ == '__main__':
    main()
