import json
import tornado.ioloop
import tornado.web
import tornado.httpclient

class Connection():
    def __init__(self, value):
        self.number = value

class Credential():
    def __init__(self, name, data):
        self.name = name
        self.data = self.serialize(data)

    def serialize(self, data: dict):
        serialized = dict()
        for key, value in data.items():
            if type(value) == dict:
                aux = self.serialize(value)
                for k, v in aux.items():
                    serialized[key + "|" + k] = v 
            else:
                serialized[key] = value
        return serialized

def query_dict(query: str):
    queries = query.split("&")
    return { query.split("=")[0]: query.split("=")[1] if len(query.split("=")) > 1 else None for query in queries } 

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        conn = Connection(2)
        queries = query_dict(self.request.query)
        if  queries.get("type", "") == "endorser":    
            self.render("root/index/index.html", title="Endorser", script="endorser.js", connections=conn, button="Create")
        else: 
            self.render("root/index/index.html", title="Author", script="author.js", connections=conn, button="Accept")

async def create_invitation():
    url = 'http://127.0.0.1:8081/out-of-band/create-invitation?auto_accept=false'
    headers = {"Content-Type": "application/json"}
    data = '{"handshake_protocols": ["did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/didexchange/1.0"]}'
    client_assync = tornado.httpclient.AsyncHTTPClient()
    resp = ""
    try:
        response = await client_assync.fetch(url, method="POST", headers=headers, body=data)
        print(response.body)
        resp = response.body
    except tornado.httpclient.HTTPError as e:
        # HTTPError is raised for non-200 responses; the response
        # can be found in e.response.
        print("Error: " + str(e))
    except Exception as e:
        # Other errors are possible, such as IOError.
        print("Error: " + str(e))
    client_assync.close()
    return resp

async def accept_invitation(data):
    url = 'http://127.0.0.1:8080/out-of-band/receive-invitation?auto_accept=false'
    headers = {"Content-Type": "application/json"}
    client_assync = tornado.httpclient.AsyncHTTPClient()
    resp = ""
    try:
        response = await client_assync.fetch(url, method="POST", headers=headers, body=data)
        print(response.body)
        resp = response.body
    except tornado.httpclient.HTTPError as e:
        # HTTPError is raised for non-200 responses; the response
        # can be found in e.response.
        print("Error: " + str(e))
    except Exception as e:
        # Other errors are possible, such as IOError.
        print("Error: " + str(e))
    client_assync.close()
    return resp

async def get_credential_data(id):
    url = 'http://localhost:8080/credential/w3c/' + id
    headers = {"accept": "application/json"}
    client_assync = tornado.httpclient.AsyncHTTPClient()
    resp = ""
    try:
        response = await client_assync.fetch(url, method="GET", headers=headers)
        resp = response.body
    except tornado.httpclient.HTTPError as e:
        # HTTPError is raised for non-200 responses; the response
        # can be found in e.response.
        print("Error: " + str(e))
    except Exception as e:
        # Other errors are possible, such as IOError.
        print("Error: " + str(e))
    client_assync.close()
    return resp


class InvitationCreateHandler(tornado.web.RequestHandler):
    async def post(self):
        resp = await create_invitation()
        if resp == "":
            self.write_error(404)
        else:
            self.write(resp)

class InvitationAcceptHandler(tornado.web.RequestHandler):
    async def post(self):
        #data = json.loads(self.request.body.decode('utf-8'))
        #print('Got JSON data:', data)
        resp = await accept_invitation(self.request.body.decode('utf-8'))
        if resp == "":
            self.write_error(404)
        else:
            self.write(resp)

class CredentialHandler(tornado.web.RequestHandler):
    async def get(self, credential_id):
        data = await get_credential_data(credential_id)
        print(json.loads(data))
        credential = Credential(credential_id, json.loads(data))
        queries = query_dict(self.request.query)
        students = ["ab", "cd", "ef"]
        if  queries.get("type", "") == "endorser":
            self.render("root/index/credential.html", title="Endorser", credential=credential, students=students)
        else:
            self.render("root/index/credential.html", title="Author", credential=credential, students=students)

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r'/invitation/create', InvitationCreateHandler),
        (r'/invitation/accept', InvitationAcceptHandler),
        (r'/static/bootstrap/(.*)', tornado.web.StaticFileHandler, {'path': "root/bootstrap-5.1.3-dist/"}),
        (r'/static/css/(.*.css)', tornado.web.StaticFileHandler, {'path': "root/css/"}),
        (r'/static/js/(.*)', tornado.web.StaticFileHandler, {'path': "root/js/"}),
        (r'/credential/(.*)', CredentialHandler),
    ], debug=True)

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()