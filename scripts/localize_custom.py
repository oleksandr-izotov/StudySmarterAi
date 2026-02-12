import os
import re
import polib
from pathlib import Path
from django.conf import settings

# Configure basic settings to access LANGUAGES
if not settings.configured:
    settings.configure(DEBUG=True, LANGUAGES=[
        ('de', 'German'),
        ('en', 'English'),
        ('ru', 'Russian'),
        ('fr', 'French'),
        ('es', 'Spanish'),
    ], BASE_DIR=Path(__file__).resolve().parent.parent)

BASE_DIR = settings.BASE_DIR
LOCALE_DIR = BASE_DIR / 'locale'

# Translations dictionary
TRANSLATIONS = {
    "Управление подпиской": {
        "en": "Subscription Management",
        "de": "Abonnementverwaltung",
        "fr": "Gestion de l'abonnement",
        "es": "Gestión de suscripciones",
        "ru": "Управление подпиской"
    },
    "Ваш текущий план": {
        "en": "Your current plan",
        "de": "Ihr aktueller Plan",
        "fr": "Votre plan actuel",
        "es": "Tu plan actual",
        "ru": "Ваш текущий план"
    },
    "Активна": {
        "en": "Active",
        "de": "Aktiv",
        "fr": "Actif",
        "es": "Activo",
        "ru": "Активна"
    },
    "Неактивна": {
        "en": "Inactive",
        "de": "Inaktiv",
        "fr": "Inactif",
        "es": "Inactivo",
        "ru": "Неактивна"
    },
    "Цена": {
        "en": "Price",
        "de": "Preis",
        "fr": "Prix",
        "es": "Precio",
        "ru": "Цена"
    },
    "месяц": {
        "en": "month",
        "de": "Monat",
        "fr": "mois",
        "es": "mes",
        "ru": "месяц"
    },
    "Лимит": {
        "en": "Limit",
        "de": "Limit",
        "fr": "Limite",
        "es": "Límite",
        "ru": "Лимит"
    },
    "день": {
        "en": "day",
        "de": "Tag",
        "fr": "jour",
        "es": "día",
        "ru": "день"
    },
    "Действия": {
        "en": "Actions",
        "de": "Aktionen",
        "fr": "Actions",
        "es": "Acciones",
        "ru": "Действия"
    },
    "Сменить план": {
        "en": "Change Plan",
        "de": "Plan ändern",
        "fr": "Changer de plan",
        "es": "Cambiar plan",
        "ru": "Сменить план"
    },
    "Вы уверены, что хотите отменить подписку?": {
        "en": "Are you sure you want to cancel your subscription?",
        "de": "Sind Sie sicher, dass Sie Ihr Abonnement kündigen möchten?",
        "fr": "Êtes-vous sûr de vouloir annuler votre abonnement ?",
        "es": "¿Estás seguro de que deseas cancelar tu suscripción?",
        "ru": "Вы уверены, что хотите отменить подписку?"
    },
    "Отменить подписку": {
        "en": "Cancel Subscription",
        "de": "Abonnement kündigen",
        "fr": "Annuler l'abonnement",
        "es": "Cancelar suscripción",
        "ru": "Отменить подписку"
    },
    "У вас нет активной подписки": {
        "en": "You have no active subscription",
        "de": "Sie haben kein aktives Abonnement",
        "fr": "Vous n'avez pas d'abonnement actif",
        "es": "No tienes una suscripción activa",
        "ru": "У вас нет активной подписки"
    },
    "Оформите подписку, чтобы получить больше возможностей": {
        "en": "Subscribe to get more features",
        "de": "Abonnieren Sie, um mehr Funktionen zu erhalten",
        "fr": "Abonnez-vous pour obtenir plus de fonctionnalités",
        "es": "Suscríbete para obtener más funciones",
        "ru": "Оформите подписку, чтобы получить больше возможностей"
    },
    "Посмотреть тарифы": {
        "en": "View Pricing",
        "de": "Preise anzeigen",
        "fr": "Voir les tarifs",
        "es": "Ver precios",
        "ru": "Посмотреть тарифы"
    },
    "Оплата успешна": {
        "en": "Payment Successful",
        "de": "Zahlung erfolgreich",
        "fr": "Paiement réussi",
        "es": "Pago exitoso",
        "ru": "Оплата успешна"
    },
    "Спасибо за подписку!": {
        "en": "Thanks for subscribing!",
        "de": "Danke für das Abonnieren!",
        "fr": "Merci de vous être abonné !",
        "es": "¡Gracias por suscribirte!",
        "ru": "Спасибо за подписку!"
    },
    "Ваша подписка успешно активирована. Наслаждайтесь всеми преимуществами вашего нового плана!": {
        "en": "Your subscription has been successfully activated. Enjoy all the benefits of your new plan!",
        "de": "Ihr Abonnement wurde erfolgreich aktiviert. Genießen Sie alle Vorteile Ihres neuen Plans!",
        "fr": "Votre abonnement a été activé avec succès. Profitez de tous les avantages de votre nouveau plan !",
        "es": "Tu suscripción se ha activado con éxito. ¡Disfruta de todos los beneficios de tu nuevo plan!",
        "ru": "Ваша подписка успешно активирована. Наслаждайтесь всеми преимуществами вашего нового плана!"
    },
    "Начать использовать": {
        "en": "Start Using",
        "de": "Anfangen zu benutzen",
        "fr": "Commencer à utiliser",
        "es": "Empezar a usar",
        "ru": "Начать использовать"
    },
    "Управление подпиской": {
        "en": "Manage Subscription",
        "de": "Abonnement verwalten",
        "fr": "Gérer l'abonnement",
        "es": "Administrar suscripción",
        "ru": "Управление подпиской"
    },
    "Отменить подписку?": {
        "en": "Cancel Subscription?",
        "de": "Abonnement kündigen?",
        "fr": "Annuler l'abonnement ?",
        "es": "¿Cancelar suscripción?",
        "ru": "Отменить подписку?"
    },
    "Вы уверены, что хотите отменить подписку? Ваш доступ сохранится до конца оплаченного периода.": {
        "en": "Are you sure you want to cancel your subscription? Your access will remain until the end of the paid period.",
        "de": "Sind Sie sicher, dass Sie Ihr Abonnement kündigen möchten? Ihr Zugang bleibt bis zum Ende des bezahlten Zeitraums erhalten.",
        "fr": "Êtes-vous sûr de vouloir annuler votre abonnement ? Votre accès restera actif jusqu'à la fin de la période payée.",
        "es": "¿Estás seguro de que deseas cancelar tu suscripción? Tu acceso permanecerá hasta el final del período pagado.",
        "ru": "Вы уверены, что хотите отменить подписку? Ваш доступ сохранится до конца оплаченного периода."
    },
    "Оставить": {
        "en": "Keep",
        "de": "Behalten",
        "fr": "Conserver",
        "es": "Mantener",
        "ru": "Оставить"
    },
    "Отменить": {
        "en": "Cancel",
        "de": "Kündigen",
        "fr": "Annuler",
        "es": "Cancelar",
        "ru": "Отменить"
    },
    "Подписка": {
        "en": "Subscription",
        "de": "Abonnement",
        "fr": "Abonnement",
        "es": "Suscripción",
        "ru": "Подписка"
    },
    "У вас бесплатный план": {
        "en": "You have a free plan",
        "de": "Sie haben einen kostenlosen Plan",
        "fr": "Vous avez un plan gratuit",
        "es": "Tienes un plan gratuito",
        "ru": "У вас бесплатный план"
    },
    "Улучшить план": {
        "en": "Upgrade Plan",
        "de": "Plan upgraden",
        "fr": "Améliorer le plan",
        "es": "Mejorar plan",
        "ru": "Улучшить план"
    }
}

