#!/usr/bin/env python3
"""Ofertómetro — procesa el dataset SEPA (Precios Claros) y genera JSON compactos.
Uso: python3 -I procesar.py <sepa_dia.zip | carpeta_extraida> <carpeta_salida>
Salida: productos.json, cadenas.json, canasta.json, meta.json, e historial.json (acumulado)."""
import csv, glob, io, json, os, re, statistics, sys, tempfile, zipfile, collections, datetime, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from categorias import clasificar_varias, SUB_NOMBRES
csv.field_size_limit(10**9)

POR_SUB = 24          # productos por subcategoría (los más presentes)
POR_SUB_GRANDE = {'vinos': 30, 'galletitas': 36, 'yogur': 30, 'gaseosas': 30, 'cervezas': 30}
MIN_CADENAS = 6

BANDERAS = {  # nombre SEPA normalizado -> (slug, nombre)
 'COTO CICSA':('coto','Coto'), 'Cooperativa Obrera Limitada de Consumo y Vivienda':('cooperativa-obrera','Cooperativa Obrera'),
 'Supermercados DIA':('dia','Día'), 'LA AGRICOLA REGIONAL COOPERATIVA LIMITADA':('la-agricola-regional','La Agrícola Regional'),
 'Toledo':('toledo','Toledo'), 'DEHEZA S.A.I.C.F. e I.':('deheza','Deheza'), 'Sup. Unicoop':('unicoop','Unicoop'),
 'Mariano Max':('mariano-max','Mariano Max'), 'Vea':('vea','Vea'), 'Disco':('disco','Disco'), 'Jumbo':('jumbo','Jumbo'),
 'Market':('carrefour-market','Carrefour Market'), 'Maxi':('carrefour-maxi','Carrefour Maxi'),
 'Hipermercado Carrefour':('carrefour','Carrefour Hipermercado'), 'Express':('carrefour-express','Carrefour Express'),
 'SuperChangomas':('changomas','ChangoMás'), 'Changomas':('changomas','ChangoMás'), 'HiperChangomas':('hiperchangomas','HiperChangoMás'),
 'La Anonima':('la-anonima','La Anónima'), 'Topsy':('topsy','Topsy'), 'Bomba':('bomba','Bomba'),
 'California Supermercados':('california','California'), 'Supermercados Comodin':('comodin','Comodín'), 'Maxi Comodin':('maxi-comodin','Maxi Comodín'),
}
EXCLUIR = ('Axion', 'ESTACION LIMA')
PROVINCIAS = {'AR-A':'Salta','AR-B':'Buenos Aires','AR-C':'CABA','AR-D':'San Luis','AR-E':'Entre Ríos','AR-F':'La Rioja',
 'AR-G':'Santiago del Estero','AR-H':'Chaco','AR-J':'San Juan','AR-K':'Catamarca','AR-L':'La Pampa','AR-M':'Mendoza',
 'AR-N':'Misiones','AR-P':'Formosa','AR-Q':'Neuquén','AR-R':'Río Negro','AR-S':'Santa Fe','AR-T':'Tucumán',
 'AR-U':'Chubut','AR-V':'Tierra del Fuego','AR-W':'Corrientes','AR-X':'Córdoba','AR-Y':'Jujuy','AR-Z':'Santa Cruz'}

def slugify(t):
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')

def rd(p):
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        r = csv.reader(f, delimiter='|'); h = [x.strip() for x in next(r)]
        for row in r:
            if len(row) >= len(h) - 1: yield dict(zip(h, row))

def num(x):
    try:
        v = float(x.replace(',', '.'));  return v if v > 0 else None
    except Exception: return None

def entradas_zip(ruta):
    """Lista [(nombre, bytes)] de un ZIP. Si el directorio central está roto (le pasa al SEPA),
    recorre los encabezados locales: las entradas vienen sin comprimir o con deflate."""
    import struct, zlib
    try:
        with zipfile.ZipFile(ruta) as z:
            return [(n, z.read(n)) for n in z.namelist() if not n.endswith('/')]
    except zipfile.BadZipFile:
        pass
    out = []
    with open(ruta, 'rb') as f:
        pos = 0
        while True:
            f.seek(pos); h = f.read(30)
            if len(h) < 30 or h[:4] != b'PK\x03\x04': break
            _, _, flag, meth, _, _, _, cs, us, nl, el = struct.unpack('<IHHHHHIIIHH', h)
            nombre = f.read(nl).decode('utf-8', 'replace'); f.seek(pos + 30 + nl + el)
            if flag & 8 and cs == 0: raise RuntimeError('ZIP con tamaños diferidos: no soportado (' + nombre + ')')
            dato = f.read(cs)
            if meth == 8: dato = zlib.decompress(dato, -15)
            if not nombre.endswith('/'): out.append((nombre, dato))
            pos += 30 + nl + el + cs
    return out

