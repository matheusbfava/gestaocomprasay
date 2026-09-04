import requests
import json

class SharePointOAuthClient:
    """
    Cliente de Autenticação OAuth2 e Integração para SharePoint Online.
    Utiliza o fluxo 'Client Credentials Grant' do Microsoft Entra ID (Azure AD)
    para autenticação de aplicativo (App-Only) sem necessidade de login interativo.
    """
    
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, site_url: str = "https://grupoayoshii.sharepoint.com/sites/DPTO_SUPRIMENTOS"):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.site_url = site_url.rstrip('/')
        self.access_token = None
        self.expires_in = 0
        
        # O escopo padrão para APIs do SharePoint Online é baseado na URL raiz do tenant
        # Exemplo: https://grupoayoshii.sharepoint.com/.default
        base_tenant_url = site_url.split('/sites/')[0]
        self.scope = f"{base_tenant_url}/.default"
        
    def acquire_token(self) -> str:
        """
        Obtém o Token de Acesso OAuth2 junto ao Microsoft Entra ID.
        """
        if not self.tenant_id or not self.client_id or not self.client_secret:
            raise ValueError("As credenciais (Tenant ID, Client ID, Client Secret) são obrigatórias.")
            
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Parâmetros padrão do fluxo Client Credentials OAuth2
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=payload, timeout=10)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                self.expires_in = token_data.get("expires_in", 3600)
                return self.access_token
            else:
                error_description = response.json().get("error_description", response.text)
                raise Exception(f"Falha na autenticação OAuth2 (HTTP {response.status_code}): {error_description}")
                
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Erro ao conectar com o servidor do Microsoft Entra ID: {str(e)}")

    def _get_auth_headers(self) -> dict:
        """
        Gera os cabeçalhos padrão de autenticação do SharePoint REST API.
        """
        if not self.access_token:
            self.acquire_token()
            
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json;odata=verbose",
            "Content-Type": "application/json;odata=verbose"
        }

    def get_list_items(self, list_name: str = "PGI_GestaoCotacoes") -> list:
        """
        Busca todos os registros da lista especificada no SharePoint.
        """
        # Endpoint REST API do SharePoint para obter itens de uma lista
        endpoint = f"{self.site_url}/_api/web/lists/getbytitle('{list_name}')/items"
        headers = self._get_auth_headers()
        
        try:
            response = requests.get(endpoint, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                # O SharePoint encapsula os resultados dentro do caminho ['d']['results'] quando em formato verbose
                return data.get("d", {}).get("results", [])
            else:
                raise Exception(f"Erro ao ler lista do SharePoint (HTTP {response.status_code}): {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Erro de conexão com o SharePoint: {str(e)}")

    def insert_list_item(self, item_data: dict, list_name: str = "PGI_GestaoCotacoes") -> dict:
        """
        Insere um novo registro (item) na lista do SharePoint.
        Importante: Todas as colunas customizadas devem ser passadas como texto de acordo com a modelagem.
        """
        endpoint = f"{self.site_url}/_api/web/lists/getbytitle('{list_name}')/items"
        headers = self._get_auth_headers()
        
        # O SharePoint REST exige o tipo de entidade da lista (ListItemEntityTypeFullName)
        # Normalmente o padrão é SP.Data.NomeDaListaListItem
        # Ex: SP.Data.PGI_GestaoCotacoesListItem
        list_entity_type = f"SP.Data.{list_name}ListItem"
        
        # Prepara o payload anexando o metadata de tipo obrigatório do SharePoint
        payload = {
            "__metadata": {
                "type": list_entity_type
            }
        }
        # Mescla com os dados do usuário
        payload.update(item_data)
        
        try:
            response = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=15)
            
            if response.status_code == 201:  # 201 Created é o retorno padrão de sucesso
                return response.json().get("d", {})
            else:
                raise Exception(f"Erro ao inserir item (HTTP {response.status_code}): {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Erro de conexão ao inserir registro: {str(e)}")

    def update_list_item(self, item_id: int, item_data: dict, list_name: str = "PGI_GestaoCotacoes") -> bool:
        """
        Atualiza um registro existente na lista do SharePoint usando o ID interno da linha (Primary Key).
        Usa o método MERGE / PATCH do protocolo OData.
        """
        # O endpoint exige o ID numérico específico do registro do SharePoint
        endpoint = f"{self.site_url}/_api/web/lists/getbytitle('{list_name}')/items({item_id})"
        
        headers = self._get_auth_headers()
        # Para atualizações parciais (PATCH/MERGE), o SharePoint exige cabeçalhos extras
        headers.update({
            "X-HTTP-Method": "MERGE",
            "IF-MATCH": "*"  # Sobrescreve concorrentemente sem checagem de eTag (pode ser refinado se necessário)
        })
        
        list_entity_type = f"SP.Data.{list_name}ListItem"
        payload = {
            "__metadata": {
                "type": list_entity_type
            }
        }
        payload.update(item_data)
        
        try:
            response = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=15)
            
            if response.status_code in [200, 204]:  # 204 No Content indica sucesso total sem dados de retorno
                return True
            else:
                raise Exception(f"Erro ao atualizar item (HTTP {response.status_code}): {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Erro de conexão ao atualizar registro: {str(e)}")
