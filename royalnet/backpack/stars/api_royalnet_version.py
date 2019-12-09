import royalnet
from starlette.requests import Request
from starlette.responses import *
from royalnet.constellation import PageStar
from ..tables import available_tables


class ApiRoyalnetVersionStar(PageStar):
    path = "/api/royalnet/version"

    tables = set(available_tables)

    async def page(self, request: Request) -> JSONResponse:
        return JSONResponse({
            "version": {
                "semantic": royalnet.__version__,
            }
        })