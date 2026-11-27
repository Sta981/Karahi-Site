"""Browser verification for shared header and homepage using seeded Jinja fixtures.
Not a live Flask request test. Run from repository with Chromium and Playwright.
"""
import runpy, pathlib, sys, base64, mimetypes, re
from types import SimpleNamespace
from playwright.sync_api import sync_playwright
root=pathlib.Path(__file__).resolve().parents[1]
# Existing fixture script exits before browser tests; execute just its rendering setup.
source=(root/'tools/check_premium_pages.py').read_text().split("if '--browser' not in sys.argv:sys.exit(0)")[0]
ns={'__file__':str(root/'tools/check_premium_pages.py')};exec(compile(source,ns['__file__'],'exec'),ns)
static=root/'app/static'
def asset(relative):
    path=static/relative
    return 'data:'+(mimetypes.guess_type(path.name)[0] or 'application/octet-stream')+';base64,'+base64.b64encode(path.read_bytes()).decode()
def inline(source):
    def css(m):
        body=(static/m.group(1)).read_text()
        body=re.sub(r"url\(['\"]?\.\./([^'\")]+)['\"]?\)",lambda m:'url('+asset(m.group(1))+')',body)
        return '<style>'+body+'</style>'
    source=re.sub(r'<link[^>]*href="/static/([^"\s]+\.css)"[^>]*>',css,source)
    source=re.sub(r'<script src="/static/([^"\s]+\.js)" defer></script>',lambda m:'<script>'+ (static/m.group(1)).read_text()+'</script>',source)
    source=re.sub(r' src="/static/([^\"]+)"',lambda m:' src="'+asset(m.group(1))+'"',source)
    return re.sub(r'<link[^>]*href="https?://[^\"]+"[^>]*>','',source)
base=ns['base'];env=ns['env'];menu=ns['menu'];out=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else root/'artifacts/glass';out.mkdir(parents=True,exist_ok=True)
guest=env.get_template('main/home.html').render(**{**base,**menu,'request':SimpleNamespace(path='/',full_path='/'),'current_user':None,'cart':None})
member=ns['html']['/']; menu_html=ns['html']['/menu']; errors=[]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    for width in [320,390,768,1024,1151,1440,1920]:
        page=browser.new_page(viewport={'width':width,'height':900 if width>=768 else 844},reduced_motion='reduce');page.on('pageerror',lambda e:errors.append(str(e)))
        for label,html in [('guest',guest),('customer',member)]:
            page.set_content(inline(html),wait_until='load');page.wait_for_timeout(100)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+2'),(label,width,'overflow')
            assert page.locator('.site-header .bar').evaluate("el=>getComputedStyle(el).backdropFilter.includes('blur')")
            assert page.locator('.site-header .bar').evaluate("el=>getComputedStyle(el).backgroundColor.includes('0.31')")
            assert page.locator('.hero-editorial').bounding_box()['y'] <= 1
            assert page.locator('.hero-actions a').first.get_attribute('href')=='/menu'
            assert page.locator('.hero-discover').get_attribute('href')=='#discover'
            assert page.locator('.nav [aria-current=page]').inner_text()=='Home'
            if label=='guest':
                assert page.locator('.account-link').get_attribute('href')=='/account/login'
                if width in (390,1440,1920):page.screenshot(path=str(out/f'homepage-{width}.png'))
            else:
                page.locator('.account-menu summary').click();assert page.locator('.account-popover a').first.is_visible();page.keyboard.press('Escape');assert not page.locator('.account-menu').evaluate('el=>el.open')
            if width<=1150:
                toggle=page.locator('.nav-toggle');toggle.click();assert toggle.get_attribute('aria-expanded')=='true';assert page.locator('.nav a').count()==5;assert page.locator('.nav a').last.is_visible();page.keyboard.press('Escape');assert toggle.get_attribute('aria-expanded')=='false'
            else:
                assert page.locator('.nav a').last.is_visible()
                assert page.locator('.nav').bounding_box()['x']+page.locator('.nav').bounding_box()['width'] <= page.locator('.actions').bounding_box()['x']+1
            page.locator('.cart-link').click();assert page.locator('#bag-drawer').evaluate('el=>el.open');page.keyboard.press('Escape')
            page.wait_for_function("!document.querySelector('#bag-drawer').open");page.wait_for_timeout(120);page.evaluate('window.scrollTo({top:500,behavior:"instant"})');page.wait_for_function("document.querySelector('.site-header').classList.contains('is-scrolled')",timeout=3000);assert abs(page.locator('.site-header').bounding_box()['y'])<1
            page.evaluate('window.scrollTo(0,0)')
        print('HEADER PASS guest + signed-in',width)
        page.close()
    assert not errors,errors
    browser.close()
print('PASS: 7 widths, both account states, glass opacity, sticky scroll, active links, mobile menu, account dropdown, cart drawer')
