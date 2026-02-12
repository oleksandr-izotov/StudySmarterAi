from django.db.models import QuerySet, Model
from typing import Optional, Any
from apps.core.utils import get_owner_filter, check_ownership


class HTMXOnlyMixin:
    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        if not request.htmx:
             pass
        return super().dispatch(request, *args, **kwargs)


class OwnershipMixin:
    def get_owner_queryset(self, model: Optional[Any] = None) -> QuerySet:
        qs_model = model or self.model
        filters = get_owner_filter(self.request)
        qs = qs_model.objects.filter(**filters).order_by('-created_at')
        if not self.request.user.is_authenticated:
            qs = qs[:10]
        return qs

    def check_object_ownership(self, obj: Model) -> bool:
        return check_ownership(self.request, obj)
