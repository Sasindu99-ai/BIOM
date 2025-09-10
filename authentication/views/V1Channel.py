import uuid

from drf_spectacular.utils import extend_schema
from rest_framework.status import HTTP_201_CREATED

from vvecon.zorion.auth import Authorized
from vvecon.zorion.logger import Logger
from vvecon.zorion.serializers import Return
from vvecon.zorion.views import API, DeleteMapping, GetMapping, Mapping, PostMapping, PutMapping

from ..payload.requests import ChannelRequest, FilterChannelRequest
from ..payload.responses import ChannelResponse
from ..services import ChannelService

__all__ = ['V1Channel']


@Mapping('api/v1/auth/channel')
class V1Channel(API):
    channelService: ChannelService = ChannelService()

    @extend_schema(
        summary='Create Channel',
        description='Create a new Channel',
        tags=['Channel'],
        request=ChannelRequest,
        responses={201: ChannelResponse().response()},
    )
    @PostMapping('/create')
    @Authorized(authorized=True, permissions=['authentication.add_channel'])
    def createChannel(self, request, data: ChannelRequest):
        Logger.info(f'Validating Channel: {data.initial_data}')
        if data.is_valid(raise_exception=True):
            Logger.info(f'Creating Channel: {data.validated_data}')
            channel = self.channelService.createChannel(request.user, data.validated_data)
            Logger.info(f'Channel created: {channel}')
            return ChannelResponse(data=channel).json(status=HTTP_201_CREATED)

    @extend_schema(
        summary='Filter Channels',
        description='Filter Channels',
        tags=['Channel'],
        request=FilterChannelRequest,
        responses={200: ChannelResponse().response()},
    )
    @PostMapping('/filter')
    @Authorized(authorized=True, permissions=['authentication.view_channel'])
    def filterChannels(self, request, data: FilterChannelRequest):
        Logger.info(f'Validating Channel filter: {data.initial_data}')
        if data.is_valid(raise_exception=True):
            Logger.info(f'Filtering Channels: {data.validated_data}')
            channels = self.channelService.match(data)
            Logger.info(f'{len(channels)} Channels found')
            return ChannelResponse(data=channels, many=True).json()

    @extend_schema(
        summary='Get User Channels',
        description='Get Channels for the current user',
        tags=['Channel'],
        responses={200: ChannelResponse().response()},
    )
    @GetMapping('/user')
    @Authorized(authorized=True, permissions=['authentication.view_channel'])
    def getUserChannels(self, request):
        Logger.info(f'Getting Channels for user: {request.user.id}')
        channels = self.channelService.getByUser(request.user.id)
        Logger.info(f'{len(channels)} Channels found')
        return ChannelResponse(data=channels, many=True).json()

    @extend_schema(
        summary='Update Channel',
        description='Update an existing Channel',
        tags=['Channel'],
        request=ChannelRequest,
        responses={200: ChannelResponse().response()},
    )
    @PutMapping('/<uuid:channelId>')
    @Authorized(authorized=True, permissions=['authentication.change_channel'])
    def updateChannel(self, request, channelId: uuid.UUID, data: ChannelRequest):
        Logger.info(f'Validating Channel: {data.initial_data}')
        if data.is_valid(raise_exception=True):
            Logger.info(f'Updating Channel: {data.validated_data}')
            channel = self.channelService.update(
                self.channelService.getByPublicId(channelId), data.validated_data,
            )
            Logger.info(f'Channel updated: {channel}')
            return ChannelResponse(data=channel).json()

    @extend_schema(
        summary='Delete Channel',
        description='Delete a Channel',
        tags=['Channel'],
    )
    @DeleteMapping('/<uuid:channelId>')
    @Authorized(authorized=True, permissions=['authentication.delete_channel'])
    def deleteChannel(self, request, channelId: uuid.UUID):
        Logger.info(f'Deleting Channel: {channelId}')
        self.channelService.delete(self.channelService.getByPublicId(channelId).pk)
        Logger.info(f'Channel deleted: {channelId}')
        return Return.noContent()