def extraer(src):
    if os.path.isdir(src): return src
    out = tempfile.mkdtemp(prefix='sepa_')
    for n, dato in entradas_zip(src):
        if not n.endswith('.zip') or not dato: continue
        d = os.path.join(out, os.path.basename(n)[:-4]); os.makedirs(d, exist_ok=True)
        tmp = os.path.join(d, '_in.zip')
        with open(tmp, 'wb') as f: f.write(dato)
        del dato
        for m, contenido in entradas_zip(tmp):
            if m.endswith('.csv'):
                with open(os.path.join(d, os.path.basename(m)), 'wb') as f: f.write(contenido)
        os.remove(tmp)
    return out

ABREV = [(r'\bX\s?(\d)', r'x \1'), (r'\bGRS?\.?\b|\bGRM\b|\bGR\b', 'g'), (r'\bLTS?\.?\b|\bLTR\b', 'L'), (r'\bCC\.?\b', 'cc'),
 (r'\bML\b', 'ml'), (r'\bCm3\b|\bCM3\b', 'cm3'), (r'\bMts\b', 'm'), (r'\bKG\.?\b', 'kg'), (r'\bUN[ID]?\.?\b|\bUD\.?\b', 'u'), (r'\bLS\b', 'La Serenísima'), (r'\bSAQ\.?\b', 'saquitos')]
PREFIJOS = [(r'^G\.\s?', 'Galletitas '), (r'^GALL\.\s?', 'Galletitas '), (r'^D\.\s?DE LECHE', 'Dulce de leche'), (r'^M\.BC\s?', 'Mermelada BC '),
 (r'^Y\.SER\s?', 'Yogur Ser '), (r'^J\.\s?', 'Jugo '), (r'^DESOD\.\s?', 'Desodorante '), (r'^ANTIT\.\s?', 'Antitranspirante '),
 (r'^ACOND\.\s?', 'Acondicionador '), (r'^DET\.\s?', 'Detergente '), (r'^LIQ\.\s?', 'Limpiador '), (r'^SH\.\s?', 'Shampoo '),
 (r'^Q\.\s?', 'Queso '), (r'^BIZC\.\s?', 'Bizcochuelo '), (r'^LUST\.\s?', 'Lustramuebles '), (r'^QUIT\.\s?', 'Quitamanchas '),
 (r'^P\.\s?HIG\.?\s?', 'Papel higiénico ')]
ACENTOS = {'Cafe':'Café','Azucar':'Azúcar','Jabon':'Jabón','Limon':'Limón','Pure':'Puré','Panales':'Pañales','Panal':'Pañal',
 'Accion':'Acción','Clasica':'Clásica','Clasico':'Clásico','Atun':'Atún','Algodon':'Algodón','Lacteo':'Lácteo','Liquido':'Líquido',
 'Polvo':'Polvo','Lavavajilla':'Lavavajillas','Higienico':'Higiénico','Mani':'Maní','Organico':'Orgánico','Maiz':'Maíz','Frances':'Francés',
 'Clasicas':'Clásicas','Nectar':'Néctar','Proteina':'Proteína','Vitaminas':'Vitaminas','Limon':'Limón','Melon':'Melón','Durazno':'Durazno'}
MINUS = {'de','del','la','las','el','los','con','sin','y','en','para','x','a'}
def nombre_bonito(d):
    t = re.sub(r'\s+', ' ', d.strip())
    for a, b in PREFIJOS: t = re.sub(a, b, t, flags=re.I)
    t = re.sub(r'(?<=[A-ZÁÉÍÓÚÑ])\.(?=[A-ZÁÉÍÓÚÑ])', ' ', t)   # "X1L.L/V" -> espacios
    t = t.replace('.', ' ').replace('  ', ' ')
    pal = []
    for i, w in enumerate(t.split(' ')):
        if not w: continue
        lw = w.lower()
        if re.match(r'^\d', w): pal.append(lw)
        elif lw in MINUS and i: pal.append(lw)
        elif len(w) <= 3 and w.isupper() and w not in ('SAL','TE','LA','EL','SER','DIA','SOJA','TÉ','PAN','OLA','AGUA','RED') and not re.match(r'^[A-Z][a-z]', w): pal.append(w)
        else: pal.append(w[:1].upper() + w[1:].lower())
    t = ' '.join(pal)
    t = re.sub(r', ([a-z])', lambda m: ', ' + m.group(1).upper(), t)
    t = re.sub(r'^([a-z])', lambda m: m.group(1).upper(), t)
    for a, b in ACENTOS.items(): t = re.sub(r'\b' + a + r'\b', b, t)
    t = re.sub(r'^Te\b', 'Té', t)
    for a, b in ABREV: t = re.sub(a, b, t, flags=re.I)
    t = re.sub(r'(\d)\s?(g|kg|ml|cc|L|u)\b', r'\1 \2', t)
    t = re.sub(r'\bx (\d)', r'x\1', t).replace('x', 'x', 1)
    t = re.sub(r'(\d),(\d{3})\b', r'\1.\2', t)
    return re.sub(r'\s+', ' ', t).strip()

