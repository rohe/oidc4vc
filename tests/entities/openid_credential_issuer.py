import os
from typing import List
from typing import Optional

from fedservice.defaults import LEAF_ENDPOINTS
from fedservice.utils import make_federation_combo
from idpyoidc.client.defaults import DEFAULT_KEY_DEFS
from idpyoidc.server.authz import AuthzHandling
from idpyoidc.server.client_authn import ClientSecretBasic
from idpyoidc.server.client_authn import ClientSecretPost
from idpyoidc.server.oauth2.add_on.dpop import DPoPClientAuth
from idpyoidc.server.user_info import UserInfo

from openid4v import ServerEntity
from openid4v.openid_credential_issuer import OpenidCredentialIssuer
from openid4v.openid_credential_issuer.client_authn import ClientAuthenticationAttestation
from tests import CRYPT_CONFIG
from tests import SESSION_PARAMS

BASEDIR = os.path.abspath(os.path.dirname(__file__))


def full_path(local_file):
    return os.path.join(BASEDIR, local_file)


OAUTH_AUTHORIZATION_SERVER_CONFIG = {
    "client_authn_methods": {
        "client_attestation":
            "openid4v.openid_credential_issuer.client_authn.ClientAuthenticationAttestation"
    },
    "httpc_params": {"verify": False, "timeout": 1},
    "preference": {
        "grant_types_supported": [
            "authorization_code",
            "implicit",
            "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "refresh_token",
        ],
    },
    "server_type": "oauth2",
    "token_handler_args": {
        "jwks_def": {
            "private_path": "private/token_jwks.json",
            "read_only": False,
            "key_defs": [
                {"type": "oct", "bytes": "24", "use": ["enc"],
                 "kid": "code"}],
        },
        "code": {"lifetime": 600, "kwargs": {"crypt_conf": CRYPT_CONFIG}},
        "token": {
            "class": "idpyoidc.server.token.jwt_token.JWTToken",
            "kwargs": {
                "lifetime": 3600,
                "add_claims_by_scope": True,
            },
        },
        "refresh": {
            "class": "idpyoidc.server.token.jwt_token.JWTToken",
            "kwargs": {
                "lifetime": 3600,
            },
        },
        "id_token": {
            "class": "idpyoidc.server.token.id_token.IDToken",
            "kwargs": {
                "base_claims": {
                    "email": {"essential": True},
                    "email_verified": {"essential": True},
                }
            },
        },
    },
    "keys": {"key_defs": DEFAULT_KEY_DEFS, "uri_path": "static/oa_jwks.json"},
    "endpoint": {
        "token": {
            "path": "token",
            "class": "openid4v.openid_credential_issuer.access_token.Token",
            "kwargs": {
                "client_authn_method": ["client_attestation"]
            }
        },
        "authorization": {
            "path": "authorization",
            "class":
                "openid4v.openid_credential_issuer.authorization.Authorization",
            "kwargs": {
                "response_types_supported": ["code"],
                "response_modes_supported": ["query", "form_post"],
                "request_parameter_supported": True,
                "request_uri_parameter_supported": True,
                "client_authn_method": ["client_attestation"]
            },
        },
    },
    "add_ons": {
        "pkce": {
            "function": "idpyoidc.server.oauth2.add_on.pkce.add_support",
            "kwargs": {"code_challenge_length": 64,
                       "code_challenge_method": "S256"},
        },
        "dpop": {
            "function": "idpyoidc.server.oauth2.add_on.dpop.add_support",
            "kwargs": {
                'dpop_signing_alg_values_supported': ["ES256"],
                "dpop_endpoints": ["token"]
            }
        }
    },
    "template_dir": "template",
    "authentication": {
        "anon": {
            "acr": "http://www.swamid.se/policy/assurance/al1",
            "class": "idpyoidc.server.user_authn.user.NoAuthn",
            "kwargs": {"user": "diana"},
        }
    },
    "userinfo": {"class": UserInfo, "kwargs": {"db_file": full_path("users.json")}},
    "authz": {
        "class": AuthzHandling,
        "kwargs": {
            "grant_config": {
                "usage_rules": {
                    "authorization_code": {
                        "supports_minting": [
                            "access_token",
                            "refresh_token",
                            "id_token",
                        ],
                        "max_usage": 1,
                    },
                    "access_token": {},
                    "refresh_token": {
                        "supports_minting": [
                            "access_token",
                            "refresh_token",
                            "id_token",
                        ],
                    },
                },
                "expires_in": 43200,
            }
        },
    },
    "session_params": SESSION_PARAMS,
}

