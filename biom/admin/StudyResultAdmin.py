# admin.py
from django.contrib import admin
from django.utils.html import format_html, format_html_join


class StudyResultAdmin(admin.ModelAdmin):
    list_display = ('study', 'status', 'createdBy', 'createdAt', 'reference', 'results_preview')
    search_fields = ('reference',)
    list_filter = ('status',)
    readonly_fields = ('createdAt', 'updatedAt', 'results_display')
    fieldsets = (
        (None, {
            'fields': ('study', 'status', 'reference', 'createdBy', 'results_display'),
        }),
        ('Timestamps', {
            'fields': ('createdAt', 'updatedAt'),
            'classes': ('collapse',),
        }),
    )

    def results_preview(self, obj):
        """Compact results inline in the list view."""
        if not obj.results:
            return '-'
        return ', '.join(
            str(getattr(r, 'value', '-'))
            for r in obj.results
        )
    results_preview.short_description = 'Results'

    def results_display(self, obj):
        """Show results as a bordered table with Variable and Value columns, with StudyVariable links."""
        if not obj.results:
            return '-'
        rows = []
        for r in obj.results:
            var_id = getattr(r, 'variable', None)
            var_name = getattr(r, 'variable_name', lambda: var_id)()
            # Link to StudyVariable change page if possible
            if var_id:
                url = f'/admin/biom/studyvariable/{var_id}/change/'
                var_html = format_html('<a href="{}" target="_blank">{}</a>', url, var_name)
            else:
                var_html = var_name
            value = getattr(r, 'value', '-')
            values = getattr(r, 'values', None)
            if values:
                value = f"{value} [{', '.join(values)}]"
            rows.append(format_html(
                "<tr>"
                "<td style='padding:6px 16px; border:1px solid #888;'>{}</td>"
                "<td style='padding:6px 16px; border:1px solid #888;'>{}</td>"
                "</tr>",
                var_html, value,
            ))
        return format_html(
            "<table style='border-collapse:collapse; border:1px solid #888; border-radius:6px;'>"
            "<thead>"
            "<tr>"
            "<th style='padding:6px 16px; border:1px solid #888; background:#484848;'>Variable</th>"
            "<th style='padding:6px 16px; border:1px solid #888; background:#484848;'>Value</th>"
            "</tr>"
            "</thead>"
            "<tbody>{}</tbody>"
            "</table>",
            format_html_join('', '{}', ((row,) for row in rows)),
        )
    results_display.short_description = 'Results'
