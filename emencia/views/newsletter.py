"""Views for emencia Newsletter"""
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext, Template, Context
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response

from django.contrib.sites.models import Site
from django.template.loader import render_to_string
# from django.template.loader import get_template
# from django.http import HttpResponseForbidden

from emencia.models import Newsletter
from emencia.models import ContactMailingStatus
# from emencia.utils import render_string
# from emencia.utils.newsletter import body_insertion
from emencia.utils.newsletter import track_links
from emencia.utils.tokens import untokenize
from emencia.settings import TRACKING_LINKS
from emencia.settings import INCLUDE_UNSUBSCRIPTION


def render_newsletter(request, slug, context):
    """Return a newsletter in HTML format"""
    newsletter = get_object_or_404(Newsletter, slug=slug)
    context = Context(context)
    context.update({
        'newsletter': newsletter,
        'title': newsletter.title,
        'domain': Site.objects.get_current().domain,
    })

    message_content = newsletter.content
    message_template = Template(message_content)

    # Render only the message provided by the user with the WYSIWYG editor
    message = message_template.render(context)
    context.update({'message': message})

    if INCLUDE_UNSUBSCRIPTION:
        unsubscription = render_to_string('newsletter/newsletter_link_unsubscribe.html', context)
        context.update({'unsubscription': unsubscription})

    if TRACKING_LINKS:
        message = track_links(message, context)

    return render_to_response("newsletter/%s" % newsletter.template, context, context_instance=RequestContext(request))

#    content = body_insertion(content, unsubscription, end=True)

#    return render_to_response('newsletter/newsletter_detail.html',
#                              {'content': content,
#                               'title': title,
#                               'object': newsletter},
#                              context_instance=RequestContext(request))


@staff_member_required
def view_newsletter_preview(request, slug):
    """View of the newsletter preview"""
    context = {'contact': request.user}
    return render_newsletter(request, slug, context)

def view_newsletter_public(request, slug):
    newsletter = Newsletter.objects.get(slug=slug)
    
    if newsletter.public: return render_newsletter(request, slug, {})

    return render_to_response('newsletter/newsletter_forbidden.html')

def view_newsletter_contact(request, slug, uidb36, token):
    """Visualization of a newsletter by an user"""
    newsletter = get_object_or_404(Newsletter, slug=slug)
    contact = untokenize(uidb36, token)
    ContactMailingStatus.objects.create(newsletter=newsletter,
                                        contact=contact,
                                        status=ContactMailingStatus.OPENED_ON_SITE)
    context = {'contact': contact,
               'uidb36': uidb36, 'token': token}

    return render_newsletter(request, slug, context)
