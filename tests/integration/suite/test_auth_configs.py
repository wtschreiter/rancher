import pytest
from rancher import ApiError
from kubernetes.client import CoreV1Api
from .conftest import wait_for


def test_auth_configs(admin_mc):
    client = admin_mc.client

    with pytest.raises(AttributeError) as e:
        client.list_github_config()

    with pytest.raises(AttributeError) as e:
        client.create_auth_config({})

    configs = client.list_auth_config()

    assert configs.pagination.total == 11

    gh = None
    local = None
    ad = None
    azure = None
    openldap = None
    freeIpa = None
    ping = None
    adfs = None
    keycloak = None
    okta = None
    googleoauth = None

    for c in configs:
        if c.type == "githubConfig":
            gh = c
        elif c.type == "localConfig":
            local = c
        elif c.type == "activeDirectoryConfig":
            ad = c
        elif c.type == "azureADConfig":
            azure = c
        elif c.type == "openLdapConfig":
            openldap = c
        elif c.type == "freeIpaConfig":
            freeIpa = c
        elif c.type == "pingConfig":
            ping = c
        elif c.type == "adfsConfig":
            adfs = c
        elif c.type == "keyCloakConfig":
            keycloak = c
        elif c.type == "oktaConfig":
            okta = c
        elif c.type == "googleOauthConfig":
            googleoauth = c

    for x in [gh, local, ad, azure, openldap,
              freeIpa, ping, adfs, keycloak, okta, googleoauth]:
        assert x is not None
        config = client.by_id_auth_config(x.id)
        with pytest.raises(ApiError) as e:
            client.delete(config)
        assert e.value.error.status == 405

    assert gh.actions.testAndApply
    assert gh.actions.configureTest

    assert ad.actions.testAndApply

    assert azure.actions.testAndApply
    assert azure.actions.configureTest

    assert openldap.actions.testAndApply

    assert freeIpa.actions.testAndApply

    assert ping.actions.testAndEnable

    assert adfs.actions.testAndEnable

    assert keycloak.actions.testAndEnable

    assert okta.actions.testAndEnable

    assert googleoauth.actions.configureTest
    assert googleoauth.actions.testAndApply


def test_auth_config_secrets(admin_mc):
    client = admin_mc.client
    key_data = {
        "spKey": "-----BEGIN PRIVATE KEY-----",
    }
    ping_config = client.by_id_auth_config("ping")
    client.update(ping_config, key_data)
    k8sclient = CoreV1Api(admin_mc.k8s_client)
    # wait for ping secret to get created
    wait_for(lambda: key_secret_creation(k8sclient), timeout=60,
             fail_handler=lambda: "failed to create secret for ping spKey")

    secrets = k8sclient.list_namespaced_secret("cattle-global-data")
    auth_configs_not_setup = ["adfsconfig-spkey", "oktaconfig-spkey",
                              "keycloakconfig-spkey"]
    for s in secrets.items:
        assert s.metadata.name not in auth_configs_not_setup


def key_secret_creation(k8sclient):
    secrets = k8sclient.list_namespaced_secret("cattle-global-data")
    for s in secrets.items:
        if s.metadata.name == "pingconfig-spkey":
            return True
    return False
