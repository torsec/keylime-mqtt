from keylime import keylime_logging
from keylime.models import RegistrarAgent
from keylime.web.base import Controller

logger = keylime_logging.init_logging("registrar")


class AgentsController(Controller):
    # GET /v2[.:minor]/agents/
    def index(self, **_params):
        print("Prova a vedere dove arriva il Tenant quando chiede la lista degli agenti registrati\n")
        results = RegistrarAgent.all_ids()

        self.respond(200, "Success", {"uuids": results})

    # GET /v2[.:minor]/agents/:agent_id/
    def show(self, agent_id, **_params):
        agent = RegistrarAgent.get(agent_id)

        if not agent:
            self.respond(404, f"Agent with ID '{agent_id}' not found")
            return

        if not agent.active:
            self.respond(404, f"Agent with ID '{agent_id}' has not been activated")
            return

        self.respond(200, "Success", agent.render())

    # POST /v2[.:minor]/agents/[:agent_id]
    def create(self, agent_id, **params):
        print("\nI am in the POST api. Before MakeCredential\n")
        agent = RegistrarAgent.get(agent_id) or RegistrarAgent.empty()  # type: ignore[no-untyped-call]
        agent.update({"agent_id": agent_id, **params})
#        print("ARRIVO questi sono i param dall'agent:\n")
#        print(agent)
#        print("\nQuesto e' l'uuid:\n")
#        print(agent.agent_id)

#        print("\nQuesto e' l'aik_tpm (bytestring):\n")
#        print(agent.aik_tpm)
#        print("\nQuesto e' l'aik_tpm (in hexadecimal):\n")
#        print(''.join(f'\\x{byte:02x}' for byte in agent.aik_tpm))

#        print("\nQuesto e' l'ek_tpm (bytestring):\n")
#        print(agent.ek_tpm)
#        print("\nQuesto e' l'ek_tpm (in hexadecimal):\n")
#        print(''.join(f'\\x{byte:02x}' for byte in agent.ek_tpm))

#        print("\n\n")

        challenge = agent.produce_ak_challenge()
        #print("I arrive after challenge\n")


        if not challenge or not agent.changes_valid:
            self.log_model_errors(agent, logger)
            self.respond(400, "Could not register agent with invalid data")
            return
        print("Do I arrive here?")
        agent.commit_changes()
        print("Do I arrive here?(after commit)\n")
        self.respond(200, "Success", {"blob": challenge})

    # DELETE /v2[.:minor]/agents/:agent_id/
    def delete(self, agent_id, **_params):
        agent = RegistrarAgent.get(agent_id)

        if not agent:
            self.respond(404, f"Agent with ID '{agent_id}' not found")
            return

        agent.delete()
        self.respond(200, "Success")

    # POST /v2[.:minor]/agents/:agent_id/[activate]
    def activate(self, agent_id, auth_tag, **_params):
        agent = RegistrarAgent.get(agent_id)

        print(f"\nThe agent is: {agent}\n")
        
        print(f"\nI am in Activate the auth tag is: {auth_tag}\n")

        if not agent:
            self.respond(404, f"Agent with ID '{agent_id}' not found")
            return

        accepted = agent.verify_ak_response(auth_tag)

        if accepted:
            agent.commit_changes()
            self.respond(200, "Success")
        else:
            agent.delete()

            self.respond(
                400,
                f"Auth tag '{auth_tag}' for agent '{agent_id}' does not match expected value. The agent has been "
                f"deleted from the database and will need to be restarted to reattempt registration",
            )
