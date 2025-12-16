from django.contrib import admin
from django.utils.html import format_html

from ..enums import BioMarkerStatus

__all__ = ['BioMarkerAdmin']


@admin.action(description='Mark selected biomarkers as Approved')
def mark_biomarkers_approved(modeladmin, request, queryset):
	queryset.update(status=BioMarkerStatus.APPROVED)


@admin.action(description='Mark selected biomarkers as Rejected')
def mark_biomarkers_rejected(modeladmin, request, queryset):
	queryset.update(status=BioMarkerStatus.REJECTED)


class BioMarkerAdmin(admin.ModelAdmin):
	list_display = (
		'name',
		'shortName',
		'commonName',
		'type',
		'biomType',
		'status',
		'uploadedBy',
		'administeredBy',
		'image_preview',
		'created_at',
	)
	search_fields = (
		'name',
		'shortName',
		'commonName',
		'type',
		'biomType',
		'uniProtKB',
		'pdb',
		'ncib',
	)
	list_filter = ('type', 'biomType', 'status')
	readonly_fields = ('created_at', 'updated_at', 'image_preview', 'deleted_at')
	autocomplete_fields = ('uploadedBy', 'administeredBy')
	actions = (mark_biomarkers_approved, mark_biomarkers_rejected)
	fieldsets = (
		(None, {
			'fields': (
				'name',
				'shortName',
				'commonName',
				'type',
				'biomType',
				'status',
				'uploadedBy',
				'administeredBy',
				'image',
				'image_preview',
			),
		}),
		('Properties', {
			'fields': ('uniProtKB', 'pdb', 'ncib', 'molecularWeight', 'molecularLength', 'aaSequence'),
			'classes': ('collapse',),
		}),
		('Timestamps', {
			'fields': ('created_at', 'updated_at', 'deleted_at'),
			'classes': ('collapse',),
		}),
	)

	@admin.display(description='Image')
	def image_preview(self, obj):
		if getattr(obj, 'image', None) and getattr(obj.image, 'url', None):
			return format_html('<img src="{}" style="max-height:60px; max-width:60px; object-fit:cover; border-radius:4px;" />', obj.image.url)
		return '-'
