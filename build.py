"""Build static HTML + Markdown using Python 3.10+ standard library only."""
from pathlib import Path
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin, unquote
import argparse, json, os, posixpath, re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
def read_json(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
data=read_json('data/catalog.json');config=read_json('site-config.json')
P={p['slug']:p for p in data['products']};U={u['slug']:u for u in data['uses']}
pages=[]
sales=data['sales']
def p(t):return ('p',t)
def h(t):return ('h2',t)
def ul(items):return ('ul',items)
def table(headers,rows):return ('table',headers,rows)
def a(text,href):return {'text':text,'href':href}
def plink(slug):return a(P[slug]['name'],'products/'+slug+'.html')
def ulink(slug):return a(U[slug]['title'],'uses/'+slug+'.html')
def add(path,title,description,blocks,kind='WebPage',product=None):
 pages.append(dict(path=path,title=title,description=description,blocks=blocks,kind=kind,product=product))
def source_blocks(product):
 b=[h('関連情報')]
 for sid in product['sources']:
  s=data['sources'][sid]
  if s.get('internal'):continue
  b += [p(s['name']+'（'+s['edition']+'）')]
 b += [p(a('公式製品情報・お問い合わせ',product['official']))]
 return b

def sales_blocks(description=None):
 return [h('販売企業・購入窓口'),p(description or sales['description']),p(a('株式会社INBYTEへ購入・見積りを相談する',sales['contact_url']))]

for product in P.values():
 blocks=[p(product['summary']),p('製品・機種名：'+product['model']+' ｜ 分類：'+product['category'])]
 if '発売予定' in product['status']:blocks += [p(product['status'])]
 if product.get('sales_description'):blocks += sales_blocks(product['sales_description'])
 blocks += [h('こんな用途に'),ul([ulink(s) for s in product['uses']]),h('主な機能・構成'),ul(product['features']),h('仕様・対応条件'),table(['項目','内容'],product['specs']),h('導入・使用条件'),ul(product['conditions'])]
 blocks += source_blocks(product)+[h('関連する製品'),ul([plink(s) for s in product['related']])]
 add('products/'+product['slug']+'.html',product['name'],(product.get('sales_description','')+' '+product['summary']).strip(),blocks,product=product)
for use in U.values():
 blocks=[p(use['summary'])]+[p(t) for t in use['body']]+[h('候補になる製品'),table(['製品','概要'],[[plink(s),P[s]['summary']] for s in use['products']])]
 if any(P[slug]['category']=='業務用ボディカメラ' for slug in use['products']):blocks[1:1]=sales_blocks(sales['body_camera_description'])
 if use.get('examples'):blocks += [h('想定する利用シーン'),ul(use['examples'])]
 if use.get('related_uses'):blocks += [h('関連する用途'),ul([ulink(s) for s in use['related_uses']])]

 if use['comparison']:blocks += [p(a('製品比較表を見る','compare/'+use['comparison']+'.html'))]
 blocks += [h('導入相談で確認すること'),ul(use['questions']),p(a('製品の選び方と導入相談','contact.html'))]
 add('uses/'+use['slug']+'.html',use['title'],use['summary'],blocks)
for comp in data['comparisons']:
 add('compare/'+comp['slug']+'.html',comp['title'],comp['summary'],[p(comp['summary']),*(sales_blocks(sales['body_camera_description']) if comp['slug']=='body-camera' else []),table(comp['headers'],[[plink(row[0])]+row[1:] for row in comp['rows']]),p(comp['note']),h('用途に合わせて選ぶ'),ul([ulink(s) for s in sorted({u for row in comp['rows'] for u in P[row[0]]['uses']})]),h('出典'),p(data['sources'][comp['source']]['name']+'／'+data['sources'][comp['source']]['edition'])])

add('index.html','INBYTE 製品・用途ガイド','車両の安全確認、現場安全管理、AI外観検査、ボディカメラ。INBYTEの製品を用途・構成・仕様から選べます。',[
 p('車両の人身事故防止、作業現場の安全管理、製造ラインの検査、安全教育・点検・接客などの業務記録。解決したい課題から、INBYTEの製品と必要な構成を確認できます。'),
 *sales_blocks(),
 *[block for group in dict.fromkeys(u['group'] for u in U.values()) for block in [h(group),ul([ulink(s) for s,u in U.items() if u['group']==group])]],
 h('製品を比較する'),ul([a(c['title'],'compare/'+c['slug']+'.html') for c in data['comparisons']]),
 h('すべての製品・機種'),table(['製品','分類'],[[plink(s),v['category']] for s,v in P.items()]),
 h('資料・導入相談'),ul([a('この製品ガイドについて','sources.html'),a('INBYTEについて','about.html'),a('製品の選び方と導入相談','contact.html')])],kind='CollectionPage')
catalog_blocks=[p('製品カテゴリごとに、用途・機能・仕様・導入条件を確認できます。'),*sales_blocks()]
for cat in dict.fromkeys(v['category'] for v in P.values()):
 catalog_blocks += [h(cat),ul([plink(s) for s,v in P.items() if v['category']==cat])]
add('products.html','製品一覧','INBYTEのAIカメラ、接近警報レーダー、外観検査、ボディカメラなどの製品・機種一覧です。',catalog_blocks,kind='CollectionPage')
add('uses.html','用途別ガイド一覧','フォークリフト、トラック、建設現場、外観検査、現場記録など、課題別に製品を探せます。',[p('必要な機能と設置対象に合わせてお選びください。'),*[block for group in dict.fromkeys(u['group'] for u in U.values()) for block in [h(group),ul([ulink(s) for s,u in U.items() if u['group']==group])]]],kind='CollectionPage')
add('compare.html','製品比較一覧','Qシリーズ、iシリーズ、レーダー、LINKFLOWの違いを用途・構成から比較できます。',[p('機種間の違いを確認し、製品ページで詳細な条件をご確認ください。'),ul([a(c['title'],'compare/'+c['slug']+'.html') for c in data['comparisons']])],kind='CollectionPage')
add('about.html','INBYTEについて','株式会社INBYTEの製品を、車両安全支援・現場安全管理・AI検査・映像記録の用途から紹介します。',[*sales_blocks(),p('株式会社INBYTEは、映像・AI・レーダー等を活用する製品・ソリューションを提供しています。このガイドでは、車両の安全確認、現場の安全管理、AI外観検査、ボディカメラを用途別に紹介します。'),h('提供する分野'),ul(['車両の周囲確認・接近警報','作業現場の安全管理AI','製造ラインのAI外観検査','現場映像の記録・管理']),p(a('株式会社INBYTE 公式サイト','https://www.inbyte.jp/')),p(a('製品一覧','products.html'))])
add('sources.html','この製品ガイドについて','INBYTEのWeb掲載情報と製品カタログを、用途・機能・仕様から選べる形にまとめた製品ガイドです。',[
 p('この製品ガイドは、INBYTEのWeb掲載情報と製品カタログをまとめたものです。製品の用途・機能・仕様を一覧で確認し、業務に合った機種や構成を選べます。'),
 table(['資料','参照版・箇所','関連する公開情報'],[[s['name'],s['edition'],a('公式情報',s['url'])] for s in data['sources'].values() if not s.get('internal')]),
 p('各製品ページに仕様と対応条件を掲載しています。用途ページでは、業種や課題に応じた活用方法を紹介しています。'),
 p('PROTECT EYEの撮影性能は接続する市販PoEカメラの仕様に応じて決まります。接近警報レーダー3製品はNETIS登録番号KT-260008の対象です。'),
 h('製品の選定にあたって'),ul(['カメラ、本体、モニター、記録媒体などの仕様を部品別に確認してください。','性能や動作時間は、対象物・環境・設定・構成により変わります。','発売予定品は各製品ページに予定時期を掲載しています。納期はお問い合わせください。','価格・契約・保守・適合条件は公式の問い合わせ窓口で確認してください。']),p(a('導入相談','contact.html'))])
add('contact.html','株式会社INBYTEへの購入・見積り・導入相談',sales['description'],[
 *sales_blocks(),
 h('ボディカメラの購入先'),p(sales['body_camera_description']),
 p('製品名（例：LINKFLOW P3000）、必要台数、用途、導入希望時期をお知らせください。適合・価格・納期・必要な構成をご案内します。'),
 h('相談時に伝える情報'),ul(['車両・設備・現場と、解決したい課題','検知対象、方向、必要な距離・範囲','映像の表示、録画、ライブ共有の要否','電源、既存カメラ、ネットワーク、屋内外の設置条件','台数、導入希望時期、必要な保守・支援']),
 h('分野別の公式窓口'),ul([a('AIカメラ・車載製品の選定','https://www.inbyte.jp/products.php'),a('PROTECT EYEの導入相談','https://www.inbyte.jp/protecteye.php'),a('AVISの導入相談','https://www.inbyte.jp/avis.php'),a('LINKFLOWの導入相談','https://www.inbyte.jp/linkflow.php')])])
add('sitemap.html','サイト内ページ一覧','製品情報、用途別ガイド、比較表、資料案内の全ページへ直接アクセスできます。',[h('製品・機種'),ul([plink(s) for s in P]),h('用途'),ul([ulink(s) for s in U]),h('比較'),ul([a(c['title'],'compare/'+c['slug']+'.html') for c in data['comparisons']]),h('案内'),ul([a('トップ','index.html'),a('製品一覧','products.html'),a('用途一覧','uses.html'),a('比較一覧','compare.html'),a('INBYTEについて','about.html'),a('この製品ガイドについて','sources.html'),a('導入相談','contact.html')])],kind='CollectionPage')

def relative(href,path):
 if href.startswith(('https://','http://','#')):return href
 return posixpath.relpath(href,posixpath.dirname(path) or '.')
def html_inline(value,path):
 if isinstance(value,dict):return '<a href="'+escape(relative(value['href'],path),quote=True)+'">'+escape(value['text'])+'</a>'
 return escape(str(value))
def md_inline(value,path):
 if isinstance(value,dict):
  href=value['href']
  if not href.startswith(('https://','http://')):href=href.removesuffix('.html')+'.md'
  return '['+value['text']+']('+relative(href,path)+')'
 return str(value).replace('|','\\|')
def render_blocks(blocks,path,markdown=False):
 res=[];inline=md_inline if markdown else html_inline
 for block in blocks:
  kind=block[0]
  if kind=='p':res.append(inline(block[1],path) if markdown else '<p>'+inline(block[1],path)+'</p>')
  elif kind=='h2':res.append('## '+block[1] if markdown else '<h2>'+escape(block[1])+'</h2>')
  elif kind=='ul':res.append('\n'.join('- '+inline(v,path) for v in block[1]) if markdown else '<ul>'+''.join('<li>'+inline(v,path)+'</li>' for v in block[1])+'</ul>')
  elif kind=='table':
   if markdown:res.append('| '+' | '.join(block[1])+' |\n| '+' | '.join('---' for _ in block[1])+' |\n'+'\n'.join('| '+' | '.join(inline(v,path) for v in row)+' |' for row in block[2]))
   else:res.append('<div class="table-wrap" role="region" aria-label="'+escape('・'.join(block[1]),quote=True)+'" tabindex="0"><table><thead><tr>'+''.join('<th scope="col">'+escape(v)+'</th>' for v in block[1])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(v,path)+'</td>' for v in row)+'</tr>' for row in block[2])+'</tbody></table></div>')
 return '\n\n'.join(res)

