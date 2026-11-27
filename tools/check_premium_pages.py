"""Render real seeded SQLAlchemy records through Jinja; not a Flask route test.
Optional Chromium screenshots and browser interactions use a local static fixture server.
"""
import runpy, pathlib, tempfile, shutil, threading, http.server, functools, contextlib, sys
from types import SimpleNamespace
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from datetime import date
root=pathlib.Path(__file__).resolve().parents[1]
data=runpy.run_path(str(root/'tools/check_demo_week.py'));m=data['m'];db=data['db']
from app.presentation import menu_image
from urllib.parse import urlencode
paths={'main.home':'/','main.menu':'/menu','main.item_detail':'/menu/{item_id}','main.reserve':'/reserve','main.about':'/about','main.contact':'/contact','main.set_order_type':'/order-type','shop.cart_view':'/cart','shop.checkout':'/checkout','shop.orders':'/orders','shop.order_detail':'/orders/{order_id}','shop.profile':'/profile','workspace.home':'/workspace/','workspace.customer':'/workspace/customer','auth.login':'/account/login','auth.register':'/account/register','auth.staff_login':'/account/staff-login','auth.logout':'/account/logout'}
def url_for(endpoint,**kwargs):
    if endpoint=='static':return '/static/'+kwargs['filename']
    path=paths.get(endpoint,'/'+endpoint.replace('.','/')); keys=list(kwargs)
    for k in keys:
        if '{'+k+'}' in path:path=path.replace('{'+k+'}',str(kwargs.pop(k)))
    return path+('?' + urlencode(kwargs) if kwargs else '')
env=Environment(loader=FileSystemLoader(root/'app/templates'),autoescape=select_autoescape(['html']),undefined=StrictUndefined)
env.globals.update(url_for=url_for,csrf_token=lambda:'fixture-only',menu_image=menu_image,currency_symbol='Rs. ',get_flashed_messages=lambda **kw:[])
u=m.User.query.filter_by(email='ayesha@example.com').one(); store=m.StoreInfo.query.first();items=m.MenuItem.query.filter_by(is_available=True).all();cats=[(c,[i for i in items if i.category_id==c.id]) for c in m.Category.query.all()];cats=[(c,i) for c,i in cats if i]; orders=m.Order.query.filter_by(user_id=u.id).order_by(m.Order.id.desc()).all(); cart=m.Cart.query.first(); assert cart and cart.items
base=dict(current_user=u,staff_profile=None,store=store,store_status={'text':'Opening hours'},cart=cart,order_type='pickup',currency_symbol='Rs. ',year=date.today().year,demo_mode=True,storefront=False,request=SimpleNamespace(path='/',full_path='/'),errors={},form={})
menu=dict(categories=cats,promos=m.Promotion.query.all(),tags=m.Tag.query.all(),q='',active_tag=None,count=len(items),storefront=True)
fixtures={'/':('main/home.html',menu),'/menu':('main/menu.html',menu),'/menu/'+str(items[0].id):('main/item.html',dict(item=items[0],my_review=None)), '/reserve':('main/reserve.html',dict(form={'guest_name':u.name,'guest_phone':u.phone})), '/about':('main/about.html',dict(hours=store.hours,days=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])), '/contact':('main/contact.html',dict(departments=[('management','Restaurant manager','Events and enquiries'),('kitchen','Kitchen','Menu questions')])), '/workspace/customer':('workspace/customer.html',dict(orders=orders,reservations=u.reservations,requests=m.ServiceRequest.query.filter_by(customer_id=u.id).all())), '/orders':('shop/orders.html',dict(orders=orders)), '/orders/'+str(orders[0].id):('shop/order_detail.html',dict(order=orders[0])), '/cart':('shop/cart.html',{}),'/checkout':('shop/checkout.html',dict(methods=m.PaymentMethod.query.all())), '/profile':('shop/profile.html',dict(user=u,favorites=m.Favorite.query.filter_by(user_id=u.id).all())), '/account/login':('auth/login.html',dict(error=None,email='')), '/account/register':('auth/register.html',{}),'/error':('error.html',dict(code=404,message='Page not found'))}
html={}
for path,(name,extra) in fixtures.items():
    ctx={**base,**extra};ctx['request']=SimpleNamespace(path=path,full_path=path); html[path]=env.get_template(name).render(**ctx);print('RENDER PASS',path)