def media_recortada(v):
    # media geométrica sin el 10% de cada punta: distingue cadenas sin que un error de carga pese
    import math
    v = sorted(min(2.0, max(0.5, x)) for x in v); k = len(v) // 10
    v = v[k:len(v) - k] or v
    return math.exp(sum(math.log(x) for x in v) / len(v))

def hasta_iso(ley):
    m = re.search(r'hasta (?:el )?(\d{4})-(\d{2})-(\d{2})', ley, re.I)
    if m: return '%s-%s-%s' % m.groups()
    m = re.search(r'hasta (?:el )?(\d{1,2})/(\d{1,2})/(\d{2,4})', ley, re.I)
    if not m: return None
    a = int(m.group(3)); a = a + 2000 if a < 100 else a
    try: return datetime.date(a, int(m.group(2)), int(m.group(1))).isoformat()
    except ValueError: return None

def puntaje_desc(d):
    return (len(re.findall(r'[A-Za-zÁÉÍÓÚÑáéíóúñ]{4,}', d)) * 3 - d.count('.') * 2 + len(d) / 30)

def main(src, outdir):
    base = extraer(src); os.makedirs(outdir, exist_ok=True)
    dirs = sorted(glob.glob(os.path.join(base, '*/')))
    fecha = None
    m = re.search(r'(\d{4}-\d{2}-\d{2})', ' '.join(dirs)); fecha = m.group(1) if m else datetime.date.today().isoformat()
    # --- comercios / banderas / sucursales
    ban = {}; suc = {}; cad_info = collections.defaultdict(lambda: {'suc': 0, 'prov': collections.Counter()})
    for d in dirs:
        for c in rd(d + 'comercio.csv'):
            nom = c.get('comercio_bandera_nombre', '').strip()
            if any(x in nom for x in EXCLUIR): continue
            sb = BANDERAS.get(nom, (slugify(nom), nom.title()))
            ban[(c['id_comercio'], c['id_bandera'])] = sb
        for s in rd(d + 'sucursales.csv'):
            k = (s['id_comercio'], s['id_bandera'])
            if k not in ban: continue
            pv = s.get('sucursales_provincia', '').strip().upper()
            pv = pv if pv in PROVINCIAS else None
            suc[(s['id_comercio'], s['id_bandera'], s['id_sucursal'])] = pv
            ci = cad_info[ban[k][0]]; ci['suc'] += 1; ci['nombre'] = ban[k][1]
            if pv: ci['prov'][pv] += 1
    # --- pasada 1: cobertura por EAN
    cov = collections.defaultdict(set); nsuc = collections.Counter(); descs = collections.defaultdict(collections.Counter); marca = {}
    for d in dirs:
        for r in rd(d + 'productos.csv'):
            e = r.get('id_producto', '').strip()
            if not e.isdigit() or len(e) < 8: continue
            k = (r['id_comercio'], r['id_bandera'])
            if k not in ban: continue
            cov[e].add(ban[k][0]); nsuc[e] += 1
            if len(descs[e]) < 12: descs[e][r['productos_descripcion'].strip()] += 1
            if r.get('productos_marca', '').strip() and e not in marca: marca[e] = r['productos_marca'].strip()
    # --- selección
    por_sub = collections.defaultdict(list)
    for e in cov:
        if len(cov[e]) < MIN_CADENAS: continue
        best = max(descs[e], key=puntaje_desc)
        cl = clasificar_varias(descs[e])
        if not cl: continue
        por_sub[cl].append((nsuc[e], e, best))
    sel = {}
    for (cat, sub), lst in por_sub.items():
        lst.sort(reverse=True)
        for n, e, best in lst[:POR_SUB_GRANDE.get(sub, POR_SUB)]: sel[e] = (cat, sub, best)
    # --- pasada 2: precios
    P = collections.defaultdict(list)       # (e, cad) -> [precio]
    PP = collections.defaultdict(list)      # (e, prov, cad) -> [precio]
    PR = collections.defaultdict(list)      # (e, cad) -> [(promo_precio, leyenda)]
    for d in dirs:
        for r in rd(d + 'productos.csv'):
            e = r.get('id_producto', '').strip()
            if e not in sel: continue
            k = (r['id_comercio'], r['id_bandera'])
            if k not in ban: continue
            p = num(r.get('productos_precio_lista', ''))
            if not p or p > 5e6: continue
            cad = ban[k][0]; P[(e, cad)].append(p)
            pv = suc.get((r['id_comercio'], r['id_bandera'], r['id_sucursal']))
            if pv: PP[(e, pv, cad)].append(p)
            pp = num(r.get('productos_precio_unitario_promo1', ''))
            ley = r.get('productos_leyenda_promo1', '').strip()
            if pp and p * 0.4 <= pp < p * 0.97 and ley:
                h = hasta_iso(ley)
                if h is None or h > fecha: PR[(e, cad)].append((pp, ley[:90], h or ''))
    prods = []
    slugs = set()
    for e, (cat, sub, best) in sel.items():
        cads = {}
        for (ee, cad), v in ((k, v) for k, v in P.items() if k[0] == e) if False else []: pass
        prods.append([e, cat, sub, best])
    idx = collections.defaultdict(dict)
    for (e, cad), v in P.items(): idx[e][cad] = v
    idxp = collections.defaultdict(lambda: collections.defaultdict(dict))
    for (e, pv, cad), v in PP.items(): idxp[e][pv][cad] = v
    idxr = collections.defaultdict(dict)
    for (e, cad), v in PR.items(): idxr[e][cad] = v
    salida = []
    for e, cat, sub, best in prods:
        if len(idx[e]) < MIN_CADENAS - 1: continue
        nom = nombre_bonito(best)
        sl = slugify(nom)[:80].strip('-')
        if sl in slugs: sl = (sl + '-' + e[-4:])
        slugs.add(sl)
        cads = {}
        for cad, v in idx[e].items():
            v.sort(); med = statistics.median(v)
            v = [x for x in v if med / 3 < x < med * 3]   # descarta errores groseros
            if not v: continue
            item = {'p': round(statistics.median(v)), 'min': round(v[0]), 'max': round(v[-1]), 'n': len(v)}
            if cad in idxr[e]:
                pr = idxr[e][cad]; pmin = min(pr)
                item['promo'] = {'p': round(pmin[0]), 'txt': pmin[1], 'n': len(pr), 'hasta': pmin[2]}
            cads[cad] = item
        if len(cads) < MIN_CADENAS - 1: continue
        grandes_c = [c for c in cads if c in cad_info and cad_info[c]['suc'] >= 10]
        meds = [cads[c]['p'] for c in (grandes_c if len(grandes_c) >= 3 else cads)]
        prov = {}
        for pv, dd in idxp[e].items():
            fila = sorted(((round(statistics.median(v)), cad) for cad, v in dd.items()))
            prov[pv] = [[c, p] for p, c in fila[:6]]
        salida.append({'ean': e, 'slug': sl, 'nombre': nom, 'marca': (marca.get(e) or '').title(), 'cat': cat, 'sub': sub,
                       'cad': cads, 'med': round(statistics.median(meds)), 'min': min(meds), 'max': max(meds), 'prov': prov})
    salida.sort(key=lambda x: (x['cat'], x['sub'], -sum(c['n'] for c in x['cad'].values())))
    # --- cadenas
    cadenas = {}
    for sl, ci in cad_info.items():
        if 'nombre' not in ci: continue
        cadenas[sl] = {'nombre': ci['nombre'], 'sucursales': ci['suc'], 'prov': dict(ci['prov'].most_common())}
    # índice de precios por cadena (precio relativo a la mediana de cada producto)
    rel = collections.defaultdict(list)
    for p in salida:
        for cad, c in p['cad'].items(): rel[cad].append(c['p'] / p['med'])
    for cad, v in rel.items():
        if cad in cadenas and len(v) >= 40:
            cadenas[cad]['indice'] = round(media_recortada(v) * 100, 1); cadenas[cad]['productos'] = len(v)
    # --- canasta: un producto por subcategoría básica, presente en la mayor cantidad de cadenas grandes
    BASICOS = ['leche','aceite','arroz','fideos','azucar','yerba','harina','cafe','sal','tomate','aderezos','dulce-de-leche',
               'manteca','yogur','queso','galletitas','gaseosas','aguas','lavandina','detergente','jabon-para-ropa','papel-y-rollos',
               'shampoo','jabon-de-tocador','pasta-dental']
    FILTRO_CANASTA = {'papel-y-rollos': r'higi', 'aderezos': r'mayonesa', 'gaseosas': r'cola', 'aguas': r'mineral|^agua (sin|con) gas', 'azucar': r'com[uú]n|blanca|tipo a|superior',
                      'leche': r'entera|3 ?%|clasica|clásica', 'yogur': r'bebible|entero', 'galletitas': r'agua|crackers|salad', 'queso': r'crema|untable',
                      'cafe': r'molido|torrado', 'aceite': r'girasol', 'arroz': r'largo|fino|parboil|doble', 'fideos': r'spaghetti|tallar|mostachol|tirabuz'}
    grandes = [c for c, v in sorted(cadenas.items(), key=lambda x: -x[1]['sucursales']) if 'indice' in v][:12]
    canasta = []
    for sub in BASICOS:
        filtro = FILTRO_CANASTA.get(sub)
        cands = [p for p in salida if p['sub'] == sub and (not filtro or re.search(filtro, p['nombre'], re.I))]
        if not cands: cands = [p for p in salida if p['sub'] == sub]
        if not cands: continue
        cands.sort(key=lambda p: (-sum(1 for g in grandes if g in p['cad']), -sum(c['n'] for c in p['cad'].values())))
        canasta.append(cands[0]['slug'])
    bys = {p['slug']: p for p in salida}
    tot = {}
    for g in grandes:
        items = [bys[s]['cad'][g]['p'] for s in canasta if g in bys[s]['cad']]
        falt = [s for s in canasta if g not in bys[s]['cad']]
        # faltantes: se imputan con la mediana × índice de la cadena para comparar parejo
        imp = sum(bys[s]['med'] * cadenas[g]['indice'] / 100 for s in falt)
        tot[g] = {'total': round(sum(items) + imp), 'reales': len(items), 'imputados': len(falt)}
    can_prov = {}
    for pv in PROVINCIAS:
        fila = {}
        for g in cadenas:
            vals = []
            for s in canasta:
                pr = dict((c, p) for c, p in bys[s]['prov'].get(pv, []))
                if g in pr: vals.append(pr[g] / bys[s]['med'])
            if len(vals) >= len(canasta) * 0.6 and cadenas[g]['sucursales'] >= 5 and cadenas[g]['prov'].get(pv, 0) >= 2: fila[g] = round(media_recortada(vals) * 100, 1)
        if fila: can_prov[pv] = dict(sorted(fila.items(), key=lambda x: x[1]))
    meta = {'fecha': fecha, 'generado': datetime.datetime.now().isoformat(timespec='seconds'), 'productos': len(salida),
            'sucursales': sum(c['sucursales'] for c in cadenas.values()), 'cadenas': len(cadenas),
            'fuente': 'SEPA – Precios Claros, Secretaría de Comercio (datos.produccion.gob.ar)',
            'subcategorias': {s: SUB_NOMBRES[s] for s in sorted({p['sub'] for p in salida})},
            'provincias': PROVINCIAS}
    def dump(n, obj):
        with open(os.path.join(outdir, n), 'w', encoding='utf-8') as f: json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
    dump('productos.json', salida); dump('cadenas.json', cadenas)
    dump('canasta.json', {'items': canasta, 'cadenas': tot, 'provincias': can_prov}); dump('meta.json', meta)
    # --- historial acumulado (mediana nacional por producto y total canasta por cadena)
    hp = os.path.join(outdir, 'historial.json')
    H = json.load(open(hp, encoding='utf-8')) if os.path.exists(hp) else {'p': {}, 'c': {}}
    for p in salida: H['p'].setdefault(p['ean'], {})[fecha] = p['med']
    for g, t in tot.items(): H['c'].setdefault(g, {})[fecha] = t['total']
    for dct in list(H['p'].values()) + list(H['c'].values()):
        for k in sorted(dct)[:-400]: del dct[k]
    dump('historial.json', H)
    print(json.dumps({k: meta[k] for k in ('fecha', 'productos', 'sucursales', 'cadenas')}, ensure_ascii=False))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
