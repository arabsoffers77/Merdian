"""Package the static backup and a separate Arabic media review. Never uploads."""
import csv
import json
from html import escape
from pathlib import Path
import re
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'delivery'
BASE=['index.html','about.html','services.html','projects.html','disciplines.html','contact.html']
PAGES=BASE+['en/'+p for p in BASE]+['ar/'+p for p in BASE]

def review_html(catalog):
    video=catalog['video']
    desktop,mobile=video['outputs']['desktop'],video['outputs']['mobile']
    cards=[]
    comparison='''<section id="colors"><h2>قارن الألوان قبل المعالجة وبعدها</h2><p>ضُبط السطوع والتشبع لكل صورة، مع طابع دافئ مشترك. المعالجة تخص العرض وتحافظ على هندسة المباني وتفاصيلها؛ لم تُولّد مشاريع بديلة ولم تتغير الصور الأصلية.</p><button id="grade-toggle" type="button" aria-pressed="false">عرض الصور الأصلية</button><p id="grade-status" role="status">المعالجة اللونية مفعّلة</p><script>document.getElementById('grade-toggle').addEventListener('click',function(){var original=document.body.classList.toggle('show-original');this.textContent=original?'عرض المعالجة الجديدة':'عرض الصور الأصلية';this.setAttribute('aria-pressed',String(original));document.getElementById('grade-status').textContent=original?'تُعرض ألوان ملفات العميل الأصلية':'المعالجة اللونية مفعّلة';});</script></section>'''
    for p in catalog['projects']:
        image=min(p['variants'],key=lambda v:abs(v['width']-800))
        extra=f" — صفحة {p['pdf_page']}" if 'pdf_page' in p else (f" — لقطة عند الثانية {p['frame_seconds']}" if 'frame_seconds' in p else '')
        cards.append(f'''<article><div class="image"><img class="client-photo" src="../{image['src']}" loading="lazy" width="{image['width']}" height="{image['height']}" alt="{escape(p['alt'],quote=True)}"></div><div class="caption"><h2>{escape(p['name'])}</h2><p dir="ltr">{escape(p['source_filename'])}{extra}</p><p>الأصل المختار: {p['width']} × {p['height']} بكسل. النسخة المعروضة: {round(image['bytes']/1000)} KB.</p><a href="{p['source_url']}" target="_blank" rel="noopener">فتح مصدر العميل</a></div></article>''')
    return f'''<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ميرديان — مراجعة الوسائط</title>
<link rel="stylesheet" href="../assets/fonts/noto-sans-arabic.css"><link rel="stylesheet" href="../assets/css/photo-grade.css">
<style>body{{margin:0;background:#f6f5f2;color:#202020;font:16px/1.85 'Noto Sans Arabic',Tahoma,sans-serif}}main{{max-width:1200px;margin:auto;padding:32px 20px}}h1{{font-size:30px}}h2{{font-size:20px;margin:0}}a{{color:#754300}}header{{max-width:850px;margin-bottom:30px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:24px}}article{{background:white;border:1px solid #ddd;border-radius:12px;overflow:hidden}}.image{{position:relative}}.image:after{{content:'';position:absolute;inset:0;pointer-events:none;background:rgba(206,138,65,.055)}}article img{{display:block;width:100%;height:auto}}.caption{{padding:18px}}article p{{overflow-wrap:anywhere;font-size:14px}}.film{{width:100%;max-width:960px;display:block;background:#151515}}.comparison{{display:block;width:100%;height:auto;margin:20px 0}}section{{margin:40px 0}}button{{font:600 15px 'Noto Sans Arabic',sans-serif;padding:12px 20px;background:#f5a623;border:1px solid #a96700;border-radius:8px;cursor:pointer}}button:focus-visible{{outline:3px solid #333;outline-offset:3px}}.show-original .client-photo{{filter:none}}.show-original .image:after{{opacity:0}}</style>
<main><header><h1>ميرديان: مراجعة الصور والفيديو</h1><p>التحديث في النسخة الاحتياطية فقط. العربية هي لغة البداية، والإنجليزية متاحة بزر تبديل اللغة. لم يُنشر الموقع ولم تتغير النسخة الأصلية أو ملفات Drive.</p><p><a href="../index.html">الرئيسية</a> · <a href="../projects.html">المشاريع</a> · <a href="../en/index.html">English</a></p></header>
<section><h2>فيديو الرئيسية: مراسي السعادة 2 — لوب أمامي وعكسي</h2><p>المصدر: night view 2.mp4 من مجلد 02-MARRASI 2، بأبعاد أصلية 3840 × 2160. يعرض ثماني ثوانٍ للأمام ثم يعكسها للخلف؛ الدورة نحو 16 ثانية. أُزيل الإطار المكرر عند كل نقطة رجوع لمنع الوقفة والقفزة إلى البداية، وفُحص الانتقال بين الإطارات على طرفي اللوب. نسخة الحاسوب {desktop['width']} × {desktop['height']} بمعدل {desktop['fps']} إطارًا في الثانية وحجم {desktop['bytes']/1e6:.2f} MB؛ نسخة الهاتف {mobile['width']} × {mobile['height']} بمعدل {mobile['fps']} إطارًا في الثانية وحجم {mobile['bytes']/1e6:.2f} MB. في الموقع يبدأ بصورة معاينة، مع زر إيقاف وتأثير التمدد عند التمرير.</p><video class="film" controls muted loop playsinline preload="none" poster="../{video['poster']}" src="../{video['desktop']}"></video></section>
<section><h2>الألوان والحركة</h2><p>توحيد السطوع والتشبع لكل صورة مع لون دافئ مشترك؛ دون تغيير تفاصيل العمارة. خُفّض دوران بطاقات صفحة المشاريع وتحريك الصور إلى ربع التأثير السابق، والتكبير من 14% إلى 3.5%. بقيت حركة أقسام الرئيسية وشبكة المشاريع الأصلية. خلفية من نحن تستخدم حتى 30 صورة مختلفة دون تكرار. الخط العربي أصبح Noto Sans Arabic بأوزان متدرجة للعناوين والنصوص، محفوظًا محليًا.</p></section>{comparison}
<section><h2>توزيع صور الصفحات</h2><p>من نحن: Training Center. الخدمات: GIM Theatre. المشاريع: Grand Resort. التخصصات: Tilal District بصورة أوسع للمخطط. التواصل: Children’s Library. الرئيسية تعرض سبعة مشاريع مختارة وصفحة المشاريع تعرض الثلاثين.</p></section>
<section><h2>صورة واحدة لكل مشروع — 30 مشروعًا</h2><p>دُمجت المجلدات المتكررة للمسرح ومكتبة الأطفال. معظم الصور تصورات معمارية؛ لا تثبت التنفيذ. لم تُنسب أسماء عملاء أو حالة إنجاز غير موثقة. استُخرجت صورة الجسر من فيديو العميل. لم يظهر محتوى في مجلدي Engineering &amp; Environment وInfrastructure &amp; Mobility.</p><div class="grid">{''.join(cards)}</div></section>
<section><h2>حدود الفحص</h2><p>اختيار الصور مبني على المعاينات المتاحة وفتح الصور الأصلية المختارة ومقارنة صور PDF. تمت مقارنة ثلاث لقطات موزعة من كل فيديو من الفيديوهات الأربعة عشر، ثم تنزيل فيديو مكتبة الأطفال وفيديو مراسي السعادة 2 كاملين وفحصهما؛ اختير مراسي لوضوح تفاصيله وهدوء حركته. لم تتم مشاهدة جميع الفيديوهات كاملة أو فتح جميع الملفات الأصلية؛ «الأفضل» يعني الأفضل بين المواد التي أمكن معاينتها.</p><h2>مقارنة عينات الفيديوهات</h2><p>كل صف يعرض ثلاث لقطات من فيديو واحد. هذه لوحات مراجعة خارج حزمة النشر.</p><img class="comparison" src="video-comparison-1.jpg" loading="lazy" alt="عينات الفيديوهات من الأول إلى السابع"><img class="comparison" src="video-comparison-2.jpg" loading="lazy" alt="عينات الفيديوهات من الثامن إلى الرابع عشر"></section></main></html>'''

