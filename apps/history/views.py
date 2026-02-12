from django.views.generic import ListView, View
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse
from apps.prompts.models import Prompt
from apps.core.mixins import OwnershipMixin
from apps.core.utils import get_owner_filter, check_ownership


class HistoryListView(OwnershipMixin, ListView):
    model = Prompt
    template_name = 'partials/history_list.html'
    context_object_name = 'prompts'
    paginate_by = 10

    def get_queryset(self):
        return self.get_owner_queryset()

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class HistorySearchView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')

        if request.user.is_authenticated:
            filters = {'user': request.user}
        else:
            filters = {'session_key': request.session.session_key}
        qs = Prompt.objects.filter(**filters)

        if query:
            qs = qs.filter(text__icontains=query)

        qs = qs.order_by('-created_at')

        return render(request, 'partials/history_list.html', {'prompts': qs})


class HistoryRerunView(View):
    def post(self, request, id):
        prompt = get_object_or_404(Prompt, id=id)
        if not check_ownership(request, prompt):
            return HttpResponseForbidden()

        return JsonResponse({'text': prompt.text})


class HistoryDeleteView(View):
    def delete(self, request, id):
        prompt = get_object_or_404(Prompt, id=id)
        if not check_ownership(request, prompt):
            return HttpResponseForbidden()

        prompt.delete()
        return JsonResponse({'status': 'deleted'})


class HistoryClearView(View):
    def post(self, request):
        Prompt.objects.filter(**get_owner_filter(request)).delete()
        return render(request, 'partials/history_list.html', {'prompts': []})
