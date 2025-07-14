# -*- coding: utf-8 -*-
"""
A implementation of a red agent that follows the specification in TensorTrust
(https://arxiv.org/abs/2311.01011)
This agent is designed to act as a prompt-injection attacker, which generates
adversarial prompts.
"""

import agentbeats as ab

ab_agent = ab.BeatsAgent(__name__)

if __name__ == "__main__":
    ab_agent.load_agent_card("agent_card.toml")
    ab_agent.run()