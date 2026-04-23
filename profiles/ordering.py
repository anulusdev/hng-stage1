from rest_framework.filters import OrderingFilter


class SeparateParamOrderingFilter(OrderingFilter):
    """
    Custom ordering filter that accepts:
        ?sort_by=age&order=desc
    Instead of DRF's default:
        ?ordering=-age

    Extends DRF's OrderingFilter so field validation still applies —
    only fields declared in ordering_fields on the view are allowed.
    """

    def filter_queryset(self, request, queryset, view):
        sort_by = request.query_params.get('sort_by')
        order = request.query_params.get('order', 'asc')

        if not sort_by:
            return queryset

        ordering_fields = getattr(view, 'ordering_fields', [])
        if sort_by not in ordering_fields:
            return queryset

        if order == 'desc':
            return queryset.order_by(f'-{sort_by}')
        return queryset.order_by(sort_by)