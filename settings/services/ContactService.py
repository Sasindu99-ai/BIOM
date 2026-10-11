from django.utils import timezone

from vvecon.zorion.core import Service

from ..models import ContactMessage

__all__ = ['ContactService']


class ContactService(Service):
    model = ContactMessage

    def getAll(self):
        return self.model.objects.all().order_by('-created_at')

    def getUnread(self):
        return self.model.objects.filter(is_read=False).order_by('-created_at')

    def getById(self, pk: int) -> ContactMessage | None:
        try:
            return self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            return None

    def markAsRead(self, pk: int, is_read: bool = True):
        msg = self.getById(pk)
        if msg:
            msg.is_read = is_read
            msg.save()
        return msg

    def markAsReplied(self, pk: int):
        msg = self.getById(pk)
        if msg:
            msg.is_read = True
            msg.replied_at = timezone.now()
            msg.save()
        return msg

    def createMessage(self, name: str, email: str, subject: str, message: str) -> ContactMessage:
        return self.model.objects.create(
            name=name.strip(),
            email=email.strip().lower(),
            subject=subject.strip(),
            message=message.strip(),
        )
