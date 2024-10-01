from rest_framework.mixins import DestroyModelMixin


class SoftDeleteMixin(DestroyModelMixin):

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