def main():
    OUT.mkdir(exist_ok=True)
    catalog=json.loads((ROOT/'assets/media/catalog.json').read_text(encoding='utf8'))
    selections=json.loads((ROOT/'tools/media_selections.json').read_text(encoding='utf8'))
    (OUT/'media-review.html').write_text(review_html(catalog),encoding='utf8')
    for n in (1,2):
        source=ROOT/f'_media_work/video-comparison-{n}.jpg'
        if source.exists():shutil.copy2(source,OUT/source.name)
    inventory_path=ROOT/'_media_work/inventory.json'
    if inventory_path.exists():
        inventory=json.loads(inventory_path.read_text(encoding='utf8'))
        with (OUT/'drive-inventory.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['Name','Path','Drive ID','Folder','Listed size','Preview available locally'])
            for p in inventory:writer.writerow([p['name'],p['path'],p['id'],p['folder'],p.get('size',''),(ROOT/f"_media_work/thumbs/{p['id']}.jpg").exists()])
    (OUT/'selected-media.json').write_text(json.dumps(selections,ensure_ascii=False,indent=2),encoding='utf8')
    files=[ROOT/p for p in PAGES]+[ROOT/'assets/img/favicon.png']
    for folder in ('css','js','vendor'):
        files.extend(p for p in (ROOT/'assets'/folder).rglob('*') if p.is_file() and p.suffix!='.json')
    font_css=ROOT/'assets/fonts/noto-sans-arabic.css'
    files.extend([font_css,ROOT/'assets/fonts/OFL-NotoSansArabic.txt'])
    files.extend(font_css.parent/ref for ref in re.findall(r'url\(([^)]+)\)',font_css.read_text(encoding='utf8')))
    media_refs={v['src'] for p in catalog['projects'] for v in p['variants']}
    media_refs.update(v for v in catalog['video'].values() if isinstance(v,str) and v.startswith('assets/media/'))
    media_refs.add('assets/media/logo.png')
    files.extend(ROOT/ref for ref in sorted(media_refs))
    names={p.relative_to(ROOT).as_posix() for p in files}
    for name in PAGES:
        html=(ROOT/name).read_text(encoding='utf8')
        for ref in re.findall(r'(?:src|href|poster|data-src|data-src-mobile|data-full-image)="([^"]+)"',html):
            if ref.startswith(('http','#','mailto:','tel:','data:')):continue
            ref=ref.split('?')[0].split('#')[0]
            resolved=((ROOT/name).parent/ref).resolve().relative_to(ROOT).as_posix() if ref else ''
            assert not ref or resolved in names,f'Missing packaged reference: {name}: {ref}'
    for ref in re.findall(r'url\(([^)]+)\)',font_css.read_text(encoding='utf8')):
        assert (font_css.parent/ref).relative_to(ROOT).as_posix() in names
    archive=OUT/'meridian-hostinger.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert 'index.html' in z.namelist()
        assert not any('_media_work' in p or p.startswith('tools/') or 'assets/img/hero-' in p or 'gim-theatre-film' in p or 'kids-library-film' in p for p in z.namelist())
        assert {p for p in z.namelist() if p.endswith('.mp4')}=={catalog['video']['desktop'],catalog['video']['mobile']}
    total=sum(p.stat().st_size for p in files)
    video=catalog['video'];desktop,mobile=video['outputs']['desktop'],video['outputs']['mobile']
    readme=f'''# تحديث ميرديان — النسخة الاحتياطية

تم العمل في D:\\work\\merdian\\Merdian فقط، دون نشر أو نسخ إلى المشروع الأصلي أو تعديل Drive.

- العربية هي النسخة الأساسية في جذر الموقع. الإنجليزية في en/. الروابط العربية السابقة ar/ ما زالت تعمل وتوجّه التنقل إلى الصفحات الأساسية.
- خط Noto Sans Arabic محفوظ محليًا مع رخصته في assets/fonts. المصدر الرسمي: https://github.com/google/fonts/tree/main/ofl/notosansarabic
- أزرار تبديل النص تتسع للعبارتين، مع ارتفاع مناسب للحروف العربية ومحاذاة وسطية ووزن ثابت للنص وسهم مستقل؛ قبل مرور المؤشر وبعده وعند استخدام لوحة المفاتيح.
- السطوع والتشبع مضبوطان لكل صورة مع طابع دافئ مشترك. المعالجة لعرض الموقع فقط دون تغيير ملفات الصور أو تفاصيل المشاريع. يمكن المقارنة قبل وبعد عبر زر في media-review.html.
- خُفّض دوران وتحريك صور صفحة المشاريع إلى 25% من السابق، والتكبير من 14% إلى 3.5%، مع الحفاظ على حركة أقسام الرئيسية وشبكة المشاريع والصور الطولية كاملة.
- فيديو مراسي السعادة 2 يتقدّم نحو 8 ثوانٍ ثم يرجع للخلف في دورة نحو 16 ثانية، دون تكرار الإطار عند طرفي الرجوع. نسخة الحاسوب 1080p/{desktop['fps']}fps وحجم {desktop['bytes']/1e6:.2f} MB؛ الهاتف 720p/{mobile['fps']}fps وحجم {mobile['bytes']/1e6:.2f} MB. له صورة معاينة وزر إيقاف ويتوقف خارج الشاشة وعند إخفاء الصفحة. تفضيل تقليل الحركة أو توفير البيانات يمنع تنزيله التلقائي.
- افتح media-review.html لمراجعة الوسائط ومصادرها. الجرد في drive-inventory.csv، والاختيارات في selected-media.json.

## حزمة هوستنجر

meridian-hostinger.zip تضم {len(files)} ملفًا، {total/1e6:.2f} MB قبل الضغط و{archive.stat().st_size/1e6:.2f} MB داخل ZIP. الصفحات الأساسية 12 صفحة بلغتين، مع 6 صفحات عربية للتوافق مع الروابط السابقة. حجم حزمة الاستضافة لا يعني أن الزائر يحمّلها كلها؛ تُختار صورة مناسبة للشاشة ويؤجّل تحميل الوسائط البعيدة عن موضع التصفح.

الحزمة لموقع HTML ثابت، ولا تحتاج Node.js أو WordPress. بعد اعتماد الشكل، احتفظ بنسخة من أي موقع قائم ثم ارفع ZIP إلى مجلد public_html للموقع الصحيح وفك ضغطه بحيث يكون index.html وassets وen وar مباشرة فيه. لا تضعها داخل مجلد إضافي. تعليمات هوستنجر: https://www.hostinger.com/support/1869114-how-to-upload-backups-with-file-manager-in-hostinger/

اختبر رابط النطاق على هاتف فعلي وتأكد من دعم أجزاء ملفات MP4 ونوع video/mp4 وملفات WebP. لم يُفتح حساب الاستضافة، لذلك لم تُفحص خطة الاشتراك أو إعدادات الخادم ولا تمثل الفحوص المحلية قياسًا لسرعته.

## نقل التحديث إلى النسخة الأصلية لاحقًا

بعد اعتمادك فقط: انقل صفحات HTML الست في الجذر، ومجلدي en وar، ومجلد assets/css كاملًا وassets/js/main.js وassets/js/drift-field.js ومجلدي assets/media وassets/fonts. للحفاظ على إمكانية إعادة التوليد، انقل أدوات build.py وarabic.py وarabic_texts.txt وsite_media.py وmedia_selections.json وprepare_media.py وphoto_grade.py وprepare_film.py وprepare_arabic_font.py وpackage_hostinger.py و.gitignore. لا تنقل _media_work أو _verify. حزمة ZIP جاهزة للاستضافة دون تشغيل أدوات البرمجة.

## فحص هذه المراجعة — 11 أكتوبر 2026

اجتازت الصفحات الأساسية الاثنتا عشرة اختبار متصفح عند عرض 1440 و390 بكسل: الخط العربي، تبديل اللغة، الصور، غياب التمرير الأفقي، تكبير الفيديو عند التمرير، ظهور الخدمات الثماني بتأثيرها الأصلي، تأثير العمق وتحريك الصورة في بطاقات المشاريع، الفلاتر والصورة الكبيرة، والتشغيل والإيقاف. فُحص العرض عند 900 بكسل، والروابط العربية القديمة، ومنع التنزيل التلقائي عند تقليل الحركة أو توفير البيانات. العربية تُفتح حتى عند تعطيل JavaScript. فحص الروابط المحلية عبر 18 صفحة: صفر ملفات أو روابط داخلية مفقودة. لا يضمن فحص المتصفح المحلي الأداء على كل جهاز أو اتصال.

بعد تحديث الخط، فُحصت الأزرار في الصفحات الست بكل لغة عند عرض 1440 و390 و320 بكسل، في الحالة العادية وعند مرور المؤشر والتركيز بلوحة المفاتيح؛ مع اختبار تكبير نص الأزرار إلى الضعف. جرى التحقق من تحميل الخط المحلي فعليًا، واكتمال النص وتمركزه وثبات أبعاد الزر. على الهاتف بعرض 320 بكسل أصبحت إحصاءات «من نحن» عمودًا واحدًا لمنع تمدد الصفحة.

## حدود النطاق

الأصول الأصلية الكبيرة وأدوات العمل والفيديو القديم والصور العامة القديمة خارج ZIP. معظم صور المشاريع تصورات معمارية لا تثبت التنفيذ، وأسماء المشاريع تحتاج اعتماد هجائها التجاري. نموذج التواصل الحالي يتحقق من الإدخال فقط ولا يرسل بريدًا؛ توصيله وبيانات الاتصال خارج نطاق تحديث الوسائط ولم تُعتمد للإطلاق.
'''
    (OUT/'README-AR.md').write_text(readme,encoding='utf8')
    print(f'Packaged {len(files)} files, {total/1e6:.2f} MB; ZIP {archive.stat().st_size/1e6:.2f} MB')

if __name__=='__main__':main()
