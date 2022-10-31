from django import template
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django import template
from django.templatetags import static

from accounts.models import Device, User

register = template.Library()

class FullStaticNode(static.StaticNode):

    def url(self, context):
        request = context['request']
        return request.build_absolute_uri(super().url(context))

@register.tag('fullstatic')
def do_static(parser, token):
    return FullStaticNode.handle_token(parser, token)

@register.simple_tag(takes_context=True)
def get_template_name(context, *args):
    if context['user'].is_tenant:
        # list of it's related visitor/staff registration
        model = 'tenant'
        app = 'self_registration'
        # related = 'visitor'
        template_name = "{}/{}/partials/{}_list_partial.html".format(app, model, model)
        return template_name
    if context['user'].is_administrator:
        # list of all visitor/staff registration
        model = context['model']
        lower_name = model.__name__.lower()
        if lower_name == 'visitor' or lower_name == 'staff':
            model = 'admin'
            app = 'accounts'
            # related = 'visitor'
            template_name = "{}/{}/partials/{}_list_partial.html".format(app, model, model)
            return template_name
        
    # Case where generic model
    model = context['model']
    app = model._meta.app_label
    lower_name = model.__name__.lower()
    template_name = "{}/{}/partials/{}_list_partial.html".format(app, lower_name, lower_name)
    return template_name
    

@register.simple_tag(takes_context=True)
def get_url(context, action, obj=None):
    # print(context)
    if context['user'].is_tenant:
        model = 'tenant'
        lower_name = 'tenant'
    else:
        model = context['model']
        app = model._meta.app_label
        lower_name = model.__name__.lower()
    if not obj:
        # print('not obj -> %s', lower_name)
        # url_string = '{}:{}-{}'.format(app, lower_name, action)
        if context['user'].is_tenant:
            url_string = 'tenants:visitor-{}'.format(lower_name, action)
        elif context['user'].is_superuser:
            url_string = 'superusers:{}'.format(lower_name, action)
        else:
            url_string = 'administrators:{}-{}'.format(lower_name, action)
        url = reverse_lazy(url_string)
    else:
        # print('before obj -> %s', lower_name)
        lower_name = obj.__class__.__name__.lower()
        # print('after obj -> %s', lower_name)
        # url_string = '{}:{}-{}'.format(app, lower_name, action)
        if context['user'].is_tenant:
            url_string = 'tenants:tenant-{}-{}'.format(lower_name, action)
        elif context['user'].is_superuser:
            url_string = 'superusers:{}-{}'.format(lower_name, action)
        else:
            url_string = 'administrators:{}-{}'.format(lower_name, action)
        if(hasattr(obj, 'uuid')):
            url = reverse_lazy(url_string, kwargs={'uuid': obj.uuid})
        elif(hasattr(obj, 'slug')):
            url = reverse_lazy(url_string, kwargs={'slug': obj.slug})
        else:
            url = reverse_lazy(url_string, kwargs={'pk': obj.pk})
    return url