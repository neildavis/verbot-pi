from verbot.server import Server as VerbotServer

def main():
    server = VerbotServer()
    server.start_server()

if __name__ == "__main__":
    # execute only if run as a script
    main()
