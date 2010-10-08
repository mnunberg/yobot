import common
common.run(
        init_args=["--no-stdio"],
        invoke_server=True,server_args=["--debug=1", "--mode=desktop"],
        invoke_agent=True,agent_args=[],
        invoke_client=True,client_args=["--plugin=gui_main"]
        )
