import common
common.run(init_args=["--no-stdio"],
        invoke_client=True,
        client_args=["-p", "triviabot"],
        invoke_agent=True,
        invoke_server=True,
        server_args=["1"]
        )
