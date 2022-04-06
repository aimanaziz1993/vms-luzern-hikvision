from django.views.generic.list import ListView

from .mixins import BaseViewMixin

class CoreListView(BaseViewMixin, ListView):
    pass
