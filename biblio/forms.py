# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, URL # Importez Optional et URL

class LivreForm(FlaskForm):
    """Formulaire pour ajouter ou modifier un livre."""
    titre = StringField(
        'Titre', 
        validators=[
            DataRequired(message="Le titre est obligatoire."),
            Length(min=1, max=100, message="Le titre doit faire entre 1 et 100 caractères.")
        ],
        render_kw={"placeholder": "Ex: Le Rouge et le Noir"}
    )
    auteur = StringField(
        'Auteur', 
        validators=[DataRequired(message="L'auteur est obligatoire."), Length(min=2, max=100)],
        render_kw={"placeholder": "Ex: Stendhal"}
    )
    annee = IntegerField(
        'Année de publication', 
        validators=[
            DataRequired(message="L'année est obligatoire."),
            NumberRange(min=1000, max=9999, message="Veuillez entrer une année valide (4 chiffres).")
        ],
        render_kw={"placeholder": "Ex: 1830"}
    )
    genre = SelectField(
        'Genre', 
        validators=[DataRequired(message="Le genre est obligatoire.")],
        coerce=str
    )
    description = TextAreaField(
        'Description',
        validators=[Length(max=500)],
        render_kw={"rows": 3, "placeholder": "Ajoutez un court résumé du livre..."}
    )
    note = SelectField(
        'Note (sur 5)', 
        choices=[
            ('5', '5 ★★★★★'),
            ('4', '4 ★★★★'),
            ('3', '3 ★★★'),
            ('2', '2 ★★'),
            ('1', '1 ★')
        ], 
        validators=[DataRequired()],
        coerce=int
    )
    # --- NOUVEAU CHAMP POUR L'IMAGE ---
    image_url = StringField(
        'URL de l\'image de couverture',
        validators=[
            Optional(), # Ce champ est optionnel
            URL(message="Veuillez entrer une URL valide.") # Valide que c'est une URL si renseigné
        ],
        render_kw={"placeholder": "Ex: https://exemple.com/image.jpg"}
    )
    submit = SubmitField('Enregistrer le livre')