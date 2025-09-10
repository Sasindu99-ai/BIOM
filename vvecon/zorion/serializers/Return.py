from typing import Any

from rest_framework.response import Response
from rest_framework.status import (
	HTTP_200_OK,
	HTTP_201_CREATED,
	HTTP_202_ACCEPTED,
	HTTP_203_NON_AUTHORITATIVE_INFORMATION,
	HTTP_204_NO_CONTENT,
	HTTP_400_BAD_REQUEST,
	HTTP_403_FORBIDDEN,
	HTTP_404_NOT_FOUND,
)

__all__ = ['Return']


class Return:
	@staticmethod
	def ok(content: Any = True) -> Response:  # noqa: FBT002
		return Response(data=content, status=HTTP_200_OK)

	@staticmethod
	def created(content: Any = True) -> Response:  # noqa: FBT002
		return Response(data=content, status=HTTP_201_CREATED)

	@staticmethod
	def notFound(content: Any = False) -> Response:  # noqa: FBT002
		return Response(data=content, status=HTTP_404_NOT_FOUND)

	@staticmethod
	def badRequest(content: Any = False) -> Response:  # noqa: FBT002
		return Response(data=content, status=HTTP_400_BAD_REQUEST)

	@staticmethod
	def noContent(content: Any = False) -> Response:  # noqa: FBT002
		return Response(data=content, status=HTTP_204_NO_CONTENT)

	@staticmethod
	def accepted(content: Any = False) -> Response:  # noqa: FBT002
		return Response(data=content, status=HTTP_202_ACCEPTED)

	@staticmethod
	def nonAuthoritativeInformation(content: Any = False) -> Response:  # noqa: FBT002
		return Response(data=content, status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

	@staticmethod
	def forbidden(content: Any = False) -> Response:  # noqa: FBT002
		return Response(data=content, status=HTTP_403_FORBIDDEN)