if '--browser' not in sys.argv:sys.exit(0)
from playwright.sync_api import sync_playwright
import re, base64, mimetypes
static=root/'app/static'
def asset(relative):
    path=static/relative
    return 'data:'+ (mimetypes.guess_type(path.name)[0] or 'application/octet-stream')+';base64,'+base64.b64encode(path.read_bytes()).decode()
def inline(source):
    # Preview without network requests; browser environment blocks navigation.
    def css(match):
        path=static/match.group(1); body=path.read_text()
        body=re.sub(r"url\(['\"]?\.\./([^'\")]+)['\"]?\)",lambda m:'url('+asset(m.group(1))+')',body)
        return '<style>'+body+'</style>'
    source=re.sub(r'<link[^>]*href="/static/([^"\s]+\.css)"[^>]*>',css,source)
    source=re.sub(r'<script src="/static/([^"\s]+\.js)" defer></script>',lambda m:'<script>'+ (static/m.group(1)).read_text().replace('const url = new URL(location.href);','const url = new URL(location.href);')+'</script>',source)
    source=re.sub(r' src="/static/([^"]+)"',lambda m:' src="'+asset(m.group(1))+'"',source)
    source=re.sub(r'<link[^>]*href="https?://[^"]+"[^>]*>','',source)
    return source
output=pathlib.Path(sys.argv[sys.argv.index('--browser')+1]);output.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);errors=[]
    for width in [1440,390]:
        page=browser.new_page(viewport={'width':width,'height':900},reduced_motion='reduce');page.on('pageerror',lambda e:errors.append(str(e)))
        for path,source in html.items():
            page.set_content(inline(source),wait_until='load');page.wait_for_timeout(50);assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2'),f'Horizontal overflow: {path} at {width}'
            if path == '/menu':
                cards=page.locator('.premium-dish')
                assert cards.count()==len(items)==24
                assert cards.first.is_visible()
                first=cards.first.bounding_box()
                assert first['y'] < 900, f'First dish below fold: {first}'
                print('MENU PASS',width,'cards',cards.count(),'first card y',round(first['y']))
            if path in ['/','/menu','/reserve','/about','/workspace/customer','/orders','/cart','/checkout','/account/login'] and width==1440:page.screenshot(path=str(output/((path.strip('/').replace('/','-') or 'home')+'.png')))
        print('VIEWPORT PASS',width);page.close()
    page=browser.new_page(viewport={'width':1440,'height':900},reduced_motion='reduce');page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(inline(html['/']));assert page.locator('.hero-discover').get_attribute('href')=='#discover';assert page.locator('#discover').count()==1;assert page.locator('.hero-actions a').first.get_attribute('href')=='/menu'
    page.locator('.cart-link').click();assert page.locator('#bag-drawer').evaluate('el=>el.open');page.keyboard.press('Escape');assert not page.locator('#bag-drawer').evaluate('el=>el.open');page.close()
    page=browser.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(inline(html['/reserve']));page.locator('[data-book-next]').click();page.locator('#when').fill('2030-01-01T18:00');page.locator('[data-book-next]').click();assert page.locator('[data-book-submit]').is_visible();assert '2030-01-01' in page.locator('[data-book-preview]').inner_text();page.locator('[data-book-back]').click();assert page.locator('#when').is_visible()
    assert not errors,errors;print('BROWSER PASS: link targets, drawer, reservation steps, no JavaScript errors');browser.close()
