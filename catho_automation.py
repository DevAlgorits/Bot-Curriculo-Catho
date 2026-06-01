import pyautogui
import time
import sys
import os

# Configuração
CONFIDENCE = 0.8  # Ajuste com base na clareza da imagem (0.0-1.0)
TIMEOUT = 10      # Máximo de segundos para aguardar um elemento
POST_CLICK_WAIT = 0.5  # Segundos para aguardar após um clique
ESC_WAIT = 0.5     # Segundos para aguardar após pressionar ESC

# Nomes dos arquivos de imagem (devem estar no mesmo diretório deste script)
IMAGES = {
    'candidatar': 'candidatar.png',
    'enviar_curriculo': 'enviar_curriculo.png',
    'pular': 'pular.png',
    'agora_nao': 'agora_nao.png',
    'resposta_obrigatorio': 'resposta_obrigatorio.png',
    'bairesdev': 'BAIRESDEV.png',
    # Para o botão adjacente após 'pular', usaremos um deslocamento ou outra imagem
    # Se você tiver uma imagem específica para o botão adjacente, adicione-a aqui:
    # 'adjacente': 'adjacente.png'
}

def find_and_click(image_key, timeout=TIMEOUT, confidence=CONFIDENCE, description=None):
    """
    Encontre uma imagem na tela e clique no seu centro.
    Retorna True se encontrado e clicado, False caso contrário.
    """
    if description is None:
        description = image_key

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            location = pyautogui.locateCenterOnScreen(
                IMAGES[image_key],
                confidence=confidence
            )
            if location:
                pyautogui.click(location)
                print(f"[{time.strftime('%H:%M:%S')}] Clicado em {description}")
                time.sleep(POST_CLICK_WAIT)
                return True
        except Exception as e:
            # Imagem não encontrada ainda, continuando aguardando
            pass
        time.sleep(0.5)  # Aguardar 500ms

    print(f"[{time.strftime('%H:%M:%S')}] Timeout: {description} não encontrado após {timeout}s")
    return False

def press_esc():
    """Pressionar a tecla ESC"""
    pyautogui.press('esc')
    print(f"[{time.strftime('%H:%M:%S')}] Tecla ESC pressionada")
    time.sleep(ESC_WAIT)

def handle_send_resume_attempt(timeout=5, description='"enviar meu currículo"'):
    """
    Tentar clicar no botão 'enviar_curriculo' e tratar qualquer resposta obrigatória.
    Retorna True se o currículo foi enviado ou a vaga foi pulada, False caso contrário.
    """
    if find_and_click('enviar_curriculo', timeout=timeout, description=description):
        # Aguardar qualquer resposta obrigatória aparecer (pelo menos 2 segundos de atraso na interação)
        time.sleep(2)
        # Verificar se a imagem de resposta obrigatória aparece
        if find_and_click('resposta_obrigatorio', timeout=1, description='resposta obrigatória', confidence=CONFIDENCE):
            # Resposta obrigatória encontrada: pressionar ESC então clicar em pular para pular a vaga
            press_esc()
            if find_and_click('pular', timeout=10, description='"pular"'):
                print("Vaga pulada devido a resposta obrigatória.")
                return True
            else:
                print("Falha ao clicar em pular após detectar resposta obrigatória.")
                return False
        else:
            # Nenhuma resposta obrigatória encontrada, prosseguir para fechar a mensagem de confirmação
            if find_and_click('agora_nao', timeout=10, description='"Agora não"'):
                print("Mensagem de confirmação fechada.")
                return True
            else:
                print("Aviso: Não foi possível fechar a mensagem de confirmação.")
                return True  # Ainda considerar como enviado mesmo se o fechamento da confirmação falhar
    else:
        return False

def main():
    print("=== Iniciando automação do Catho ===")
    print("Certifique-se de que:")
    print("1. O navegador está aberto em https://www.catho.com.br/area-candidato/")
    print("2. As imagens de referência estão na mesma pasta deste script")
    print("3. Você não moverá o mouse durante a execução\n")
    print("Pressione Ctrl+C a qualquer momento para interromper a automação.\n")

    application_count = 0
    while True:
        application_count += 1
        print(f"\n=== Processando candidatura #{application_count} ===")

        # Dar tempo para o usuário mudar para o navegador (apenas na primeira vez)
        if application_count == 1:
            print("Iniciando em 5 segundos... (mude para o navegador agora)")
            time.sleep(1)
        else:
            # Entre aplicações, aguardar um pouco
            time.sleep(1)

        # PRIMEIRA VERIFICAÇÃO: Verificar e fechar qualquer mensagem de confirmação bloqueante
        # antes de começar o fluxo normal
        find_and_click('agora_nao', timeout=1, description='fechar mensagem de confirmação')

        # VERIFICAR BAIRESDEV: Se a imagem BAIRESDEV for encontrada, pular a vaga
        if find_and_click('bairesdev', timeout=1, description='BAIRESDEV detectado'):
            print("BAIRESDEV detectado. Pulando a vaga...")
            if find_and_click('pular', timeout=10, description='"pular" após BAIRESDEV'):
                print("Vaga pulada devido a BAIRESDEV.")
                continue  # Reiniciar o processo para a próxima candidatura
            else:
                print("Falha ao clicar em pular após detectar BAIRESDEV.")
                # Ainda continuar para a próxima candidatura
                continue

        # Etapa 1: Clicar no botão 'me candidatar'
        if not find_and_click('candidatar', description='"me candidatar" rosa'):
            print("Botão 'me candidatar' não encontrado. Aguardando 10 segundos antes de tentar novamente...")
            time.sleep(10)
            continue  # Tentar novamente para encontrar o botão

        # Etapa 2: Tentar enviar o currículo diretamente
        if handle_send_resume_attempt():
            # Currículo enviado com sucesso ou vaga pulada, passa para a próxima candidatura
            continue

        # Etapa 3: Se o envio direto falhar, tratar perguntas potenciais
        print("Botão 'enviar meu currículo' não encontrado imediatamente. Verificando se há perguntas...")

        # Pressionar ESC para descartar qualquer pop-up de pergunta
        press_esc()

        # Etapa 4: Procurar pelo botão 'pular' após ESC
        if find_and_click('pular', timeout=10, description='"pular"'):
            print("Botão 'pular' clicado.")

            # Após pular, verificar novamente o botão de envio
            if handle_send_resume_attempt(timeout=15, description='"enviar meu currículo" após pular'):
                print("Currículo enviado após pular perguntas!")
                continue  # Passar para a próxima candidatura
            else:
                print("Falha: Botão 'enviar meu currículo' não apareceu após pular perguntas.")
                # Continuar para a próxima candidatura mesmo após falha
                continue
        else:
            print("Falha: Botão 'pular' não encontrado após pressionar ESC.")
            # Continuar para a próxima candidatura
            continue

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nAutomação interrompida pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        sys.exit(1)