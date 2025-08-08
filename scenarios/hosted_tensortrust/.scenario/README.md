# Hosted Mode

## TODOS:

+ Support user provide docker image, we run it
+ Support user provide github link, we CI build & run it
+ 













我在设计一个 agent 对抗网站，目前已经支持了 remote mode，也就是用户提供 agent link，我们进行比赛。同时，我们希望支持 hosted mode，也就是用户提供 docker image，我们负责 docker build（如果需要）以及 run 相关指令。请你设计一个 hosted mode 的规范。我会提供已有的设施以及要求，如下。

首先，我们希望 hosted mode = docker build/run + local remote run，也就是在本地 serve 需要的所有 agent，得到本地 （localhost） link 然后剩下的就和 remote run 的模式一模一样了，因为都是通过 link 交互。

其次，我们需要这个 docker 有某种意义上的 tag，方便后端服务器进行管理。暂时我们就假定 tag 的名称就是当前 folder 的名称，以后再定。你可以考虑一下这个怎么实现。

接着，如何 serve 一组 agent ？我们拿到 docker 之后他必须要支持的功能是：
```bash
# 安装 python >= 3.11
pip install agentbeats
ab load_scenario some_docker_root_folder/some_user_defined_scenario
```
这里some_docker_root_folder/some_user_defined_scenario是一个文件夹，内部包含了所有需要的 agent, tools, 以及 scenarios.toml （定义了所有需要启动的agent。实际上 ab load_scenario 就利用文件夹里的这个文件来启动所有的 agent。）
这个命令会启动所有的 agent。

例如，一个 scenario 的文件夹的结构可能是这样的
scenarios.toml
green_agent_card.toml
red_agent_card.toml
blue_agent_card.toml
green_tools/green_tool.py
其中除了 scenarios.toml 在根目录以外，其他文件的位置都不确定，需要依赖 scenarios.toml 来找到。scenarios.toml的文件内容，可能如下：

```toml
[scenario]
name = "tensortrust"
description = "TensorTrust AI security challenge scenario"
version = "1.0.0"

# Agents to be launched
[[agents]]
name = "Blue Agent"
card = "blue_agent_card.toml"
launcher_host = "0.0.0.0"
launcher_port = 9010
agent_host = "0.0.0.0"
agent_port = 9011
model_type = "openai"
model_name = "o4-mini"
tools = []
mcp_servers = []

[[agents]]
name = "Red Agent"
card = "red_agent_card.toml"
launcher_host = "0.0.0.0"
launcher_port = 9020
agent_host = "0.0.0.0"
agent_port = 9021
model_type = "openai"
model_name = "gpt-4o-mini"
tools = []
mcp_servers = []

[[agents]]
name = "Green Agent"
card = "green_agent/green_agent_card.toml"
launcher_host = "0.0.0.0"
launcher_port = 9030
agent_host = "0.0.0.0"
agent_port = 9031
model_type = "openai"
model_name = "o4-mini"
tools = ["green_agent/tools.py"]
mcp_servers = ["http://localhost:9001/sse"]
is_green = true

# Launch configuration
[launch]
mode = "separate"  # Options: "tmux", "separate", "current"
tmux_session_name = "agentbeats-tensortrust"
startup_interval = 1  # seconds between launching each component
wait_for_services = true  # wait for services to be healthy before starting agents
```

现在，请你设计一套 docker 方案，包含必要的 docker command, docker config, docker file, docker compose 方法等，并且给我一个简易的 readme 告诉我，假设服务器上有这个 docker，需要怎么运行，怎么得到返回的 agent url / launcher url 等。