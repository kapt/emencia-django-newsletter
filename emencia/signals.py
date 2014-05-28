from django.dispatch import Signal

contact_unsubscribed = Signal(providing_args=["mailing_list"])
contact_subscribed = Signal(providing_args=["contact", "request"])
