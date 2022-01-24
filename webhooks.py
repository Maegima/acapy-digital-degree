import json
import asyncio
import base64
from aiohttp import (
    web,
    ClientRequest
)

CRED_FORMAT_INDY = "indy"
CRED_FORMAT_JSON_LD = "json-ld"
DID_METHOD_SOV = "sov"
DID_METHOD_KEY = "key"
SIG_TYPE_ED255 = "ed25519"
KEY_TYPE_BLS = "bls12381g2"
SIG_TYPE_BLS = "BbsBlsSignature2020"
SIG_TYPE_ED255 = "Ed25519Signature2018"
ACA_PY = "aca-py"

class WebHookServer():
    def __init__(
        self,
        webhook_host: str,
        webhook_port: int,
        webhook_handler,
        connection_handler 
    ):
        self.webhook_host = webhook_host
        self.webhook_port = webhook_port
        self.webhook_handler = webhook_handler
        self.connection_handler = connection_handler
        self.webhook_site = None

    async def listen_webhooks(self):
        self.webhook_url = f"http://{self.webhook_host}:{str(self.webhook_port)}/webhooks"
        app = web.Application()
        app.add_routes(
            [
                web.post("/webhooks/topic/{topic}/", self._receive_webhook),
                # route for fetching proof request for connectionless requests
                #web.get(
                #    '/webhooks/pres_req/{pres_req_id}/',
                #    self._send_connectionless_proof_req,
                #),
                web.get(
                    "/webhooks/test/",
                    self._test,
                ),
                web.get("/connections/{conn_id}/", self._connection_handler)
            ]
        )
        runner = web.AppRunner(app)
        await runner.setup()
        self.webhook_site = web.TCPSite(runner, "0.0.0.0", self.webhook_port)
        await self.webhook_site.start()
        print("Started webhook listener on port:",  self.webhook_port)
        while(True):
            await asyncio.sleep(3600)

    async def _test(self, request: ClientRequest):
        return web.Response(body="test", status=200) 

    async def _receive_webhook(self, request: ClientRequest):
        topic = request.match_info["topic"].replace("-", "_")
        payload = await request.json()
        await self.webhook_handler(topic, payload, request.headers)
        return web.Response(status=200)

    async def _connection_handler(self, request: ClientRequest):
        conn_id = request.match_info["conn_id"]
        return await self.connection_handler(conn_id)
    '''
    async def _send_connectionless_proof_req(self, request: ClientRequest):
        pres_req_id = request.match_info["pres_req_id"]
        url = "/present-proof/records/" + pres_req_id
        proof_exch = await self.admin_get(url)
        if not proof_exch:
            return web.Response(status=404)
        proof_reg_txn = proof_exch["presentation_request_dict"]
        proof_reg_txn["~service"] = await self.service_decorator()
        objJsonStr = json.dumps(proof_reg_txn)
        objJsonB64 = base64.b64encode(objJsonStr.encode("ascii"))
        service_url = self.webhook_url
        redirect_url = service_url + "/?m=" + objJsonB64.decode("ascii")
        print(f"Redirecting to: {redirect_url}")
        raise web.HTTPFound(redirect_url)
    '''
    def generate_credential_offer(self, connection_id, cred_type, issuer, subject):
        if cred_type == CRED_FORMAT_JSON_LD:
            offer_request = {
                "connection_id": connection_id,
                "filter": {
                    "ld_proof": {
                        "credential": {
                            "@context": [
                                "https://www.w3.org/2018/credentials/v1",
                                "https://w3id.org/citizenship/v1",
                                "https://w3id.org/security/bbs/v1",
                            ],
                            "type": [
                                "VerifiableCredential",
                                "PermanentResident",
                            ],
                            "id": "https://credential.example.com/residents/1234567890",
                            "issuer": issuer,
                            "issuanceDate": "2020-01-01T12:00:00Z",
                            "credentialSubject": {
                                "type": ["PermanentResident"],
                                "givenName": "ALICE",
                                "familyName": "SMITH",
                                "gender": "Female",
                                "birthCountry": "Bahamas",
                                "birthDate": "1958-07-17",
                            },
                        },
                        "options": {"proofType": SIG_TYPE_ED255},
                    }
                },
            }
            return offer_request

        else:
            raise Exception(f"Error invalid credential type: {cred_type}")