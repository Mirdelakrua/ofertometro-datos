# Reglas de categoría por descripción SEPA (mayúsculas, abreviada)
import re
CATS = [
 # (slug, nombre, subcat, regex)
 ('almacen','Almacén','aceite',r'^ACEITE\b(?!.*(MOTOR|BEBE|CORPORAL|JOHNSON|OLIVA EN AEROSOL))'),
 ('almacen','Almacén','arroz',r'^ARROZ\b'),
 ('almacen','Almacén','fideos',r'^FIDEO'),
 ('almacen','Almacén','harina',r'^HARINA\b(?!.*MAIZ)'),
 ('almacen','Almacén','azucar',r'^AZ[UÚ]CAR\b'),
 ('almacen','Almacén','yerba',r'\bYERBA\b|^Y\.M\.|\bYERBA MATE\b'),
 ('almacen','Almacén','cafe',r'^CAF[EÉ]\b'),
 ('almacen','Almacén','te-y-mate-cocido',r'^TE\b|\bTE EN SAQ|\bMATE COCIDO\b|^TE '),
 ('almacen','Almacén','sal',r'^SAL\b'),
 ('almacen','Almacén','tomate',r'PURE TOMATE|PUR[EÉ] DE TOMATE|TOMATE TRITURADO|PULPA DE TOMATE|TOMATES PERITA'),
 ('almacen','Almacén','aderezos',r'\bMAYONESA\b|\bKETCHUP\b|\bMOSTAZA\b|\bSAVORA\b|\bSALSA GOLF\b'),
 ('almacen','Almacén','conservas',r'\bATUN\b|\bAT[UÚ]N\b|\bARVEJAS\b|\bCHOCLO\b|\bDURAZNO.*(MITAD|ALMIBAR)|\bCABALLA\b'),
 ('almacen','Almacén','galletitas',r'^GALL|^G\.|\bGALLETITA'),
 ('almacen','Almacén','dulce-de-leche',r'DULCE DE LECHE|^D\.DE LECHE|^D\. DE LECHE'),
 ('almacen','Almacén','caldos-y-sopas',r'\bCALDO\b|\bSOPA\b'),
 ('almacen','Almacén','legumbres',r'^(LENTEJA|POROTO|GARBANZO|ARVEJA)'),
 ('almacen','Almacén','polenta',r'\bPOLENTA\b|\bHARINA DE MAIZ'),
 ('almacen','Almacén','mermeladas',r'MERMELADA|^M\.BC|\bDULCE DE (BATATA|MEMBRILLO)'),
 ('almacen','Almacén','cacao',r'\bCACAO\b|\bNESQUIK\b|\bTODDY\b'),
 ('lacteos','Lácteos','leche',r'^LECHE\b(?!.*(POLVO.*BEBE|CORPORAL))'),
 ('lacteos','Lácteos','yogur',r'\bYOG|^Y\.SER|\bACTIMEL\b'),
 ('lacteos','Lácteos','manteca',r'^MANTECA\b'),
 ('lacteos','Lácteos','queso',r'^QUESO\b|^Q\.|\bCASANCREM\b'),
 ('lacteos','Lácteos','crema',r'^CREMA (LS|DE LECHE|SERENISIMA|LA SERENISIMA)|CREMA DE LECHE'),
 ('bebidas','Bebidas','gaseosas',r'\bGASEOSA\b|\bCOCA COLA\b|\bPEPSI\b|\bSPRITE\b|\bFANTA\b|\b7 ?UP\b|\bSCHWEPPES\b'),
 ('bebidas','Bebidas','aguas',r'^AGUA\b(?!.*(OXIGENADA|COLONIA|MICELAR|DE ROSAS))|\bAQUARIUS\b'),
 ('bebidas','Bebidas','jugos',r'^JUGO\b|^J\.(?!LIQ)|\bCEPITA\b|\bBAGGIO\b|\bTANG\b'),
 ('bebidas','Bebidas','cervezas',r'\bCERVEZA\b|\bCERV\.'),
 ('bebidas','Bebidas','vinos',r'^VINO\b'),
 ('bebidas','Bebidas','aperitivos',r'\bFERNET\b|\bAPERITIVO\b|\bCYNAR\b|\bGANCIA\b|\bCAMPARI\b|\bVODKA\b|\bWHISKY\b'),
 ('limpieza','Limpieza','lavandina',r'\bLAVANDINA\b'),
 ('limpieza','Limpieza','detergente',r'^DET(ERGENTE)?\b|\bLAVAV'),
 ('limpieza','Limpieza','jabon-para-ropa',r'JAB(ON|ÓN).*(POLVO|LIQ.*ROPA|ROPA)|\bALA MATIC\b|\bSKIP\b|\bJABON LIQ\.ALA'),
 ('limpieza','Limpieza','suavizante',r'\bSUAVIZANTE\b|\bSUAV\.|\bVIVERE\b|\bCOMFORT\b'),
 ('limpieza','Limpieza','limpiadores',r'\bLIMPIADOR|^LIQ\.(POETT|PROCENEX|CIF)|\bCIF\b|\bMR\.? ?MUSCULO\b'),
 ('limpieza','Limpieza','papel-y-rollos',r'PAPEL HIG|^P\.HIG|ROLLO (DE )?COCINA|\bSERVILLETA'),
 ('perfumeria','Perfumería','shampoo',r'^SHAMPOO\b|^SH\.|\bSHAMPOO\b'),
 ('perfumeria','Perfumería','acondicionador',r'^ACOND'),
 ('perfumeria','Perfumería','jabon-de-tocador',r'^JAB(ON|ÓN)\b(?!.*(POLVO|ROPA|MATIC|LIQ.*ROPA))'),
 ('perfumeria','Perfumería','desodorante',r'^DESOD|^ANTIT|ANTITRANSPIRANTE'),
 ('perfumeria','Perfumería','pasta-dental',r'PASTA DENTAL|CREMA DENTAL|^C\.DENT'),
 ('perfumeria','Perfumería','panales',r'PA[ÑN]AL'),
 ('perfumeria','Perfumería','toallitas-femeninas',r'TOALLITAS? FEM|\bCAREFREE\b|\bLADYSOFT\b|\bSIEMPRE LIBRE\b|\bKOTEX\b'),
]
SUB_NOMBRES = {
 'aceite':'Aceite','arroz':'Arroz','fideos':'Fideos','harina':'Harina','azucar':'Azúcar','yerba':'Yerba mate',
 'cafe':'Café','te-y-mate-cocido':'Té y mate cocido','sal':'Sal','tomate':'Puré y tomate','aderezos':'Mayonesa y aderezos',
 'conservas':'Conservas','galletitas':'Galletitas','dulce-de-leche':'Dulce de leche','caldos-y-sopas':'Caldos y sopas',
 'legumbres':'Legumbres','polenta':'Polenta','mermeladas':'Mermeladas','cacao':'Cacao en polvo',
 'leche':'Leche','yogur':'Yogur','manteca':'Manteca','queso':'Queso','crema':'Crema de leche',
 'gaseosas':'Gaseosas','aguas':'Agua','jugos':'Jugos','cervezas':'Cerveza','vinos':'Vino','aperitivos':'Fernet y aperitivos',
 'lavandina':'Lavandina','detergente':'Detergente','jabon-para-ropa':'Jabón para ropa','suavizante':'Suavizante',
 'limpiadores':'Limpiadores','papel-y-rollos':'Papel higiénico y rollos',
 'shampoo':'Shampoo','acondicionador':'Acondicionador','jabon-de-tocador':'Jabón de tocador','desodorante':'Desodorante',
 'pasta-dental':'Pasta dental','panales':'Pañales','toallitas-femeninas':'Toallitas femeninas',
}
_C = [(a,b,c,re.compile(r)) for a,b,c,r in CATS]
EXCL = re.compile(r'CHOCOLATAD|\bALFAJOR|\bHELADO|\bFILTRO|\bPALITOS\b|\bRAVIOL|\bMEDALL|\bSALSA QUESO|\bTAPA|\bJABONERA|\bCEPILLO|\bHILO DENTAL|\bENJUAGUE|\bCONDIMENTO|\bROCKLETS|\bMANI\b|\bHUMMUS|\bREBOZADOR|\bPAN RALLADO|\bBIZCOCHUELO|\bPREMEZCLA')
def clasificar(desc):
    d = desc.upper()
    if EXCL.search(d): return None
    for a,b,c,r in _C:
        if r.search(d): return a,c
    return None
def clasificar_varias(descs):
    """descs: Counter desc->n. Excluye si alguna descripción pega en la lista negra; vota la categoría."""
    if any(EXCL.search(d.upper()) for d in descs): return None
    v = {}
    for d, n in descs.items():
        k = clasificar(d)
        if k: v[k] = v.get(k, 0) + n
    if not v: return None
    k = max(v, key=v.get)
    return k if v[k] >= sum(descs.values()) * 0.34 else None
