from rest_framework.filters import OrderingFilter


class CustomOrderingFilter(OrderingFilter):
    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        if not ordering:
            return ['id']
        return ordering
