# -*- coding: utf-8 -*-
"""
Views for emencia Subscriber Verification
"""
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_str

from emencia.models \
    import SMTPServer, MailingList, SubscriberVerification
from emencia.settings import DEFAULT_HEADER_REPLY

from django.utils import translation

def view_subscriber_verification(request, form_class):
    """
    A simple view that shows a form for subscription for the newsletter.
    """
    context = {}

    if request.POST:
        context['form'] = form_class(request.POST)
        subscription = SubscriberVerification()
        if context['form'].is_valid():
            contact = context['form'].save()

            subscription.contact = context['form'].instance
            subscription.save()
            link_id = subscription.link_id

            # select smtpserver, maybe, a boolean field for 'standard' will be
            # a nice idea.
            server = SMTPServer.objects.get(id=1)

            # set server settings to django
            settings.EMAIL_HOST = smart_str(server.host)
            settings.EMAIL_HOST_PASSWORD = smart_str(server.password)
            settings.EMAIL_HOST_USER = smart_str(server.user)
            settings.EMAIL_PORT = int(server.port)
            settings.EMAIL_USE_TLS = server.tls

            # mail settings
            subject = _('Subriber verification')
            message = _('Thanks for subscription, please click the following link to verificate your email address.')
            from_mail = DEFAULT_HEADER_REPLY
            to_mail = context['form'].instance.email

            link = 'http://{0}/newsletters/subscribe/{1}'.format(str(request.get_host()), str(link_id))
            text_content = u'{0!s}\n\n {1}'.format(message, link)
            html_content = u'<body><p>{0!s}</p><p><a href="{1}">{2}</a></p></body>'.format(message, link, _('verify link'))
            msg = EmailMultiAlternatives(
                subject,
                text_content,
                from_mail,
                [to_mail]
            )
            msg.attach_alternative(html_content, 'text/html')
            msg.send()

            context['send'] = True

    else:
        context['form'] = form_class()

    return render_to_response('newsletter/subscriber_verification.html',
                              context,
                              context_instance=RequestContext(request))

def view_uuid_verification(request, link_id, form_class=None):
    """
    A simple view that shows if verification is true or false.
    """
    ready = False
    context = {}
    context['mailinglists'] = mailinglists = MailingList.objects.filter(public=True)
    context['mailing_list_count'] = mailinglists.count()
    context['link_id'] = link_id

    try:
        subscription = {}
        subscription['object'] = SubscriberVerification.objects.get(
            link_id=link_id
        )
        context['uuid_exist'] = True
        subscription['contact'] = subscription['object'].contact

        if context['mailing_list_count'] == 1:
            mailing_list = mailinglists.get().subscribers.add(
                subscription['contact'].id
            )
            ready = True
            
        elif request.POST:
            form = form_class(request.POST)
            if form.is_valid():
                form.save(subscription['contact'].id)
                context['send'] = True
                ready = True
                
        else:
            context['form'] = form_class()

        if ready:
            subscription['contact'].verified = True
            subscription['contact'].save()
            subscription['object'].delete()
        
    except SubscriberVerification.DoesNotExist:
        context['uuid_exist'] = False

    return render_to_response('newsletter/uuid_verification.html',
                              context,
                              context_instance=RequestContext(request))
