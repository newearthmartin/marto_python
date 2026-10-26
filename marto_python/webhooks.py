from django.contrib.admin import ModelAdmin
from django.db import models


class WebhookMessageBase(models.Model):
    """
    Raw record of every request that reaches a webhook endpoint, written before anything is done
    with it and updated as the request progresses, so an event that failed verification, matched
    nothing or raised while processing can still be read or replayed by hand.
    A subclass adds what its sender's events carry, and extends Admin.
    """
    received_on = models.DateTimeField(auto_now_add=True, db_index=True)
    event_type = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    body = models.TextField()
    verified = models.BooleanField(blank=True, null=True)  # None until the signature is checked
    processed = models.BooleanField(default=False, db_index=True)
    error = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f'{type(self).__name__}-{self.pk}-{self.event_type}'

    def finish(self, **fields):
        """Record how far the request got, saving only the fields given."""
        for name, value in fields.items():
            setattr(self, name, value)
        self.save(update_fields=list(fields))

    class Admin(ModelAdmin):
        list_display = ['pk', 'received_on', 'event_type', 'verified', 'processed', 'error']
        list_filter = ['event_type', 'verified', 'processed', 'received_on']
        search_fields = ['event_type', 'body']
        readonly_fields = ['received_on']

        @classmethod
        def list_display_with(cls, *columns, at=1):
            """The shared columns with the subclass's own inserted - right after pk by default."""
            base = list(cls.list_display)
            return base[:at] + list(columns) + base[at:]
