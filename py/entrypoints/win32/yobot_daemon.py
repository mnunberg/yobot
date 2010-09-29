import common
common.run(invoke_server=True,
        server_args=["1", "daemon"],
        init_args=["--no-stdio"]
        )
