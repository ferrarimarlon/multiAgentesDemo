from abc import abstractmethod

from spade.behaviour import CyclicBehaviour
from spade.agent import Agent
from spade.message import Message

import asyncio
import pandas as pd

import openai


class agente_suporte(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)

    @abstractmethod
    async def processa_base(self, id_cliente):
        '''Método que executa etapas dado um id
        do cliente no atendimento
        Deve retornar a mensagem que será lida pelos
        demais agentes sobre a busca.
        '''
        pass

    class reportar_status(CyclicBehaviour):
        '''
        Classe que compõe o comportamento default dos agents
        de receberem uma mensagem e processar na base.
        '''
        async def run(self):
            # Aguarda mensagem
            msg = await self.receive(timeout=10)

            if msg:
                print(f"{msg.to} Acionado: {msg.body}")
                cliente_cadastrado = await self.agent.processa_base(msg.body)
                print(cliente_cadastrado)
                reply = Message(to=str(msg.sender))
                reply.set_metadata("performative", "inform")
                reply.set_metadata("language", "pt")
                # monta uma string para saber quem é o cliente da solicitação
                reply.body = msg.body+'-'+cliente_cadastrado
                try:
                    await self.send(reply)
                except:
                    # Reset the behavior after sending the message
                    print("Reiniciando comportamento após mensagem enviada...")
                    self.agent.remove_behaviour(self)
                    await self.agent.setup()
            else:
                print("Aguardando...")

    async def setup(self):
        print(' Iniciado...')
        # Adiciona o comportamento de escuta
        reportar = self.reportar_status()
        self.add_behaviour(reportar)


class cadastro_agente(agente_suporte):
    '''
    Checa se o usuário atual está cadastrado
    '''
    async def processa_base(self, id_cliente):
        # Load the CSV file into a DataFrame
        df = pd.read_csv('clientes_streaming.csv', sep=';')

        # Search for rows where the ID column equals 123
        result = df[df['ID'] == id_cliente]
        if not result.empty:
            result = result.to_numpy().flatten()
            return f'Usuário consta no Cadastro. Seu nome é {result[1]}'
        else:
            return f'Usuário {id_cliente} não consta no Cadastro'


class cobranca_agente(agente_suporte):
    '''
    Checa se o usuário atual está em dia e não cancelou
    '''
    async def processa_base(self, id_cliente):
        df = pd.read_csv('clientes_streaming.csv', sep=';')
        result = df[df['ID'] == id_cliente]
        if not result.empty:
            # transforma em registro
            result = result.to_numpy().flatten()
            # verifica se o plano está cancelado
            if result[3] == 'Sim':
                return 'Assinatura Cancelada'
            else:
                return 'Assinatura Ativa'
        else:
            # cadastro não foi identificado,
            # mas cabe ao agente de cadastro validar
            return ''


class qualidade_agente(agente_suporte):
    '''
    Checa a qualidade da rede do cliente
    '''
    async def processa_base(self, id_cliente):
        # identifica até qual valor
        parametros = {
            'Limite_Qualidade': range(4, 6)
        }

        df = pd.read_csv('clientes_streaming.csv', sep=';')
        result = df[df['ID'] == id_cliente]
        if not result.empty:
            # transforma em registro
            result = result.to_numpy().flatten()
            # verifica a qualidade da rede  do cliente
            print(result)
            # baseada nos parametros
            if int(result[4]) in parametros['Limite_Qualidade']:
                return 'Qualidade da Rede Adequada'
            else:
                return 'Qualidade da Rede Abaixo do Esperado'
        else:
            # cadastro não foi identificado,
            # mas cabe ao agente de cadastro validar
            return ''


class atendente_agente(agente_suporte):

    async def process_message(self, user_message, context):
        # formas simples de ler a chave openai
        with open('openai_key.txt', 'r') as file:
            api_key = file.read()
            self.gpt = openai.OpenAI(api_key=api_key)

        """Utiliza a API OpenAI para processar mensagens."""
        response = self.gpt.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": context},
                        {"role": "user", "content": user_message}
                    ]
            )

        return response.choices[0].message.content

    class interagir(CyclicBehaviour):
        async def envia_mensagem(self, sender, message):
            reply = Message(to=sender)
            reply.set_metadata("performative", "inform")
            reply.set_metadata("language", "pt")
            reply.body = message
            print(reply)
            try:
                await self.send(await super().send(reply))
            except:
                pass

        async def run(self):
            msg = await self.receive(timeout=10)  # Aguardando mensagem
            # verifica se mensagem é de cliente
            if msg:
                if 'humano' in str(msg.sender):
                    print(f"Mensagem Recebida: {msg.body}")
                    # dispara as tarefas aos agentes
                    await asyncio.gather(
                        self.envia_mensagem('cadastro@localhost/agentic',
                                            str(msg.sender)),
                        self.envia_mensagem('cobranca@localhost/agentic',
                                            str(msg.sender)),
                        self.envia_mensagem('qualidade@localhost/agentic',
                                            str(msg.sender))
                    )

                if 'agentic' in str(msg.sender):
                    # Processa a mensagem utilizando a API OpenAI
                    contexto = '''
                            O usuário receberá um retorno dos agentes
                            de acordo com o domínio:
                            1- Cadastro: se o cadastro está ativo ou não.
                            2- Cobrança: se a assinatura ainda está ativa.
                            3- Qualidade da Rede: se a qualidade da rede
                            está de acordo.
                            Responda suscintamente se a resposta do agente foi
                            de problema com o domínio.
                            Em caso de problema detectado no domínio,
                            recomende algumas destas opções:
                            1- Cadastro: realize um novo cadastro
                            na plataforma com um cartão de crédito ativo.
                            2- Cobrança: vá nas opções de assinatura e
                            reative a sua assinatura.
                            3- Qualidade da Rede: faça um teste de velocidade
                            da rede e verifique se ela é de pelo menos 100MB.
                    '''
                    # processa o body separando o cliente da mensagem
                    cliente_destino = msg.body.split('-')[0]
                    mensagem_destino = msg.body.split('-')[1]
                    # evita respostas vazias dos agentes
                    if mensagem_destino != '':
                        texto_retorno = await self.agent.process_message(
                            mensagem_destino, contexto)
                        await self.envia_mensagem(cliente_destino,
                                                  texto_retorno)
            else:
                print("Aguardando...")

    async def setup(self):
        print("Atendente Online")
        # Adiciona o comportamento de escuta
        interagir = self.interagir()
        self.add_behaviour(interagir)


async def main():
    atendente = atendente_agente('atendente@localhost/agentic', 'ate')
    await atendente.start()
    cadastro = cadastro_agente('cadastro@localhost/agentic', 'cad')
    await cadastro.start()
    cobranca = cobranca_agente('cobranca@localhost/agentic', 'cob')
    await cobranca.start()
    qualidade = qualidade_agente('qualidade@localhost/agentic', 'qua')
    await qualidade.start()

    print("Agentes iniciados. Pressione Ctrl+C para encerrar.")
    try:
        while atendente.is_alive():
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Encerrando agente...")
    await cobranca.stop()


if __name__ == "__main__":
    # Executa o loop assíncrono
    asyncio.run(main())