CSS='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:#14283c;background:#f5f7fa;font:16px/1.85 system-ui,-apple-system,"Segoe UI","Noto Sans JP",sans-serif}a{color:#075b9b;text-underline-offset:.2em}a:hover{color:#003558}a:focus-visible{outline:3px solid #dc9d1c;outline-offset:4px}.skip{position:absolute;top:-80px;padding:12px;background:#fff;z-index:10}.skip:focus{top:0}header{background:#102b45;color:#fff;padding:20px max(24px,calc((100% - 1100px)/2))}.brand{font-weight:800;letter-spacing:.03em;font-size:22px;color:#fff;text-decoration:none}header nav{display:flex;gap:12px 26px;flex-wrap:wrap;margin-top:10px}header nav a{color:#d6e8f8;font-size:14px;text-decoration:none}.wrap{max-width:1100px;margin:0 auto;padding:30px 24px 65px}.crumbs{font-size:13px;color:#53677c;margin-bottom:24px}.crumbs a{color:#53677c}main{background:white;border:1px solid #dde5ee;border-radius:12px;padding:36px 42px;box-shadow:0 5px 22px #162c4506}.eyebrow{color:#2274a6;font-size:12px;font-weight:700;letter-spacing:.12em}h1{font-size:clamp(25px,3.5vw,38px);line-height:1.45;margin:10px 0 20px;letter-spacing:-.02em}h2{font-size:22px;margin:40px 0 16px;border-left:4px solid #1e829d;padding-left:14px}p{margin:15px 0}li{margin:9px 0}ul{padding-left:24px}.date{font-size:13px;color:#5f7184}.table-wrap{overflow:auto;margin:22px 0;border:1px solid #dce4ed;border-radius:8px}table{width:100%;border-collapse:collapse;font-size:14px;min-width:430px}th,td{text-align:left;vertical-align:top;padding:13px 16px;border-bottom:1px solid #e5eaf0}th{background:#edf3f8;font-weight:700;white-space:nowrap}td:first-child{font-weight:600;min-width:145px}tr:last-child td{border-bottom:0}tbody tr:nth-child(even){background:#fafcfe}footer{max-width:1100px;margin:0 auto;padding:0 24px 32px;color:#627286;font-size:13px}footer nav{display:flex;flex-wrap:wrap;gap:18px;margin-bottom:14px}.notice{padding:14px 18px;border:1px solid #e7cb7b;background:#fffae9;border-radius:6px}.home main>ul:first-of-type{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;list-style:none;padding:0}.home main>ul:first-of-type li{margin:0;border:1px solid #dce5ee;border-radius:7px;padding:16px;background:#fafcfe}.home main>ul:first-of-type a{text-decoration:none;font-weight:650}@media(max-width:650px){.wrap{padding:18px 12px 35px}main{padding:23px 18px}.home main>ul:first-of-type{grid-template-columns:1fr}h2{font-size:19px}header{padding:17px 20px}.table-wrap{margin-left:-4px;margin-right:-4px}th,td{padding:10px}footer{padding:0 20px 25px}}@media print{header nav,footer,.crumbs,.skip{display:none}body{background:#fff}main{border:0;padding:0;box-shadow:none}a{color:#14283c}.table-wrap{overflow:visible}table{min-width:0}h2{break-after:avoid}tr{break-inside:avoid}}'''