OPENID_CREDENTIAL_ISSUER_CONFIG = {
    "client_authn_methods": {
        "client_secret_basic": ClientSecretBasic,
        "client_secret_post": ClientSecretPost,
        "client_assertion": ClientAuthenticationAttestation,
        "dpop_client_auth": DPoPClientAuth
    },
    "keys": {"key_defs": DEFAULT_KEY_DEFS},
    "endpoint": {
        "credential": {
            "path": "credential",
            "class": "openid4v.openid_credential_issuer.credential.Credential",
            "kwargs": {
                "client_authn_method": [
                    "dpop_client_auth"
                ]
            },
        },
        "pushed_authorization": {
            "path": "pushed_authorization",
            "class":
                "idpyoidc.server.oauth2.pushed_authorization.PushedAuthorization",
            "kwargs": {
                "client_authn_method": [
                    "client_assertion",
                ]
            },
        },
    },
    "add_ons": {
        "dpop": {
            "function": "idpyoidc.server.oauth2.add_on.dpop.add_support",
            "kwargs": {
                'dpop_signing_alg_values_supported': ["ES256"],
                "dpop_endpoints": ["credential"]
            }
        }
    },
    "userinfo": {
        "class": "idpyoidc.server.user_info.UserInfo",
        "kwargs": {
            "db_file": full_path("users.json")
        }
    },
    'preference': {
        "acr_values_supported": [
            "https://www.spid.gov.it/SpidL1",
            "https://www.spid.gov.it/SpidL2",
            "https://www.spid.gov.it/SpidL3"
        ],
        "credentials_supported": [
            {
                "format": "vc+sd-jwt",
                "id": "eudiw.pid.se",
                "cryptographic_binding_methods_supported": ["jwk"],
                "cryptographic_suites_supported": ["RS256", "RS512", "ES256",
                                                   "ES512"],
                "display": [
                    {
                        "name": "Example Swedish PID Provider",
                        "locale": "en-US",
                    }
                ],
                "credential_definition": {
                    "type": ["PersonIdentificationData"],
                    "credentialSubject": {
                        "given_name": {
                            "mandatory": True,
                            "display": [
                                {
                                    "name": "Current First Name",
                                    "locale": "en-US"
                                }
                            ]
                        },
                        "family_name": {
                            "mandatory": True,
                            "display": [
                                {
                                    "name": "Current Family Name",
                                    "locale": "en-US"
                                },
                            ]
                        },
                        "birthdate": {
                            "mandatory": True,
                            "display": [
                                {
                                    "name": "Date of Birth",
                                    "locale": "en-US"
                                },
                            ]
                        },
                        "place_of_birth": {
                            "mandatory": True,
                            "display": [
                                {
                                    "name": "Place of Birth",
                                    "locale": "en-US"
                                },
                            ]
                        },
                        "unique_id": {
                            "mandatory": True,
                            "display": [
                                {
                                    "name": "Unique Identifier",
                                    "locale": "en-US"
                                },
                            ]
                        },
                        "tax_id_code": {
                            "mandatory": True,
                            "display": [
                                {
                                    "name": "Tax Id Number",
                                    "locale": "en-US"
                                },
                            ]
                        }
                    }
                }
            }
        ],
        "attribute_disclosure": {
            "": ["given_name",
                 "family_name",
                 "birthdate",
                 "place_of_birth",
                 "unique_id",
                 "tax_id_code"]
        }
    }
}


def main(entity_id: str,
         authority_hints: Optional[List[str]] = None,
         trust_anchors: Optional[dict] = None,
         preference: Optional[dict] = None,
         endpoints: Optional[list] = None,
         key_config: Optional[dict] = None,
         entity_type_config: Optional[dict] = None,
         services: Optional[list] = None
         ):
    if preference is None:
        preference = {
            "organization_name": "The PID provider",
        }
    if not endpoints:
        endpoints = LEAF_ENDPOINTS
    if not key_config:
        key_config = {"key_defs": DEFAULT_KEY_DEFS}
    if not services:
        services = {
            "metadata": {"class": "idpyoidc.client.oauth2.server_metadata.ServerMetadata"},
            "authorization": {"class": "idpyoidc.client.oauth2.authorization.Authorization"},
            "access_token": {"class": "idpyoidc.client.oauth2.access_token.AccessToken"},
            "credential": {"class": "openid4v.client.pid_eaa.Credential"},
        }

    if not entity_type_config:
        entity_type_config = {
            "oauth_authorization_server": OAUTH_AUTHORIZATION_SERVER_CONFIG,
            "openid_credential_issuer": OPENID_CREDENTIAL_ISSUER_CONFIG
        }
    else:
        if "oauth_authorization_server" not in entity_type_config:
            entity_type_config["oauth_authorization_server"] = OAUTH_AUTHORIZATION_SERVER_CONFIG
        if "openid_credential_issuer" not in entity_type_config:
            entity_type_config["openid_credential_issuer"] = OPENID_CREDENTIAL_ISSUER_CONFIG

    entity = make_federation_combo(
        entity_id,
        trust_anchors=trust_anchors,
        preference=preference,
        authority_hints=authority_hints,
        key_config=key_config,
        endpoints=endpoints,
        services=services,
        entity_type={
            "oauth_authorization_server": {
                'class': ServerEntity,
                'kwargs': {
                    'config': entity_type_config["oauth_authorization_server"]
                }
            },
            "openid_credential_issuer": {
                'class': OpenidCredentialIssuer,
                'kwargs': {
                    'config': entity_type_config["openid_credential_issuer"]
                }
            }
        }
    )

    return entity
