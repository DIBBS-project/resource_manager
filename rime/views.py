from rest_framework import viewsets

from . import models, serializers


class CredentialViewSet(viewsets.ModelViewSet):
    queryset = models.Credential.objects.all()
    serializer_class = serializers.CredentialSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ResourceViewSet(viewsets.ModelViewSet):
    queryset = models.Resource.objects.all()
    serializer_class = serializers.ResourceSerializer

    def perform_create(self, serializer):
        serializer.save(root_owner=self.request.user)
