import agentbeats as ab

ab_agent = ab.BeatsAgent(__name__)

if __name__ == "__main__":
    ab_agent.load_agent_card("blue_agent/blue_agent_card.toml")
    ab_agent.run()
