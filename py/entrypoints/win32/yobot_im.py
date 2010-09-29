import common
common.run(
        init_args=["--no-stdio"],
        invoke_server=True,server_args=["1"],
        invoke_agent=True,agent_args=[],
        invoke_client=True,client_args=["-p", "gui_main"]
        )
