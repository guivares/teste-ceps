import pandas as pd
import requests
import os
import time
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager 

# Cria pasta de prints se não existir
os.makedirs("prints", exist_ok=True)

def ler_ceps_csv(path="lista_ceps.csv"):
    df = pd.read_csv(path)
    return df["CEP"].astype(str).tolist()

def consultar_via_cep(cep):
    url = f"https://viacep.com.br/ws/{cep}/json/"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if "erro" in data:
                print(f"⚠️ CEP inválido: {cep}")
                return None
            return {
                "cep": data.get("cep"),
                "logradouro": data.get("logradouro"),
                "bairro": data.get("bairro"),
                "cidade": data.get("localidade"),
                "estado": data.get("uf"),
                "clima": ""  # preenchido depois
            }
        else:
            print(f"Erro ao consultar o CEP {cep}")
            return None
    except Exception as e:
        print(f"Erro na requisição do CEP {cep}: {e}")
        return None

def configurar_driver():
    options = Options()
    # options.add_argument("--headless")  # opcional
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Usando o webdriver-manager para obter o ChromeDriver
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    
    # Remove a identificação do Selenium no JS
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    
    return driver

def buscar_cep_google(driver, cep):
    try:
        url = f"https://www.google.com/search?q={cep}&hl=pt-BR&gl=br"
        driver.get(url)
        time.sleep(6)  # tempo extra pro conteúdo carregar

        screenshot_path = f"prints\\{cep}.png"  # Caminho de arquivo no Windows
        driver.save_screenshot(screenshot_path)

        try:
            clima_element = driver.find_element(By.CSS_SELECTOR, ".LrzXr.kno-fv")
            clima = clima_element.text
        except Exception:
            clima = ""

        return clima

    except Exception as e:
        print(f"Erro ao buscar no Google: {cep}, erro: {e}")
        return ""


def salvar_dados(dados, output="ceps.csv"):
    df = pd.DataFrame(dados)
    df.to_csv(output, index=False)

def digitar_na_calculadora(ceps):
    print("Abrindo a calculadora.")
    os.system("calc")  # Comando para abrir a calculadora no Windows
    time.sleep(2)
    for cep in ceps:
        print(f"⌨️ Digitando CEP: {cep}")
        pyautogui.typewrite(cep)
        pyautogui.press("enter")
        time.sleep(1)

def main():
    ceps = ler_ceps_csv()
    resultados = []
    driver = configurar_driver()

    for cep in ceps:
        print(f"🔍 Processando CEP: {cep}")
        data = consultar_via_cep(cep)
        if data:
            clima = buscar_cep_google(driver, cep)
            data["clima"] = clima
        else:
            # Se o CEP for inválido ou a API falhar
            data = {
                "cep": cep,
                "logradouro": "CEP inválido",
                "bairro": "",
                "cidade": "",
                "estado": "",
                "clima": ""
            }

        resultados.append(data)
        time.sleep(1)

    driver.quit()
    salvar_dados(resultados)
    print("✅ Dados salvos em ceps.csv")

    digitar_na_calculadora(ceps)

if __name__ == "__main__":
    main()
