import common
common.run(invoke_server=True,
        server_args=["--debug=1", "--mode=daemon"],
        init_args=["--no-stdio"]
        )
