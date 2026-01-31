"""
ELK Pack - Knowledge Base
Domain: Civil Protection (Kabyle/Algeria)
Region: Wilaya de Béjaïa (06)
"""

# 1. Geographic Data (Béjaïa)
DAIRATE_BEJAIA = {
    "Bejaia": ["Bejaia", "Oued Ghir"],
    "Amizour": ["Amizour", "Ferraoun", "Smaoun", "Kendira"],
    "Sidi-Aich": ["Sidi-Aich", "Tinebdar", "El Flaye", "Tibane", "Sidi Ayad"],
    "Chemini": ["Chemini", "Souk Oufella", "Tibane", "Akfadou"],
    "Kherrata": ["Kherrata", "Dra El Caid"],
    "Tichy": ["Tichy", "Tala Hamza", "Boukhelifa"],
    "Aokas": ["Aokas", "Tizi N'Berber"],
    "Souk El Tenine": ["Souk El Tenine", "Melbou", "Tamridjet"],
    "Akbou": ["Akbou", "Chellata", "Ighram", "Tamokra"],
    "Tazmalt": ["Tazmalt", "Beni Mellikeche", "Boudjellil"],
    "El Kseur": ["El Kseur", "Fenaia Ilmaten", "Toudja"],
    "Adekar": ["Adekar", "Taourirt Ighil", "Beni Ksila"],
    "Beni Maouche": ["Beni Maouche"],
    "Seddouk": ["Seddouk", "Bouhamza", "M'cisna", "Amalou"],
    "Ighil Ali": ["Ighil Ali", "Ait R'zine"],
    "Barbacha": ["Barbacha", "Kendira"],
    "Timezrit": ["Timezrit"],
    "Darguina": ["Darguina", "Taskriout", "Ait Smail"]
}

# Flattened list for RAG
COMMUNES_FLAT = [c for sublist in DAIRATE_BEJAIA.values() for c in sublist]

# Urban Neighborhoods (Quartiers Pop)
QUARTIERS_BEJAIA = [
    "Ihaddaden", "Sidi Ahmed", "Ighil Ouazzoug", "Dar Nacer", "Amriw", 
    "Sidi Ali Lebhar", "Boulimat", "Targa Ouzemour", "La Brise de Mer",
    "Les Oliviers", "Cité Tobbal"
]

# 2. Vocabulary Mapping (Kabyle/Arabizi -> Standard French)
VOCAB_MAP = {
    # Fire
    "times": "incendie",
    "l3afia": "incendie",
    "lḥriq": "incendie",
    "lhrik": "incendie",
    
    # Accident
    "aksida": "accident",
    "mdaggan": "collision",
    "teqleb": "renversé",
    "yeqleb": "renversé",
    
    # Medical
    "amdiw": "malade",
    "yeḥrec": "grave",
    "yemmut": "décédé",
    "irrouḥ": "décédé",
    
    # Context
    "azul": "bonjour",
    "salam": "bonjour",
    "ya": "yak"
}
