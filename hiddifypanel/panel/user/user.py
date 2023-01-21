from flask import abort, render_template,request,Response
from wtforms.validators import Regexp,ValidationError
import urllib,uuid
import datetime
from hiddifypanel.models import User,Domain,BoolConfig,StrConfig,DomainType,ConfigEnum,get_hconfigs,get_hdomains

def index(secret,lang="fa"):
    c=get_common_data(secret)
    if lang=="fa":
        return render_template('index_fa.html',**c)
    return  render_template('index_en.html',**c)



def clash_proxies(secret,meta_or_normal="normal"):
    c=get_common_data(secret)
    resp= Response(render_template('clash_proxies.yml',meta_or_normal=meta_or_normal,**c))
    resp.mimetype="text/plain"
    return resp

def clash_config(secret,meta_or_normal="normal",mode="all.yml"):
    
    
    c=get_common_data(secret)
    


    resp= Response(render_template('clash_config.yml',mode=mode,meta_or_normal=meta_or_normal,**c,hash=hash(f'{c}')))
    resp.mimetype="text/plain"
    resp.headers['Subscription-Userinfo']=f"upload=0;download={c['usage_current_b']};total={c['usage_limit_b']};expire={c['expire_s']}"
    return resp


def all_configs(secret):
    c=get_common_data(secret)
    # response.content_type = 'text/plain';
    
    resp= render_template('all_configs.txt',**c,base64=do_base_64)
    res=""
    for line in resp.split("\n"):
        if "vmess://" in line:
            line="vmess://"+do_base_64(line.replace("vmess://",""))
        res+=line+"\n"
    return Response(res,mimetype="text/plain")

def do_base_64(str):
    import base64
    resp=base64.b64encode(f'{str}'.encode("utf-8"))
    return resp.decode()
    
def get_common_data(secret):
    from urllib.parse import urlparse
    
    o = urlparse(request.base_url)
    db_domain=Domain.query.filter(Domain.domain==o.hostname).first()
    domain=o.hostname
    is_cdn=False
    if db_domain and db_domain.mode==DomainType.cdn:
        direct_host=urllib.request.urlopen('https://v4.ident.me/').read().decode('utf8')
        is_cdn=True
        
    direct_host= domain
    uuid_secret=str(uuid.UUID(secret))
    user=User.query.filter(User.uuid==uuid_secret).first()
    if user is None:
        raise ValidationError("Invalid User")

    return {
        'direct_host':direct_host,
        'user':user,
        'domain':domain,
        'is_cdn':is_cdn,
        'usage_limit_b':User.monthly_usage_limit_GB*1024*1024*1024,
        'usage_current_b':User.current_usage_GB*1024*1024*1024,
        'expire_s':(user.expiry_time-datetime.date(1970, 1, 1)).total_seconds,
        'expire_days':(user.expiry_time-datetime.date.today()).days,
        'hconfigs':get_hconfigs(),
        'hdomains':get_hdomains(),
        'ConfigEnum':ConfigEnum,
    }
    