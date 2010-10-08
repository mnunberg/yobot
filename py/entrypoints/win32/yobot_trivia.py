import common
common.run(init_args=["--no-stdio"],
        invoke_client=True,
        client_args=["--plugin=triviabot"],
        invoke_agent=True,
        invoke_server=True,
        server_args=["--debug=1"]
        )
