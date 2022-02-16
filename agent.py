import random
import json
import os
import asyncio
import subprocess
import functools
import base64
from aiohttp.web_response import Response
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit import print_formatted_text
from timeit import default_timer
from prompt_toolkit.formatted_text import FormattedText, PygmentsTokens
from aiohttp import (
    web,
    ClientSession,
    ClientRequest,
    ClientResponse,
    ClientError,
    ClientTimeout,
)
from utils import *
from webhooks import WebHookServer

CRED_FORMAT_INDY = "indy"
CRED_FORMAT_JSON_LD = "json-ld"
DID_METHOD_SOV = "sov"
DID_METHOD_KEY = "key"
KEY_TYPE_ED255 = "ed25519"
KEY_TYPE_BLS = "bls12381g2"
SIG_TYPE_BLS = "BbsBlsSignature2020"
ACA_PY = "aca-py"
START_TIMEOUT = float(os.getenv("START_TIMEOUT", 30.0))

class AriesAgent:
    def __init__(
        self,
        genesis_url: str,
        admin: tuple,
        endpoint: str,
        inbound_transport: tuple,
        outbound_transport: tuple,
        webhook_url: str = None,
        seed: str = None,
        admin_insecure_mode: bool = False,   
        #genesis_data: str = None,
        label: str = None,
        #color: str = None,
        #prefix: str = None,
        #tails_server_base_url: str = None,
        #timing: bool = False,
        #timing_log: str = None,
        #postgres: bool = None,
        #revocation: bool = False,
        multitenant: bool = False,
        #mediation: bool = False,
        #aip: int = 20,
        #arg_file: str = None,
        endorser_protocol_role: str = None,
        #extra_args=None,
        #**params,
    ):
        #self.genesis_data = genesis_data
        self.genesis_url = genesis_url
        #self.label = label or ident
        self.label = label
        #self.color = color
        #self.prefix = prefix
        #self.timing = timing
        #self.timing_log = timing_log
        #self.postgres = postgres
        #self.tails_server_base_url = tails_server_base_url
        self.endorser_protocol_role = endorser_protocol_role
        self.endorser_did = None  # set this later
        self.endorser_invite = None  # set this later
        #self.extra_args = extra_args
        self.trace_enabled = False
        self.trace_target = False
        self.trace_tag = False
        self.multitenant = multitenant
        self.external_webhook_target = None
        #self.mediation = mediation
        #self.mediator_connection_id = None
        #self.mediator_request_id = None
        #self.aip = aip
        #self.arg_file = arg_file
        self.admin = admin
        self.endpoint = endpoint
        self.inbound_transport = inbound_transport
        self.outbound_transport = outbound_transport
        self.admin_insecure_mode = admin_insecure_mode
        #self.webhook_port = None
        self.webhook_url = webhook_url
        #self.webhook_site = None
        
        #self.params = params
        #self.proc = None

        if self.endorser_protocol_role and not seed:
            seed = "random"
        rand_name = str(random.randint(100_000, 999_999))
        self.seed = (
            ("my_seed_000000000000000000000000" + rand_name)[-32:]
            if seed == "random"
            else seed
        )
        #self.storage_type = params.get("storage_type")
        #self.wallet_type = "indy"
        #self.wallet_name = (
        #    "test" + rand_name
        #)
        #self.wallet_key = "test" + rand_name
        self.did = None
        #self.wallet_stats = []

        # for multitenancy, storage_type and wallet_type are the same for all wallets
        #if self.multitenant:
        #    self.agency_ident = self.ident
        #    self.agency_wallet_name = self.wallet_name
        #    self.agency_wallet_seed = self.seed
        #    self.agency_wallet_did = self.did
        #    self.agency_wallet_key = self.wallet_key

    '''
    async def get_wallets(self):
        """Get registered wallets of agent (this is an agency call)."""
        wallets = await self.admin_get("/multitenancy/wallets")
        return wallets

    def get_new_webhook_port(self):
        """Get new webhook port for registering additional sub-wallets"""
        self.webhook_port = self.webhook_port + 1
        return self.webhook_port

    async def get_public_did(self):
        """Get public did of wallet (called for a sub-wallet)."""
        did = await self.admin_get("/wallet/did/public")
        return did
    '''
    def get_agent_parameters(self):
        param_list = [ "--" + param.replace("_", "-") if type(value) == bool else ("--" + param.replace("_", "-"), value) 
        for param, value in self.__dict__.items() if value ]
        return param_list

    async def start_process(self, aca_py_path: str = None, wait: bool = True):
        my_env = os.environ.copy()
        aca_py = ACA_PY if aca_py_path is None else aca_py_path

        agent_args = list(flatten(([aca_py, "start"], self.get_agent_parameters())))
        #self.log(agent_args)

        # start agent sub-process
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(None, self._process, agent_args, my_env, loop)
        proc = await asyncio.wait_for(future, 20)
        if wait:
            await asyncio.sleep(1.0)
            await self.detect_process()

    def _process(self, args, env, loop):
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            encoding="utf-8",
            close_fds=True,
        )
        loop.run_in_executor(
            None,
            output_reader,
            proc.stdout,
            functools.partial(self.handle_output, source="stdout"),
        )
        loop.run_in_executor(
            None,
            output_reader,
            proc.stderr,
            functools.partial(self.handle_output, source="stderr"),
        )
        return proc
    
    async def detect_process(self, headers=None):
        async def fetch_status(url: str, timeout: float, headers=None):
            code = None
            text = None
            start = default_timer()
            async with ClientSession(timeout=ClientTimeout(total=3.0)) as session:
                while default_timer() - start < timeout:
                    try:
                        async with session.get(url, headers=headers) as resp:
                            code = resp.status
                            if code == 200:
                                text = await resp.text()
                                break
                    except (ClientError, asyncio.TimeoutError):
                        pass
                    await asyncio.sleep(0.5)
            return code, text

        #status_url = self.admin_url + "/status"
        status_url = f"http://{self.admin[0]}:{self.admin[1]}" + "/status"
        status_code, status_text = await fetch_status(
            status_url, START_TIMEOUT, headers=headers
        )

        if not status_text:
            raise Exception(
                f"Timed out waiting for agent process to start (status={status_code}). "
                + f"Admin URL: {status_url}"
            )
        ok = False
        try:
            status = json.loads(status_text)
            ok = isinstance(status, dict) and "version" in status
        except json.JSONDecodeError:
            pass
        if not ok:
            raise Exception(
                f"Unexpected response from agent process. Admin URL: {status_url}"
            )

    def handle_output(self, *output, source: str = None, **kwargs):
        end = "" if source else "\n"
        if source == "stderr":
            color = "fg:ansired"
        elif not source:
            color = self.color or "fg:ansiblue"
        else:
            color = None
        log_msg(*output, color=color, prefix=self.label, end=end, **kwargs)

    async def generate_invitation(
        self,
        use_did_exchange: bool,
        auto_accept: bool = True,
        wait: bool = False,
    ):
        self._connection_ready = asyncio.Future()
            # Generate an invitation
        print(
                "#7 Create a connection to alice and print out the invite details"
        )
        invi_rec = await self.get_invite(use_did_exchange, auto_accept)

        print(
                "Use the following JSON to accept the invite from another demo agent."
        )
        print(
                json.dumps(invi_rec["invitation"]), label="Invitation Data:", color=None
        )

        if wait:
            print("Waiting for connection...")
            await self.detect_connection()

        return invi_rec

    async def get_invite(self, use_did_exchange: bool, auto_accept: bool = True):
        self.connection_id = None
        if use_did_exchange:
            # TODO can mediation be used with DID exchange connections?
            invi_rec = await self.admin_POST(
                "/out-of-band/create-invitation",
                {"handshake_protocols": ["rfc23"]},
                params={"auto_accept": json.dumps(auto_accept)},
            )
        else:
            if self.mediation:
                invi_rec = await self.admin_POST(
                    "/connections/create-invitation",
                    {"mediation_id": self.mediator_request_id},
                    params={"auto_accept": json.dumps(auto_accept)},
                )
            else:
                invi_rec = await self.admin_POST("/connections/create-invitation")

        return invi_rec