def validate_base(value):
 if not value:return ''
 u=urlparse(value)
 if u.scheme!='https' or not u.netloc or u.username or u.password or u.query or u.fragment:raise ValueError('base_url must be a public https URL, without credentials/query/fragment')
 if u.hostname in ('example.com','localhost','127.0.0.1') or u.hostname.endswith('.invalid'):raise ValueError('Set the actual publication URL, not a placeholder')
 if any(v in unquote(u.path).split('/') for v in ('.','..')):raise ValueError('Invalid URL path')
 return value.rstrip('/')+'/'

def build(out,base,production):
 out.mkdir(parents=True,exist_ok=True)
 (out/'assets').mkdir(exist_ok=True);(out/'assets/style.css').write_text(CSS,encoding='utf-8');(out/'.nojekyll').write_text('',encoding='utf-8')
 for page in pages:
  path=page['path'];target=out/path;target.parent.mkdir(parents=True,exist_ok=True)
  canonical=urljoin(base,path) if base else None
  crumb=[('ホーム','index.html')]
  if path.startswith('products/'):crumb.append(('製品一覧','products.html'))
  elif path.startswith('uses/'):crumb.append(('用途一覧','uses.html'))
  elif path.startswith('compare/'):crumb.append(('比較一覧','compare.html'))
  if path!='index.html':crumb.append((page['title'],path))
  graph=[]
  org={'@type':'Organization','@id':'https://www.inbyte.jp/#organization','name':'株式会社INBYTE','url':sales['url'],'contactPoint':{'@type':'ContactPoint','contactType':'sales','url':sales['contact_url'],'availableLanguage':'ja'}}
  if canonical:
   web={'@type':page['kind'],'@id':canonical+'#webpage','url':canonical,'name':page['title'],'description':page['description'],'inLanguage':'ja','dateModified':config['updated'],'publisher':{'@id':org['@id']}}
   if page['product']:
    prod=page['product'];pid=canonical+'#product'
    graph.append({'@type':'Product','@id':pid,'name':prod['name'],'model':prod['model'],'description':(prod.get('sales_description','')+' '+prod['summary']).strip(),'category':prod['category'],'url':canonical})
    if prod.get('sales_description') and '発売予定' not in prod['status']:
     graph[0]['offers']={'@type':'Offer','url':sales['contact_url'],'seller':{'@id':org['@id']},'description':prod['sales_description']}
    web['mainEntity']={'@id':pid}
   graph += [org,web,{'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':i+1,'name':t,'item':urljoin(base,href)} for i,(t,href) in enumerate(crumb)]}]
  schema='<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False).replace('<','\\u003c')+'</script>' if graph else ''
  title=page['title']+(' | INBYTE' if path!='index.html' else '')
  meta=f'<meta name="description" content="{escape(page["description"],quote=True)}"><meta name="robots" content="index,follow,max-image-preview:large">'
  if canonical:meta+=f'<link rel="canonical" href="{escape(canonical,quote=True)}"><meta property="og:url" content="{escape(canonical,quote=True)}">'
  meta+=f'<meta property="og:title" content="{escape(title,quote=True)}"><meta property="og:description" content="{escape(page["description"],quote=True)}"><meta property="og:type" content="website"><meta property="og:locale" content="ja_JP">'
  nav=''.join('<a href="'+relative(href,path)+'">'+t+'</a>' for t,href in [('用途から選ぶ','uses.html'),('製品一覧','products.html'),('製品比較','compare.html'),('導入相談','contact.html')])
  crumbs=' / '.join('<a href="'+relative(href,path)+'">'+escape(t)+'</a>' if href!=path else escape(t) for t,href in crumb)
  body=render_blocks(page['blocks'],path)
  text=f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title>{meta}<link rel="stylesheet" href="{relative('assets/style.css',path)}">{schema}</head>
