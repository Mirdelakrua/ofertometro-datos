#!/usr/bin/env python3
"""Baja el último SEPA publicado y regenera los JSON de la raíz del repo.
Uso (desde la raíz del repo): python3 -I pipeline/actualizar.py
Sale con código 0 y el texto SIN-CAMBIOS si el dataset más reciente ya estaba procesado."""
import json, os, subprocess, sys, tempfile, urllib.request
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = 'https://datos.produccion.gob.ar/api/3/action/package_show?id=sepa-precios'
DIAS = {'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'}

def main():
    res = json.load(urllib.request.urlopen(API, timeout=60))['result']['resources']
    res = [r for r in res if r['name'] in DIAS and r['url'].endswith('.zip')]
    r = max(res, key=lambda x: x.get('last_modified') or x.get('created') or '')
    marca = (r.get('last_modified') or '')[:19]
    meta = os.path.join(RAIZ, 'meta.json')
    prev = json.load(open(meta, encoding='utf-8')) if os.path.exists(meta) else {}
    if prev.get('sepa_publicado') == marca:
        print('SIN-CAMBIOS', marca); return
    tmp = tempfile.mkdtemp(prefix='sepa_')
    z = os.path.join(tmp, 'sepa.zip')
    print('Bajando', r['url'], r.get('size'))
    subprocess.run(['curl', '-sSL', '--retry', '3', '-o', z, r['url']], check=False)
    if os.path.getsize(z) < 100_000_000:
        sys.exit('ZIP demasiado chico: %d bytes' % os.path.getsize(z))
    subprocess.run([sys.executable, '-I', os.path.join(RAIZ, 'pipeline', 'procesar.py'), z, RAIZ], check=True)
    m = json.load(open(meta, encoding='utf-8'))
    m['sepa_publicado'] = marca
    m['sepa_recurso'] = r['name']
    json.dump(m, open(meta, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('OK', m['fecha'], m['productos'], 'productos')

if __name__ == '__main__':
    main()