class WebhookAgent():
    def __init__(
        self,
        ident: str,
        http_port: int,
        admin_port: int,
        internal_host: str = None,
        external_host: str = None,
        webhook_port: int = None,
        webhook_url: str = None,
        genesis_data: str = None,
        seed: str = None,
        label: str = None,
        color: str = None,
        prefix: str = None,
        tails_server_base_url: str = None,
        timing: bool = False,
        timing_log: str = None,
        postgres: bool = None,
        revocation: bool = False,
        multitenant: bool = False,
        mediation: bool = False,
        aip: int = 20,
        arg_file: str = None,
        endorser_role: str = None,
        #connection_id: str = None
        #extra_args=None,
        #**params,
    ):
        self.ident = ident
        self.internal_host = internal_host
        self.external_host = external_host
        self.client_session: ClientSession = ClientSession()
        self.webhook_url = webhook_url
        self.did = None
        self.connection_id = None
        self.cred_ex_id = None
        self.connections = []
        self.admin_url = convert_to_http(internal_host, admin_port)
        if(webhook_url == None and webhook_port != None):
            self.webhook_port = webhook_port
            self.webhook_site = WebHookServer(external_host, webhook_port, self.handle_webhook, self.connection_handle)
            self.webhook_url = convert_to_http(external_host, webhook_port, "webhooks")
        self.agent = AriesAgent(
            genesis_url = convert_to_http(external_host, 9000), 
            admin = (internal_host, str(admin_port)),
            endpoint = convert_to_http(external_host, http_port),
            inbound_transport = ("http", internal_host, str(http_port)),
            outbound_transport = "http",
            webhook_url = self.webhook_url,
            admin_insecure_mode= True,
            endorser_protocol_role = endorser_role
        )

    async def send_request(
        self, method, path, data=None, text=False, params=None, headers=None
    ) -> ClientResponse:
        params = {k: v for (k, v) in (params or {}).items() if v is not None}
        async with self.client_session.request(
            method, self.admin_url + path, json=data, params=params, headers=headers
        ) as resp:
            resp_text = await resp.text()
            try:
                resp.raise_for_status()
            except Exception as e:
                # try to retrieve and print text on error
                raise Exception(f"Error: {resp_text}") from e
            if not resp_text and not text:
                return None
            if not text:
                try:
                    return json.loads(resp_text)
                except json.JSONDecodeError as e:
                    raise Exception(f"Error decoding JSON: {resp_text}") from e
            return resp_text

    async def admin_request(
        self, method, path, data=None, params=None, headers=None
    ) -> ClientResponse:
        try:
            if self.agent.multitenant and not headers:
                headers = {}
                headers["Authorization"] = (
                    "Bearer " + self.managed_wallet_params["token"]
                )
            if method == "GET":
                print("Controller GET %s request to Agent", path)
                response = await self.send_request("GET", path, None, None, params, headers)
                print("Response from GET %s received: \n%s", path, repr_json(response))
                return response
            elif method == "POST":
                print("Controller POST %s request to Agent%s",path,
                    (" with data: \n{}".format(repr_json(data)) if data else ""))
                response = await self.send_request("POST", path, data, None, params, headers)
                print("Response from POST %s received: \n%s", path,repr_json(response))
                return response
            else:
                raise Exception(f"Method {method} not supported")
        except ClientError as e:
            print(f"Error during GET {path}: {str(e)}")
            raise
    
    async def register_wallet(self):
        if not self.did:
            self.did = []
            data = {"method": DID_METHOD_KEY, "options": {"key_type": KEY_TYPE_BLS}}
            new_did = await self.admin_request("POST", "/wallet/did/create", data=data)
            self.did.append(new_did["result"]["did"])

            data = {"method": DID_METHOD_KEY, "options": {"key_type": KEY_TYPE_ED255}}
            new_did = await self.admin_request("POST", "/wallet/did/create", data=data)
            self.did.append(new_did["result"]["did"])

    async def handle_webhook(self, topic: str, payload, headers: dict):
        if topic != "webhook":  # would recurse
            handler = f"handle_{topic}"
            wallet_id = headers.get("x-wallet-id")
            method = getattr(self, handler, None)
            if method:
                print(
                    "Agent called controller webhook: %s%s%s%s",
                    handler,
                    f"\nPOST {self.webhook_url}/topic/{topic}/",
                    (f" for wallet: {wallet_id}" if wallet_id else ""),
                    (f" with payload: \n{repr_json(payload)}\n" if payload else ""),
                )
                asyncio.get_event_loop().create_task(method(payload))
            else:
                print(
                    f"Error: agent"
                    f"has no method {handler} "
                    f"to handle webhook on topic {topic}"
                )

    async def handle_basicmessages(self, message):
        print("Received message:", message["content"])
    
    async def handle_issue_credential_v2_0(self, message):
        self.cred_ex_id = message["cred_ex_id"]
        if message["state"] == "request-received":
            data = {"comment": "issuing credential"}
            await self.admin_request("POST", f"/issue-credential-2.0/records/{self.cred_ex_id}/issue", data=data)
        #if message["state"] == "credential-received":
        #    data = {"credential_id": "my-credential"}
        #    await self.admin_request("POST", f"/issue-credential-2.0/records/{self.cred_ex_id}/store", data=data)

    async def handle_connections(self, message):
        self.connection_id = message["connection_id"]
        if message["rfc23_state"] == "invitation-received":
            await self.admin_request("POST", f"/connections/{self.connection_id}/accept-invitation")

        if message["rfc23_state"] == "request-received":
            await self.admin_request("POST", f"/connections/{self.connection_id}/accept-request")
        
        if message["rfc23_state"] == "response-received":
            self.connections.append(self.connection_id)

    async def handle_present_proof_v2_0(self, message):
        print("OK")

    async def connection_handle(self, connection):
        if connection not in self.connections:
            return web.Response(status=404)
        body = f"<html><body><p>{connection} OK</p></body></html>"
        return web.Response(body=body, content_type='text/html', status=200)

    async def start_process(self):
        await self.agent.start_process()
        await self.register_wallet()
        if self.webhook_site:
            await self.webhook_site.listen_webhooks()