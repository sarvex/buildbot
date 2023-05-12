
from buildbot.secrets.providers.base import SecretProviderBase


class FakeSecretStorage(SecretProviderBase):

    name = "SecretsInFake"

    def reconfigService(self, secretdict=None):
        if secretdict is None:
            secretdict = {}
        self.allsecrets = secretdict

    def get(self, key):
        return self.allsecrets[key] if key in self.allsecrets else None
