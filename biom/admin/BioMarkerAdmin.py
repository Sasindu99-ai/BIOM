from django.contrib import admin

__all__ = ['BioMarkerAdmin']


class BioMarkerAdmin(admin.ModelAdmin):
	list_display = ('name', 'type', 'biomType', 'status', 'uploadedBy', 'createdAt')
	search_fields = ('name', 'type', 'biomType')
	list_filter = ('type', 'biomType', 'status')
	readonly_fields = ('createdAt', 'updatedAt')
	fieldsets = (
		(None, {
			'fields': (
				'name', 'shortName', 'commonName', 'type', 'biomType', 'status', 'uploadedBy', 'imagePath',
			),
		}),
		('Properties', {
			'fields': ('uniProtKB', 'pdb', 'molecularWeight', 'molecularLength', 'aaSequence'),
			'classes': ('collapse',),
		}),
		('Timestamps', {
			'fields': ('createdAt', 'updatedAt'),
			'classes': ('collapse',),
		}),
	)
