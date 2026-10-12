"""Build real Arabic pages with RTL layout; English remains the source language."""
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
TEXT={}
for line in (ROOT/'tools/arabic_texts.txt').read_text(encoding='utf8').splitlines():
    if '|' in line:
        key,value=line.split('|',1);TEXT[key]=value
TEXT.update({
 'Mrasi Al Saada 2 · Film':'مراسي السعادة 2 · فيديو المشروع',
 'Animated architectural visualization of Mrasi Al Saada 2 supplied by Meridian':'تصوّر معماري متحرك لمراسي السعادة 2 مقدّم من ميرديان',
 'Children’s Library · Film':'مكتبة الأطفال · فيديو المشروع',
 'Animated architectural visualization of the Children’s Library supplied by Meridian':'تصوّر معماري متحرك لمكتبة الأطفال مقدّم من ميرديان',
 'Meridian Engineering Consultancy — Innovative Engineering, Lasting Solutions.':'ميرديان للاستشارات الهندسية — هندسة مبتكرة، حلول مستدامة.',
 'Selected projects across Oman — coastal developments, hotels, resorts, townships and hospitality venues.':'مشاريع مختارة في سلطنة عُمان، تشمل الواجهات الساحلية والفنادق والمنتجعات والمخططات العمرانية.',
 'Ten core disciplines — buildings, roads, bridges, tunnels, airports, railways, water, dams, sewage and oil & gas.':'عشرة تخصصات هندسية تشمل المباني والطرق والجسور والأنفاق والمطارات والسكك الحديدية والمياه والسدود والصرف الصحي والنفط والغاز.',
 'Building exterior visualization supplied in the Meridian project presentation.':'تصوّر لواجهة المبنى مقدّم ضمن عرض مشروع ميرديان.',
 'Pedestrian bridge visualization supplied by Meridian; still extracted from the project film.':'تصوّر لجسر مشاة مقدّم من ميرديان؛ لقطة مستخرجة من فيديو المشروع.',
})
SUFFIX=' Every engagement is scoped, programmed and reported against agreed deliverables.'

def translate(value):
    key=' '.join(value.split())
    if key in TEXT:return TEXT[key]
    if key.endswith(' details'):return 'تفاصيل '+translate(key[:-len(' details')])
    if key.endswith(SUFFIX):return translate(key[:-len(SUFFIX)])+' يُحدد نطاق كل مهمة وجدولها ومخرجاتها المتفق عليها وتُتابع عبر التقارير.'
    if key.endswith(' Imagery supplied by Meridian.'):return translate(key[:-len(' Imagery supplied by Meridian.')])+' الصور مقدّمة من ميرديان.'
    if ' — Meridian Engineering Consultancy' in key:return translate(key.replace(' — Meridian Engineering Consultancy',''))+' — ميرديان للاستشارات الهندسية'
    if key.startswith('Meridian on '):return 'ميرديان على '+key[len('Meridian on '):]
    if key.endswith(' — exterior visualization'):return translate(key.replace(' — exterior visualization',''))+' — تصوّر للواجهة'
    return key

class ArabicPage(HTMLParser):
    def __init__(self,page,asset_prefix='',switch_prefix='en/',page_prefix='',language='ar'):
        super().__init__(convert_charrefs=True)
        self.page=page;self.parts=[];self.raw=0;self.missing=[];self.language_link=False
        self.asset_prefix=asset_prefix;self.switch_prefix=switch_prefix;self.page_prefix=page_prefix;self.language=language
    def handle_decl(self,d):self.parts.append('<!'+d+'>')
    def handle_comment(self,d):self.parts.append('<!--'+d+'-->')
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if self.language=='ar' and tag=='link' and attrs.get('href','').startswith(('https://fonts.googleapis.com','https://fonts.gstatic.com')):return
        if tag in ('script','style'):self.raw+=1
        if tag=='html':attrs.update(lang=self.language,dir='rtl' if self.language=='ar' else 'ltr')
        switch=attrs.get('class')=='language-switch'
        if switch:
            self.language_link=True
            target='en' if self.language=='ar' else 'ar'
            attrs.update(href=self.switch_prefix+self.page,lang=target,hreflang=target,**{'aria-label':'View this page in English' if target=='en' else 'عرض الموقع باللغة العربية'})
        for key,value in list(attrs.items()):
            if value is None:continue
            if key in ('src','href','poster','data-src','data-src-mobile','data-full-image') and value.startswith('assets/'):
                attrs[key]=self.asset_prefix+value
            elif key=='href' and re.match(r'^[a-z]+\.html(?:#.*)?$',value):attrs[key]=self.page_prefix+value
            elif key=='srcset':attrs[key]=re.sub(r'(?<![\w/])assets/',self.asset_prefix+'assets/',value)
            elif self.language=='ar':
                if key=='data-words':attrs[key]=json.dumps([translate(w) for w in json.loads(value)],ensure_ascii=False)
                elif key in ('alt','title','placeholder','data-name','data-client','data-cat-label','data-desc','aria-label') and not switch:attrs[key]=translate(value)
                elif tag=='meta' and key=='content' and attrs.get('name',attrs.get('property','')) in ('description','og:title','og:description'):attrs[key]=translate(value)
        self.parts.append('<'+tag+''.join(' '+k+(('="'+escape(v,quote=True)+'"') if v is not None else '') for k,v in attrs.items())+'>')
    def handle_startendtag(self,t,a):
        self.handle_starttag(t,a)
        self.parts[-1]=self.parts[-1][:-1]+' />'
    def handle_endtag(self,t):
        self.parts.append('</'+t+'>')
        if t in ('script','style'):self.raw-=1
        if t=='a':self.language_link=False
        if t=='head' and self.language=='ar':
            self.parts.insert(len(self.parts)-1,f'<link rel="stylesheet" href="{self.asset_prefix}assets/fonts/noto-sans-arabic.css"><link rel="preload" href="{self.asset_prefix}assets/fonts/noto-sans-arabic-variable-arabic.woff2" as="font" type="font/woff2" crossorigin>')
    def handle_data(self,value):
        if self.raw or not value.strip():self.parts.append(value);return
        if self.language_link:self.parts.append('English' if self.language=='ar' else 'العربية');return
        if self.language=='en':self.parts.append(escape(value));return
        translated=translate(value)
        key=' '.join(value.split())
        if translated==key and re.search('[A-Za-z]{3}',key) and not re.search(r'@|^\+?\d|^SAS$|^FIC$',key):self.missing.append(key)
        leading=value[:len(value)-len(value.lstrip())];trailing=value[len(value.rstrip()):]
        self.parts.append(leading+escape(translated)+trailing)

def render_arabic(html,page,**options):
    p=ArabicPage(page,**options);p.feed(html)
    if p.missing:raise ValueError('Missing Arabic text: '+json.dumps(p.missing,ensure_ascii=False))
    return ''.join(p.parts)

def render_english(html,page):
    p=ArabicPage(page,asset_prefix='../',switch_prefix='../',language='en');p.feed(html)
    return ''.join(p.parts)
