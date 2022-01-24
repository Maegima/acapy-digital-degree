import os
import asyncio
import argparse
from agent import WebhookAgent


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
   
    parser.add_argument('--ident', dest='ident', nargs="?", default="", help="Agent self atested id")
    parser.add_argument('--http-port', dest='hport', type=int, help="Inbound http port")
    parser.add_argument('--admin-port', dest='aport', type=int, help="Admin http port")
    parser.add_argument('--internal-host', dest='ihost', nargs="?", default="127.0.0.1", help="Host for admin and inbound connections")
    parser.add_argument('--external-host', dest='ehost', nargs="?", default="127.0.0.1", help="Host for external connection ex.: webhooks server")
    parser.add_argument('--webhook-port', dest='wport', nargs="?", type=int, default=0, help="Webhook server port")
    parser.add_argument('--endorser-role', dest='erole', nargs="?", default="author", help="Agent endorser role")

    args = parser.parse_args()
    
    
    agent = WebhookAgent(args.ident, args.hport, args.aport, args.ihost, args.ehost, args.wport, endorser_role=args.erole)
    #agent = WebhookAgent("author", 8000, 8080, "127.0.0.1", "0.0.0.0", 8090, endorser_role="author")
    print(agent.agent.get_agent_parameters())

    try:
        asyncio.get_event_loop().run_until_complete(agent.start_process())
    except KeyboardInterrupt:
        os._exit(1)


