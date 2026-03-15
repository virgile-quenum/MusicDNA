"""
filters.py — Source unique de vérité pour les exclusions daughters/kids.
"""

DAUGHTERS_ARTISTS = {
    # Contes & livres audio
    'Alain Royer','Gérard Philipe','Gallimard Jeunesse','Contes pour enfants',
    # Chansons enfants
    'Henri Dès','Les Petites Tounes','Gérard Delahaye','Monde des Titounis',
    'Anny Versini','Magguy Faraux','HeyKids Comptine Pour Bébé',
    'Le Choeur des Enfants',"Les plus belles comptines d'Okoo",
    'La Reine des chansons pour enfants et bébés',
    # Lullabies bébé 2020-2021
    'Judson Mancebo','Lullaby Time','Marco Bernardo','Beth McLaughlin',
    "Baby Music from I'm In Records",'Miles Patrick',
    'Christian Music For Babies From I\'m In Records',
    'Baby Bedtime Lullaby','Jammy Jams',
    # Bollywood
    'Jatin-Lalit','Pritam','Sanjay Leela Bhansali','Neha Kakkar',
    'Panjabi MC','Sonu Nigam','Kumar Sanu','Alka Yagnik',
    'Lata Mangeshkar','Udit Narayan','Shankar-Ehsaan-Loy','Shreya Ghoshal',
    # Rumba congolaise / Wolof twins
    'Emile Biayenda','Jean-Emile Biayenda',"Lamine M'bengue",
    # Latin filles
    'Shakira',
    # Divers filles
    'GIMS','Meryl','Claire Keim','Sanseverino','Issa Dakuyo','Naza',
}

DAUGHTERS_TRACKS = {('On se connaît','Youssoupha')}

DAUGHTERS_KW = [
    'pirates','chaperon','neige','cirque','haricot','sirène',
    'cendrillon','poucet','barbe bleue','carnaval chocolat',
    'titounis','comptine','berceuse','okoo','lullaby','ninna nanna',
]

def is_daughters(r):
    if r['artistName'] in DAUGHTERS_ARTISTS: return True
    if (r['trackName'], r['artistName']) in DAUGHTERS_TRACKS: return True
    return any(k in r['trackName'].lower() for k in DAUGHTERS_KW)

def split(records):
    my  = [r for r in records if not is_daughters(r)]
    dau = [r for r in records if is_daughters(r)]
    return my, dau
