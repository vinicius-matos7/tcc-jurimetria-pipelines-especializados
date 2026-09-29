"""
===============================================================================
JusMetrIA - Script de Extração da API Pública DataJud (CNJ / TJBA)
===============================================================================
Este script realiza a coleta automatizada dos metadados processuais das 20 Varas
de Relações de Consumo da Comarca de Salvador (TJBA) para o período de 2020 a 2024.

Regra de Negócio Crucial (Hierarquia de Sentenças de Mérito):
A classificação dos desfechos obedece à seguinte ordem de precedência:
1. Sentenças com Resolução de Mérito (Procedente = 219, Parcialmente Procedente = 221,
   Improcedente = 220) SEMPRE prevalecem sobre arquivamento simples ou baixa.
2. Arquivamento / Baixa Definitiva (246 ou 196) apenas se não houver sentença de mérito.

Pré-requisitos:
1. Crie um arquivo `.env` na raiz do projeto contendo sua chave pública:
   DATAJUD_API_KEY=c3J0cF9zb21lX2tleQ==
2. Instale as dependências:
   pip install requests pandas python-dotenv
===============================================================================
"""

import os
import sys
import time
import requests
import pandas as pd
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

URL_DATAJUD = "https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search"
API_KEY = os.environ.get("DATAJUD_API_KEY", "").strip()

if not API_KEY:
    print("\n" + "=" * 75)
    print(" [AVISO CRÍTICO] Chave de API do DataJud não configurada!")
    print(" Por favor, crie o arquivo '.env' na raiz do projeto com:")
    print(" DATAJUD_API_KEY=sua_chave_aqui")
    print(" (Você pode obter sua chave pública gratuitamente no portal do CNJ/DataJud)")
    print("=" * 75 + "\n")

HEADERS = {
    "Authorization": f"APIKey {API_KEY}",
    "Content-Type": "application/json"
}


def classificar_movimentos(movimentos: list) -> str:
    """Classifica o desfecho processual respeitando a hierarquia de mérito do CPC/CNJ."""
    codigos = set()
    for m in movimentos:
        if isinstance(m, dict):
            codigo = m.get('codigo') or m.get('codigoNacional') or m.get('movimentoNacional')
            if codigo is not None:
                try:
                    codigos.add(int(codigo))
                except (ValueError, TypeError):
                    pass
            
    # HIERARQUIA DE PRIORIDADE: Mérito SEMPRE prevalece sobre arquivamento simples
    if 219 in codigos:
        return "Procedente"
    elif 221 in codigos:
        return "Parcialmente Procedente"
    elif 220 in codigos:
        return "Improcedente"
    elif 246 in codigos or 196 in codigos:
        return "Definitivo / Extinção"
    else:
        return "Sem Sentença Mapeada"


def extrair_ano(ano: int) -> pd.DataFrame:
    """Extrai todos os processos de relações de consumo autuados no ano especificado."""
    print(f"[*] Coletando processos autuados em {ano} (Salvador/BA)...")
    query_base = {
        "size": 200,
        "sort": [{"dataAjuizamento": "asc"}],
        "query": {
            "bool": {
                "must": [
                    {"match_phrase": {"orgaoJulgador.nome": "VARA DE RELACOES DE CONSUMO"}}
                ],
                "filter": [
                    {"term": {"orgaoJulgador.codigoMunicipioIBGE": 2927408}},  # Salvador - BA
                    {"range": {"dataAjuizamento": {"gte": f"{ano}0101000000", "lte": f"{ano}1231235959"}}}
                ]
            }
        }
    }
    
    search_after = None
    linhas_ano = []
    t0 = time.time()
    lote = 0
    max_retries = 3
    
    while True:
        if search_after:
            query_base["search_after"] = search_after
            
        retries = 0
        success = False
        while retries < max_retries:
            try:
                res = requests.post(URL_DATAJUD, headers=HEADERS, json=query_base, timeout=120)
                if res.status_code == 200:
                    success = True
                    break
                elif res.status_code == 401 or res.status_code == 403:
                    print(f"    [ERRO DE AUTENTICAÇÃO] HTTP {res.status_code}. Verifique sua DATAJUD_API_KEY no .env")
                    return pd.DataFrame(linhas_ano)
                else:
                    print(f"    [!] HTTP {res.status_code} para {ano}. Tentativa {retries + 1}/{max_retries}...")
            except Exception as e:
                print(f"    [!] Conexão instável para {ano}: {e}. Aguardando 5s...")
            
            time.sleep(5)
            retries += 1
            
        if not success:
            print(f"    [!] Limite de tentativas excedido para o ano {ano}.")
            break
            
        dados = res.json()
        hits = dados.get('hits', {}).get('hits', [])
        if not hits:
            break
            
        for proc in hits:
            src = proc.get('_source', {})
            movs = src.get('movimentos') or []
            desfecho = classificar_movimentos(movs)
            
            assuntos = src.get('assuntos') or []
            assunto_cod = 'N/A'
            assunto_nome = 'N/A'
            if isinstance(assuntos, list) and len(assuntos) > 0 and isinstance(assuntos[0], dict):
                assunto_cod = assuntos[0].get('codigo') or assuntos[0].get('codigoNacional') or 'N/A'
                assunto_nome = assuntos[0].get('nome', 'N/A')
                
            linhas_ano.append({
                'processo': src.get('numeroProcesso'),
                'vara': src.get('orgaoJulgador', {}).get('nome'),
                'data_distribuicao': src.get('dataAjuizamento'),
                'assunto_tpu': assunto_cod,
                'assunto_desc': assunto_nome,
                'desfecho': desfecho
            })
            
        lote += 1
        search_after = hits[-1]['sort']
        if lote % 10 == 0:
            print(f"    [{ano}] Lote {lote}: {len(linhas_ano):,} processos acumulados ({time.time()-t0:.1f}s)")
            
    print(f"[+] Ano {ano} finalizado: {len(linhas_ano):,} processos coletados em {time.time()-t0:.1f}s.")
    return pd.DataFrame(linhas_ano)


def main():
    workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(workspace_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    print("=" * 75)
    print(" INICIANDO EXTRAÇÃO DE PROCESSOS DO DATAJUD (TJBA - CONSUMO)")
    print(" Período Alvo: 2020 a 2024")
    print("=" * 75)
    
    dfs = []
    for ano in range(2020, 2025):
        df_a = extrair_ano(ano)
        dfs.append(df_a)
        
    df_completo = pd.concat(dfs, ignore_index=True)
    out_csv = os.path.join(data_dir, "dataset_relacoes_consumo.csv")
    df_completo.to_csv(out_csv, index=False, encoding='utf-8')
    
    print("\n" + "=" * 75)
    print(" EXTRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 75)
    print(f" Arquivo salvo em: {out_csv}")
    print(f" Total de processos extraídos: {df_completo.shape[0]:,}")
    if not df_completo.empty and 'desfecho' in df_completo.columns:
        print("\n Distribuição dos Desfechos:")
        print(df_completo['desfecho'].value_counts())
    print("=" * 75 + "\n")


if __name__ == '__main__':
    main()