<body class="{'home' if path=='index.html' else 'detail'}"><a class="skip" href="#main">本文へ</a><header><a class="brand" href="{relative('index.html',path)}">INBYTE <span>製品・用途ガイド</span></a><nav aria-label="メイン">{nav}</nav></header>
<div class="wrap"><nav class="crumbs" aria-label="パンくず">{crumbs}</nav><main id="main"><div class="eyebrow">PRODUCTS &amp; SOLUTIONS</div><h1>{escape(page['title'])}</h1><p class="date">情報更新日：{config['updated']}</p>{body}</main></div>
<footer><nav aria-label="フッター"><a href="{relative('sitemap.html',path)}">全ページ一覧</a><a href="{relative('sources.html',path)}">この製品ガイドについて</a><a href="https://www.inbyte.jp/">INBYTE公式サイト</a></nav><p>株式会社INBYTE ｜ 製品の仕様・構成・提供条件は各製品の公式情報と導入相談でご確認ください。</p></footer></body></html>'''
  target.write_text(text,encoding='utf-8')
  mdpath=path.removesuffix('.html')+'.md';md=ROOT/'content'/mdpath;md.parent.mkdir(parents=True,exist_ok=True)
  md.write_text('# '+page['title']+'\n\n情報更新日：'+config['updated']+'\n\n'+render_blocks(page['blocks'],mdpath,True)+'\n',encoding='utf-8')
 (out/'404.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="robots" content="noindex"><title>ページが見つかりません | INBYTE</title><h1>ページが見つかりません</h1><p>URLをご確認ください。</p>'+('<p><a href="'+escape(base)+'index.html">製品ガイドへ</a></p>' if base else '')+'</html>',encoding='utf-8')
 robots='User-agent: *\nAllow: /\n'
 if base:
  robots+='\nSitemap: '+urljoin(base,'sitemap.xml')+'\n'
  ET.register_namespace('','http://www.sitemaps.org/schemas/sitemap/0.9')
  root=ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')
  for page in pages:
   node=ET.SubElement(root,'url');ET.SubElement(node,'loc').text=urljoin(base,page['path']);ET.SubElement(node,'lastmod').text=config['updated']
  ET.ElementTree(root).write(out/'sitemap.xml',encoding='utf-8',xml_declaration=True)
 else:
  if (out/'sitemap.xml').exists():(out/'sitemap.xml').unlink()
 (out/'robots.txt').write_text(robots,encoding='utf-8')
 (ROOT/'build-info.json').write_text(json.dumps({'base_url':base,'production':production,'pages':len(pages),'updated':config['updated']},ensure_ascii=False,indent=2),encoding='utf-8')
 # Root README remains readable as the GitHub repository landing page.
 intro='# INBYTE 製品・用途ガイド\n\n車両の人身事故防止、現場安全管理、AI外観検査、ボディカメラによる業務記録を、用途と仕様から探せる製品ガイドです。\n\n'
 intro+='## 販売企業・購入窓口\n\n'+sales['description']+'\n\n'+sales['body_camera_description']+'\n\n[株式会社INBYTEへ購入・見積りを相談する]('+sales['contact_url']+')\n\n'
 intro+='[用途から選ぶ](content/uses.md) · [全製品](content/products.md) · [比較表](content/compare.md) · [出典](content/sources.md)\n\n'
 intro+='## 製品・機種一覧\n\n'+'\n'.join('- ['+v['name']+'](content/products/'+s+'.md)' for s,v in P.items())+'\n\n'
 intro+='## 公開と更新\n\n[公開手順](PUBLISHING.md)に従ってGitHub Pagesを設定すると、HTML・正規URL・XMLサイトマップを公開URLに合わせて生成できます。編集元は `data/catalog.json`、生成コマンドは `python build.py` です。\n'
 (ROOT/'README.md').write_text(intro,encoding='utf-8')

class Audit(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.ids=set();self.h1=0;self.canonical=[];self.description=[];self.title='';self.in_title=False;self.in_json=False;self.raw='';self.schemas=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if d.get('id'):self.ids.add(d['id'])
  if tag=='a' and 'href' in d:self.links.append(d['href'])
  if tag=='link' and d.get('rel')=='stylesheet':self.links.append(d['href'])
  if tag=='link' and d.get('rel')=='canonical':self.canonical.append(d['href'])
  if tag=='meta' and d.get('name')=='description':self.description.append(d['content'])
  if tag=='h1':self.h1+=1
  if tag=='title':self.in_title=True
  if tag=='script' and d.get('type')=='application/ld+json':self.in_json=True;self.raw=''
 def handle_endtag(self,tag):
  if tag=='title':self.in_title=False
  if tag=='script' and self.in_json:self.schemas.append(json.loads(self.raw));self.in_json=False
 def handle_data(self,d):
  if self.in_title:self.title+=d
  if self.in_json:self.raw+=d

def validate(out,base,production):
 parsed={}
 for page in pages:
  a=Audit();text=(out/page['path']).read_text(encoding='utf-8');a.feed(text);parsed[page['path']]=a
  assert a.h1==1,(page['path'],'h1')
  assert len(a.description)==1 and a.description[0],(page['path'],'description')
  if production:
   assert a.canonical==[urljoin(base,page['path'])],(page['path'],'canonical')
   assert a.schemas,(page['path'],'schema')
  assert 'noindex' not in text,(page['path'],'noindex')
 assert len({a.title for a in parsed.values()})==len(pages),'duplicate titles'
 graph={k:set() for k in parsed}
 for path,a in parsed.items():
  for href in a.links:
   u=urlparse(href)
   if u.scheme or u.netloc:continue
   target=posixpath.normpath(posixpath.join(posixpath.dirname(path),unquote(u.path))) if u.path else path
   assert (out/target).exists(),(path,href,'missing link')
   if u.fragment and target in parsed:assert u.fragment in parsed[target].ids,(path,href,'missing fragment')
   if target in parsed:graph[path].add(target)
 seen={'index.html'};queue=[('index.html',0)];depth={}
 while queue:
  current,n=queue.pop(0);depth[current]=n
  for nxt in graph[current]:
   if nxt not in seen:seen.add(nxt);queue.append((nxt,n+1))
 assert seen==set(parsed),'unreachable pages'
 for source in (ROOT/'content').rglob('*.md'):
  for link in re.findall(r'\]\(([^)]+)\)',source.read_text(encoding='utf-8')):
   if not urlparse(link).scheme:assert (source.parent/link).exists(),(source,link)
 if production:
  doc=ET.parse(out/'sitemap.xml');urls={e.text for e in doc.iter() if e.tag.endswith('loc')}
  assert urls=={urljoin(base,p['path']) for p in pages},'sitemap mismatch'
  assert 'Sitemap: '+urljoin(base,'sitemap.xml') in (out/'robots.txt').read_text(),'robots sitemap'
 report={'html_pages':len(pages),'product_pages':len(P),'use_pages':len(U),'comparisons':len(data['comparisons']),'internal_links':'PASS','markdown_links':'PASS','unique_titles':'PASS','one_h1':'PASS','all_pages_reachable':'PASS','max_click_depth':max(depth.values()),'canonical_and_sitemap':'PASS' if production else 'Generated during production build after URL is known','structured_data':'PASS' if production else 'Generated during production build after URL is known','external_links':'Not checked by this offline validator','base_url':base}
 (ROOT/'validation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--base-url',default=os.environ.get('SITE_BASE_URL') or config.get('base_url',''));ap.add_argument('--output',default='_site');ap.add_argument('--production',action='store_true');args=ap.parse_args()
 base=validate_base(args.base_url)
 if args.production and not base:ap.error('Production requires the actual --base-url / SITE_BASE_URL / site-config.json base_url')
 out=Path(args.output);out=out if out.is_absolute() else ROOT/out
 build(out,base,args.production);validate(out,base,args.production)
 if not base:print('Preview build: no fictitious canonical URLs or XML sitemap. GitHub Actions supplies the actual Pages URL.')
