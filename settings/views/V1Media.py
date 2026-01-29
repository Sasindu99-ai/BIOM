import os
import random
import string
from pathlib import Path

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR

from vvecon.zorion.app import settings
from vvecon.zorion.auth import Authorized
from vvecon.zorion.logger import Logger
from vvecon.zorion.serializers import Return
from vvecon.zorion.views import API, Mapping, PostMapping

__all__ = ['V1Media']


@Mapping('api/v1/media')
class V1Media(API):
	@extend_schema(
		tags=['Media'],
		summary='Upload file',
		description='Upload a file to the media directory',
	)
	@PostMapping('/upload')
	@Authorized(True, permissions=[])
	def uploadFile(self, request):
		Logger.info('Starting file upload')

		if 'file' not in request.FILES:
			return Return.badRequest(dict(error='No file provided', message='No file provided'))

		uploaded_file = request.FILES['file']

		# Create upload directory
		upload_dir = Path(settings.MEDIA_ROOT) / 'uploads'
		upload_dir.mkdir(parents=True, exist_ok=True)

		# Generate unique filename
		timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
		# file_ext = Path(uploaded_file.name).suffix.lower()
		file_name = f'{timestamp}_{uploaded_file.name}'
		file_path = upload_dir / file_name

		try:
			# Save file
			with Path(file_path).open('wb+') as destination:
				destination.writelines(uploaded_file.chunks())

			# Return relative path from MEDIA_ROOT
			relative_path = str(file_path.relative_to(settings.MEDIA_ROOT))
			file_url = f'/media/{relative_path}'

			Logger.info(f'File uploaded successfully: {relative_path}')

			return Return.ok(dict(
				success=True,
				file_path=relative_path,
				file_url=file_url,
				file_name=uploaded_file.name,
			))
		except Exception as e:
			Logger.error(f'Error uploading file: {e!s}')
			return Response(
				data=dict(error='Error uploading file', message=str(e)),
				status=HTTP_500_INTERNAL_SERVER_ERROR,
			)

	@extend_schema(
		tags=['Media'],
		summary='Upload file with streaming',
		description='Upload files with streaming support for progress tracking. Supports CSV/Excel for bulk imports '
		'and images for profile photos.',
	)
	@PostMapping('/upload-stream')
	@Authorized(True, permissions=[])
	def uploadStreamFile(self, request):
		Logger.info('Starting streaming file upload')

		if 'file' not in request.FILES:
			return Return.badRequest(dict(error='No file provided', message='No file provided'))

		uploaded_file = request.FILES['file']

		# Determine file type and upload directory
		file_ext = Path(uploaded_file.name).suffix.lower()

		# Allowed file types
		bulk_extensions = ['.csv', '.xlsx', '.xls']
		image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

		is_bulk_file = file_ext in bulk_extensions
		is_image_file = file_ext in image_extensions

		if not is_bulk_file and not is_image_file:
			return Return.badRequest(dict(
				error='Invalid file type',
				message=f'Only CSV, Excel, and image files are allowed. Got: {file_ext}',
				allowed_types=bulk_extensions + image_extensions,
			))

		# Set upload directory based on file type
		if is_bulk_file:
			upload_dir = Path(settings.MEDIA_ROOT) / 'uploads' / 'bulk'
		else:  # is_image_file
			upload_dir = Path(settings.MEDIA_ROOT) / 'patients' / 'profiles'

		upload_dir.mkdir(parents=True, exist_ok=True)

		timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
		random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))  # noqa: S311

		if is_image_file:
			file_name = f'profile_{timestamp}_{random_str}{file_ext}'
		else:
			file_name = f'{timestamp}_{uploaded_file.name}'

		file_path = upload_dir / file_name

		try:
			# Save file with streaming chunk
			total_size = uploaded_file.size
			bytes_written = 0
			chunk_size = 8192  # 8KB chunks

			with Path(file_path).open('wb+') as destination:
				for chunk in uploaded_file.chunks(chunk_size=chunk_size):
					destination.write(chunk)
					bytes_written += len(chunk)

			# Return relative path from MEDIA_ROOT
			relative_path = str(file_path.relative_to(settings.MEDIA_ROOT))
			file_url = f'/media/{relative_path}'

			Logger.info(f'File uploaded successfully via streaming: {relative_path}')

			return Return.ok(dict(
				success=True,
				file_path=relative_path,
				file_url=file_url,
				file_name=uploaded_file.name,
				file_size=total_size,
				file_type=file_ext,
				upload_complete=True,
				message='File uploaded successfully',
			))
		except Exception as e:
			Logger.error(f'Error uploading streaming file: {e!s}')

			if file_path.exists():
				try:
					os.remove(file_path)  # noqa: PTH107
				except Exception as e:
					Logger.error(f'Error removing partial file: {e!s}')

			return Response(
				data=dict(error='Error uploading file', message=str(e)),
				status=HTTP_500_INTERNAL_SERVER_ERROR,
			)


