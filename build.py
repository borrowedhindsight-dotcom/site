"""Build borrowedhindsight.com into _site/ from stories.json (stories dated in the future stay hidden)."""
import json, html, shutil, pathlib, datetime as dt

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / '_site'
TODAY = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=5, minutes=30)).date().isoformat()
SITE = 'https://borrowedhindsight.com'
E = html.escape

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Caveat+Brush&family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">')


def page(title, desc, body, path='/'):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">
<link rel="canonical" href="{SITE}{path}"><link rel="icon" href="/assets/favicon.png"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:image" content="{SITE}/assets/og.png"><meta property="og:url" content="{SITE}{path}">
{FONTS}<link rel="stylesheet" href="/assets/style.css"></head><body>
<header class="top"><div class="wrap"><img src="/assets/logo.svg" alt=""><a class="brand" href="/">Borrowed Hindsight</a>
<nav><a href="/#stories">Stories</a><a href="https://www.instagram.com/borrowed.hindsight/">Instagram</a><a href="https://www.youtube.com/@borrowedhindsight">YouTube</a></nav></div></header>
{body}
<footer><div class="wrap"><span>© {dt.date.today().year} Borrowed Hindsight</span><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a><a href="mailto:borrowedhindsight@gmail.com">Contact</a>
<span>General education, not personal or financial advice.</span></div></footer></body></html>'''


def write(rel, content):
    p = OUT / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content)


def main():
    shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir()
    shutil.copytree(ROOT / 'assets', OUT / 'assets'); shutil.copy(ROOT / 'CNAME', OUT / 'CNAME')
    stories = sorted([s for s in json.load(open(ROOT / 'stories.json')) if s['date'] <= TODAY], key=lambda s: s['date'], reverse=True)

    cards = ''.join(f'<a class="card" href="/stories/{s["slug"]}/"><span class="tag">{E(s["tag"])}</span><h3>{E(s["title"])}</h3><p>{E(s["summary"])}</p></a>' for s in stories)
    home = f'''<section class="hero"><div class="wrap"><h1>Other people's hindsight, <span class="script">borrowed</span> for your next big decision.</h1>
<p class="lead">True stories of money and career decisions: what people chose, what happened, and the one question worth asking before you decide.</p>
<div class="btns"><a class="btn" href="https://www.instagram.com/borrowed.hindsight/">Follow on Instagram</a><a class="btn alt" href="https://www.youtube.com/@borrowedhindsight">Watch on YouTube</a></div></div></section>
<main class="wrap"><h2 id="stories">Latest stories</h2><div class="cards">{cards or "<p>First stories coming soon.</p>"}</div>
<p class="note">Every story is researched and sourced. Videos are animated and AI-narrated. Nothing here is personal or financial advice.</p></main>'''
    write('index.html', page('Borrowed Hindsight: lessons you don’t have to learn the hard way', 'True stories of money and career decisions, with sources, and one question worth asking before you decide.', home))

    for s in stories:
        paras = ''.join(f'<p>{E(p)}</p>' for p in s['body'])
        checks = ''.join(f'<li>{E(c)}</li>' for c in s['check'])
        srcs = ''.join(f'<li>{f"<a href={chr(34)}{E(u)}{chr(34)} rel=nofollow>{E(t)}</a>" if u else E(t)}</li>' for t, u in s['sources'])
        d = dt.date.fromisoformat(s['date']).strftime('%-d %B %Y')
        body = f'''<main class="wrap"><article><span class="meta">{E(s["tag"])} · {d}</span><h1>{E(s["title"])}</h1>{paras}
<div class="lesson"><b>The borrowed hindsight</b>{E(s["lesson"])}</div>
<div class="check"><h3>{E(s["check_title"])}</h3><ul>{checks}</ul></div>
<p><a class="btn" href="{E(s["reel"])}">Watch the 60-second version</a></p>
<div class="sources"><b>Sources</b><ol>{srcs}</ol><p class="note">General education, not personal or financial advice. Spotted an error? Email borrowedhindsight@gmail.com and we'll correct it.</p></div></article></main>'''
        write(f'stories/{s["slug"]}/index.html', page(f'{s["title"]} | Borrowed Hindsight', s['summary'], body, f'/stories/{s["slug"]}/'))

    for name in ('privacy', 'terms'):
        body = (ROOT / f'{name}.html').read_text()
        title = 'Privacy policy' if name == 'privacy' else 'Terms of use'
        write(f'{name}/index.html', page(f'{title} | Borrowed Hindsight', f'{title} for borrowedhindsight.com and the Borrowed Hindsight channels.', f'<main class="wrap legal">{body}</main>', f'/{name}/'))
    write('404.html', page('Not found | Borrowed Hindsight', 'Page not found', '<main class="wrap legal"><h1>Not found</h1><p><a href="/">Back to the stories</a></p></main>'))
    urls = ['/', '/privacy/', '/terms/'] + [f'/stories/{s["slug"]}/' for s in stories]
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{SITE}{u}</loc></url>' for u in urls) + '</urlset>')
    write('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n')
    print('built', len(stories), 'stories')


if __name__ == '__main__':
    main()
