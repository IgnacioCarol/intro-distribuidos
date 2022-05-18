from src.lib.cli import CLI


def main():
    args = CLI().parse_args()

    print(
        "If you read this line it means that you have provided "
        "all the parameters which are:"
    )
    print(args)


main()
