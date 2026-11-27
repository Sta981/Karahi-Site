"""Render seeded records in Jinja and test static browser interactions, not Flask requests."""
import runpy, pathlib, re, base64, mimetypes
from types import SimpleNamespace
from datetime import date
from jinja2 import Environment,FileSystemLoader,StrictUndefined,select_autoescape
from playwright.sync_api import sync_playwright
root=pathlib.Path(__file__).resolve().parents[1];r=runpy.run_path(str(root/'tools/check_demo_week.py'));m=r['m'];db=r['db']
from app.operations import due,paid_total
from app.staff_operations import table_state,cash_summary,ingredient_balance
from app.access import ROLE_PERMISSIONS,role_name
from urllib.parse import urlencode

def url_for(endpoint,**kw):
    return '/static/'+kw['filename'] if endpoint=='static' else '/'+endpoint.replace('.','/')+('?' +urlencode(kw) if kw else '')
env=Environment(loader=FileSystemLoader(root/'app/templates'),autoescape=select_autoescape(['html']),undefined=StrictUndefined)
env.globals.update(url_for=url_for,csrf_token=lambda:'fixture',role_name=role_name,permitted=lambda u,p:p in ROLE_PERMISSIONS[role_name(u)],get_flashed_messages=lambda **kw:[])
users={u.role.name:u for u in m.User.query.all()};orders=m.Order.query.all();active=[o for o in orders if o.status in ('placed','preparing','ready','out_for_delivery')];tables=m.DiningTable.query.all();states={t.id:table_state(t)[0] for t in tables};items=m.MenuItem.query.all();ingredients=m.Ingredient.query.all();sessions=m.CashSession.query.all();history=m.Payment.query.filter_by(status='paid').all();owner=users['owner'];cashier=users['cashier'];chef=users['chef'];waiter=users['waiter'];staff=m.StaffMember.query.filter_by(user_id=chef.id).first()
fixtures=[('kitchen',chef,dict(orders=active)),('waiter',waiter,dict(orders=[o for o in active if o.waiter_id==waiter.id],tables=tables,table_states=states,items=items)),('billing',cashier,dict(orders=active,methods=m.PaymentMethod.query.all(),due=due,history=history)),('purchases',users['inventory'],dict(purchases=m.PurchaseOrder.query.all(),suppliers=m.Supplier.query.all(),ingredients=ingredients)),('cash_register',cashier,dict(active=next(s for s in sessions if not s.closed_at),sessions=sessions,summaries={s.id:cash_summary(s) for s in sessions})),('floor',waiter,dict(tables=tables,table_states=states)),('history',chef,dict(orders=[o for o in orders if o.status=='completed'])),('recipes',chef,dict(items=items,recipes=m.ItemIngredient.query.all(),ingredients={i.id:i for i in ingredients},balances={i.id:ingredient_balance(i,date.today()) for i in ingredients})),('notifications',owner,dict(notifications=m.Notification.query.filter_by(user_id=owner.id).all())),('personal',chef,dict(profile=staff,shifts=m.StaffShift.query.filter_by(staff_id=staff.id).all(),attendance=m.AttendanceRecord.query.filter_by(staff_id=staff.id).all(),leaves=staff.leaves,payroll=staff.payroll_records))]
base=dict(demo_mode=True,currency_code='PKR',currency_symbol='Rs. ',unread_notifications=1)
html={}
for kind,u,extra in fixtures:
    html[kind]=env.get_template('workspace/dashboard.html').render(**base,**extra,current_user=u,kind=kind,request=SimpleNamespace(endpoint='workspace.'+kind,args={}))
    print('RENDER PASS',kind)
payment=history[0];html['receipt']=env.get_template('workspace/receipt.html').render(**base,current_user=cashier,request=SimpleNamespace(endpoint='workspace.receipt'),payment=payment,paid=paid_total(payment.order),balance=due(payment.order));print('RENDER PASS receipt')
static=root/'app/static'
def inline(s):
    s=re.sub(r'<link[^>]*href="/static/([^"\s]+\.css)"[^>]*>',lambda a:'<style>'+ (static/a.group(1)).read_text()+'</style>',s)
    s=re.sub(r'<script src="/static/([^"\s]+\.js)"[^>]*></script>',lambda a:'<script>'+ (static/a.group(1)).read_text()+'</script>',s)
    s=re.sub(r' src="/static/([^"]+)"',lambda a:' src="data:'+ (mimetypes.guess_type(a.group(1))[0] or 'application/octet-stream')+';base64,'+base64.b64encode((static/a.group(1)).read_bytes()).decode()+'"',s)
    return s
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);errors=[]
    for width in (1440,390):
        page=browser.new_page(viewport={'width':width,'height':900},reduced_motion='reduce');page.on('pageerror',lambda e:errors.append(str(e)))
        for kind,s in html.items():
            page.set_content(inline(s));assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2'),(width,kind)
            if kind in ('waiter','purchases'):
                form=page.locator('[data-lines]');form.locator('[data-add]').click();assert form.locator('[data-line]').count()==2;form.locator('[data-remove]').last.click();assert form.locator('[data-line]').count()==1
                if kind=='waiter':form.locator('[name=item_id]').select_option(str(items[0].id));form.locator('[name=qty]').fill('2');assert float(form.locator('[data-total]').inner_text())==round(items[0].effective_price*2,2)
            if kind=='floor':assert page.locator('.floor-table').count()==len(tables)
        print('VIEWPORT PASS',width);page.close()
    assert not errors,errors;browser.close();print('BROWSER PASS: staff page widths, multi-line add/remove, price preview, floor tiles')
