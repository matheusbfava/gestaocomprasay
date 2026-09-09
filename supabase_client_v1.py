import json
import requests

class SupabaseClient:
    """
    Cliente de Conexão Ultra-Rápido para Supabase.
    Suporta tanto a biblioteca 'supabase-py' quanto requisições REST diretas (PostgREST API)
    para garantir resposta imediata e compatibilidade em qualquer ambiente.
    """
    
    def __init__(self, url: str, key: str):
        self.url = url.rstrip('/') if url else ""
        self.key = key if key else ""
        self.client = None
        self.rest_url = f"{self.url}/rest/v1" if self.url else ""
        self.connected = False
        
    def connect(self) -> bool:
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL e SUPABASE_KEY são obrigatórios.")
            
        try:
            # Tenta usar a biblioteca oficial supabase se disponível
            from supabase import create_client
            self.client = create_client(self.url, self.key)
            self.connected = True
            return True
        except ImportError:
            # Se a biblioteca não estiver instalada, usa REST API direto via requests (ultra-rápido)
            self.connected = True
            return True
        except Exception as e:
            raise Exception(f"Erro ao conectar com Supabase: {str(e)}")

    def _get_headers(self) -> dict:
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def get_list_items(self, list_name: str = "PGI_GestaoCotacoes") -> list:
        """
        Busca registros do Supabase em milissegundos.
        """
        if self.client:
            try:
                response = self.client.table(list_name).select("*").execute()
                return response.data if response.data else []
            except Exception:
                pass # Fallback para REST API
                
        endpoint = f"{self.rest_url}/{list_name}?select=*"
        try:
            res = requests.get(endpoint, headers=self._get_headers(), timeout=10)
            if res.status_code == 200:
                return res.json()
            else:
                raise Exception(f"HTTP {res.status_code}: {res.text}")
        except Exception as e:
            raise Exception(f"Erro ao consultar Supabase ({list_name}): {str(e)}")

    def insert_list_item(self, item_data: dict, list_name: str = "PGI_GestaoCotacoes") -> bool:
        """
        Insere um novo registro no Supabase.
        """
        if self.client:
            try:
                self.client.table(list_name).insert(item_data).execute()
                return True
            except Exception:
                pass
                
        endpoint = f"{self.rest_url}/{list_name}"
        try:
            res = requests.post(endpoint, headers=self._get_headers(), json=item_data, timeout=10)
            if res.status_code in (200, 201):
                return True
            else:
                raise Exception(f"HTTP {res.status_code}: {res.text}")
        except Exception as e:
            raise Exception(f"Erro ao inserir no Supabase ({list_name}): {str(e)}")

    def update_list_item(self, item_id: str, item_data: dict, list_name: str = "PGI_GestaoCotacoes") -> bool:
        """
        Atualiza um registro existente no Supabase pelo ID_PGI.
        """
        id_pgi = item_data.get("ID_PGI", item_id)
        if self.client:
            try:
                self.client.table(list_name).update(item_data).eq("ID_PGI", str(id_pgi)).execute()
                return True
            except Exception:
                pass
                
        endpoint = f"{self.rest_url}/{list_name}?ID_PGI=eq.{id_pgi}"
        try:
            res = requests.patch(endpoint, headers=self._get_headers(), json=item_data, timeout=10)
            if res.status_code in (200, 204):
                return True
            else:
                raise Exception(f"HTTP {res.status_code}: {res.text}")
        except Exception as e:
            raise Exception(f"Erro ao atualizar no Supabase ({list_name}): {str(e)}")

    def delete_list_item(self, item_id: str, list_name: str = "PGI_GestaoCotacoes") -> bool:
        """
        Exclui um registro no Supabase pelo ID_PGI.
        """
        if self.client:
            try:
                self.client.table(list_name).delete().eq("ID_PGI", str(item_id)).execute()
                return True
            except Exception:
                pass
                
        endpoint = f"{self.rest_url}/{list_name}?ID_PGI=eq.{item_id}"
        try:
            res = requests.delete(endpoint, headers=self._get_headers(), timeout=10)
            if res.status_code in (200, 204):
                return True
            else:
                raise Exception(f"HTTP {res.status_code}: {res.text}")
        except Exception as e:
            raise Exception(f"Erro ao excluir no Supabase ({list_name}): {str(e)}")
