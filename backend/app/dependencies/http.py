from typing import Annotated
import ssl
from ssl import SSLContext

from fastapi import Depends

from .config import ConfigDep


def get_sber_ssl_context(config: ConfigDep) -> SSLContext:
    ssl_ctx = ssl.create_default_context(cafile=config.sber_ca_cert_path)
    ssl_ctx.load_cert_chain(
        certfile=config.sber_client_cert_path,
        keyfile=config.sber_client_key_path,
    )

    return ssl_ctx


SSLSberContextDep = Annotated[SSLContext, Depends(get_sber_ssl_context)]
