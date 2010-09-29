#it's ok if we use sys.path.append here as this is only to satisfy py2exe
import common

common.run(invoke_server=True, server_args=["1"],
        invoke_agent=True, agent_args=[],
        invoke_client=True, client_args = "-p triviabot -p gui_main".split(),
        init_args=["--use-window"])

