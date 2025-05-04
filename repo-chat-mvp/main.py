# main.py
import sys
from chat import ChatCore


def main():
    """
    Main entry point for the CLI chat application.
    
    This function initializes the ChatCore, ingests a repository provided as a
    command-line argument, and starts an interactive chat loop. The user can ask
    questions about the repository, and the bot will respond with relevant information.
    
    The function exits when the user types 'exit' or 'quit'.
    
    Args:
        None: Arguments are read from sys.argv
        
    Returns:
        None
    
    Raises:
        SystemExit: If no repository path is provided as an argument
    """
    if len(sys.argv) != 2:
        print("Usage: python main.py /path/to/local/repo")
        sys.exit(1)
    bot = ChatCore()
    print("Indexing repository… this may take a moment.")
    bot.ingest(sys.argv[1])
    print("Done. You can now chat. Type 'exit' to quit.\n")
    while True:
        q = input("You> ")
        if q.lower() in ("exit", "quit"):
            break
        print(f"\nBot> {bot.answer(q)}\n")


if __name__ == "__main__":
    main()
