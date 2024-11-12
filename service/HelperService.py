import json

class ServicosGerais:
    @staticmethod
    def abrir_config(tipo:str=['PADRAO','RESTRITO']) -> dict:
        if tipo =='RESTRITO':
            nome = 'configRestrito'

        else:
            nome = 'config'

        with open(f'config/{nome}.json',encoding='utf8') as f:
            config=json.load(f)
        
        return config
    
    @staticmethod
    def modificar_config(key, value) -> None:
        file_path = "../../../config/config.json"
        # Carregando o arquivo json
        with open(file_path, "r",encoding='utf8') as f:
            data = json.load(f)

        # Modificando o valor da chave especificada
        data[key] = value

        # Escrevendo o arquivo json modificado
        with open(file_path, "w",encoding='utf8') as f:
            json.dump(data, f, ensure_ascii=False)
    