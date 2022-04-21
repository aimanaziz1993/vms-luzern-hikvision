from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import ProtectedError
from django.template.loader import render_to_string

class ModelMixin:
    """
    Add app and model to context
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model'] = self.model
        context['model_name'] = self.model.__name__.lower()
        context['app_name'] = self.model._meta.app_label
        context['page_title'] = self.model.__name__.capitalize()
        # print(context)
        return context

class ObjectMixin:
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()
        if request.is_ajax():
            html_form = render_to_string(
                self.ajax_partial, context, request)
            return JsonResponse({'html_form': html_form})
        return super().get(request, *args, **kwargs)

class BaseViewMixin(ModelMixin):
    pass

class AjaxCreateMixin:
    def get(self, request, *args, **kwargs):
        self.object = None
        context = self.get_context_data()
        if request.is_ajax():
            html_form = render_to_string(
                self.ajax_partial, context, request)
            return JsonResponse({'html_form': html_form})
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        data = dict()
        context = self.get_context_data()
        if form.is_valid():
            if form.instance.pk:
                data['form_is_valid'] = True
            else:
                data['form_is_valid'] = False
                data['html_form'] = render_to_string(
                    self.ajax_partial, context, request=self.request)
        if self.request.is_ajax():
            return JsonResponse(data)
        return super().form_valid(form)

    def form_invalid(self, form, **kwargs):
        data = dict()
        for field in form.errors:
            form[field].field.widget.attrs['class'] += ' is-invalid'
        context = self.get_context_data(form=form)
        data['html_form'] = render_to_string(
            self.ajax_partial, context, request=self.request)
        if self.request.is_ajax():
            return JsonResponse(data)

        messages.error(
            self.request, 'error ocured for {}'.format(
                self.model.__name__))
        return self.render_to_response(self.get_context_data(form=form))

class AjaxUpdateMixin(ObjectMixin):
    
    def form_valid(self, form):
        data = dict()
        context = self.get_context_data()
        if form.is_valid():
            if form.instance.pk:
                data['form_is_valid'] = True
            else:
                data['form_is_valid'] = False
            data['html_form'] = render_to_string(
                self.ajax_partial, context, request=self.request)
        if self.request.is_ajax():
            return JsonResponse(data)
        return super().form_valid(form)

    def form_invalid(self, form, **kwargs):
        data = dict()
        for field in form.errors:
            form[field].field.widget.attrs['class'] += ' is-invalid'
        context = self.get_context_data(form=form)
        data['html_form'] = render_to_string(
            self.ajax_partial, context, request=self.request)
        if self.request.is_ajax():
            return JsonResponse(data)

        messages.error(
            self.request, 'error ocured for {}'.format(
                self.model.__name__))
        return self.render_to_response(self.get_context_data(form=form))

class AjaxDetailMixin(ObjectMixin):
    pass

class AjaxDeleteMixin(ObjectMixin):
    
    def post(self, *args, **kwargs):
        try:
            if self.request.is_ajax():
                self.object = self.get_object()
                self.object.delete()
                # self.delete()
                data = dict()
                data['form_is_valid'] = True
                messages.success(self.request, "Object Deleted Successfully")
                return JsonResponse(data)
            else:
                return self.delete(*args, **kwargs)
        except ProtectedError as e:
            protected_details = ", ".join([str(obj) for obj in e.protected_objects])
            messages.error(self.request, "{}".format(e))
            return JsonResponse(e)
        except Exception as exc:
            messages.error(self.request, exc)
            return JsonResponse(exc)

class PassRequestToFormViewMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs