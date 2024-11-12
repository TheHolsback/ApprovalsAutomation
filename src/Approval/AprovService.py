"""
Module: ServicoAprovacoes

This module contains the ServicoAprovacoes class, which is responsible for managing approval workflows using Microsoft Graph API and Selenium WebDriver.
The class allows for the creation of approvals, login to Microsoft services, and checking the status of approvals.

Dependencies:
- msal: Microsoft Authentication Library for Python
- selenium: Web automation library
- requests: HTTP library for making requests
- src.Services.HelperService: Custom service for general operations
- src.Automacao.Aprovacoes.Repository.RepoAprov: Base repository for approvals

Class: ServicoAprovacoes

Attributes:
- servicos_gerais: An instance of the ServicosGerais class for general services.
- headers: A dictionary containing the authorization headers for API requests.

Methods:
- __init__: Initializes the class, sets up authentication with Microsoft Graph API, and retrieves an access token.
- faz_login_ms: Handles the login process to Microsoft services using Selenium WebDriver.
- cria_aprovacao: Creates a new approval request in Microsoft Graph API.
- cria_aprovacao_sequencial: Creates a sequential approval request using the Microsoft Teams interface.
- verifica_status: Checks the status of an approval request by its title.

Usage:
1. Instantiate the ServicoAprovacoes class.
2. Use methods to create approvals, check status, etc.
"""

from msal import ConfidentialClientApplication
from selenium.webdriver.common.by import By
from selenium import webdriver
from time import sleep
import requests

from service.HelperService import ServicosGerais

class ServicoAprovacoes():
    """
    A class to manage approval workflows using Microsoft Graph API and Selenium WebDriver.

    Methods:
    - __init__: Initializes the class and sets up authentication.
    - faz_login_ms: Performs Microsoft login via Selenium WebDriver.
    - cria_aprovacao: Creates a new approval item in Microsoft Graph API.
    - cria_aprovacao_sequencial: Creates a sequential approval in Microsoft Teams.
    - verifica_status: Checks the status of an approval by its title.
    """

    def __init__(self) -> None:
        """
        Initializes the ServicoAprovacoes class, sets up authentication with Microsoft Graph API,
        and retrieves an access token.
        """
        self.servicos_gerais = ServicosGerais()

        self.config_restrito = self.servicos_gerais.abrir_config('RESTRITO')
        client_id = self.config_restrito['approvals']['client_id']
        client_secret = self.config_restrito['approvals']['client_secret']
        tenant_id = self.config_restrito['approvals']['tenant_id']
        
        msal_authority = f"https://login.microsoftonline.com/{tenant_id}" 
        msal_scope = ["https://graph.microsoft.com/.default"]

        app_msal = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=msal_authority
        )

        url_auth = app_msal.get_authorization_request_url(scopes=msal_scope)

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url_auth)
        code = self.faz_login_ms(driver, 'localhost')
        
        driver.close()

        result = app_msal.acquire_token_silent(
            scopes=msal_scope,
            account=None
        )
        
        if not result:
            result = app_msal.acquire_token_by_authorization_code(
                code=code,
                scopes=msal_scope
            )
        
        if "access_token" in result:
            token = result['access_token']
        else:
            raise Exception("Token de acesso não encontrado")

        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def faz_login_ms(self, driver: webdriver, url_final: str) -> str:
        """
        Handles the Microsoft login process using Selenium WebDriver.

        Parameters:
        - driver (webdriver): The Selenium WebDriver instance.
        - url_final (str): The final URL to confirm successful login.

        Returns:
        - str: The authorization code obtained after login.
        """
        while True:
            try:
                driver.find_element(By.NAME, "loginfmt").send_keys(f"{self.config_restrito['approvals']['login']}\n")
                break
            except: pass

        while True:
            try:
                driver.find_element(By.NAME, "passwd").send_keys(f"{self.config_restrito['approvals']['pass']}\n\n")
                break
            except: pass

        url_atual = driver.current_url
        while url_final not in url_atual:
            try:
                driver.find_element(By.ID, "idSIButton9").click()
            except: pass
            url_atual = driver.current_url
        
        code = url_atual.split("code=")[1]
        code = code.split("&")[0]
        
        return code

    def cria_aprovacao(self, titulo: str, descricao: str, aprovadores: list):
        """
        Creates a new approval request in Microsoft Graph API.

        Parameters:
        - titulo (str): The title of the approval request.
        - descricao (str): The description of the approval request.
        - aprovadores (list): A list of email addresses of approvers.

        Returns:
        - Response: The HTTP response from the Microsoft Graph API.
        """
        def pega_infos_email(email) -> str:
            """
            Retrieves user information from Microsoft Graph API based on email.

            Parameters:
            - email (str): The email address of the user.

            Returns:
            - dict: A dictionary containing user ID and display name.
            """
            response = requests.get(url=f"https://graph.microsoft.com/beta/users?$filter=mail eq '{email}'", headers=self.headers)
            aux = response.json()['value'][0]
            
            return {'user': {"id": aux['id'], 'displayName': aux['displayName']}}
        
        url = "https://graph.microsoft.com/beta/solutions/approval/approvalItems"
        payload = {
            "approvers": [pega_infos_email(item) for item in aprovadores if item != ''],
            "displayName": titulo,
            "description": descricao,
            "approvalType": "basic",
            "allowEmailNotification": True
        }

        response = requests.post(url, json=payload, headers=self.headers)
        return response
    
    def cria_aprovacao_sequencial(self, titulo: str, descricao: str, aprovadores: list):
        """
        Creates a sequential approval request using the Microsoft Teams interface.

        Parameters:
        - titulo (str): The title of the approval request.
        - descricao (str): The description of the approval request.
        - aprovadores (list): A list of approvers, which can be either a single email or a list of emails.

        Returns:
        - None: This method does not return a value but performs actions in the Teams interface.
        """
        chrome_options = webdriver.ChromeOptions()
        # Uncomment the following line to run the browser in headless mode.
        # chrome_options.add_argument("--headless=new")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(options=chrome_options)
        driver.get('https://teams.microsoft.com/v2/')

        self.faz_login_ms(driver, 'https://teams.microsoft.com/')

        driver.find_element(By.XPATH, "//button[contains(.,'Aprovações')]").click()  # Click on Approvals tab
        driver.switch_to.frame(0)

        driver.find_element(By.CSS_SELECTOR, "#new-approval-button").click()  # Click to create new approval
        driver.find_element(By.XPATH, "//*[@aria-label='Nome da solicitação']").send_keys(titulo)  # Enter title

        driver.find_element(By.ID, "sequential-request-toggle-button").click()  # Enable sequential requests

        for grupo in aprovadores:
            if isinstance(grupo, list):
                for pessoa in grupo:
                    nomes_input = driver.find_element(By.XPATH, "//*[@placeholder='Insira os nomes aqui']")
                    nomes_input.click()

                    nomes_input.send_keys(f"{pessoa}\t")
                    sleep(1)
                    nomes_input.send_keys("\t")
            else:
                nomes_input = driver.find_element(By.XPATH, "//*[@placeholder='Insira os nomes aqui']")
                nomes_input.click()

                nomes_input.send_keys(f"{grupo}\t")
                sleep(1)
                nomes_input.send_keys("\t")
            
            driver.find_element(By.XPATH, "//button[contains(.,'Adicionar outro destinatário')]").click()  # Add another recipient

        # Cancels the last empty recipient
        cancelar = driver.find_elements(By.XPATH, "//*[@data-icon-name='Cancel']")
        cancelar[-1].click()

        driver.find_element(By.XPATH, "//*[@aria-label='Digite detalhes adicionais para esta solicitação']").send_keys(descricao)  # Enter additional details

        driver.find_element(By.XPATH, "//*[@aria-label='Enviar']").click()  # Submit the approval request

        driver.close()

    def verifica_status(self, titulo: str) -> str:
        """
        Checks the status of an approval request by its title.

        Parameters:
        - titulo (str): The title of the approval request to check.

        Returns:
        - str: The result status of the approval request (e.g., "approved", "rejected", etc.) or None if not found.
        """
        response = requests.get(
            url="https://graph.microsoft.com/beta/solutions/approval/approvalItems",
            headers=self.headers
        )
        aprovacoes = response.json()['value']
        
        for aprov in aprovacoes:
            if titulo in aprov['displayName']:
                return aprov['result']
        
        return None  # If no approval with the given title is found

# End of class ServicoAprovacoes