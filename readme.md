## Digital Degree Application
Aplicação desenvolvida para testar algumas das funcionalidades presentes nos Agentes do ACA-Py.

## Execução
Para execução dessa aplicação é necessário ter uma instância do VON-Network em execução, detalhes sobre a execução do VON-Network está disponível em seu próprio repositório https://github.com/bcgov/von-network.

### Instalação de requisitos
pip install -r requirements.txt

### Agente author
python ./run.py --ident author --http-port 8000 --admin-port 8080 --internal-host 127.0.0.1 --external-host 0.0.0.0 --webhook-port 8090

### Agente endorser
python ./run.py --ident endorser --http-port 8001 --admin-port 8081 --internal-host 127.0.0.1 --external-host 0.0.0.0 --webhook-port 8091 --endorser-role endorser


### Cliente web
python ./wallet_manager.py