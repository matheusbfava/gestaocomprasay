import json
import pandas as pd

class GoogleSheetsClient:
    """
    Cliente de Integração para Google Sheets.
    Suporta leitura pública rápida (via pandas) e leitura/escrita privada 
    (via biblioteca gspread usando Service Account JSON).
    """
    
    def __init__(self, spreadsheet_url: str, credentials_json: str = None):
        self.spreadsheet_url = spreadsheet_url
        self.credentials_json = credentials_json
        self.client = None
        self.sheet = None
        self.connected = False
        
        # Extrai o ID da planilha da URL fornecida
        self.spreadsheet_id = self._extract_id(spreadsheet_url)
        
    def _extract_id(self, url: str) -> str:
        if not url:
            return ""
        if "/d/" in url:
            parts = url.split("/d/")
            if len(parts) > 1:
                return parts[1].split("/")[0]
        return url
        
    def connect(self) -> bool:
        """
        Inicia a conexão com a planilha do Google.
        Se não houver JSON de credenciais, valida apenas a leitura pública.
        """
        if not self.spreadsheet_url:
            raise ValueError("A URL da planilha do Google Sheets é obrigatória.")
            
        if not self.credentials_json:
            # Modo Público (Somente Leitura) - Apenas valida se consegue puxar via Pandas
            try:
                url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/gviz/tq?tqx=out:csv"
                pd.read_csv(url, nrows=1)
                self.connected = True
                return True
            except Exception as e:
                raise Exception(f"Falha ao acessar planilha pública. Certifique-se de que o link está compartilhado como 'Qualquer pessoa com o link pode ler'. Erro: {str(e)}")
            
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            
            # Carrega credenciais do JSON inserido pelo usuário
            creds_dict = json.loads(self.credentials_json)
            scopes = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(self.spreadsheet_id)
            self.connected = True
            return True
        except ImportError:
            raise ImportError("As bibliotecas 'gspread' ou 'google-auth' não estão instaladas. Certifique-se de que estão no seu requirements.txt.")
        except json.JSONDecodeError:
            raise ValueError("O formato do JSON de credenciais da Service Account é inválido.")
        except Exception as e:
            raise Exception(f"Falha ao conectar via Service Account: {str(e)}")

    def get_list_items(self, list_name: str = "PGI_GestaoCotacoes") -> list:
        """
        Busca todos os registros da aba/página especificada no Google Sheets.
        Se conectada em modo privado, usa gspread (leitura e escrita).
        Se pública, usa pandas read_csv.
        """
        # Se autenticado com gspread (Modo Privado)
        if self.sheet:
            try:
                worksheet = self.sheet.worksheet(list_name)
                records = worksheet.get_all_records()
                # Cria um ID de compatibilidade sequencial baseado na linha da planilha
                for idx, record in enumerate(records):
                    record["ID"] = idx + 2 # O cabeçalho é a linha 1, os dados começam na linha 2
                return records
            except Exception as e:
                raise Exception(f"Erro ao ler planilha com gspread: {str(e)}")
        
        # Modo Público (Pandas)
        try:
            url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={list_name}"
            df = pd.read_csv(url)
            df = df.fillna("")
            records = df.to_dict(orient="records")
            for idx, record in enumerate(records):
                record["ID"] = idx + 2
            return records
        except Exception as e:
            raise Exception(f"Erro ao ler planilha pública: {str(e)}")

    def insert_list_item(self, item_data: dict, list_name: str = "PGI_GestaoCotacoes") -> bool:
        """
        Insere uma nova linha de dados na planilha. Requer Modo Privado.
        """
        if not self.sheet:
            raise ValueError("A gravação de dados só é permitida no Modo Privado. Configure as credenciais da Service Account.")
            
        try:
            worksheet = self.sheet.worksheet(list_name)
            
            # Mapeamento estrito das colunas para gravação correta
            columns = [
                "ID_PGI", "tipo", "Comprador", "grupoinsumo", "cotacao", "due_dilligence", 
                "equalizacao", "orcamento", "validacao_eng", "validacao_ger", "validacao_sup", 
                "req_mega", "contr_mega", "param_fiscal", "minuta", "ass_digital", 
                "credenciamento", "comunicar", "savings", "aud_pasta", "valor_fechado"
            ]
            row = [str(item_data.get(col, "")) for col in columns]
            worksheet.append_row(row)
            return True
        except Exception as e:
            raise Exception(f"Erro ao inserir linha no Google Sheets: {str(e)}")

    def update_list_item(self, item_id: int, item_data: dict, list_name: str = "PGI_GestaoCotacoes") -> bool:
        """
        Atualiza uma linha existente na planilha com base no ID_PGI. Requer Modo Privado.
        """
        if not self.sheet:
            raise ValueError("A atualização de dados só é permitida no Modo Privado. Configure as credenciais da Service Account.")
            
        try:
            import gspread
            worksheet = self.sheet.worksheet(list_name)
            
            columns = [
                "ID_PGI", "tipo", "Comprador", "grupoinsumo", "cotacao", "due_dilligence", 
                "equalizacao", "orcamento", "validacao_eng", "validacao_ger", "validacao_sup", 
                "req_mega", "contr_mega", "param_fiscal", "minuta", "ass_digital", 
                "credenciamento", "comunicar", "savings", "aud_pasta", "valor_fechado"
            ]
            
            # Localiza a linha correta pelo ID_PGI na coluna A (Coluna 1)
            id_pgi = item_data.get("ID_PGI")
            cell = worksheet.find(str(id_pgi), in_column=1)
            
            if cell:
                row_idx = cell.row
                current_row = worksheet.row_values(row_idx)
                while len(current_row) < len(columns):
                    current_row.append("")
                    
                # Atualiza apenas os campos fornecidos que existem na planilha
                for key, val in item_data.items():
                    if key in columns:
                        col_idx = columns.index(key)
                        current_row[col_idx] = str(val)
                        
                # Atualiza a linha completa usando notação A1 (Ex: A5:U5)
                range_str = f"A{row_idx}:{gspread.utils.rowcol_to_a1(row_idx, len(columns))}"
                worksheet.update(range_str, [current_row])
                return True
            else:
                # Se não encontrar pelo ID_PGI, tenta atualizar pela linha diretamente (item_id)
                row_idx = int(item_id)
                current_row = worksheet.row_values(row_idx)
                while len(current_row) < len(columns):
                    current_row.append("")
                    
                for key, val in item_data.items():
                    if key in columns:
                        col_idx = columns.index(key)
                        current_row[col_idx] = str(val)
                        
                range_str = f"A{row_idx}:{gspread.utils.rowcol_to_a1(row_idx, len(columns))}"
                worksheet.update(range_str, [current_row])
                return True
        except Exception as e:
            raise Exception(f"Erro ao atualizar linha no Google Sheets: {str(e)}")

    def delete_list_item(self, item_id: int, list_name: str = "PGI_GestaoCotacoes") -> bool:
        """
        Deleta uma linha de dados no Google Sheets usando o número da linha. Requer Modo Privado.
        """
        if not self.sheet:
            raise ValueError("A exclusão de dados só é permitida no Modo Privado. Configure as credenciais da Service Account.")
            
        try:
            worksheet = self.sheet.worksheet(list_name)
            row_idx = int(item_id)
            worksheet.delete_rows(row_idx)
            return True
        except Exception as e:
            raise Exception(f"Erro ao excluir linha no Google Sheets: {str(e)}")
