# Ciudades principales por provincia: (nombre, lat, lng, radio en km).
# Cada sucursal se asigna a la ciudad más cercana dentro del radio (las localidades del SEPA vienen
# mal cargadas: Día pone "BUENOS AIRES" en todas). El conurbano se divide en zonas Norte, Oeste y Sur.
import math

CIUDADES = {
 'AR-B': [('La Plata', -34.921, -57.955, 15), ('Mar del Plata', -38.005, -57.556, 20), ('Bahía Blanca', -38.719, -62.272, 15),
          ('Tandil', -37.321, -59.134, 10), ('Olavarría', -36.893, -60.322, 10), ('Junín', -34.585, -60.959, 10), ('Pergamino', -33.890, -60.573, 10),
          ('San Nicolás', -33.334, -60.211, 10), ('Zárate', -34.098, -59.028, 7), ('Campana', -34.163, -58.959, 6), ('Necochea', -38.555, -58.739, 10),
          ('Azul', -36.777, -59.858, 8), ('Tres Arroyos', -38.377, -60.275, 8), ('Trenque Lauquen', -35.970, -62.734, 8), ('Luján', -34.570, -59.105, 8),
          ('Chivilcoy', -34.896, -60.017, 8), ('Punta Alta', -38.879, -62.075, 6), ('Carmen de Patagones', -40.798, -62.984, 8), ('Nueve de Julio', -35.444, -60.884, 7),
          ('Mercedes', -34.651, -59.430, 7), ('Villa Gesell', -37.264, -56.973, 8), ('Pinamar', -37.108, -56.861, 8), ('Coronel Pringles', -37.983, -61.355, 6)],
 'AR-S': [('Rosario', -32.947, -60.639, 20), ('Santa Fe capital', -31.633, -60.700, 15), ('Rafaela', -31.253, -61.492, 10), ('Venado Tuerto', -33.746, -61.969, 10),
          ('Reconquista', -29.150, -59.651, 10), ('Sunchales', -30.944, -61.561, 6), ('Esperanza', -31.449, -60.931, 6), ('San Lorenzo', -32.745, -60.737, 8),
          ('Casilda', -33.044, -61.168, 6)],
 'AR-X': [('Córdoba capital', -31.420, -64.188, 20), ('Río Cuarto', -33.123, -64.349, 12), ('Villa María', -32.410, -63.240, 10), ('Villa Carlos Paz', -31.424, -64.497, 8),
          ('San Francisco', -31.428, -62.083, 8), ('Jesús María', -30.981, -64.094, 8), ('Alta Gracia', -31.659, -64.430, 8), ('Bell Ville', -32.626, -62.689, 6),
          ('Río Tercero', -32.173, -64.113, 6)],
 'AR-M': [('Gran Mendoza', -32.890, -68.845, 22), ('San Rafael', -34.617, -68.330, 12), ('General Alvear', -34.977, -67.700, 8), ('Tunuyán', -33.578, -69.015, 8),
          ('San Martín', -33.081, -68.468, 8)],
 'AR-T': [('San Miguel de Tucumán', -26.808, -65.218, 15), ('Concepción', -27.343, -65.592, 8)],
 'AR-E': [('Paraná', -31.732, -60.529, 12), ('Concordia', -31.393, -58.021, 10), ('Gualeguaychú', -33.009, -58.517, 8), ('Concepción del Uruguay', -32.484, -58.233, 8),
          ('Gualeguay', -33.145, -59.310, 6), ('Victoria', -32.618, -60.155, 6), ('Villaguay', -31.866, -59.027, 6), ('Chajarí', -30.751, -57.987, 6), ('Colón', -32.224, -58.144, 6)],
 'AR-A': [('Salta capital', -24.782, -65.423, 15), ('Tartagal', -22.516, -63.801, 8), ('Orán', -23.132, -64.326, 8), ('Metán', -25.497, -64.973, 6)],
 'AR-Q': [('Neuquén capital', -38.951, -68.059, 15), ('Cutral Có', -38.934, -69.230, 8), ('Zapala', -38.899, -70.054, 8), ('San Martín de los Andes', -40.157, -71.353, 8)],
 'AR-R': [('Bariloche', -41.133, -71.310, 12), ('General Roca', -39.033, -67.583, 10), ('Cipolletti', -38.934, -67.990, 8), ('Viedma', -40.813, -62.997, 8),
          ('Villa Regina', -39.100, -67.083, 6), ('Allen', -38.977, -67.827, 5), ('San Antonio Oeste', -40.731, -64.948, 6), ('El Bolsón', -41.964, -71.534, 6)],
 'AR-U': [('Comodoro Rivadavia', -45.864, -67.497, 15), ('Trelew', -43.253, -65.309, 10), ('Puerto Madryn', -42.769, -65.038, 10), ('Rawson', -43.300, -65.102, 5),
          ('Esquel', -42.911, -71.319, 8)],
 'AR-Z': [('Río Gallegos', -51.623, -69.216, 10), ('Caleta Olivia', -46.439, -67.528, 8), ('El Calafate', -50.338, -72.265, 8)],
 'AR-V': [('Ushuaia', -54.801, -68.303, 10), ('Río Grande', -53.787, -67.709, 10)],
 'AR-W': [('Corrientes capital', -27.469, -58.830, 12), ('Goya', -29.144, -59.264, 8), ('Paso de los Libres', -29.713, -57.088, 6), ('Mercedes', -29.184, -58.075, 6)],
 'AR-H': [('Resistencia', -27.451, -58.986, 12), ('Presidencia Roque Sáenz Peña', -26.785, -60.439, 8)],
 'AR-N': [('Posadas', -27.367, -55.896, 12), ('Oberá', -27.487, -55.120, 8), ('Eldorado', -26.404, -54.616, 8)],
 'AR-P': [('Formosa capital', -26.185, -58.175, 10)],
 'AR-Y': [('San Salvador de Jujuy', -24.186, -65.299, 12), ('San Pedro de Jujuy', -24.231, -64.866, 6), ('Libertador General San Martín', -23.806, -64.788, 6)],
 'AR-G': [('Santiago del Estero capital', -27.795, -64.261, 12), ('Termas de Río Hondo', -27.493, -64.860, 6)],
 'AR-K': [('San Fernando del Valle de Catamarca', -28.469, -65.779, 10)],
 'AR-F': [('La Rioja capital', -29.413, -66.856, 10), ('Chilecito', -29.163, -67.498, 6)],
 'AR-J': [('San Juan capital', -31.537, -68.536, 15)],
 'AR-D': [('San Luis capital', -33.301, -66.338, 10), ('Villa Mercedes', -33.675, -65.462, 10)],
 'AR-L': [('Santa Rosa', -36.620, -64.290, 10), ('General Pico', -35.656, -63.757, 8)],
}
OBELISCO = (-34.6037, -58.3816)

def km(a, b, c, d):
    r = math.pi / 180
    x = (d - b) * r * math.cos((a + c) / 2 * r); y = (c - a) * r
    return 6371 * math.hypot(x, y)

def ciudad(pv, lat, lng):
    """Nombre de la ciudad/zona de una sucursal, o None si queda fuera de las ciudades conocidas."""
    if pv == 'AR-C' or lat is None: return None
    mejor = None
    for n, la, lo, rad in CIUDADES.get(pv, []):
        dd = km(lat, lng, la, lo)
        if dd <= rad and (mejor is None or dd < mejor[1]): mejor = (n, dd)
    if mejor: return mejor[0]
    if pv == 'AR-B' and km(lat, lng, *OBELISCO) <= 55:
        ang = math.degrees(math.atan2(lat - OBELISCO[0], lng - OBELISCO[1])) % 360
        if 90 <= ang < 175: return 'GBA Zona Norte'
        if 175 <= ang < 225: return 'GBA Zona Oeste'
        return 'GBA Zona Sur'
    return None
