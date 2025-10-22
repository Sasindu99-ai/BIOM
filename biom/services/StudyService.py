from biom.models import Study
from vvecon.zorion.core import Service

__all__ = ['StudyService']


class StudyService(Service):
	model = Study
	searchableFields = ('name', 'description', 'category')
	filterableFields = ('status', 'category', 'createdBy')
	
	def getPaginatedStudies(self, page=1, limit=10, search=None, filters=None):
		"""
		Get paginated studies with optional search and filters
		"""
		queryset = self.model.objects.all()
		
		# Apply search
		if search:
			from django.db.models import Q
			query = Q()
			for field in self.searchableFields:
				query |= Q(**{f'{field}__icontains': search})
			queryset = queryset.filter(query)
		
		# Apply filters
		if filters:
			for field, value in filters.items():
				if field in self.filterableFields and value:
					queryset = queryset.filter(**{field: value})
		
		# Get total count before pagination
		total_count = queryset.count()
		
		# Apply pagination
		start = (page - 1) * limit
		end = start + limit
		studies = queryset[start:end]
		
		# Calculate pagination info
		total_pages = (total_count + limit - 1) // limit
		has_next = page < total_pages
		has_previous = page > 1
		
		return {
			'studies': list(studies),
			'pagination': {
				'current_page': page,
				'limit': limit,
				'total_count': total_count,
				'total_pages': total_pages,
				'has_next': has_next,
				'has_previous': has_previous,
			}
		}
