# main.py
import sys
from chat import ChatCore


def main():
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