target_files = [
    BASE_DIR / 'templates' / 'pages' / 'checkout_success.html',
    BASE_DIR / 'templates' / 'pages' / 'account.html',
]

def extract_strings(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Regex to find {% trans "string" %} or {% trans 'string' %}
    matches = re.findall(r'{%\s*trans\s+["\'](.*?)["\']\s*%}', content)
    return matches

def update_po_file(lang_code):
    po_path = LOCALE_DIR / lang_code / 'LC_MESSAGES' / 'django.po'
    
    if not po_path.exists():
        print(f"Creating new PO file for {lang_code}")
        po = polib.POFile()
        po.metadata = {
            'Project-Id-Version': 'StudyAssistant',
            'Report-Msgid-Bugs-To': '',
            'POT-Creation-Date': '2026-02-09 00:00+0000',
            'PO-Revision-Date': '2026-02-09 00:00+0000',
            'Last-Translator': '',
            'Language-Team': '',
            'Language': lang_code,
            'MIME-Version': '1.0',
            'Content-Type': 'text/plain; charset=UTF-8',
            'Content-Transfer-Encoding': '8bit',
        }
    else:
        print(f"Updating existing PO file for {lang_code}")
        po = polib.pofile(str(po_path))

    # Extract strings from templates
    all_strings = set()
    for file_path in target_files:
        all_strings.update(extract_strings(file_path))

    # Add or update entries
    for msgid in all_strings:
        entry = po.find(msgid)
        translation = TRANSLATIONS.get(msgid, {}).get(lang_code, "")
        
        if entry:
            if not entry.msgstr and translation:
                 entry.msgstr = translation
                 if 'fuzzy' in entry.flags:
                     entry.flags.remove('fuzzy')
        else:
            entry = polib.POEntry(
                msgid=msgid,
                msgstr=translation,
            )
            po.append(entry)

    po.save(str(po_path))
    print(f"Saved {po_path}")

    # Compile to .mo
    mo_path = LOCALE_DIR / lang_code / 'LC_MESSAGES' / 'django.mo'
    po.save_as_mofile(str(mo_path))
    print(f"Compiled to {mo_path}")

def main():
    for lang_code, _ in settings.LANGUAGES:
        update_po_file(lang_code)

if __name__ == '__main__':
    main()
