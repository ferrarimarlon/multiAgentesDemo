from spade import agent
from spade.message import Message
import asyncio
from spade.behaviour import OneShotBehaviour


class MyAgent(agent.Agent):
    class enviarMensagem(OneShotBehaviour):
        async def run(self):
            try:
                reply = Message(to="jonas@profmarlon/humano")
                reply.set_metadata("performative", "inform")
                reply.set_metadata("language", "en")
                reply.body = "teste X"
                await self.send(reply)
            except:
                pass

    async def setup(self):
        print("Atendente Online")
        # Adiciona o comportamento de escuta
        enviar = self.enviarMensagem()
        self.add_behaviour(enviar)


async def main():
    # Start the agent
    my_agent = MyAgent("atendente_responder@localhost/agentic", "ate2")
    await my_agent.start()  # Await the coroutine to start the agent

    # Run the agent for a while, then stop
    await asyncio.sleep(5)  # Keep the agent running for 5 seconds
    await my_agent.stop()

if __name__ == "__main__":
    asyncio.run(main())